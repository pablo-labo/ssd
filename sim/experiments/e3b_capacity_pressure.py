"""E3b: capacity-pressure sweep (static single-shot allocation).

Punchline experiment for the scheduler chapter. Holds a set of clients fixed and
sweeps the verifier capacity C so that the capacity-pressure ratio

    rho = sum_i k_i*  /  C

moves from the slack regime (rho < 1, spare capacity) through the binding regime
(rho > 1, contended). At each operating point we run three schedulers on the SAME
calibrated unimodal service mu^SSD and measure *realized* throughput on the true
curve:

  * capped_ssd  (F)  -- marginal greedy + peak cap; refuses to push a client past
                        its interior optimum k_i*, leaving spare budget idle.
  * ssd_greedy       -- same curve, cap removed; forced to spend the full budget,
                        so it overcommits past the peak.
  * goodspeed   (E)  -- greedy on the monotone mu^GS = e_hit; allocates as if more
                        lookahead is always better, then we score that allocation
                        on the real mu^SSD.

This isolates two effects separately:
  - capped_ssd vs ssd_greedy  -> the cap alone (identical service curve).
  - capped_ssd vs goodspeed   -> the monotone-service modelling error.

mu^SSD is a throughput RATE (per sim.policy.ssd_service), so this is a static
allocation experiment with large, non-binding backlog -- not the backlog-queueing
dynamics used by the monotone modes. Primary objective is sum-throughput;
proportional-fairness (sum log mu) is reported as a secondary column.

Run (CPU-only):
    python -m sim.experiments.e3b_capacity_pressure
    python -m sim.experiments.e3b_capacity_pressure --no-plots
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from sim.client import SimClient
from sim.scheduler import CappedSSDScheduler, GoodSpeedScheduler, SSDGreedyScheduler
from sim.ssd_math import Block1Params, curve_point, curve_summary
from sim.types import ClientConfig


DEFAULT_RESULTS_DIR = Path(__file__).parent / "results" / "e3b_capacity_pressure"

# Alpaca / Qwen3-8B+0.6B calibration anchor (see paper/scheduler_design.md).
ALPHA_CENTER = 0.735
SSD_R = 0.6
SSD_A = 2.628523
SSD_B = 0.0038445
SSD_T_V = 20.0
NON_BINDING_BACKLOG = 1.0e6
KSTAR_SEARCH_MAX = 12

_EPS = 1.0e-9


# --------------------------------------------------------------------------- #
# Client construction and per-client mu^SSD helpers
# --------------------------------------------------------------------------- #
def _clamp_alpha(alpha: float) -> float:
    return min(max(alpha, 1.0e-6), 1.0 - 1.0e-6)


def make_client_configs(n: int, alpha_spread: float) -> list[ClientConfig]:
    """N clients spread symmetrically in alpha around ALPHA_CENTER.

    alpha_spread is the half-width: alphas span [center - spread, center + spread].
    Only base_acceptance (= alpha) varies; r/a/b/t_v are shared (model/hardware
    level), matching the block3 convention that b varies per client only when a b
    scan is requested.
    """
    if n <= 0:
        raise ValueError("n must be >= 1")
    if n == 1:
        alphas = [ALPHA_CENTER]
    else:
        lo = ALPHA_CENTER - alpha_spread
        hi = ALPHA_CENTER + alpha_spread
        step = (hi - lo) / (n - 1)
        alphas = [lo + step * i for i in range(n)]

    configs = []
    for i, alpha in enumerate(alphas):
        configs.append(
            ClientConfig(
                name=f"c{i}",
                arrival_rate=1,
                base_acceptance=_clamp_alpha(alpha),
                frontier_quality=0.5,
                expansion_policy="linear",
                initial_backlog=NON_BINDING_BACKLOG,
                ssd_r=SSD_R,
                ssd_a=SSD_A,
                ssd_b=SSD_B,
                ssd_t_v=SSD_T_V,
            )
        )
    return configs


def _params_of(cfg: ClientConfig) -> Block1Params:
    return Block1Params(
        alpha=_clamp_alpha(cfg.base_acceptance),
        r=cfg.ssd_r,
        a=cfg.ssd_a,
        b=cfg.ssd_b,
        t_v=cfg.ssd_t_v,
    )


def mu_at(cfg: ClientConfig, k: int) -> float:
    """Realized true-curve throughput mu^SSD(k) for one client (0 if infeasible)."""
    if k <= 0:
        return 0.0
    point = curve_point(int(k), _params_of(cfg))
    return float(point.mu) if point.valid else 0.0


def kstar_of(cfg: ClientConfig, k_max: int = KSTAR_SEARCH_MAX) -> int:
    """Interior optimum k* = argmax_k mu^SSD(k) for one client."""
    points = [curve_point(k, _params_of(cfg)) for k in range(1, k_max + 1)]
    summary = curve_summary(points)
    best_k = int(summary["best_k"])
    return best_k if best_k > 0 else 0


# --------------------------------------------------------------------------- #
# Scheduler evaluation
# --------------------------------------------------------------------------- #
@dataclass
class AllocationMetrics:
    sum_mu: float          # realized total throughput on true mu^SSD (primary)
    total_k: int           # total lookahead actually allocated
    idle: int              # C - total_k (capacity deliberately left unspent)
    overcommit: int        # sum_i max(0, k_i - k_i*) (units pushed past the peak)
    pf: float              # sum_i log(mu_i) (proportional fairness, secondary)


def evaluate_allocation(
    cfgs: list[ClientConfig],
    budgets: dict[str, int],
    kstars: dict[str, int],
    capacity: int,
) -> AllocationMetrics:
    sum_mu = 0.0
    total_k = 0
    overcommit = 0
    pf = 0.0
    for cfg in cfgs:
        k = int(budgets.get(cfg.name, 0))
        mu = mu_at(cfg, k)
        sum_mu += mu
        total_k += k
        overcommit += max(0, k - kstars[cfg.name])
        pf += math.log(max(mu, _EPS))
    return AllocationMetrics(
        sum_mu=sum_mu,
        total_k=total_k,
        idle=capacity - total_k,
        overcommit=overcommit,
        pf=pf,
    )


def run_one_point(
    cfgs: list[ClientConfig],
    capacity: int,
    kstars: dict[str, int],
) -> dict[str, AllocationMetrics]:
    """Run all three schedulers at one capacity and score each on true mu^SSD.

    allocate() only reads client service (it never mutates client state), so a
    single SimClient list is safely reused across the three schedulers.
    """
    clients = [SimClient(cfg) for cfg in cfgs]
    schedulers = {
        "capped_ssd": CappedSSDScheduler(),
        "ssd_greedy": SSDGreedyScheduler(),
        "goodspeed": GoodSpeedScheduler(),
    }
    out: dict[str, AllocationMetrics] = {}
    for label, sched in schedulers.items():
        alloc = sched.allocate(
            clients,
            total_budget=capacity,
            freshness_lambda=0.0,
            enable_freshness=False,
        )
        out[label] = evaluate_allocation(cfgs, alloc.budgets, kstars, capacity)
    return out


# --------------------------------------------------------------------------- #
# Sweep
# --------------------------------------------------------------------------- #
@dataclass
class SweepRow:
    n: int
    alpha_spread: float
    capacity: int
    sum_kstar: int
    rho: float
    capped_sum_mu: float
    capped_total_k: int
    capped_idle: int
    capped_overcommit: int
    capped_pf: float
    greedy_sum_mu: float
    greedy_total_k: int
    greedy_idle: int
    greedy_overcommit: int
    greedy_pf: float
    gs_sum_mu: float
    gs_total_k: int
    gs_idle: int
    gs_overcommit: int
    gs_pf: float
    gap_capped_vs_greedy_pct: float
    gap_capped_vs_gs_pct: float


def _pct_gain(winner: float, baseline: float) -> float:
    if baseline <= _EPS:
        return float("nan")
    return 100.0 * (winner - baseline) / baseline


def run_sweep(
    n_values: list[int],
    spread_values: list[float],
    rho_grid: list[float],
) -> list[SweepRow]:
    rows: list[SweepRow] = []
    for n, spread in product(n_values, spread_values):
        cfgs = make_client_configs(n, spread)
        kstars = {cfg.name: kstar_of(cfg) for cfg in cfgs}
        sum_kstar = sum(kstars.values())
        if sum_kstar <= 0:
            continue

        # Translate target rho into an integer capacity C = round(sum_kstar / rho).
        capacities = sorted(
            {max(1, round(sum_kstar / rho)) for rho in rho_grid}
        )
        for capacity in capacities:
            rho = sum_kstar / capacity
            res = run_one_point(cfgs, capacity, kstars)
            cap = res["capped_ssd"]
            gre = res["ssd_greedy"]
            gs = res["goodspeed"]
            rows.append(
                SweepRow(
                    n=n,
                    alpha_spread=spread,
                    capacity=capacity,
                    sum_kstar=sum_kstar,
                    rho=rho,
                    capped_sum_mu=cap.sum_mu,
                    capped_total_k=cap.total_k,
                    capped_idle=cap.idle,
                    capped_overcommit=cap.overcommit,
                    capped_pf=cap.pf,
                    greedy_sum_mu=gre.sum_mu,
                    greedy_total_k=gre.total_k,
                    greedy_idle=gre.idle,
                    greedy_overcommit=gre.overcommit,
                    greedy_pf=gre.pf,
                    gs_sum_mu=gs.sum_mu,
                    gs_total_k=gs.total_k,
                    gs_idle=gs.idle,
                    gs_overcommit=gs.overcommit,
                    gs_pf=gs.pf,
                    gap_capped_vs_greedy_pct=_pct_gain(cap.sum_mu, gre.sum_mu),
                    gap_capped_vs_gs_pct=_pct_gain(cap.sum_mu, gs.sum_mu),
                )
            )
    return rows


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_csv(rows: list[SweepRow], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "e3b_capacity_pressure.csv"
    fieldnames = list(SweepRow.__dataclass_fields__.keys())
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: getattr(row, name) for name in fieldnames})
    return csv_path


def make_plots(rows: list[SweepRow], out_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    groups = sorted({(r.n, r.alpha_spread) for r in rows})
    ncols = len({g[0] for g in groups}) or 1
    nrows = len({g[1] for g in groups}) or 1

    fig, axes = plt.subplots(
        nrows, ncols, figsize=(5.0 * ncols, 3.6 * nrows), squeeze=False, sharex=True
    )
    n_index = {n: j for j, n in enumerate(sorted({g[0] for g in groups}))}
    s_index = {s: i for i, s in enumerate(sorted({g[1] for g in groups}))}

    for (n, spread) in groups:
        ax = axes[s_index[spread]][n_index[n]]
        sub = sorted([r for r in rows if r.n == n and r.alpha_spread == spread], key=lambda r: r.rho)
        rho = [r.rho for r in sub]
        ax.plot(rho, [r.capped_sum_mu for r in sub], "o-", label="capped_ssd (F)")
        ax.plot(rho, [r.greedy_sum_mu for r in sub], "s--", label="ssd_greedy")
        ax.plot(rho, [r.gs_sum_mu for r in sub], "^:", label="goodspeed")
        ax.axvline(1.0, color="grey", lw=0.8, ls=":")
        ax.set_title(f"N={n}, alpha_spread={spread:g}")
        ax.set_xlabel("rho = sum(k*) / C")
        ax.set_ylabel("realized sum mu^SSD")
        ax.grid(alpha=0.25)
    axes[0][0].legend(fontsize=8, loc="best")
    fig.suptitle("E3b: realized throughput vs capacity pressure (slack -> binding)")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    p1 = out_dir / "e3b_throughput_vs_rho.png"
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    paths.append(p1)

    # Overcommit panel: how many units each scheduler pushes past the peak.
    fig2, axes2 = plt.subplots(
        nrows, ncols, figsize=(5.0 * ncols, 3.6 * nrows), squeeze=False, sharex=True
    )
    for (n, spread) in groups:
        ax = axes2[s_index[spread]][n_index[n]]
        sub = sorted([r for r in rows if r.n == n and r.alpha_spread == spread], key=lambda r: r.rho)
        rho = [r.rho for r in sub]
        ax.plot(rho, [r.capped_overcommit for r in sub], "o-", label="capped_ssd (F)")
        ax.plot(rho, [r.greedy_overcommit for r in sub], "s--", label="ssd_greedy")
        ax.plot(rho, [r.gs_overcommit for r in sub], "^:", label="goodspeed")
        ax.axvline(1.0, color="grey", lw=0.8, ls=":")
        ax.set_title(f"N={n}, alpha_spread={spread:g}")
        ax.set_xlabel("rho = sum(k*) / C")
        ax.set_ylabel("overcommit units (sum max(0, k-k*))")
        ax.grid(alpha=0.25)
    axes2[0][0].legend(fontsize=8, loc="best")
    fig2.suptitle("E3b: overcommit past peak vs capacity pressure")
    fig2.tight_layout(rect=(0, 0, 1, 0.97))
    p2 = out_dir / "e3b_overcommit_vs_rho.png"
    fig2.savefig(p2, dpi=150)
    plt.close(fig2)
    paths.append(p2)

    return paths


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _int_list(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(",", " ").split()]


def _float_list(raw: str) -> list[float]:
    return [float(x) for x in raw.replace(",", " ").split()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="E3b capacity-pressure sweep: capped_ssd vs ssd_greedy vs goodspeed on mu^SSD."
    )
    parser.add_argument("--n-values", type=_int_list, default=[2, 3, 5])
    parser.add_argument("--alpha-spreads", type=_float_list, default=[0.0, 0.1, 0.18])
    parser.add_argument(
        "--rho-grid",
        type=_float_list,
        default=[0.5, 0.667, 0.8, 1.0, 1.25, 1.5, 2.0],
        help="Target capacity-pressure ratios; each maps to C = round(sum_kstar / rho).",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--no-plots", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    rows = run_sweep(args.n_values, args.alpha_spreads, args.rho_grid)
    csv_path = write_csv(rows, args.out_dir)
    print(f"[e3b] wrote {len(rows)} rows -> {csv_path}")

    # Headline: largest capped_ssd win over goodspeed in the slack regime.
    slack = [r for r in rows if r.rho <= 1.0 and math.isfinite(r.gap_capped_vs_gs_pct)]
    if slack:
        best = max(slack, key=lambda r: r.gap_capped_vs_gs_pct)
        print(
            f"[e3b] slack headline: N={best.n} spread={best.alpha_spread:g} "
            f"rho={best.rho:.2f} C={best.capacity} | "
            f"capped sum_mu={best.capped_sum_mu:.3f} (idle={best.capped_idle}) "
            f"vs goodspeed {best.gs_sum_mu:.3f} -> +{best.gap_capped_vs_gs_pct:.1f}% | "
            f"vs ssd_greedy {best.greedy_sum_mu:.3f} -> "
            f"{best.gap_capped_vs_greedy_pct:+.1f}%"
        )

    if not args.no_plots:
        try:
            plot_paths = make_plots(rows, args.out_dir)
            for p in plot_paths:
                print(f"[e3b] wrote plot -> {p}")
        except Exception as exc:  # headless / no matplotlib: keep the CSV usable
            print(f"[e3b] plotting skipped ({type(exc).__name__}: {exc})")


if __name__ == "__main__":
    main()
