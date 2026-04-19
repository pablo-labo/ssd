#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$ROOT_DIR/bench"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${OUT_DIR:-$BENCH_DIR/results/calibration_$STAMP}"

NUMSEQS="${NUMSEQS:-32}"
OUTPUT_LEN="${OUTPUT_LEN:-128}"
INPUT_LEN="${INPUT_LEN:-128}"
ASYNC_GPUS="${ASYNC_GPUS:-2}"
SYNC_GPUS="${SYNC_GPUS:-1}"
DATASET_FLAG="${DATASET_FLAG:-}"
RUN_BASELINES="${RUN_BASELINES:-1}"

mkdir -p "$OUT_DIR"

cd "$BENCH_DIR"

common_args=(
  --qwen
  --size 8
  --b 1
  --temp 0
  --input_len "$INPUT_LEN"
  --numseqs "$NUMSEQS"
  --output_len "$OUTPUT_LEN"
)

if [[ -n "$DATASET_FLAG" ]]; then
  common_args+=("$DATASET_FLAG")
fi

echo "Writing calibration JSON files to: $OUT_DIR"

if [[ "$RUN_BASELINES" == "1" ]]; then
  python -O bench.py \
    "${common_args[@]}" \
    --gpus "$SYNC_GPUS" \
    --name ar_baseline \
    --calibration-json "$OUT_DIR/ar_baseline.json"

  python -O bench.py \
    "${common_args[@]}" \
    --gpus "$SYNC_GPUS" \
    --spec --draft 0.6 --k 6 \
    --name sync_sd_k6 \
    --calibration-json "$OUT_DIR/sync_sd_k6.json"
fi

python -O bench.py \
  "${common_args[@]}" \
  --gpus "$ASYNC_GPUS" \
  --spec --async --draft 0.6 --k 4 --f 2 \
  --name async_ssd_k4_f2 \
  --calibration-json "$OUT_DIR/async_ssd_k4_f2.json"

python -O bench.py \
  "${common_args[@]}" \
  --gpus "$ASYNC_GPUS" \
  --spec --async --draft 0.6 --k 6 --f 3 \
  --name async_ssd_k6_f3 \
  --calibration-json "$OUT_DIR/async_ssd_k6_f3.json"

python -O bench.py \
  "${common_args[@]}" \
  --gpus "$ASYNC_GPUS" \
  --spec --async --draft 0.6 --k 8 --f 4 \
  --name async_ssd_k8_f4 \
  --calibration-json "$OUT_DIR/async_ssd_k8_f4.json"

python summarize_calibration.py "$OUT_DIR" --csv "$OUT_DIR/summary.csv"

echo
echo "Calibration complete."
echo "JSON directory: $OUT_DIR"
echo "CSV summary:    $OUT_DIR/summary.csv"
