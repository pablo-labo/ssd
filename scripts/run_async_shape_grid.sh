#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$ROOT_DIR/bench"
STAMP="$(date +%Y%m%d_%H%M%S)"

OUT_DIR="${OUT_DIR:-$BENCH_DIR/results/async_shape_grid_$STAMP}"
SHAPES="${SHAPES:-4:1 4:2 4:4 6:1 6:2 6:3 8:1 8:2 8:4}"
PROMPT_OFFSETS="${PROMPT_OFFSETS:-0 4 8}"

MODEL_SIZE="${MODEL_SIZE:-8}"
DRAFT_SIZE="${DRAFT_SIZE:-0.6}"
ASYNC_GPUS="${ASYNC_GPUS:-2}"
NUMSEQS="${NUMSEQS:-4}"
OUTPUT_LEN="${OUTPUT_LEN:-64}"
INPUT_LEN="${INPUT_LEN:-128}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-1024}"
BLOCK_SZ="${BLOCK_SZ:-128}"
TEMP="${TEMP:-0}"
BATCH_SIZE="${BATCH_SIZE:-1}"
DATASET_FLAG="${DATASET_FLAG:-}"

mkdir -p "$OUT_DIR"

export HF_HOME="${HF_HOME:-$ROOT_DIR/models/huggingface}"
export SSD_HF_CACHE="${SSD_HF_CACHE:-$HF_HOME/hub}"
export SSD_DATASET_DIR="${SSD_DATASET_DIR:-$ROOT_DIR/datasets}"
export SSD_CUDA_ARCH="${SSD_CUDA_ARCH:-8.9}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1}"
export NCCL_P2P_DISABLE="${NCCL_P2P_DISABLE:-1}"
export NCCL_IB_DISABLE="${NCCL_IB_DISABLE:-1}"
export NCCL_DEBUG="${NCCL_DEBUG:-WARN}"
export TORCH_NCCL_ASYNC_ERROR_HANDLING="${TORCH_NCCL_ASYNC_ERROR_HANDLING:-1}"
export TORCH_NCCL_BLOCKING_WAIT="${TORCH_NCCL_BLOCKING_WAIT:-1}"

cd "$BENCH_DIR"

echo "Async SSD shape grid"
echo "  output dir:      $OUT_DIR"
echo "  shapes:          $SHAPES"
echo "  prompt offsets:  $PROMPT_OFFSETS"
echo "  model size:      Qwen3-$MODEL_SIZE"
echo "  draft size:      Qwen3-$DRAFT_SIZE"
echo "  numseqs:         $NUMSEQS"
echo "  output_len:      $OUTPUT_LEN"
echo "  max_model_len:   $MAX_MODEL_LEN"
echo "  CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo

python - <<'PY'
import torch
print("torch.cuda.device_count =", torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(i, torch.cuda.get_device_name(i))
PY

common_args=(
  --qwen
  --size "$MODEL_SIZE"
  --gpus "$ASYNC_GPUS"
  --spec
  --async
  --draft "$DRAFT_SIZE"
  --b "$BATCH_SIZE"
  --temp "$TEMP"
  --input_len "$INPUT_LEN"
  --numseqs "$NUMSEQS"
  --output_len "$OUTPUT_LEN"
  --max_model_len "$MAX_MODEL_LEN"
  --block_sz "$BLOCK_SZ"
)

if [[ -n "$DATASET_FLAG" ]]; then
  common_args+=("$DATASET_FLAG")
fi

for shape in $SHAPES; do
  k="${shape%%:*}"
  f="${shape##*:}"
  for offset in $PROMPT_OFFSETS; do
    run_name="async_qwen${MODEL_SIZE}b_k${k}_f${f}_n${NUMSEQS}_o${OUTPUT_LEN}_off${offset}"
    out_json="$OUT_DIR/${run_name}.json"

    if [[ -s "$out_json" ]]; then
      echo "Skipping existing $out_json"
      continue
    fi

    echo
    echo "============================================================"
    echo "Running $run_name"
    echo "============================================================"

    python -O bench.py \
      "${common_args[@]}" \
      --k "$k" \
      --f "$f" \
      --prompt_offset "$offset" \
      --name "$run_name" \
      --calibration-json "$out_json"
  done
done

python summarize_calibration.py "$OUT_DIR" \
  --csv "$OUT_DIR/per_run_summary.csv" \
  --group-csv "$OUT_DIR/shape_summary.csv" \
  --profile-json "$OUT_DIR/empirical_profiles.json"

echo
echo "Done."
echo "Per-run CSV:       $OUT_DIR/per_run_summary.csv"
echo "Shape summary CSV: $OUT_DIR/shape_summary.csv"
echo "Profile JSON:      $OUT_DIR/empirical_profiles.json"
