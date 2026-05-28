"""G3: exact-optimality check for the capped greedy scheduler (claim C4).

The scheduler chapter claims that ``CappedSSDScheduler`` ("F" in
``paper/scheduler_design.md``) returns the *exact* optimum of the static
sum-throughput allocation problem

    maximize   sum_i mu^SSD_i(k_i)
    subject to sum_i k_i <= C,   k_i in {0, 1, 2, ...}

This is the classical separable integer resource-allocation problem. The
incremental marginal-greedy algorithm that F implements is provably optimal
*iff* every per-client service ``mu^SSD_i(.)`` is discrete-concave (its
marginal gains are non-increasing). G3 turns that proposition into a measured
fact and stress-tests its precondition:

  1. MAIN GRID. For each (N, alpha_spread, C) we run the *real*
     ``CappedSSDScheduler`` and compare its realized objective against two
     independent exact solvers:
       - a dynamic program (exact for any separable integer allocation,
         concave or not), and
       - a MILP oracle (scipy.optimize.milp / HiGHS) as a cross-check on the DP.
     We record the objective gaps and whether the allocations coincide.

  2. CONCAVITY AUDIT. For every client config on the grid we check whether the
     valid prefix of mu^SSD has non-increasing marginals -- i.e. whether the
     precondition of the optimality proposition actually holds in the calibrated
     regime.

  3. NON-CONCAVE COUNTEREXAMPLE. A small synthetic curve with an increasing
     marginal segment, on which the same greedy rule is provably suboptimal and
     the DP/MILP catch the gap. This shows the solvers are not rubber stamps and
     that the "exact-optimal" claim is genuinely conditional on concavity
     (honest-threshold item in progress_handoff.md sec 7).

mu^SSD is a throughput RATE, so this is a static single-shot allocation (large
non-binding backlog), consistent with E3b.

Run (CPU-only):
    python -m sim.experiments.g3_exact_oracle
    python -m sim.experiments.g3_exact_oracle --no-plots
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from sim.client import SimClient
from sim.scheduler import CappedSSDScheduler
from sim.experiments.e3b_capacity_pressure import (
    KSTAR_SEARCH_MAX,
    kstar_of,
    make_client_configs,
    mu_at,
)
from sim.types import ClientConfig

DEFAULT_RESULTS_DIR = Path(__file__).parent / "results" / "g3_exact_oracle"

# k candidates per client. mu_at() returns 0 for infeasible k, so an over-wide
# range is harmless: no exact solver ever prefers a zero-gain unit to idle.
K_MAX = KSTAR_SEARCH_MAX

# Objectives are O(1) sums of mu values ~ O(1); 1e-9 separates a true tie from a
# real optimality gap comfortably.
_TOL = 1.0e-9


# --------------------------------------------------------------------------- #
# Per-client mu table
# --------------------------------------------------------------------------- #
def mu_table(cfg: ClientConfig, k_max: int = K_MAX) -> list[float]:
    """[mu(0)=0, mu(1), ..., mu(k_max)] on the true calibrated curve."""
    return [0.0] + [mu_at(cfg, k) for k in range(1, k_max + 1)]


def is_discrete_concave(mus: list[float], tol: float = 1e-12) -> bool:
    """Non-increasing marginals over the valid (mu>0) contiguous prefix.

    The feasible region of mu^SSD is a contiguous block of k (drafter budget
    B(k) > 0 and fan-out >= 1); past it mu drops to 0. We test concavity on that
    valid block, which is exactly the region the greedy can allocate into before
    the peak cap stops it.
    """
    valid = [m for m in mus if m > 0.0]
    if len(valid) < 2:
        return True
    marg = [valid[i + 1] - valid[i] for i in range(len(valid) - 1)]
    return all(marg[i + 1] <= marg[i] + tol for i in range(len(marg) - 1))


# --------------------------------------------------------------------------- #
# Exact solver 1: dynamic program
# --------------------------------------------------------------------------- #
def dp_optimum(mu_tables: list[list[float]], capacity: int) -> tuple[float, list[int]]:
    """Exact max of sum_i mu_i(k_i) s.t. sum_i k_i <= capacity (k_i integer).

    f[c] = best objective achievable with total budget exactly considered up to
    the current client and <= c units spent. Standard bounded knapsack-style DP;
    exact regardless of whether the per-client curves are concave.
    """
    neg = float("-inf")
    # f[c] best objective using clients processed so far with at most c units.
    f = [0.0] * (capacity + 1)
    choice: list[list[int]] = []  # choice[i][c] = k chosen for client i at budget c
    for mus in mu_tables:
        k_hi = min(len(mus) - 1, capacity)
        new_f = [neg] * (capacity + 1)
        ch = [0] * (capacity + 1)
        for c in range(capacity + 1):
            best_val = neg
            best_k = 0
            for k in range(0, min(k_hi, c) + 1):
                prev = f[c - k]
                if prev == neg:
                    continue
                val = prev + mus[k]
                if val > best_val + 1e-15:
                    best_val = val
                    best_k = k
            new_f[c] = best_val
            ch[c] = best_k
        f = new_f
        choice.append(ch)

    # f is monotone non-decreasing in c (idle is always allowed), so the optimum
    # over "<= capacity" sits at c = capacity.
    best_obj = f[capacity]
    # Backtrack an optimal allocation.
    alloc = [0] * len(mu_tables)
    c = capacity
    for i in range(len(mu_tables) - 1, -1, -1):
        k = choice[i][c]
        alloc[i] = k
        c -= k
    return best_obj, alloc


# --------------------------------------------------------------------------- #
# Exact solver 2: MILP oracle (independent cross-check on the DP)
# --------------------------------------------------------------------------- #
def milp_optimum(mu_tables: list[list[float]], capacity: int) -> tuple[float, list[int]] | None:
    """Same problem as an assignment ILP, solved by scipy.optimize.milp (HiGHS).

    Binary x[i,k] = 1 iff client i is given lookahead k. Exactly one k per client
    (k=0 allowed = allocate nothing); total lookahead <= capacity; maximize total
    mu. Returns None if scipy/HiGHS is unavailable so the DP result still stands.
    """
    try:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
    except Exception:
        return None

    n = len(mu_tables)
    # Flatten (i, k) -> column index. Cap k by capacity (k > C can never be used).
    cols: list[tuple[int, int]] = []
    for i, mus in enumerate(mu_tables):
        for k in range(0, min(len(mus) - 1, capacity) + 1):
            cols.append((i, k))
    ncols = len(cols)

    c = np.zeros(ncols)            # minimize -objective
    a_budget = np.zeros(ncols)
    a_pick = np.zeros((n, ncols))  # one-hot per client
    for j, (i, k) in enumerate(cols):
        c[j] = -mu_tables[i][k]
        a_budget[j] = k
        a_pick[i, j] = 1.0

    constraints = [
        LinearConstraint(a_pick, lb=1, ub=1),                 # exactly one k per client
        LinearConstraint(a_budget, lb=-np.inf, ub=capacity),  # budget cap
    ]
    res = milp(
        c,
        constraints=constraints,
        integrality=np.ones(ncols),
        bounds=Bounds(0, 1),
    )
    if not res.success or res.x is None:
        return None

    alloc = [0] * n
    for j, (i, k) in enumerate(cols):
        if res.x[j] > 0.5:
            alloc[i] = k
    return float(-res.fun), alloc


# --------------------------------------------------------------------------- #
# The scheduler under test (real CappedSSDScheduler), scored on true mu^SSD
# --------------------------------------------------------------------------- #
def greedy_allocation(cfgs: list[ClientConfig], capacity: int) -> tuple[float, list[int]]:
    clients = [SimClient(cfg) for cfg in cfgs]
    alloc = CappedSSDScheduler().allocate(
        clients, total_budget=capacity, freshness_lambda=0.0, enable_freshness=False
    )
    budgets = [int(alloc.budgets.get(cfg.name, 0)) for cfg in cfgs]
    obj = sum(mu_at(cfg, k) for cfg, k in zip(cfgs, budgets))
    return obj, budgets


# --------------------------------------------------------------------------- #
# Sweep
# --------------------------------------------------------------------------- #
@dataclass
class G3Row:
    n: int
    alpha_spread: float
    capacity: int
    sum_kstar: int
    rho: float
    regime: str               # "binding" (C < sum k*) or "slack" (C >= sum k*)
    all_clients_concave: bool
    greedy_obj: float
    dp_obj: float
    milp_obj: float
    greedy_minus_dp: float    # <= 0 always if DP is the true optimum
    dp_minus_milp: float      # should be ~0: two exact solvers agree
    greedy_is_optimal: bool   # |greedy - dp| <= tol
    alloc_matches_dp: bool    # greedy allocation identical to a DP argmax
    greedy_alloc: str
    dp_alloc: str


def run_sweep(
    n_values: list[int],
    spread_values: list[float],
    extra_slack: int,
) -> list[G3Row]:
    rows: list[G3Row] = []
    for n, spread in product(n_values, spread_values):
        cfgs = make_client_configs(n, spread)
        kstars = {cfg.name: kstar_of(cfg) for cfg in cfgs}
        sum_kstar = sum(kstars.values())
        if sum_kstar <= 0:
            continue
        max_kstar = max(kstars.values())
        tables = [mu_table(cfg) for cfg in cfgs]
        all_concave = all(is_discrete_concave(t) for t in tables)

        # Sweep C from heavily binding (each client ~1 unit) up to slack
        # (sum_kstar + extra_slack), at unit granularity.
        c_lo = max(1, n)
        c_hi = sum_kstar + extra_slack
        for capacity in range(c_lo, c_hi + 1):
            g_obj, g_alloc = greedy_allocation(cfgs, capacity)
            d_obj, d_alloc = dp_optimum(tables, capacity)
            m = milp_optimum(tables, capacity)
            m_obj = m[0] if m is not None else float("nan")

            rows.append(
                G3Row(
                    n=n,
                    alpha_spread=spread,
                    capacity=capacity,
                    sum_kstar=sum_kstar,
                    rho=sum_kstar / capacity,
                    regime="slack" if capacity >= sum_kstar else "binding",
                    all_clients_concave=all_concave,
                    greedy_obj=g_obj,
                    dp_obj=d_obj,
                    milp_obj=m_obj,
                    greedy_minus_dp=g_obj - d_obj,
                    dp_minus_milp=(d_obj - m_obj) if m is not None else float("nan"),
                    greedy_is_optimal=abs(g_obj - d_obj) <= _TOL,
                    alloc_matches_dp=(g_alloc == d_alloc),
                    greedy_alloc="|".join(str(x) for x in g_alloc),
                    dp_alloc="|".join(str(x) for x in d_alloc),
                )
            )
    return rows


# --------------------------------------------------------------------------- #
# Non-concave counterexample (shows the solvers detect a real greedy gap)
# --------------------------------------------------------------------------- #
@dataclass
class Counterexample:
    description: str
    mu_tables: list[list[float]]
    capacity: int
    greedy_obj: float
    greedy_alloc: list[int]
    dp_obj: float
    dp_alloc: list[int]
    milp_obj: float
    greedy_is_optimal: bool


def _greedy_on_tables(mu_tables: list[list[float]], capacity: int) -> tuple[float, list[int]]:
    """Replicates CappedSSDScheduler's incremental marginal rule on raw mu
    tables (peak cap = stop when best available marginal <= 0). Used only for the
    synthetic counterexample, where we cannot route an arbitrary curve through
    SimClient/ssd_service.
    """
    alloc = [0] * len(mu_tables)
    for _ in range(capacity):
        best_i, best_gain = -1, 0.0
        for i, mus in enumerate(mu_tables):
            nxt = alloc[i] + 1
            if nxt >= len(mus):
                continue
            gain = mus[nxt] - mus[alloc[i]]
            if gain > best_gain:
                best_gain = gain
                best_i = i
        if best_i < 0 or best_gain <= 0.0:  # peak cap
            break
        alloc[best_i] += 1
    obj = sum(mus[alloc[i]] for i, mus in enumerate(mu_tables))
    return obj, alloc


def non_concave_counterexample() -> Counterexample:
    # Two clients sharing C = 3 units.
    #   A: 0, 1.00, 1.10, 1.90, 1.95   marginals 1.00, 0.10, 0.80, 0.05
    #      -> NOT discrete-concave: the +0.80 step (2->3) exceeds the +0.10
    #         step (1->2) before it; mu^SSD's true marginals never do this.
    #   B: 0, 0.50, 0.60, 0.65, 0.68   marginals 0.50, 0.10, 0.05, 0.03 (concave).
    #
    # Incremental greedy (CappedSSD's rule):
    #   step1  A 0->1 (+1.00) wins   -> A=1
    #   step2  B 0->1 (+0.50) wins   -> B=1
    #   step3  A 1->2 (+0.10) ties B 1->2 (+0.10), A taken -> A=2
    #   greedy obj = 1.10 + 0.50 = 1.60, alloc [2, 1].
    # Exact optimum:  A=3, B=0 -> 1.90, alloc [3, 0].
    #   Greedy is trapped by A's 0.10 dip and never reaches A's buried 0.80 step;
    #   the DP/MILP look across the dip. Gap = 0.30 (~16%).
    a = [0.0, 1.00, 1.10, 1.90, 1.95]
    b = [0.0, 0.50, 0.60, 0.65, 0.68]
    cap = 3
    g_obj, g_alloc = _greedy_on_tables([a, b], cap)
    d_obj, d_alloc = dp_optimum([a, b], cap)
    m = milp_optimum([a, b], cap)
    return Counterexample(
        description=(
            "2 clients, C=3. Client A is unimodal but NOT discrete-concave "
            "(marginals 1.00, 0.10, 0.80, 0.05 -- the 0.80 step is larger than "
            "the 0.10 before it). Greedy follows the early small marginals and "
            "strands client A in the dip; the DP/MILP reach across it."
        ),
        mu_tables=[a, b],
        capacity=cap,
        greedy_obj=g_obj,
        greedy_alloc=g_alloc,
        dp_obj=d_obj,
        dp_alloc=d_alloc,
        milp_obj=(m[0] if m else float("nan")),
        greedy_is_optimal=abs(g_obj - d_obj) <= _TOL,
    )


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_csv(rows: list[G3Row], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "g3_exact_oracle.csv"
    fieldnames = list(G3Row.__dataclass_fields__.keys())
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: getattr(row, name) for name in fieldnames})
    return csv_path


def make_plots(rows: list[G3Row], out_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)

    # Single diagnostic: greedy objective vs DP optimum across all grid points,
    # colored by regime. Points on the diagonal => greedy is exactly optimal.
    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    binding = [r for r in rows if r.regime == "binding"]
    slack = [r for r in rows if r.regime == "slack"]
    ax.scatter(
        [r.dp_obj for r in binding], [r.greedy_obj for r in binding],
        s=42, marker="o", facecolors="none", edgecolors="tab:red", label="binding (C < sum k*)",
    )
    ax.scatter(
        [r.dp_obj for r in slack], [r.greedy_obj for r in slack],
        s=28, marker="x", color="tab:blue", label="slack (C >= sum k*)",
    )
    lo = min([r.dp_obj for r in rows] + [r.greedy_obj for r in rows])
    hi = max([r.dp_obj for r in rows] + [r.greedy_obj for r in rows])
    ax.plot([lo, hi], [lo, hi], color="grey", lw=1.0, ls="--", label="greedy = optimum")
    ax.set_xlabel("DP / MILP exact optimum  (sum mu^SSD)")
    ax.set_ylabel("CappedSSD greedy (F) objective")
    ax.set_title("G3: capped greedy = exact optimum (calibrated curve)")
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    p1 = out_dir / "g3_greedy_vs_optimum.png"
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    return [p1]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _int_list(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(",", " ").split()]


def _float_list(raw: str) -> list[float]:
    return [float(x) for x in raw.replace(",", " ").split()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="G3 exact-optimality check: CappedSSD greedy vs DP + MILP oracle."
    )
    parser.add_argument("--n-values", type=_int_list, default=[2, 3, 5, 8])
    parser.add_argument("--alpha-spreads", type=_float_list, default=[0.0, 0.1, 0.18])
    parser.add_argument(
        "--extra-slack", type=int, default=4,
        help="Sweep C up to sum_kstar + this many units (to cover the slack regime).",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--no-plots", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    rows = run_sweep(args.n_values, args.alpha_spreads, args.extra_slack)
    csv_path = write_csv(rows, args.out_dir)
    print(f"[g3] wrote {len(rows)} rows -> {csv_path}")

    # Headline 1: did greedy ever miss the exact optimum?
    n_total = len(rows)
    n_opt = sum(1 for r in rows if r.greedy_is_optimal)
    worst_gap = min((r.greedy_minus_dp for r in rows), default=0.0)
    n_binding = sum(1 for r in rows if r.regime == "binding")
    print(
        f"[g3] greedy optimal on {n_opt}/{n_total} grid points "
        f"({n_binding} of them in the binding regime); "
        f"worst greedy-minus-DP gap = {worst_gap:.3e}"
    )

    # Headline 2: do the two exact solvers agree?
    milp_rows = [r for r in rows if math.isfinite(r.dp_minus_milp)]
    if milp_rows:
        worst_dp_milp = max(abs(r.dp_minus_milp) for r in milp_rows)
        print(
            f"[g3] DP vs MILP agree on {len(milp_rows)}/{n_total} points; "
            f"max |DP - MILP| = {worst_dp_milp:.3e}"
        )
    else:
        print("[g3] MILP oracle unavailable (scipy.optimize.milp not importable); DP-only.")

    # Headline 3: concavity precondition.
    n_concave = sum(1 for r in rows if r.all_clients_concave)
    print(f"[g3] discrete-concave precondition holds on {n_concave}/{n_total} grid points.")

    # Headline 4: synthetic non-concave counterexample.
    ce = non_concave_counterexample()
    print(
        f"[g3] non-concave counterexample: greedy={ce.greedy_obj:.3f} "
        f"alloc={ce.greedy_alloc} vs optimum={ce.dp_obj:.3f} alloc={ce.dp_alloc} "
        f"(MILP={ce.milp_obj:.3f}); greedy_optimal={ce.greedy_is_optimal}"
    )

    if not args.no_plots:
        try:
            for p in make_plots(rows, args.out_dir):
                print(f"[g3] wrote plot -> {p}")
        except Exception as exc:
            print(f"[g3] plotting skipped ({type(exc).__name__}: {exc})")


if __name__ == "__main__":
    main()
