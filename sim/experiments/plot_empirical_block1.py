from __future__ import annotations

import argparse
import csv
from pathlib import Path


METRICS = [
    ("suffix_per_verify_sec_mean", "Accepted suffix / verifier second"),
    ("decode_tokens_per_verify_sec_mean", "Decode tokens / verifier second"),
    ("avg_suffix_mean", "Accepted suffix length"),
    ("cache_hit_mean", "Cache hit rate"),
    ("verify_ms_mean", "Target verify time (ms)"),
]


def _float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return [row for row in rows if row.get("shape_mode") == "async_ssd"]


def _print_best(rows: list[dict[str, str]]) -> None:
    budgets = sorted({_float(row, "fanout_budget") for row in rows if _float(row, "fanout_budget") is not None})
    for budget in budgets:
        subset = [row for row in rows if _float(row, "fanout_budget") == budget]
        if not subset:
            continue
        print(f"budget={budget:g}")
        for metric, _ in METRICS[:2]:
            valid = [row for row in subset if _float(row, metric) is not None]
            if not valid:
                continue
            best = max(valid, key=lambda row: _float(row, metric) or float("-inf"))
            print(f"  best_{metric}: k={best.get('k')} value={_float(best, metric):.4f}")


def _plot(rows: list[dict[str, str]], out_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        print(f"plots_skipped=missing_dependency:{exc.name}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    budgets = sorted({_float(row, "fanout_budget") for row in rows if _float(row, "fanout_budget") is not None})
    for metric, ylabel in METRICS:
        fig, ax = plt.subplots(figsize=(7, 4))
        plotted = False
        for budget in budgets:
            subset = [
                row for row in rows
                if _float(row, "fanout_budget") == budget and _float(row, metric) is not None
            ]
            subset.sort(key=lambda row: _float(row, "k") or -1)
            if not subset:
                continue
            xs = [_float(row, "k") for row in subset]
            ys = [_float(row, metric) for row in subset]
            ax.plot(xs, ys, marker="o", linewidth=1.8, label=f"B={budget:g}")
            best_idx = max(range(len(ys)), key=lambda idx: ys[idx])
            ax.scatter([xs[best_idx]], [ys[best_idx]], s=60)
            plotted = True
        if not plotted:
            plt.close(fig)
            continue
        ax.set_xlabel("k")
        ax.set_ylabel(ylabel)
        ax.set_title(metric)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / f"{metric}.png", dpi=170)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot empirical Block 1 curves from geometric fan-out LLM runs.")
    parser.add_argument("shape_summary_csv", type=Path)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    out_dir = args.out_dir or args.shape_summary_csv.parent / "figures"
    rows = _load_rows(args.shape_summary_csv)
    if not rows:
        raise SystemExit(f"No async_ssd rows found in {args.shape_summary_csv}")
    _print_best(rows)
    _plot(rows, out_dir)
    print(f"wrote={out_dir}")


if __name__ == "__main__":
    main()
