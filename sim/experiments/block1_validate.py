from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from itertools import product
from pathlib import Path

from sim.ssd_math import Block1Params, curve, curve_summary


DEFAULT_RESULTS_DIR = Path(__file__).parent / "results" / "block1_validate"


def _float_list(raw: str) -> list[float]:
    return [float(item) for item in raw.replace(",", " ").split()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Block 1 SSD unimodality over a parameter grid.")
    parser.add_argument("--alphas", default="0.5 0.6 0.7 0.8 0.9 0.95 0.98")
    parser.add_argument("--rs", default="0.3 0.5 0.8 1.2")
    parser.add_argument("--as", dest="a_values", default="0.05 0.1 0.2")
    parser.add_argument("--bs", dest="b_values", default="0.01 0.02 0.05 0.1")
    parser.add_argument("--tvs", default="10 20 40 80")
    parser.add_argument("--tbs", default="0.5 1.0 2.0")
    parser.add_argument("--max-k", type=int, default=None)
    parser.add_argument("--min-valid-k", type=int, default=4)
    parser.add_argument("--tol", type=float, default=1e-8)
    parser.add_argument("--allow-fractional-fanout", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--no-plots", action="store_true")
    return parser


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _scan(args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    rows = []
    curve_rows = []
    require_integer_fanout = not args.allow_fractional_fanout

    for alpha, r, a, b, t_v, t_b in product(
        _float_list(args.alphas),
        _float_list(args.rs),
        _float_list(args.a_values),
        _float_list(args.b_values),
        _float_list(args.tvs),
        _float_list(args.tbs),
    ):
        params = Block1Params(alpha=alpha, r=r, a=a, b=b, t_v=t_v, t_b=t_b)
        points = curve(params, max_k=args.max_k, require_integer_fanout=require_integer_fanout)
        summary = curve_summary(points, tol=args.tol)
        enough_valid = int(summary["num_valid_k"]) >= args.min_valid_k

        row = {
            **asdict(params),
            **summary,
            "enough_valid": enough_valid,
            "valid_unimodal": bool(summary["is_unimodal"]) and enough_valid,
        }
        rows.append(row)

        for point in points:
            curve_rows.append({**asdict(params), **asdict(point)})

    return rows, curve_rows


def _monotonicity_report(rows: list[dict]) -> dict[str, tuple[int, int, float]]:
    valid_rows = [row for row in rows if row["enough_valid"]]

    checks = {
        "alpha_nondecreasing": ("alpha", True),
        "b_nonincreasing": ("b", False),
        "t_v_nondecreasing": ("t_v", True),
    }
    report = {}
    for name, (axis, should_increase) in checks.items():
        other_axes = ["alpha", "r", "a", "b", "t_v", "t_b"]
        other_axes.remove(axis)
        grouped = {}
        for row in valid_rows:
            key = tuple(row[item] for item in other_axes)
            grouped.setdefault(key, []).append(row)

        total = 0
        violations = 0
        for group in grouped.values():
            ordered = sorted(group, key=lambda row: row[axis])
            if len(ordered) < 2:
                continue
            best_ks = [int(row["best_k"]) for row in ordered]
            pairs = list(zip(best_ks, best_ks[1:]))
            total += len(pairs)
            if should_increase:
                violations += sum(left > right for left, right in pairs)
            else:
                violations += sum(left < right for left, right in pairs)

        report[name] = (violations, total, violations / total if total else 0.0)
    return report


def _print_summary(rows: list[dict]) -> None:
    total = len(rows)
    enough = [row for row in rows if row["enough_valid"]]
    unimodal = [row for row in enough if row["is_unimodal"]]
    all_unimodal = [row for row in rows if row["is_unimodal"]]

    print(f"evaluated_cases={total}")
    print(f"enough_valid_cases={len(enough)}/{total} ({len(enough) / total:.1%})")
    print(f"unimodal_all_cases={len(all_unimodal)}/{total} ({len(all_unimodal) / total:.1%})")
    print(f"unimodal_enough_valid_cases={len(unimodal)}/{len(enough)} ({len(unimodal) / len(enough):.1%})")

    print("monotonicity")
    for name, (violations, checks, rate) in _monotonicity_report(rows).items():
        print(f"  {name}: violations={violations}/{checks} ({rate:.1%})")

    failures = [row for row in enough if not row["is_unimodal"]]
    print(f"non_unimodal_enough_valid_cases={len(failures)}")
    for row in failures[:10]:
        print(
            "  "
            f"alpha={row['alpha']} r={row['r']} a={row['a']} b={row['b']} "
            f"t_v={row['t_v']} t_b={row['t_b']} best_k={row['best_k']} "
            f"valid_k=[{row['first_valid_k']},{row['last_valid_k']}]"
        )


def _make_plots(rows: list[dict], curve_rows: list[dict], out_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as exc:
        print(f"plots_skipped=missing_dependency:{exc.name}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    curve_df = pd.DataFrame(curve_rows)

    examples = [
        ("alpha_sweep", {"r": 0.8, "a": 0.1, "b": 0.02, "t_v": 40.0, "t_b": 1.0}, "alpha"),
        ("b_sweep", {"alpha": 0.9, "r": 0.8, "a": 0.1, "t_v": 40.0, "t_b": 1.0}, "b"),
        ("tv_sweep", {"alpha": 0.9, "r": 0.8, "a": 0.1, "b": 0.02, "t_b": 1.0}, "t_v"),
    ]
    for filename, fixed, varying in examples:
        mask = curve_df["valid"]
        for key, value in fixed.items():
            mask &= curve_df[key] == value
        subset = curve_df[mask]
        if subset.empty:
            continue
        fig, ax = plt.subplots(figsize=(7, 4))
        for value, group in subset.groupby(varying):
            ax.plot(group["k"], group["mu"], marker="o", linewidth=1.5, markersize=3, label=f"{varying}={value:g}")
        ax.set_xlabel("k")
        ax.set_ylabel("mu_ssd")
        ax.set_title(filename)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out_dir / f"{filename}.png", dpi=160)
        plt.close(fig)

    heat = df[(df["r"] == 0.8) & (df["a"] == 0.1) & (df["t_v"] == 40.0) & (df["t_b"] == 1.0) & df["enough_valid"]]
    if not heat.empty:
        pivot = heat.pivot_table(index="b", columns="alpha", values="best_k", aggfunc="mean")
        fig, ax = plt.subplots(figsize=(7, 4))
        image = ax.imshow(pivot.values, aspect="auto", origin="lower")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([f"{value:g}" for value in pivot.columns])
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([f"{value:g}" for value in pivot.index])
        ax.set_xlabel("alpha")
        ax.set_ylabel("b")
        ax.set_title("best k heatmap")
        fig.colorbar(image, ax=ax, label="best k")
        fig.tight_layout()
        fig.savefig(out_dir / "best_k_alpha_b_heatmap.png", dpi=160)
        plt.close(fig)


def main() -> None:
    args = _build_parser().parse_args()
    rows, curve_rows = _scan(args)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.out_dir / "summary.csv", rows)
    _write_csv(args.out_dir / "curves.csv", curve_rows)
    _print_summary(rows)

    if not args.no_plots:
        _make_plots(rows, curve_rows, args.out_dir)

    print(f"wrote={args.out_dir}")


if __name__ == "__main__":
    main()
