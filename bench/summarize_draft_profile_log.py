from __future__ import annotations

import argparse
import csv
import re
import statistics
from pathlib import Path


RUN_RE = re.compile(r"^Running (?P<run_name>\S+)")
SERVICE_RE = re.compile(
    r"^\[PROFILE draft\] "
    r"service=(?P<service>[-+0-9.]+)ms "
    r"build_tree=(?P<build_tree>[-+0-9.]+)ms "
    r"decode_tree=(?P<decode_tree>[-+0-9.]+)ms "
    r"populate=(?P<populate>[-+0-9.]+)ms "
    r"total=(?P<total>[-+0-9.]+)ms"
)
DETAIL_RE = re.compile(
    r"^\[PROFILE draft_detail\] "
    r"K=(?P<k>\d+) "
    r"total=(?P<detail_total>[-+0-9.]+)ms "
    r"avg_step=(?P<avg_step>[-+0-9.]+)ms"
)


FIELDS = [
    "run_name",
    "draft_profile_steps",
    "draft_service_ms_mean",
    "draft_build_tree_ms_mean",
    "draft_decode_tree_ms_mean",
    "draft_populate_ms_mean",
    "draft_total_ms_mean",
    "draft_total_ms_p50",
    "draft_total_ms_p90",
    "draft_detail_steps",
    "draft_detail_total_ms_mean",
    "draft_detail_avg_step_ms_mean",
    "profile_k",
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize SSD_PROFILE_DRAFT lines from a timing-grid log.")
    parser.add_argument("log", type=Path)
    parser.add_argument("--csv", type=Path, required=True)
    return parser


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _fmt(value: float | int | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def parse_log(path: Path) -> dict[str, dict[str, list[float] | list[int]]]:
    runs: dict[str, dict[str, list[float] | list[int]]] = {}
    current_run: str | None = None

    with path.open(errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            run_match = RUN_RE.match(line)
            if run_match:
                current_run = run_match.group("run_name")
                runs.setdefault(current_run, _empty_record())
                continue

            if current_run is None:
                continue

            service_match = SERVICE_RE.match(line)
            if service_match:
                record = runs.setdefault(current_run, _empty_record())
                for key in ("service", "build_tree", "decode_tree", "populate", "total"):
                    record[key].append(float(service_match.group(key)))  # type: ignore[index, union-attr]
                continue

            detail_match = DETAIL_RE.match(line)
            if detail_match:
                record = runs.setdefault(current_run, _empty_record())
                record["profile_k"].append(int(detail_match.group("k")))  # type: ignore[index, union-attr]
                record["detail_total"].append(float(detail_match.group("detail_total")))  # type: ignore[index, union-attr]
                record["avg_step"].append(float(detail_match.group("avg_step")))  # type: ignore[index, union-attr]

    return runs


def _empty_record() -> dict[str, list[float] | list[int]]:
    return {
        "service": [],
        "build_tree": [],
        "decode_tree": [],
        "populate": [],
        "total": [],
        "detail_total": [],
        "avg_step": [],
        "profile_k": [],
    }


def build_rows(runs: dict[str, dict[str, list[float] | list[int]]]) -> list[dict[str, str]]:
    rows = []
    for run_name, record in sorted(runs.items()):
        totals = record["total"]  # type: ignore[assignment]
        detail_totals = record["detail_total"]  # type: ignore[assignment]
        avg_steps = record["avg_step"]  # type: ignore[assignment]
        profile_ks = record["profile_k"]  # type: ignore[assignment]
        profile_k = int(statistics.mode(profile_ks)) if profile_ks else None
        rows.append({
            "run_name": run_name,
            "draft_profile_steps": _fmt(len(totals)),
            "draft_service_ms_mean": _fmt(_mean(record["service"])),  # type: ignore[arg-type]
            "draft_build_tree_ms_mean": _fmt(_mean(record["build_tree"])),  # type: ignore[arg-type]
            "draft_decode_tree_ms_mean": _fmt(_mean(record["decode_tree"])),  # type: ignore[arg-type]
            "draft_populate_ms_mean": _fmt(_mean(record["populate"])),  # type: ignore[arg-type]
            "draft_total_ms_mean": _fmt(_mean(totals)),  # type: ignore[arg-type]
            "draft_total_ms_p50": _fmt(_percentile(totals, 0.50)),  # type: ignore[arg-type]
            "draft_total_ms_p90": _fmt(_percentile(totals, 0.90)),  # type: ignore[arg-type]
            "draft_detail_steps": _fmt(len(detail_totals)),
            "draft_detail_total_ms_mean": _fmt(_mean(detail_totals)),  # type: ignore[arg-type]
            "draft_detail_avg_step_ms_mean": _fmt(_mean(avg_steps)),  # type: ignore[arg-type]
            "profile_k": _fmt(profile_k),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = _build_parser().parse_args()
    rows = build_rows(parse_log(args.log))
    write_csv(args.csv, rows)
    populated = [row for row in rows if row["draft_profile_steps"] != "0"]
    print(f"runs_seen={len(rows)}")
    print(f"runs_with_draft_profile={len(populated)}")
    print(f"wrote={args.csv}")


if __name__ == "__main__":
    main()
