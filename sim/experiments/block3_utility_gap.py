"""Per-mechanism utility-gap analysis for the Block 3 allocation comparison.

Companion to ``block3_make_native_order_figures.py``. That script reports how
*often* GoodSpeed and SSD-aware scheduling disagree (the scheduler-native
mechanism frequencies). This script reports how *much* the disagreement costs,
by aggregating the per-client geometric-mean goodput shortfall
(``utility_gap_pct``) within each scheduler-native mechanism.

Definitions (consistent with ``block3_reversal_scan.py``):

* Mechanism is classified from the native allocation orders ``gs_order`` and
  ``ssd_order`` over *all* scanned cases:
    - agreement       : gs_order == ssd_order
    - blindness       : gs_order == 0 (GoodSpeed tie) and ssd_order != 0
    - overcommit      : gs_order != 0 and ssd_order == 0 (SSD tie)
    - strict_reversal : gs_order != 0, ssd_order != 0, gs_order != ssd_order
* ``utility_gap_pct`` = expm1((U_ssd_opt - U_goodspeed) / 2), the per-client
  geometric-mean goodput shortfall of running GoodSpeed's allocation under the
  SSD service model relative to the SSD-aware optimum. It is *only defined when
  the case is valid* (all three allocations executable under the SSD model).
  Cases with ``valid == False`` are GoodSpeed allocations that are infeasible
  under the SSD timing model (budget/fanout violations) and have no defined
  utility gap; their count is reported separately.

Outputs (written to --out-dir):
* utility_gap_by_mechanism.csv : one row per mechanism (+ an "all" row) with
  count, frequency, validity rate, and the gap distribution summary.
* utility_gap_cdf.{png,pdf,svg} : CDF of utility_gap_pct per mechanism.
* utility_gap_box.{png,pdf,svg} : mean +/- IQR of utility_gap_pct per mechanism.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np


DEFAULT_SUMMARY = Path(
    "sim/experiments/results/block3_reversal_alpaca_calibrated/summary.csv"
)
DEFAULT_OUT_DIR = Path("sim/experiments/results/block3_summary")

MECHANISMS = ["agreement", "blindness", "overcommit", "strict_reversal"]
MECH_COLORS = {
    "agreement": "#9aa6ad",
    "blindness": "#4f7f9f",
    "overcommit": "#7d9b6f",
    "strict_reversal": "#c76b3a",
}
MECH_LABELS = {
    "agreement": "Agreement (same order)",
    "blindness": "GoodSpeed blindness",
    "overcommit": "GoodSpeed overcommit",
    "strict_reversal": "Strict reversal",
}


@dataclass
class MechanismGapSummary:
    mechanism: str
    count: int
    frequency_pct: float
    valid_count: int
    valid_rate_pct: float
    gap_mean_pct: float
    gap_median_pct: float
    gap_p10_pct: float
    gap_p25_pct: float
    gap_p75_pct: float
    gap_p90_pct: float
    gap_max_pct: float
    frac_ge_15pct: float


def _classify(gs_order: int, ssd_order: int) -> str:
    if gs_order == ssd_order:
        return "agreement"
    if gs_order == 0 and ssd_order != 0:
        return "blindness"
    if gs_order != 0 and ssd_order == 0:
        return "overcommit"
    return "strict_reversal"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Per-mechanism utility-gap analysis for Block 3."
    )
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--no-figures", action="store_true", help="Write CSV only, skip plots."
    )
    return parser


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _summarize(mechanism: str, total_rows: int, count: int, gaps: list[float],
               valid_count: int) -> MechanismGapSummary:
    arr = np.array(sorted(gaps), dtype=float)
    if arr.size:
        pct = lambda q: float(np.percentile(arr, q)) * 100.0
        summary = MechanismGapSummary(
            mechanism=mechanism,
            count=count,
            frequency_pct=100.0 * count / total_rows if total_rows else 0.0,
            valid_count=valid_count,
            valid_rate_pct=100.0 * valid_count / count if count else 0.0,
            gap_mean_pct=float(arr.mean()) * 100.0,
            gap_median_pct=pct(50),
            gap_p10_pct=pct(10),
            gap_p25_pct=pct(25),
            gap_p75_pct=pct(75),
            gap_p90_pct=pct(90),
            gap_max_pct=float(arr.max()) * 100.0,
            frac_ge_15pct=100.0 * float((arr >= 0.15).mean()),
        )
    else:
        summary = MechanismGapSummary(
            mechanism, count,
            100.0 * count / total_rows if total_rows else 0.0,
            valid_count, 0.0, *([float("nan")] * 7), 0.0,
        )
    return summary


def analyze(rows: list[dict[str, str]]) -> tuple[list[MechanismGapSummary], dict[str, list[float]]]:
    total = len(rows)
    counts: dict[str, int] = {m: 0 for m in MECHANISMS}
    valid_counts: dict[str, int] = {m: 0 for m in MECHANISMS}
    gaps: dict[str, list[float]] = {m: [] for m in MECHANISMS}

    for row in rows:
        mech = _classify(int(row["gs_order"]), int(row["ssd_order"]))
        counts[mech] += 1
        if row.get("valid", "") == "True":
            valid_counts[mech] += 1
            try:
                gap = float(row["utility_gap_pct"])
            except (KeyError, ValueError):
                gap = float("nan")
            if math.isfinite(gap):
                gaps[mech].append(gap)

    summaries = [
        _summarize(m, total, counts[m], gaps[m], valid_counts[m]) for m in MECHANISMS
    ]

    # Append an aggregate "all_valid" row across every mechanism.
    all_gaps = [g for m in MECHANISMS for g in gaps[m]]
    all_valid = sum(valid_counts.values())
    summaries.append(_summarize("all_valid", total, total, all_gaps, all_valid))
    return summaries, gaps


def write_csv(summaries: list[MechanismGapSummary], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(summaries[0]).keys())
    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            row = asdict(summary)
            for key, value in row.items():
                if isinstance(value, float):
                    row[key] = round(value, 3)
            writer.writerow(row)


def _save(fig, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_dir / f"{stem}.{ext}", bbox_inches="tight", dpi=150)


def plot_cdf(gaps: dict[str, list[float]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    for mech in MECHANISMS:
        data = np.array(sorted(gaps[mech]), dtype=float) * 100.0
        if data.size == 0:
            continue
        ys = np.arange(1, data.size + 1) / data.size
        ax.plot(data, ys, color=MECH_COLORS[mech], linewidth=2.2,
                label=f"{MECH_LABELS[mech]} (n={data.size})")
    ax.axvline(15.0, color="#444444", linestyle="--", linewidth=1.0)
    ax.text(15.5, 0.04, "15% gate", color="#444444", fontsize=9)
    ax.set_xlabel("Per-client goodput shortfall of GoodSpeed vs SSD optimum (%)")
    ax.set_ylabel("Cumulative fraction of cases")
    ax.set_title("Utility-gap distribution by scheduler-native mechanism")
    ax.set_ylim(0, 1.0)
    ax.set_xlim(left=0)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    _save(fig, out_dir, "utility_gap_cdf")
    plt.close(fig)


def plot_box(gaps: dict[str, list[float]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    data = [np.array(gaps[m]) * 100.0 for m in MECHANISMS]
    positions = range(len(MECHANISMS))
    bp = ax.boxplot(data, positions=list(positions), widths=0.6,
                    showmeans=True, patch_artist=True, showfliers=False)
    for patch, mech in zip(bp["boxes"], MECHANISMS):
        patch.set_facecolor(MECH_COLORS[mech])
        patch.set_alpha(0.7)
    ax.axhline(15.0, color="#444444", linestyle="--", linewidth=1.0)
    ax.set_xticks(list(positions))
    ax.set_xticklabels([MECH_LABELS[m].replace(" ", "\n", 1) for m in MECHANISMS],
                       fontsize=9)
    ax.set_ylabel("Per-client goodput shortfall (%)")
    ax.set_title("Utility gap by mechanism (box = IQR, triangle = mean)")
    ax.grid(True, axis="y", alpha=0.3)
    _save(fig, out_dir, "utility_gap_box")
    plt.close(fig)


def main() -> None:
    args = _build_parser().parse_args()
    rows = _read_rows(args.summary)
    summaries, gaps = analyze(rows)

    write_csv(summaries, args.out_dir / "utility_gap_by_mechanism.csv")

    print(f"source: {args.summary}")
    print(f"total cases: {len(rows)}")
    header = (f"{'mechanism':16}{'count':>7}{'freq%':>7}{'valid':>7}"
              f"{'valid%':>8}{'mean%':>8}{'median%':>9}{'p90%':>7}{'>=15%':>8}")
    print(header)
    for s in summaries:
        print(f"{s.mechanism:16}{s.count:>7}{s.frequency_pct:>7.1f}"
              f"{s.valid_count:>7}{s.valid_rate_pct:>8.1f}{s.gap_mean_pct:>8.1f}"
              f"{s.gap_median_pct:>9.1f}{s.gap_p90_pct:>7.1f}{s.frac_ge_15pct:>8.1f}")

    if not args.no_figures:
        plot_cdf(gaps, args.out_dir)
        plot_box(gaps, args.out_dir)
        print(f"figures + csv written to {args.out_dir}")
    else:
        print(f"csv written to {args.out_dir}")


if __name__ == "__main__":
    main()
