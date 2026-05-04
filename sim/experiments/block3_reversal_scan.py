from __future__ import annotations

import argparse
import csv
import math
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

from sim.ssd_math import e_hit, fanouts, mu_ssd_from_parts, phit_primary


DEFAULT_RESULTS_DIR = Path(__file__).parent / "results" / "block3_reversal"


@dataclass(frozen=True)
class ClientParams:
    alpha: float
    r: float
    a: float
    b: float


@dataclass(frozen=True)
class AllocationResult:
    k1: int
    k2: int
    utility: float
    mu1: float
    mu2: float
    budget1: float
    budget2: float
    valid: bool
    invalid_reason: str = ""


@dataclass(frozen=True)
class ScanRow:
    alpha1: float
    alpha2: float
    r1: float
    r2: float
    a1: float
    a2: float
    b1: float
    b2: float
    capacity: int
    t_v_base: float
    t_v_slope: float
    continuous_budget: bool
    k1_gs: int
    k2_gs: int
    k1_ssd: int
    k2_ssd: int
    gs_utility_gs_model: float
    gs_utility_ssd_model: float
    ssd_utility: float
    utility_gap_abs: float
    utility_gap_pct: float
    gs_mu1_ssd_model: float
    gs_mu2_ssd_model: float
    ssd_mu1: float
    ssd_mu2: float
    gs_budget1_ssd_model: float
    gs_budget2_ssd_model: float
    ssd_budget1: float
    ssd_budget2: float
    gs_order: int
    ssd_order: int
    reversal: bool
    valid: bool
    invalid_reason: str


def _float_list(raw: str) -> list[float]:
    return [float(item) for item in raw.replace(",", " ").split()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan the Block 3 two-client GoodSpeed-vs-SSD allocation reversal region."
    )
    parser.add_argument("--alphas", default="0.50 0.55 0.60 0.65 0.70 0.75 0.80 0.85 0.90 0.95")
    parser.add_argument("--rs", default="0.8")
    parser.add_argument("--as", dest="a_values", default="0.1")
    parser.add_argument("--bs", dest="b_values", default="0.01 0.02 0.05 0.1")
    parser.add_argument("--capacity", type=int, default=10)
    parser.add_argument("--min-k", type=int, default=1)
    parser.add_argument("--t-v-base", type=float, default=10.0)
    parser.add_argument("--t-v-slope", type=float, default=1.0)
    parser.add_argument("--t-b", type=float, default=1.0)
    parser.add_argument("--e-miss", type=float, default=1.0)
    parser.add_argument("--l-hit", type=float, default=1.0)
    parser.add_argument("--allow-fractional-fanout", action="store_true")
    parser.add_argument(
        "--continuous-budget",
        action="store_true",
        help="Use the relaxed continuous B_i instead of the roadmap floor_+ drafter budget.",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--no-plots", action="store_true")
    return parser


def goodspeed_mu(k: int, alpha: float) -> float:
    if k <= 0 or not 0.0 < alpha < 1.0:
        return float("nan")
    return (1.0 - alpha ** (k + 1)) / (1.0 - alpha)


def verifier_time(k1: int, k2: int, t_v_base: float, t_v_slope: float) -> float:
    return t_v_base + t_v_slope * (k1 + k2)


def ssd_budget(
    k_i: int,
    other_k: int,
    params: ClientParams,
    t_v_base: float,
    t_v_slope: float,
    continuous_budget: bool,
) -> float:
    t_v = verifier_time(k_i, other_k, t_v_base, t_v_slope)
    relaxed_budget = (t_v - params.a * k_i) / (params.b * k_i)
    if continuous_budget:
        return relaxed_budget
    if not math.isfinite(relaxed_budget):
        return float("nan")
    return float(max(0, math.floor(relaxed_budget)))


def ssd_mu(
    k_i: int,
    other_k: int,
    params: ClientParams,
    t_v_base: float,
    t_v_slope: float,
    t_b: float,
    e_miss: float,
    l_hit: float,
    require_integer_fanout: bool,
    continuous_budget: bool,
) -> tuple[float, float, str]:
    budget = ssd_budget(k_i, other_k, params, t_v_base, t_v_slope, continuous_budget)
    if not math.isfinite(budget) or budget <= 0.0:
        return float("nan"), budget, "budget"

    if require_integer_fanout:
        fanout_values = fanouts(k_i, budget, params.alpha, params.r)
        if not fanout_values.size or float(fanout_values.min()) < 1.0:
            return float("nan"), budget, "fanout"

    phit = phit_primary(k_i, budget, params.alpha, params.r)
    if not math.isfinite(phit) or phit < -1e-9 or phit > 1.0 + 1e-9:
        return float("nan"), budget, "phit"

    phit = min(1.0, max(0.0, phit))
    value = mu_ssd_from_parts(
        phit=phit,
        e_hit_value=e_hit(k_i, params.alpha),
        e_miss=e_miss,
        l_hit=l_hit,
        l_miss=l_hit + t_b,
    )
    if not math.isfinite(value) or value <= 0.0:
        return float("nan"), budget, "mu"

    return value, budget, ""


def _utility(mu1: float, mu2: float) -> float:
    if not math.isfinite(mu1) or not math.isfinite(mu2) or mu1 <= 0.0 or mu2 <= 0.0:
        return float("-inf")
    return math.log(mu1) + math.log(mu2)


def _candidate_allocations(min_k: int, capacity: int) -> list[tuple[int, int]]:
    candidates = []
    for k1 in range(min_k, capacity + 1):
        for k2 in range(min_k, capacity + 1):
            if k1 + k2 <= capacity:
                candidates.append((k1, k2))
    return candidates


def optimize_goodspeed(
    client1: ClientParams,
    client2: ClientParams,
    candidates: list[tuple[int, int]],
) -> AllocationResult:
    best: AllocationResult | None = None
    for k1, k2 in candidates:
        mu1 = goodspeed_mu(k1, client1.alpha)
        mu2 = goodspeed_mu(k2, client2.alpha)
        utility = _utility(mu1, mu2)
        if best is None or (utility, k1 + k2, -abs(k1 - k2), -k1) > (
            best.utility,
            best.k1 + best.k2,
            -abs(best.k1 - best.k2),
            -best.k1,
        ):
            best = AllocationResult(k1, k2, utility, mu1, mu2, float("nan"), float("nan"), True)

    if best is None:
        return AllocationResult(-1, -1, float("-inf"), float("nan"), float("nan"), float("nan"), float("nan"), False, "no_candidates")
    return best


def evaluate_ssd_allocation(
    client1: ClientParams,
    client2: ClientParams,
    k1: int,
    k2: int,
    t_v_base: float,
    t_v_slope: float,
    t_b: float,
    e_miss: float,
    l_hit: float,
    require_integer_fanout: bool,
    continuous_budget: bool,
) -> AllocationResult:
    mu1, budget1, reason1 = ssd_mu(
        k1,
        k2,
        client1,
        t_v_base,
        t_v_slope,
        t_b,
        e_miss,
        l_hit,
        require_integer_fanout,
        continuous_budget,
    )
    mu2, budget2, reason2 = ssd_mu(
        k2,
        k1,
        client2,
        t_v_base,
        t_v_slope,
        t_b,
        e_miss,
        l_hit,
        require_integer_fanout,
        continuous_budget,
    )
    utility = _utility(mu1, mu2)
    valid = math.isfinite(utility)
    reasons = ",".join(reason for reason in (reason1, reason2) if reason)
    return AllocationResult(k1, k2, utility, mu1, mu2, budget1, budget2, valid, reasons)


def optimize_ssd(
    client1: ClientParams,
    client2: ClientParams,
    candidates: list[tuple[int, int]],
    t_v_base: float,
    t_v_slope: float,
    t_b: float,
    e_miss: float,
    l_hit: float,
    require_integer_fanout: bool,
    continuous_budget: bool,
) -> AllocationResult:
    best: AllocationResult | None = None
    for k1, k2 in candidates:
        result = evaluate_ssd_allocation(
            client1,
            client2,
            k1,
            k2,
            t_v_base,
            t_v_slope,
            t_b,
            e_miss,
            l_hit,
            require_integer_fanout,
            continuous_budget,
        )
        if not result.valid:
            continue
        if best is None or (result.utility, -(k1 + k2), -abs(k1 - k2), -k1) > (
            best.utility,
            -(best.k1 + best.k2),
            -abs(best.k1 - best.k2),
            -best.k1,
        ):
            best = result

    if best is None:
        return AllocationResult(-1, -1, float("-inf"), float("nan"), float("nan"), float("nan"), float("nan"), False, "no_valid_ssd")
    return best


def _order(k1: int, k2: int) -> int:
    return (k1 > k2) - (k1 < k2)


def _scan(args: argparse.Namespace) -> list[ScanRow]:
    alphas = _float_list(args.alphas)
    rs = _float_list(args.rs)
    a_values = _float_list(args.a_values)
    b_values = _float_list(args.b_values)
    candidates = _candidate_allocations(args.min_k, args.capacity)
    require_integer_fanout = not args.allow_fractional_fanout
    rows: list[ScanRow] = []

    for alpha1, alpha2, r1, r2, a1, a2, b1, b2 in product(
        alphas,
        alphas,
        rs,
        rs,
        a_values,
        a_values,
        b_values,
        b_values,
    ):
        client1 = ClientParams(alpha=alpha1, r=r1, a=a1, b=b1)
        client2 = ClientParams(alpha=alpha2, r=r2, a=a2, b=b2)
        gs = optimize_goodspeed(client1, client2, candidates)
        gs_under_ssd = evaluate_ssd_allocation(
            client1,
            client2,
            gs.k1,
            gs.k2,
            args.t_v_base,
            args.t_v_slope,
            args.t_b,
            args.e_miss,
            args.l_hit,
            require_integer_fanout,
            args.continuous_budget,
        )
        ssd = optimize_ssd(
            client1,
            client2,
            candidates,
            args.t_v_base,
            args.t_v_slope,
            args.t_b,
            args.e_miss,
            args.l_hit,
            require_integer_fanout,
            args.continuous_budget,
        )

        valid = gs.valid and gs_under_ssd.valid and ssd.valid
        gs_order = _order(gs.k1, gs.k2)
        ssd_order = _order(ssd.k1, ssd.k2)
        reversal = valid and gs_order != 0 and ssd_order != 0 and gs_order != ssd_order
        utility_gap_abs = ssd.utility - gs_under_ssd.utility if valid else float("nan")
        utility_gap_pct = math.expm1(utility_gap_abs / 2.0) if valid else float("nan")
        invalid_reason = ",".join(
            reason
            for reason in (gs.invalid_reason, gs_under_ssd.invalid_reason, ssd.invalid_reason)
            if reason
        )

        rows.append(
            ScanRow(
                alpha1=alpha1,
                alpha2=alpha2,
                r1=r1,
                r2=r2,
                a1=a1,
                a2=a2,
                b1=b1,
                b2=b2,
                capacity=args.capacity,
                t_v_base=args.t_v_base,
                t_v_slope=args.t_v_slope,
                continuous_budget=args.continuous_budget,
                k1_gs=gs.k1,
                k2_gs=gs.k2,
                k1_ssd=ssd.k1,
                k2_ssd=ssd.k2,
                gs_utility_gs_model=gs.utility,
                gs_utility_ssd_model=gs_under_ssd.utility,
                ssd_utility=ssd.utility,
                utility_gap_abs=utility_gap_abs,
                utility_gap_pct=utility_gap_pct,
                gs_mu1_ssd_model=gs_under_ssd.mu1,
                gs_mu2_ssd_model=gs_under_ssd.mu2,
                ssd_mu1=ssd.mu1,
                ssd_mu2=ssd.mu2,
                gs_budget1_ssd_model=gs_under_ssd.budget1,
                gs_budget2_ssd_model=gs_under_ssd.budget2,
                ssd_budget1=ssd.budget1,
                ssd_budget2=ssd.budget2,
                gs_order=gs_order,
                ssd_order=ssd_order,
                reversal=reversal,
                valid=valid,
                invalid_reason=invalid_reason,
            )
        )

    return rows


def _write_csv(path: Path, rows: list[ScanRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _print_summary(rows: list[ScanRow]) -> None:
    total = len(rows)
    valid = [row for row in rows if row.valid]
    reversals = [row for row in valid if row.reversal]
    positive_gap = [row for row in valid if row.utility_gap_abs > 0.0]
    gate_gap = [row for row in reversals if row.utility_gap_pct >= 0.15]

    print(f"evaluated_cases={total}")
    print(f"valid_cases={len(valid)}/{total} ({len(valid) / total:.1%})")
    if not valid:
        return
    print(f"positive_ssd_gap_cases={len(positive_gap)}/{len(valid)} ({len(positive_gap) / len(valid):.1%})")
    print(f"reversal_cases={len(reversals)}/{len(valid)} ({len(reversals) / len(valid):.1%})")
    print(f"reversal_cases_with_geomean_gap_ge_15pct={len(gate_gap)}/{len(valid)} ({len(gate_gap) / len(valid):.1%})")

    if reversals:
        avg_gap = sum(row.utility_gap_pct for row in reversals) / len(reversals)
        print(f"avg_reversal_geomean_gap_pct={avg_gap:.1%}")
        print("top_reversal_cases")
        top = sorted(reversals, key=lambda row: (row.utility_gap_pct, abs(row.k1_gs - row.k2_gs)), reverse=True)[:8]
        for row in top:
            print(
                "  "
                f"alpha=({row.alpha1:g},{row.alpha2:g}) b=({row.b1:g},{row.b2:g}) "
                f"k_gs=({row.k1_gs},{row.k2_gs}) k_ssd=({row.k1_ssd},{row.k2_ssd}) "
                f"gap={row.utility_gap_pct:.1%}"
            )


def _make_plots(rows: list[ScanRow], out_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as exc:
        print(f"png_plots_skipped=missing_dependency:{exc.name}")
        _make_svg_plots(rows, out_dir)
        return

    valid = [row for row in rows if row.valid]
    if not valid:
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(asdict(row) for row in valid)
    for (b1, b2), group in df.groupby(["b1", "b2"]):
        reversal_pivot = (
            group.pivot_table(index="alpha2", columns="alpha1", values="reversal", aggfunc="max")
            .fillna(False)
            .astype(float)
        )
        gap_pivot = (
            group.pivot_table(index="alpha2", columns="alpha1", values="utility_gap_pct", aggfunc="mean")
            .fillna(0.0)
            .astype(float)
        )

        fig, ax = plt.subplots(figsize=(6, 5))
        image = ax.imshow(reversal_pivot.values, aspect="auto", origin="lower", vmin=0, vmax=1)
        ax.set_xticks(range(len(reversal_pivot.columns)))
        ax.set_xticklabels([f"{value:g}" for value in reversal_pivot.columns], rotation=45)
        ax.set_yticks(range(len(reversal_pivot.index)))
        ax.set_yticklabels([f"{value:g}" for value in reversal_pivot.index])
        ax.set_xlabel("alpha1")
        ax.set_ylabel("alpha2")
        ax.set_title(f"reversal map b1={b1:g}, b2={b2:g}")
        fig.colorbar(image, ax=ax, label="reversal")
        fig.tight_layout()
        fig.savefig(out_dir / f"reversal_b1_{b1:g}_b2_{b2:g}.png", dpi=160)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 5))
        image = ax.imshow(gap_pivot.values, aspect="auto", origin="lower")
        ax.set_xticks(range(len(gap_pivot.columns)))
        ax.set_xticklabels([f"{value:g}" for value in gap_pivot.columns], rotation=45)
        ax.set_yticks(range(len(gap_pivot.index)))
        ax.set_yticklabels([f"{value:g}" for value in gap_pivot.index])
        ax.set_xlabel("alpha1")
        ax.set_ylabel("alpha2")
        ax.set_title(f"geomean utility gap b1={b1:g}, b2={b2:g}")
        fig.colorbar(image, ax=ax, label="SSD over GS")
        fig.tight_layout()
        fig.savefig(out_dir / f"utility_gap_b1_{b1:g}_b2_{b2:g}.png", dpi=160)
        plt.close(fig)


def _group_by_b_pair(rows: list[ScanRow]) -> dict[tuple[float, float], list[ScanRow]]:
    grouped: dict[tuple[float, float], list[ScanRow]] = {}
    for row in rows:
        if row.valid:
            grouped.setdefault((row.b1, row.b2), []).append(row)
    return grouped


def _blue(value: float, max_value: float) -> str:
    if max_value <= 0.0 or not math.isfinite(value):
        value = 0.0
    ratio = max(0.0, min(1.0, value / max_value))
    start = (247, 251, 255)
    end = (8, 81, 156)
    rgb = tuple(round(start[i] + (end[i] - start[i]) * ratio) for i in range(3))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _svg_escape(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _write_svg_heatmap(
    path: Path,
    title: str,
    alpha1_values: list[float],
    alpha2_values: list[float],
    values: dict[tuple[float, float], float],
    color_fn,
    label_fn,
) -> None:
    cell = 34
    left = 74
    top = 62
    right = 24
    bottom = 70
    width = left + cell * len(alpha1_values) + right
    height = top + cell * len(alpha2_values) + bottom
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="24" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700">{_svg_escape(title)}</text>',
        f'<text x="{width / 2:.1f}" y="{height - 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">alpha1</text>',
        f'<text x="18" y="{top + cell * len(alpha2_values) / 2:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" transform="rotate(-90 18 {top + cell * len(alpha2_values) / 2:.1f})">alpha2</text>',
    ]

    for x_index, alpha1 in enumerate(alpha1_values):
        x = left + x_index * cell + cell / 2
        parts.append(
            f'<text x="{x:.1f}" y="{top - 10}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10">{alpha1:g}</text>'
        )
    for y_index, alpha2 in enumerate(alpha2_values):
        y = top + (len(alpha2_values) - 1 - y_index) * cell + cell / 2 + 4
        parts.append(
            f'<text x="{left - 10}" y="{y:.1f}" text-anchor="end" font-family="Arial, sans-serif" font-size="10">{alpha2:g}</text>'
        )

    for x_index, alpha1 in enumerate(alpha1_values):
        for y_index, alpha2 in enumerate(alpha2_values):
            value = values.get((alpha1, alpha2), 0.0)
            x = left + x_index * cell
            y = top + (len(alpha2_values) - 1 - y_index) * cell
            color = color_fn(value)
            label = label_fn(value)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" stroke="#d9d9d9"/>')
            if label:
                parts.append(
                    f'<text x="{x + cell / 2:.1f}" y="{y + cell / 2 + 4:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="9" fill="#111111">{_svg_escape(label)}</text>'
                )

    parts.append("</svg>")
    path.write_text("\n".join(parts))


def _make_svg_plots(rows: list[ScanRow], out_dir: Path) -> None:
    grouped = _group_by_b_pair(rows)
    if not grouped:
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for (b1, b2), group in grouped.items():
        alpha1_values = sorted({row.alpha1 for row in group})
        alpha2_values = sorted({row.alpha2 for row in group})
        reversal_values = {(row.alpha1, row.alpha2): float(row.reversal) for row in group}
        gap_values = {(row.alpha1, row.alpha2): row.utility_gap_pct for row in group}
        max_gap = max([0.0, *(value for value in gap_values.values() if math.isfinite(value))])

        _write_svg_heatmap(
            out_dir / f"reversal_b1_{b1:g}_b2_{b2:g}.svg",
            f"reversal map b1={b1:g}, b2={b2:g}",
            alpha1_values,
            alpha2_values,
            reversal_values,
            lambda value: "#b2182b" if value >= 0.5 else "#f7f7f7",
            lambda value: "R" if value >= 0.5 else "",
        )
        _write_svg_heatmap(
            out_dir / f"utility_gap_b1_{b1:g}_b2_{b2:g}.svg",
            f"geomean utility gap b1={b1:g}, b2={b2:g}",
            alpha1_values,
            alpha2_values,
            gap_values,
            lambda value, max_gap=max_gap: _blue(max(0.0, value), max_gap),
            lambda value: f"{value:.0%}" if value > 0.0 else "",
        )
        written += 2

    print(f"svg_plots_written={written}")


def main() -> None:
    args = _build_parser().parse_args()
    rows = _scan(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.out_dir / "summary.csv", rows)
    reversal_rows = sorted(
        [row for row in rows if row.valid and row.reversal],
        key=lambda row: (row.utility_gap_pct, abs(row.k1_gs - row.k2_gs)),
        reverse=True,
    )
    _write_csv(args.out_dir / "reversal_cases.csv", reversal_rows)
    _print_summary(rows)
    if not args.no_plots:
        _make_plots(rows, args.out_dir)
    print(f"wrote={args.out_dir}")


if __name__ == "__main__":
    main()
