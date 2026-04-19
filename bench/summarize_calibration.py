import argparse
import csv
import json
import math
import statistics
from pathlib import Path


SUMMARY_FIELDS = [
    "run_name",
    "model_name",
    "dataset",
    "shape_mode",
    "k",
    "f",
    "fan_out_list_hit",
    "fan_out_list_miss",
    "batch_size",
    "temperature",
    "numseqs",
    "output_len",
    "official_end_to_end_throughput",
    "metrics_decode_throughput",
    "metrics_avg_accepted_suffix_lens_with_recovery",
    "metrics_avg_accepted_suffix_lens_on_hit",
    "metrics_avg_accepted_suffix_lens_on_miss",
    "metrics_avg_cache_hits",
    "metrics_avg_target_verify_time_ms",
    "metrics_decode_tokens_per_target_verify_second",
    "metrics_accepted_suffix_tokens_per_target_verify_second",
    "metrics_spec_steps",
]


GROUP_FIELDS = [
    "model_name",
    "dataset",
    "shape_mode",
    "k",
    "f",
    "runs",
    "total_spec_steps",
    "avg_suffix_mean",
    "avg_suffix_std",
    "cache_hit_mean",
    "cache_hit_std",
    "verify_ms_mean",
    "verify_ms_std",
    "suffix_per_verify_sec_mean",
    "suffix_per_verify_sec_std",
    "decode_tokens_per_verify_sec_mean",
    "decode_tokens_per_verify_sec_std",
    "decode_throughput_mean",
    "decode_throughput_std",
    "official_throughput_mean",
    "official_throughput_std",
]


PROFILE_FIELDS = {
    "accepted_suffix": "metrics_avg_accepted_suffix_lens_with_recovery",
    "cache_hit_rate": "metrics_avg_cache_hits",
    "target_verify_time_ms": "metrics_avg_target_verify_time_ms",
    "accepted_suffix_per_verify_sec": "metrics_accepted_suffix_tokens_per_target_verify_second",
    "decode_tokens_per_verify_sec": "metrics_decode_tokens_per_target_verify_second",
}


def _load_records(paths):
    records = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            files = sorted(path.glob("*.json"))
        else:
            files = [path]
        for file_path in files:
            with file_path.open() as f:
                record = json.load(f)
            records.append(record)
    return records


def _row(record):
    shape = record.get("shape", {})
    row = {field: record.get(field) for field in SUMMARY_FIELDS}
    row["shape_mode"] = shape.get("mode")
    row["k"] = shape.get("k", record.get("k"))
    row["f"] = shape.get("f", record.get("f"))
    row["fan_out_list_hit"] = shape.get("fan_out_list_hit", record.get("fan_out_list_hit"))
    row["fan_out_list_miss"] = shape.get("fan_out_list_miss", record.get("fan_out_list_miss"))
    return row


def _format_value(value):
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def print_markdown(rows):
    print("| " + " | ".join(SUMMARY_FIELDS) + " |")
    print("| " + " | ".join(["---"] * len(SUMMARY_FIELDS)) + " |")
    for row in rows:
        print("| " + " | ".join(_format_value(row.get(field)) for field in SUMMARY_FIELDS) + " |")


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _numeric(value):
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _mean(values):
    nums = [_numeric(value) for value in values]
    nums = [value for value in nums if value is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _std(values):
    nums = [_numeric(value) for value in values]
    nums = [value for value in nums if value is not None]
    if len(nums) < 2:
        return 0.0 if nums else None
    return statistics.stdev(nums)


def _group_key(row):
    return (
        row.get("model_name"),
        row.get("dataset"),
        row.get("shape_mode"),
        row.get("k"),
        row.get("f"),
    )


def build_group_rows(rows):
    groups = {}
    for row in rows:
        groups.setdefault(_group_key(row), []).append(row)

    group_rows = []
    for (model_name, dataset, shape_mode, k, f), items in groups.items():
        group_rows.append({
            "model_name": model_name,
            "dataset": dataset,
            "shape_mode": shape_mode,
            "k": k,
            "f": f,
            "runs": len(items),
            "total_spec_steps": sum(int(_numeric(item.get("metrics_spec_steps")) or 0) for item in items),
            "avg_suffix_mean": _mean(item.get("metrics_avg_accepted_suffix_lens_with_recovery") for item in items),
            "avg_suffix_std": _std(item.get("metrics_avg_accepted_suffix_lens_with_recovery") for item in items),
            "cache_hit_mean": _mean(item.get("metrics_avg_cache_hits") for item in items),
            "cache_hit_std": _std(item.get("metrics_avg_cache_hits") for item in items),
            "verify_ms_mean": _mean(item.get("metrics_avg_target_verify_time_ms") for item in items),
            "verify_ms_std": _std(item.get("metrics_avg_target_verify_time_ms") for item in items),
            "suffix_per_verify_sec_mean": _mean(item.get("metrics_accepted_suffix_tokens_per_target_verify_second") for item in items),
            "suffix_per_verify_sec_std": _std(item.get("metrics_accepted_suffix_tokens_per_target_verify_second") for item in items),
            "decode_tokens_per_verify_sec_mean": _mean(item.get("metrics_decode_tokens_per_target_verify_second") for item in items),
            "decode_tokens_per_verify_sec_std": _std(item.get("metrics_decode_tokens_per_target_verify_second") for item in items),
            "decode_throughput_mean": _mean(item.get("metrics_decode_throughput") for item in items),
            "decode_throughput_std": _std(item.get("metrics_decode_throughput") for item in items),
            "official_throughput_mean": _mean(item.get("official_end_to_end_throughput") for item in items),
            "official_throughput_std": _std(item.get("official_end_to_end_throughput") for item in items),
        })

    group_rows.sort(key=lambda row: (
        row.get("dataset") or "",
        row.get("shape_mode") or "",
        row.get("k") if row.get("k") is not None else -1,
        row.get("f") if row.get("f") is not None else -1,
    ))
    return group_rows


def write_group_csv(path, group_rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=GROUP_FIELDS)
        writer.writeheader()
        for row in group_rows:
            writer.writerow(row)


def write_profile_json(path, group_rows):
    profiles = []
    for row in group_rows:
        profiles.append({
            "model_name": row.get("model_name"),
            "dataset": row.get("dataset"),
            "shape_mode": row.get("shape_mode"),
            "k": row.get("k"),
            "f": row.get("f"),
            "runs": row.get("runs"),
            "total_spec_steps": row.get("total_spec_steps"),
            "metrics": {
                "accepted_suffix_mean": row.get("avg_suffix_mean"),
                "accepted_suffix_std": row.get("avg_suffix_std"),
                "cache_hit_rate_mean": row.get("cache_hit_mean"),
                "cache_hit_rate_std": row.get("cache_hit_std"),
                "target_verify_time_ms_mean": row.get("verify_ms_mean"),
                "target_verify_time_ms_std": row.get("verify_ms_std"),
                "accepted_suffix_per_verify_sec_mean": row.get("suffix_per_verify_sec_mean"),
                "accepted_suffix_per_verify_sec_std": row.get("suffix_per_verify_sec_std"),
                "decode_tokens_per_verify_sec_mean": row.get("decode_tokens_per_verify_sec_mean"),
                "decode_tokens_per_verify_sec_std": row.get("decode_tokens_per_verify_sec_std"),
            },
        })

    with open(path, "w") as f:
        json.dump({"profiles": profiles}, f, indent=2, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(description="Summarize SSD calibration JSON records")
    parser.add_argument("inputs", nargs="+", help="Calibration JSON files or directories")
    parser.add_argument("--csv", type=str, default=None, help="Optional CSV output path")
    parser.add_argument("--group-csv", type=str, default=None,
                        help="Optional CSV output with mean/std grouped by model, dataset, mode, k, f")
    parser.add_argument("--profile-json", type=str, default=None,
                        help="Optional grouped JSON profile for feeding empirical curves into sim")
    args = parser.parse_args()

    records = _load_records(args.inputs)
    rows = [_row(record) for record in records]
    rows.sort(key=lambda row: (
        row.get("dataset") or "",
        row.get("shape_mode") or "",
        row.get("k") if row.get("k") is not None else -1,
        row.get("f") if row.get("f") is not None else -1,
        row.get("run_name") or "",
    ))

    print_markdown(rows)

    if args.csv:
        write_csv(args.csv, rows)

    if args.group_csv or args.profile_json:
        group_rows = build_group_rows(rows)
        if args.group_csv:
            write_group_csv(args.group_csv, group_rows)
        if args.profile_json:
            write_profile_json(args.profile_json, group_rows)


if __name__ == "__main__":
    main()
