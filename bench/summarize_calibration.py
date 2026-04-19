import argparse
import csv
import json
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


def main():
    parser = argparse.ArgumentParser(description="Summarize SSD calibration JSON records")
    parser.add_argument("inputs", nargs="+", help="Calibration JSON files or directories")
    parser.add_argument("--csv", type=str, default=None, help="Optional CSV output path")
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


if __name__ == "__main__":
    main()
