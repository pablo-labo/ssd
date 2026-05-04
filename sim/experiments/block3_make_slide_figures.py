from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_SUMMARY = Path("sim/experiments/results/block3_summary/gate3_summary.csv")
DEFAULT_B_RATIO = Path("sim/experiments/results/block3_summary/b_ratio_summary.csv")
DEFAULT_CASES = Path("sim/experiments/results/block3_reversal_alpaca_calibrated/reversal_cases.csv")
DEFAULT_OUT_DIR = Path("sim/experiments/results/block3_slide_figures")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _save(fig, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        kwargs = {"bbox_inches": "tight"}
        if ext == "png":
            kwargs["dpi"] = 220
        fig.savefig(out_dir / f"{stem}.{ext}", **kwargs)


def _style_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#d7dde5", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)


def _make_scenario_summary(summary_path: Path, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = _read_rows(summary_path)
    labels = ["Default", "Wide b", "Semi-cal.", "Alpaca-cal."]
    scenario_order = ["default", "wide_b", "semi_calibrated", "alpaca_calibrated"]
    by_name = {row["scenario"]: row for row in rows}
    reversal_rate = [_float(by_name[name], "reversal_rate") * 100 for name in scenario_order]
    avg_gap = [_float(by_name[name], "avg_reversal_gap_pct") * 100 for name in scenario_order]

    fig, ax = plt.subplots(figsize=(8.4, 4.7))
    x = list(range(len(labels)))
    width = 0.34
    colors = {"rate": "#2f6f9f", "gap": "#c76b3a"}
    ax.bar([value - width / 2 for value in x], reversal_rate, width, label="Reversal region size", color=colors["rate"])
    ax.bar([value + width / 2 for value in x], avg_gap, width, label="Avg gap when reversal occurs", color=colors["gap"])

    for xpos, value in zip([value - width / 2 for value in x], reversal_rate):
        ax.text(xpos, value + 1.0, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)
    for xpos, value in zip([value + width / 2 for value in x], avg_gap):
        ax.text(xpos, value + 1.0, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Percent")
    ax.set_ylim(0, max(avg_gap) + 10)
    ax.set_title("Real timing narrows reversal, but surviving cases are large")
    ax.legend(frameon=False, loc="upper left")
    _style_axes(ax)
    _save(fig, out_dir, "calibrated_scenario_summary")
    plt.close(fig)


def _make_b_ratio_focus(b_ratio_path: Path, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    rows = [row for row in _read_rows(b_ratio_path) if row["scenario"] == "alpaca_calibrated"]
    rows = sorted(rows, key=lambda row: _float(row, "b_ratio"))
    ratios = [_float(row, "b_ratio") for row in rows]
    rates = [_float(row, "reversal_rate") * 100 for row in rows]
    gaps = [_float(row, "avg_reversal_gap_pct") * 100 for row in rows]
    sizes = [max(30, int(row["valid_cases"]) * 0.7) for row in rows]

    fig, ax = plt.subplots(figsize=(8.4, 4.7))
    ax.scatter(ratios, rates, s=sizes, color="#2f6f9f", alpha=0.75, edgecolor="white", linewidth=0.8)
    ax.plot(ratios, rates, color="#2f6f9f", linewidth=1.5, alpha=0.65)
    ax.set_xscale("log")
    ax.set_xlabel("Draft-cost heterogeneity: max(b1,b2) / min(b1,b2)")
    ax.set_ylabel("Reversal rate (%)", color="#2f6f9f")
    ax.tick_params(axis="y", labelcolor="#2f6f9f")
    ax.set_ylim(0, max(rates) + 4)
    _style_axes(ax)

    ax2 = ax.twinx()
    ax2.plot(ratios, gaps, color="#c76b3a", marker="o", linewidth=2.0, label="Avg reversal gap")
    ax2.set_ylabel("Avg gap among reversal cases (%)", color="#c76b3a")
    ax2.tick_params(axis="y", labelcolor="#c76b3a")
    ax2.spines["top"].set_visible(False)
    ax2.set_ylim(0, max(gaps) + 8)

    ax.set_title("Alpaca-calibrated reversal appears only under cost heterogeneity")
    ax.text(
        0.02,
        0.92,
        "Bubble size = valid cases at each b-ratio",
        transform=ax.transAxes,
        fontsize=9,
        color="#4b5563",
    )
    _save(fig, out_dir, "alpaca_calibrated_b_ratio")
    plt.close(fig)


def _make_case_study(cases_path: Path, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    row = _read_rows(cases_path)[0]
    labels = ["Client 1\nalpha=0.65\nb=0.00384", "Client 2\nalpha=0.80\nb=0.02307"]
    gs_k = [_float(row, "k1_gs"), _float(row, "k2_gs")]
    ssd_k = [_float(row, "k1_ssd"), _float(row, "k2_ssd")]
    gs_budget = [_float(row, "gs_budget1_ssd_model"), _float(row, "gs_budget2_ssd_model")]
    ssd_budget = [_float(row, "ssd_budget1"), _float(row, "ssd_budget2")]
    gap = _float(row, "utility_gap_pct") * 100

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2), gridspec_kw={"width_ratios": [1, 1]})
    x = [0, 1]
    width = 0.34
    for ax, left_values, right_values, ylabel, title in [
        (axes[0], gs_k, ssd_k, "Allocated depth k", "Depth allocation reverses"),
        (axes[1], gs_budget, ssd_budget, "Feasible fanout budget B", "SSD-aware allocation restores budget"),
    ]:
        ax.bar([value - width / 2 for value in x], left_values, width, label="GoodSpeed", color="#6b7280")
        ax.bar([value + width / 2 for value in x], right_values, width, label="SSD-aware", color="#2f6f9f")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        _style_axes(ax)

    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle(f"Representative calibrated reversal case: SSD-aware geomean utility +{gap:.1f}%", y=1.04)
    _save(fig, out_dir, "alpaca_calibrated_reversal_case")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create slide-friendly Block 3 calibrated figures.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--b-ratio", type=Path, default=DEFAULT_B_RATIO)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    _make_scenario_summary(args.summary, args.out_dir)
    _make_b_ratio_focus(args.b_ratio, args.out_dir)
    _make_case_study(args.cases, args.out_dir)
    print(f"wrote={args.out_dir}")


if __name__ == "__main__":
    main()
