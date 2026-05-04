#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"

OUT_DIR="${OUT_DIR:-$ROOT_DIR/bench/results/block3_timing_$STAMP}"
LOG_PATH="${LOG_PATH:-$OUT_DIR/run.log}"

# Overnight defaults: fine k grid, multiple budgets, three prompt offsets.
K_VALUES="${K_VALUES:-2 3 4 5 6 7 8 9 10 11 12}"
BUDGETS="${BUDGETS:-16 24 36 48 64}"
PROMPT_OFFSETS="${PROMPT_OFFSETS:-0 8 16}"

# Shape prior from the latest Block 1 rough calibration.
ALPHA="${ALPHA:-0.735}"
R="${R:-0.6}"

# Real-run defaults.
MODEL_SIZE="${MODEL_SIZE:-8}"
DRAFT_SIZE="${DRAFT_SIZE:-0.6}"
NUMSEQS="${NUMSEQS:-4}"
OUTPUT_LEN="${OUTPUT_LEN:-64}"
INPUT_LEN="${INPUT_LEN:-128}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-1024}"
BLOCK_SZ="${BLOCK_SZ:-128}"
BATCH_SIZE="${BATCH_SIZE:-1}"
ASYNC_GPUS="${ASYNC_GPUS:-2}"
DATASET_FLAG="${DATASET_FLAG:-}"

mkdir -p "$OUT_DIR"

echo "Block 3 timing calibration grid"
echo "  out dir:        $OUT_DIR"
echo "  log path:       $LOG_PATH"
echo "  k values:       $K_VALUES"
echo "  budgets:        $BUDGETS"
echo "  alpha, r:       $ALPHA, $R"
echo "  prompt offsets: $PROMPT_OFFSETS"
echo "  dataset flag:   ${DATASET_FLAG:-<gsm default>}"
echo

export SSD_PROFILE_DRAFT="${SSD_PROFILE_DRAFT:-1}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl_block3_timing}"

(
  OUT_DIR="$OUT_DIR" \
  K_VALUES="$K_VALUES" \
  BUDGETS="$BUDGETS" \
  PROMPT_OFFSETS="$PROMPT_OFFSETS" \
  ALPHA="$ALPHA" \
  R="$R" \
  MODEL_SIZE="$MODEL_SIZE" \
  DRAFT_SIZE="$DRAFT_SIZE" \
  NUMSEQS="$NUMSEQS" \
  OUTPUT_LEN="$OUTPUT_LEN" \
  INPUT_LEN="$INPUT_LEN" \
  MAX_MODEL_LEN="$MAX_MODEL_LEN" \
  BLOCK_SZ="$BLOCK_SZ" \
  BATCH_SIZE="$BATCH_SIZE" \
  ASYNC_GPUS="$ASYNC_GPUS" \
  DATASET_FLAG="$DATASET_FLAG" \
  bash "$ROOT_DIR/scripts/run_geometric_block1_grid.sh"
) 2>&1 | tee "$LOG_PATH"

python "$ROOT_DIR/bench/summarize_draft_profile_log.py" "$LOG_PATH" \
  --csv "$OUT_DIR/draft_profile_summary.csv"

echo
echo "Done."
echo "Run log:              $LOG_PATH"
echo "Per-run summary:      $OUT_DIR/per_run_summary.csv"
echo "Shape summary:        $OUT_DIR/shape_summary.csv"
echo "Draft profile CSV:    $OUT_DIR/draft_profile_summary.csv"
