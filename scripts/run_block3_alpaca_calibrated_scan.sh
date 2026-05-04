#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl_block3_calibrated}"

if [[ -n "${CONDA_ENV:-}" ]]; then
  PYTHON_CMD=(conda run -n "$CONDA_ENV" python)
else
  PYTHON_CMD=("${PYTHON:-python}")
fi

OUT_DIR="${OUT_DIR:-sim/experiments/results/block3_reversal_alpaca_calibrated}"
SUMMARY_DIR="${SUMMARY_DIR:-sim/experiments/results/block3_summary}"

# Fitted from bench/results/block3_timing_alpaca_full_v2/block3_timing_analysis_summary.csv:
#   draft_detail_total_ms ~= -0.003456 + 2.628523*k + 0.007689*k*B
#   verify_ms            ~= 19.613020 + 0.094370*k
ALPHAS="${ALPHAS:-0.60 0.65 0.70 0.735 0.75 0.80 0.85 0.90}"
RS="${RS:-0.6}"
A_VALUES="${A_VALUES:-2.628523}"
B_VALUES="${B_VALUES:-0.0038445 0.005126 0.007689 0.0115335 0.015378 0.023067 0.030756 0.061512 0.07689}"
CAPACITY="${CAPACITY:-12}"
MIN_K="${MIN_K:-1}"
T_V_BASE="${T_V_BASE:-19.613020}"
T_V_SLOPE="${T_V_SLOPE:-0.094370}"

echo "Block 3 Alpaca-calibrated reversal scan"
echo "  out dir:      $OUT_DIR"
echo "  summary dir:  $SUMMARY_DIR"
echo "  alphas:       $ALPHAS"
echo "  r:            $RS"
echo "  a values:     $A_VALUES"
echo "  b values:     $B_VALUES"
echo "  capacity:     $CAPACITY"
echo "  T_V(k):       $T_V_BASE + $T_V_SLOPE*k"

"${PYTHON_CMD[@]}" -m sim.experiments.block3_reversal_scan \
  --alphas "$ALPHAS" \
  --rs "$RS" \
  --as "$A_VALUES" \
  --bs "$B_VALUES" \
  --capacity "$CAPACITY" \
  --min-k "$MIN_K" \
  --t-v-base "$T_V_BASE" \
  --t-v-slope "$T_V_SLOPE" \
  --out-dir "$OUT_DIR"

"${PYTHON_CMD[@]}" -m sim.experiments.block3_summarize_results \
  --out-dir "$SUMMARY_DIR"
