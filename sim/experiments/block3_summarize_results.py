from __future__ import annotations

import argparse
import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_RESULTS_ROOT = Path(__file__).parent / "results"
DEFAULT_SCENARIOS = [
    ("default", DEFAULT_RESULTS_ROOT / "block3_reversal" / "summary.csv"),
    ("wide_b", DEFAULT_RESULTS_ROOT / "block3_reversal_wide_b" / "summary.csv"),
    ("semi_calibrated", DEFAULT_RESULTS_ROOT / "block3_reversal_semi_calibrated" / "summary.csv"),
    ("alpaca_calibrated", DEFAULT_RESULTS_ROOT / "block3_reversal_alpaca_calibrated" / "summary.csv"),
]
DEFAULT_OUT_DIR = DEFAULT_RESULTS_ROOT / "block3_summary"


@dataclass(frozen=True)
class ScenarioSummary:
    scenario: str
    total_cases: int
    valid_cases: int
    valid_rate: float
    positive_gap_cases: int
    positive_gap_rate: float
    reversal_cases: int
    reversal_rate: float
    strong_reversal_cases: int
    strong_reversal_rate: float
    avg_reversal_gap_pct: float
    top_reversal_gap_pct: float
    gate_region_pass: bool
    gate_gap_pass: bool
    gate_pass: bool


@dataclass(frozen=True)
class BRatioSummary:
    scenario: str
    b_ratio: float
    valid_cases: int
    reversal_cases: int
    reversal_rate: float
    strong_reversal_cases: int
    strong_reversal_rate: float
    avg_reversal_gap_pct: float
    top_reversal_gap_pct: float


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize Block 3 reversal scan outputs.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario in label=path form. Defaults to default, wide_b, and semi_calibrated.",
    )
    parser.add_argument("--no-plots", action="store_true")
    return parser


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _is_true(value: str) -> bool:
    return value == "True"


def _float(row: dict[str, str], key: str) -> float:
    try:
        value = float(row[key])
    except (KeyError, ValueError):
        return float("nan")
    return value


def _safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _summarize_scenario(label: str, rows: list[dict[str, str]]) -> ScenarioSummary:
    total = len(rows)
    valid = [row for row in rows if _is_true(row.get("valid", ""))]
    positive = [row for row in valid if _float(row, "utility_gap_pct") > 0.0]
    reversals = [row for row in valid if _is_true(row.get("reversal", ""))]
    strong = [row for row in reversals if _float(row, "utility_gap_pct") >= 0.15]
    reversal_gaps = [_float(row, "utility_gap_pct") for row in reversals]
    avg_reversal_gap = sum(reversal_gaps) / len(reversal_gaps) if reversal_gaps else 0.0
    top_reversal_gap = max(reversal_gaps) if reversal_gaps else 0.0
    reversal_rate = _safe_rate(len(reversals), len(valid))

    return ScenarioSummary(
        scenario=label,
        total_cases=total,
        valid_cases=len(valid),
        valid_rate=_safe_rate(len(valid), total),
        positive_gap_cases=len(positive),
        positive_gap_rate=_safe_rate(len(positive), len(valid)),
        reversal_cases=len(reversals),
        reversal_rate=reversal_rate,
        strong_reversal_cases=len(strong),
        strong_reversal_rate=_safe_rate(len(strong), len(valid)),
        avg_reversal_gap_pct=avg_reversal_gap,
        top_reversal_gap_pct=top_reversal_gap,
        gate_region_pass=reversal_rate >= 0.20,
        gate_gap_pass=avg_reversal_gap >= 0.15,
        gate_pass=reversal_rate >= 0.20 and avg_reversal_gap >= 0.15,
    )


def _summarize_b_ratios(label: str, rows: list[dict[str, str]]) -> list[BRatioSummary]:
    groups: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        if not _is_true(row.get("valid", "")):
            continue
        b1 = _float(row, "b1")
        b2 = _float(row, "b2")
        if not math.isfinite(b1) or not math.isfinite(b2) or b1 <= 0.0 or b2 <= 0.0:
            continue
        ratio = round(max(b1, b2) / min(b1, b2), 10)
        groups.setdefault(ratio, []).append(row)

    summaries = []
    for ratio, group in sorted(groups.items()):
        reversals = [row for row in group if _is_true(row.get("reversal", ""))]
        strong = [row for row in reversals if _float(row, "utility_gap_pct") >= 0.15]
        gaps = [_float(row, "utility_gap_pct") for row in reversals]
        summaries.append(
            BRatioSummary(
                scenario=label,
                b_ratio=ratio,
                valid_cases=len(group),
                reversal_cases=len(reversals),
                reversal_rate=_safe_rate(len(reversals), len(group)),
                strong_reversal_cases=len(strong),
                strong_reversal_rate=_safe_rate(len(strong), len(group)),
                avg_reversal_gap_pct=sum(gaps) / len(gaps) if gaps else 0.0,
                top_reversal_gap_pct=max(gaps) if gaps else 0.0,
            )
        )
    return summaries


def _write_csv(path: Path, rows: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _make_plots(b_ratio_rows: list[BRatioSummary], out_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        print(f"plots_skipped=missing_dependency:{exc.name}")
        return

    grouped: dict[str, list[BRatioSummary]] = {}
    for row in b_ratio_rows:
        grouped.setdefault(row.scenario, []).append(row)

    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for scenario, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: row.b_ratio)
        ax.plot(
            [row.b_ratio for row in ordered],
            [row.reversal_rate for row in ordered],
            marker="o",
            linewidth=1.8,
            label=scenario,
        )
    ax.set_xscale("log")
    ax.set_xlabel("b heterogeneity ratio: max(b1,b2) / min(b1,b2)")
    ax.set_ylabel("reversal rate")
    ax.set_title("Block 3 reversal rate vs drafter-cost heterogeneity")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "b_ratio_reversal_rate.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for scenario, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: row.b_ratio)
        ax.plot(
            [row.b_ratio for row in ordered],
            [row.avg_reversal_gap_pct for row in ordered],
            marker="o",
            linewidth=1.8,
            label=scenario,
        )
    ax.set_xscale("log")
    ax.set_xlabel("b heterogeneity ratio: max(b1,b2) / min(b1,b2)")
    ax.set_ylabel("average gap among reversal cases")
    ax.set_title("Block 3 utility gap vs drafter-cost heterogeneity")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "b_ratio_reversal_gap.png", dpi=180)
    plt.close(fig)


def _parse_scenarios(raw_scenarios: list[str]) -> list[tuple[str, Path]]:
    if not raw_scenarios:
        return DEFAULT_SCENARIOS
    scenarios = []
    for raw in raw_scenarios:
        if "=" not in raw:
            raise ValueError(f"Expected label=path, got {raw}")
        label, path = raw.split("=", 1)
        scenarios.append((label, Path(path)))
    return scenarios


def main() -> None:
    args = _build_parser().parse_args()
    scenarios = _parse_scenarios(args.scenario)
    scenario_rows: list[ScenarioSummary] = []
    b_ratio_rows: list[BRatioSummary] = []

    for label, path in scenarios:
        rows = _read_rows(path)
        if not rows:
            print(f"skipped_missing_or_empty={label}:{path}")
            continue
        scenario_rows.append(_summarize_scenario(label, rows))
        b_ratio_rows.extend(_summarize_b_ratios(label, rows))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.out_dir / "gate3_summary.csv", scenario_rows)
    _write_csv(args.out_dir / "b_ratio_summary.csv", b_ratio_rows)
    if not args.no_plots:
        _make_plots(b_ratio_rows, args.out_dir)

    for row in scenario_rows:
        print(
            f"{row.scenario}: valid={row.valid_cases}/{row.total_cases} "
            f"reversal_rate={row.reversal_rate:.1%} "
            f"avg_rev_gap={row.avg_reversal_gap_pct:.1%} "
            f"gate_pass={row.gate_pass}"
        )
    print(f"wrote={args.out_dir}")


if __name__ == "__main__":
    main()
