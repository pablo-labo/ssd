from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SUMMARY = Path("sim/experiments/results/block3_reversal_alpaca_calibrated/summary.csv")
DEFAULT_OUT_DIR = Path("sim/experiments/results/block3_native_order_figures")


@dataclass(frozen=True)
class NativeOrderSummary:
    label: str
    total_cases: int
    ssd_cases: int
    order_mismatch_cases: int
    strict_reversal_cases: int

    @property
    def order_mismatch_rate(self) -> float:
        return self.order_mismatch_cases / self.ssd_cases if self.ssd_cases else 0.0

    @property
    def strict_reversal_rate(self) -> float:
        return self.strict_reversal_cases / self.ssd_cases if self.ssd_cases else 0.0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def _order(k1: int, k2: int) -> int:
    return (k1 > k2) - (k1 < k2)


def _orders(row: dict[str, str]) -> tuple[int, int] | None:
    k1_ssd = int(row["k1_ssd"])
    k2_ssd = int(row["k2_ssd"])
    if k1_ssd < 0 or k2_ssd < 0:
        return None
    gs_order = _order(int(row["k1_gs"]), int(row["k2_gs"]))
    ssd_order = _order(k1_ssd, k2_ssd)
    return gs_order, ssd_order


def _summarize(label: str, rows: list[dict[str, str]]) -> NativeOrderSummary:
    ssd_cases = 0
    mismatch = 0
    strict = 0
    for row in rows:
        orders = _orders(row)
        if orders is None:
            continue
        gs_order, ssd_order = orders
        ssd_cases += 1
        if gs_order != ssd_order:
            mismatch += 1
        if gs_order != 0 and ssd_order != 0 and gs_order != ssd_order:
            strict += 1
    return NativeOrderSummary(label, len(rows), ssd_cases, mismatch, strict)


def _transition_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    labels = {
        (0, 1): "GS tie -> SSD k1>k2",
        (0, -1): "GS tie -> SSD k1<k2",
        (-1, 0): "GS k1<k2 -> SSD tie",
        (1, 0): "GS k1>k2 -> SSD tie",
        (-1, 1): "GS k1<k2 -> SSD k1>k2",
        (1, -1): "GS k1>k2 -> SSD k1<k2",
    }
    counts = {label: 0 for label in labels.values()}
    for row in rows:
        orders = _orders(row)
        if orders is None:
            continue
        gs_order, ssd_order = orders
        if gs_order != ssd_order:
            counts[labels[(gs_order, ssd_order)]] += 1
    return counts


def _b_ratio_rows(rows: list[dict[str, str]]) -> list[tuple[float, int, int, int]]:
    groups: dict[float, list[int]] = {}
    for row in rows:
        orders = _orders(row)
        if orders is None:
            continue
        b1 = float(row["b1"])
        b2 = float(row["b2"])
        ratio = round(max(b1, b2) / min(b1, b2), 10)
        gs_order, ssd_order = orders
        is_mismatch = int(gs_order != ssd_order)
        is_strict = int(gs_order != 0 and ssd_order != 0 and gs_order != ssd_order)
        if ratio not in groups:
            groups[ratio] = [0, 0, 0]
        groups[ratio][0] += 1
        groups[ratio][1] += is_mismatch
        groups[ratio][2] += is_strict
    return [(ratio, *values) for ratio, values in sorted(groups.items())]


def _save(fig, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        kwargs = {"bbox_inches": "tight"}
        if ext == "png":
            kwargs["dpi"] = 220
        fig.savefig(out_dir / f"{stem}.{ext}", **kwargs)


def _style_axes(ax, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis=grid_axis, color="#d7dde5", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)


def _make_capacity_chart(paths: list[tuple[str, Path]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    summaries = [_summarize(label, _read_rows(path)) for label, path in paths]
    x = [float(summary.label) for summary in summaries]
    mismatch = [summary.order_mismatch_rate * 100 for summary in summaries]
    strict = [summary.strict_reversal_rate * 100 for summary in summaries]

    fig, ax = plt.subplots(figsize=(8.4, 4.7))
    ax.plot(x, mismatch, color="#2f6f9f", marker="o", linewidth=2.2, label="Order mismatch")
    ax.plot(x, strict, color="#c76b3a", marker="o", linewidth=2.2, label="Strict reversal")
    for xpos, value in zip(x, mismatch):
        ax.text(xpos, value + 1.3, f"{value:.1f}%", ha="center", va="bottom", fontsize=9, color="#2f6f9f")
    for xpos, value in zip(x, strict):
        ax.text(xpos, value + 1.1, f"{value:.1f}%", ha="center", va="bottom", fontsize=9, color="#c76b3a")
    ax.set_xlabel("Total depth capacity C")
    ax.set_ylabel("Rate under scheduler-native definition (%)")
    ax.set_ylim(0, max(mismatch) + 10)
    ax.set_title("Native-order reversal remains under aggressive capacity")
    ax.legend(frameon=False, loc="upper right")
    _style_axes(ax)
    _save(fig, out_dir, "native_order_by_capacity")
    plt.close(fig)


def _mechanism_rates(rows: list[dict[str, str]]) -> tuple[float, float, float]:
    total = 0
    blindness = 0
    overcommit = 0
    strict = 0
    for row in rows:
        orders = _orders(row)
        if orders is None:
            continue
        total += 1
        gs_order, ssd_order = orders
        if gs_order == 0 and ssd_order != 0:
            blindness += 1
        elif gs_order != 0 and ssd_order == 0:
            overcommit += 1
        elif gs_order != 0 and ssd_order != 0 and gs_order != ssd_order:
            strict += 1
    if not total:
        return 0.0, 0.0, 0.0
    return blindness / total * 100, overcommit / total * 100, strict / total * 100


def _make_capacity_mechanism_stack(paths: list[tuple[str, Path]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    labels = [label for label, _ in paths]
    rates = [_mechanism_rates(_read_rows(path)) for _, path in paths]
    blindness = [row[0] for row in rates]
    overcommit = [row[1] for row in rates]
    strict = [row[2] for row in rates]
    totals = [sum(row) for row in rates]
    x = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    colors = {
        "blindness": "#4f7f9f",
        "overcommit": "#7d9b6f",
        "strict": "#c76b3a",
    }
    ax.bar(x, strict, color=colors["strict"], label="Strict reversal")
    ax.bar(x, blindness, bottom=strict, color=colors["blindness"], label="GS blindness")
    ax.bar(
        x,
        overcommit,
        bottom=[a + b for a, b in zip(strict, blindness)],
        color=colors["overcommit"],
        label="GS overcommit",
    )

    for xpos, total in zip(x, totals):
        ax.text(xpos, total + 1.0, f"{total:.1f}%", ha="center", va="bottom", fontsize=9)
    segments = [
        (strict, [0.0 for _ in strict], "white"),
        (blindness, strict, "white"),
        (overcommit, [a + b for a, b in zip(strict, blindness)], "white"),
    ]
    for values, bottoms, color in segments:
        for xpos, value, bottom in zip(x, values, bottoms):
            if value < 4.0:
                continue
            ax.text(
                xpos,
                bottom + value / 2,
                f"{value:.1f}%",
                ha="center",
                va="center",
                fontsize=8,
                color=color,
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Total depth capacity C")
    ax.set_ylabel("Share of scheduler-native cases (%)")
    ax.set_ylim(0, max(totals) + 8)
    ax.set_title("Scheduler-native Disagreement By Capacity", pad=18)
    ax.legend(
        frameon=False,
        ncols=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        columnspacing=1.6,
        handlelength=1.8,
    )
    ax.text(
        0.5,
        -0.32,
        "Top label = total mismatch; in-bar labels = component shares.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=10,
        color="#4b5563",
    )
    _style_axes(ax)
    fig.subplots_adjust(top=0.86, bottom=0.28)
    _save(fig, out_dir, "native_order_mechanisms_by_capacity")
    plt.close(fig)


def _make_b_ratio_chart(rows: list[dict[str, str]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    data = _b_ratio_rows(rows)
    ratios = [row[0] for row in data]
    denom = [row[1] for row in data]
    mismatch = [row[2] / row[1] * 100 for row in data]
    strict = [row[3] / row[1] * 100 for row in data]
    sizes = [max(35, value * 0.55) for value in denom]

    fig, ax = plt.subplots(figsize=(8.4, 4.7))
    ax.scatter(ratios, mismatch, s=sizes, color="#2f6f9f", alpha=0.72, edgecolor="white", linewidth=0.8)
    ax.plot(ratios, mismatch, color="#2f6f9f", linewidth=1.7, alpha=0.72, label="Order mismatch")
    ax.plot(ratios, strict, color="#c76b3a", marker="o", linewidth=2.0, label="Strict reversal")
    ax.set_xscale("log")
    ax.set_xlabel("Draft-cost heterogeneity: max(b1,b2) / min(b1,b2)")
    ax.set_ylabel("Rate at C=12 (%)")
    ax.set_ylim(0, max(mismatch) + 10)
    ax.set_title("Native-order mismatch rises with draft-cost heterogeneity")
    ax.text(0.02, 0.92, "Bubble size = cases at each b-ratio", transform=ax.transAxes, fontsize=9, color="#4b5563")
    ax.legend(frameon=False, loc="lower right")
    _style_axes(ax)
    _save(fig, out_dir, "native_order_by_b_ratio")
    plt.close(fig)


def _make_transition_chart(rows: list[dict[str, str]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    counts = _transition_counts(rows)
    labels = list(counts.keys())
    values = list(counts.values())
    colors = ["#78909c", "#78909c", "#80a07a", "#80a07a", "#c76b3a", "#c76b3a"]

    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    y = list(range(len(labels)))
    ax.barh(y, values, color=colors)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Cases at C=12")
    ax.set_title("What changes when GS and SSD scheduler orders differ?")
    for ypos, value in zip(y, values):
        ax.text(value + 12, ypos, str(value), va="center", fontsize=9)
    _style_axes(ax, grid_axis="x")
    _save(fig, out_dir, "native_order_transition_breakdown")
    plt.close(fig)


def _make_mechanism_chart(rows: list[dict[str, str]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    total = 0
    blindness = 0
    overcommit = 0
    strict = 0
    for row in rows:
        orders = _orders(row)
        if orders is None:
            continue
        total += 1
        gs_order, ssd_order = orders
        if gs_order == 0 and ssd_order != 0:
            blindness += 1
        elif gs_order != 0 and ssd_order == 0:
            overcommit += 1
        elif gs_order != 0 and ssd_order != 0 and gs_order != ssd_order:
            strict += 1

    labels = [
        "GS blindness\nGS tie -> SSD non-tie",
        "GS overcommit\nGS non-tie -> SSD tie",
        "Strict reversal\nopposite directions",
    ]
    counts = [blindness, overcommit, strict]
    rates = [count / total * 100 for count in counts]
    colors = ["#4f7f9f", "#7d9b6f", "#c76b3a"]

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    x = list(range(len(labels)))
    bars = ax.bar(x, rates, color=colors, width=0.58)
    for bar, count, rate in zip(bars, counts, rates):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.0,
            f"{rate:.1f}%\n({count} cases)",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Share of scheduler-native cases at C=12 (%)")
    ax.set_ylim(0, max(rates) + 8)
    ax.set_title("Scheduler-native disagreement decomposes into three mechanisms")
    ax.text(
        0.5,
        -0.20,
        "Do not report the sum as one reversal rate; strict reversal is the strongest subset.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=10,
        color="#4b5563",
    )
    _style_axes(ax)
    _save(fig, out_dir, "native_order_three_mechanisms")
    plt.close(fig)


def _parse_capacity_paths(values: list[str]) -> list[tuple[str, Path]]:
    paths = []
    for value in values:
        label, raw_path = value.split("=", 1)
        paths.append((label, Path(raw_path)))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Create scheduler-native Block 3 order reversal figures.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--capacity-summary",
        action="append",
        default=[],
        help="Capacity summary in C=path form. If omitted, only C=12 single-scenario figures are made.",
    )
    args = parser.parse_args()

    rows = _read_rows(args.summary)
    _make_b_ratio_chart(rows, args.out_dir)
    _make_transition_chart(rows, args.out_dir)
    _make_mechanism_chart(rows, args.out_dir)
    if args.capacity_summary:
        capacity_paths = _parse_capacity_paths(args.capacity_summary)
        _make_capacity_chart(capacity_paths, args.out_dir)
        _make_capacity_mechanism_stack(capacity_paths, args.out_dir)
    print(f"wrote={args.out_dir}")


if __name__ == "__main__":
    main()
