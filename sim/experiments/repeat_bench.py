import argparse
import csv
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_CONFIGS = [
    {
        "label": "ar",
        "args": [
            "--qwen", "--size", "8", "--gpus", "1",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "sync_k6",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--draft", "0.6", "--k", "6",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "async_k4_f2",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--async", "--draft", "0.6", "--k", "4", "--f", "2",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "async_k4_f3",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--async", "--draft", "0.6", "--k", "4", "--f", "3",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "async_k6_f2",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--async", "--draft", "0.6", "--k", "6", "--f", "2",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "async_k6_f3",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--async", "--draft", "0.6", "--k", "6", "--f", "3",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "async_k6_f4",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--async", "--draft", "0.6", "--k", "6", "--f", "4",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "async_k8_f3",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--async", "--draft", "0.6", "--k", "8", "--f", "3",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
    {
        "label": "async_k8_f4",
        "args": [
            "--qwen", "--size", "8", "--gpus", "2",
            "--spec", "--async", "--draft", "0.6", "--k", "8", "--f", "4",
            "--b", "1", "--temp", "0", "--numseqs", "32", "--output_len", "128",
            "--random",
        ],
    },
]

SUMMARY_FIELDS = [
    "official_end_to_end_throughput",
    "official_total_time",
    "metrics_decode_throughput",
    "metrics_prefill_throughput",
    "metrics_avg_target_step_time_ms",
    "metrics_avg_target_verify_time_ms",
    "metrics_avg_cache_hits",
    "metrics_avg_accepted_suffix_lens_with_recovery",
    "metrics_avg_accepted_suffix_lens_on_hit",
    "metrics_avg_accepted_suffix_lens_on_miss",
]


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    mu = _mean(values)
    variance = sum((value - mu) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _load_config(path: str | None):
    if path is None:
        return DEFAULT_CONFIGS
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Config file must contain a JSON list")
    return data


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run benchmark combinations multiple times and average the results.")
    parser.add_argument("--repeats", type=int, default=3, help="Number of times to run each configuration.")
    parser.add_argument("--configs", type=str, default=None, help="Optional JSON file describing benchmark configs.")
    parser.add_argument("--output-dir", type=str, default="sim/experiments/results/repeat_runs", help="Directory for per-run summaries and aggregate CSVs.")
    parser.add_argument("--group", type=str, default="qwen8b-repeat-random", help="WandB group name.")
    parser.add_argument("--with-wandb", action="store_true", help="Also log each run to WandB.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    bench_path = repo_root / "bench" / "bench.py"
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    configs = _load_config(args.configs)
    per_run_rows: list[dict] = []

    for config in configs:
        label = config["label"]
        bench_args = list(config["args"])
        for repeat_idx in range(1, args.repeats + 1):
            run_name = f"{label}_r{repeat_idx}"
            summary_path = output_dir / f"{run_name}.json"
            cmd = [
                sys.executable,
                "-O",
                str(bench_path),
                *bench_args,
                "--name", run_name,
                "--group", args.group,
                "--summary-json", str(summary_path),
            ]
            if args.with_wandb:
                cmd.append("--wandb")

            print(f"Running {run_name}: {' '.join(cmd)}", flush=True)
            subprocess.run(cmd, cwd=repo_root / "bench", check=True)

            with summary_path.open() as f:
                summary = json.load(f)
            summary["label"] = label
            summary["repeat"] = repeat_idx
            per_run_rows.append(summary)

    per_run_fieldnames = sorted({key for row in per_run_rows for key in row.keys()})
    _write_csv(output_dir / "per_run_results.csv", per_run_rows, per_run_fieldnames)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in per_run_rows:
        grouped[row["label"]].append(row)

    aggregate_rows: list[dict] = []
    for label, rows in grouped.items():
        aggregate = {
            "label": label,
            "repeats": len(rows),
            "mode": rows[0].get("mode"),
            "gpus": rows[0].get("gpus"),
            "k": rows[0].get("k"),
            "f": rows[0].get("f"),
        }
        for field in SUMMARY_FIELDS:
            values = [row[field] for row in rows if row.get(field) is not None]
            mean = _mean(values)
            std = _std(values)
            if mean is not None:
                aggregate[f"{field}_mean"] = mean
                aggregate[f"{field}_std"] = std
        aggregate_rows.append(aggregate)

    aggregate_fieldnames = sorted({key for row in aggregate_rows for key in row.keys()})
    _write_csv(output_dir / "aggregate_results.csv", aggregate_rows, aggregate_fieldnames)
    print(f"Wrote per-run results to {output_dir / 'per_run_results.csv'}")
    print(f"Wrote aggregate results to {output_dir / 'aggregate_results.csv'}")


if __name__ == "__main__":
    main()
