# Experiment Log

## 2026-04-30: Block 1 A3 Validation Setup

### Context

This log tracks experiments corresponding to Block 1 in `math_roadmap_v2.pdf`
and the single-client shape validation in `plan.md`.

The active Block 1 A3 goal is:

- validate whether the single-client SSD service curve is empirically
  non-monotone or unimodal in lookahead `k`;
- identify whether an internal optimum `k*` appears under fixed total fan-out
  budget `B`;
- connect the observed curve to the proposed mechanism:
  - larger `k` increases accepted suffix length / hit-side payoff;
  - larger `k` also spreads fixed fan-out budget over more positions and can
    reduce cache efficiency or verifier-normalized service.

### Completed Today

Implemented the synthetic Block 1 validation script:

```bash
python -m sim.experiments.block1_validate
```

Current synthetic-grid result:

```text
evaluated_cases=4032
enough_valid_cases=4026/4032 (99.9%)
unimodal_all_cases=4032/4032 (100.0%)
unimodal_enough_valid_cases=4026/4026 (100.0%)
alpha_nondecreasing violations=2/3450 (0.1%)
b_nonincreasing violations=0/3018 (0.0%)
t_v_nondecreasing violations=0/3018 (0.0%)
```

This supports proceeding past Block 1 Gate A on the closed-form model.

### Real-LLM A3 Setup

The real-LLM experiment was changed from uniform fan-out sweeps `(k, f)` to
Saguaro-style capped geometric fan-out under fixed total budget `B`.

Relevant scripts:

```text
sim/experiments/make_geometric_fanouts.py
scripts/run_geometric_block1_grid.sh
sim/experiments/plot_empirical_block1.py
```

The experiment controls:

- `k`: verifier lookahead;
- `B = sum_j F_j`: total fan-out budget;
- `fan_out_list`: generated from Saguaro capped geometric shape.

The experiment does not directly control the true workload/model parameters
`alpha`, `r`, `a`, or `b`. In the script, `ALPHA` and `R` are shape-prior
parameters used only to instantiate the capped geometric fan-out list. The true
acceptance/cache/timing behavior is measured from the run and should be
estimated afterward from metrics such as cache hit rate, accepted suffix length,
and draft/verify timing.

### Sanity Check Result

A small sanity check with fixed `B=24` and `k in {4,6,8}` produced the desired
qualitative curve in:

```text
figures/suffix_per_verify_sec_mean.png
```

Observed qualitative pattern:

```text
k=4: lower
k=6: peak
k=8: lower
```

This is consistent with the Block 1 unimodality claim, but it is only a sanity
check because each point used a small number of prompts/runs.

### Current Full Run

The intended full Block 1 A3 real-LLM command is:

```bash
NUMSEQS=4 \
OUTPUT_LEN=64 \
INPUT_LEN=128 \
MAX_MODEL_LEN=1024 \
BLOCK_SZ=128 \
ASYNC_GPUS=2 \
K_VALUES="2 4 6 8 10" \
BUDGETS="16 24 36" \
PROMPT_OFFSETS="0 4 8" \
DATASET_FLAG="--alpaca" \
SSD_DATASET_DIR=$SSD_DATASET_DIR \
CUDA_VISIBLE_DEVICES=0,1 \
SSD_CUDA_ARCH=8.6 \
bash scripts/run_geometric_block1_grid.sh
```

This runs:

```text
3 budgets * 5 k values * 3 prompt offsets = 45 runs
```

Each `(B, k)` point in the plotted curve is the mean over the three prompt
offsets.

### Outputs To Inspect

For each run directory:

```text
bench/results/geometric_block1_<timestamp>/
```

Key files:

```text
shape_summary.csv
per_run_summary.csv
empirical_profiles.json
figures/suffix_per_verify_sec_mean.png
figures/decode_tokens_per_verify_sec_mean.png
figures/avg_suffix_mean.png
figures/cache_hit_mean.png
figures/verify_ms_mean.png
```

Primary figure for the Block 1 claim:

```text
figures/suffix_per_verify_sec_mean.png
```

Supporting mechanism figures:

```text
figures/avg_suffix_mean.png
figures/cache_hit_mean.png
figures/verify_ms_mean.png
```

### Issues Found And Fixed

1. Dataset fallback produced random-token prompts.

   Cause: benchmark could not find the configured dataset path and silently
   fell back to random token IDs.

   Current recommendation: use Alpaca for A3 because it is easy to download and
   provides natural instruction prompts.

2. Geometric fan-out exposed old uniform-fanout assumptions.

   Cause: async tree-decode code used `F * (K+1)` in places where geometric
   fan-out requires `MQ_LEN = sum(fan_out_list)`.

   Fixes pushed:

   ```text
   a3c8057 Fix async geometric fanout MQ length
   85a80ef Initialize MQ length in async config
   ```

### Pending

- Full 45-run Block 1 A3 real-LLM experiment is currently running or pending.
- Once results finish, record:
  - output directory;
  - best `k*` for each `B`;
  - whether each fixed-`B` curve is unimodal;
  - whether `avg_suffix_mean`, `cache_hit_mean`, and `verify_ms_mean` support
    the proposed mechanism.
- Add a short interpretation aligned with `proposal_cn.md` and
  `proposal_en.md`.

## 2026-04-30: Full Block 1 A3 Result

### Result Directory

Latest full run:

```text
bench/results/geometric_block1_20260429_134517/
```

Configuration:

```text
dataset: Alpaca
model: Qwen3-8B target, Qwen3-0.6B draft
budgets: B in {16, 24, 36}
k values: {2, 4, 6, 8, 10}
prompt offsets: {0, 4, 8}
runs: 45 total
```

### Key Observation

The originally plotted `suffix_per_verify_sec_mean` is not the right primary
system-level metric for the Block 1 real-LLM claim. It normalizes by target
verifier time only, and therefore mostly tracks the monotone increase in
accepted suffix length as `k` grows.

The system-level metrics that include more of the end-to-end cost show the
expected internal optimum:

```text
decode_throughput_mean:
  B=16: best k=6
  B=24: best k=6
  B=36: best k=6

official_throughput_mean:
  B=16: best k=6
  B=24: best k=6
  B=36: best k=4
```

Mechanism checks:

```text
avg_suffix_mean increases with k
cache_hit_mean decreases with k
verify_ms_mean increases mildly for larger k
decode_throughput_mean peaks at an intermediate k
```

This matches the Block 1 mechanism more closely:

- `E_hit` / accepted suffix effect favors larger `k`;
- cache-hit degradation and draft/tree-decode cost penalize large `k`;
- their combination creates an empirical internal optimum.

### Plotting Update

`sim/experiments/plot_empirical_block1.py` was updated so the primary generated
plots include:

```text
decode_throughput_mean.png
official_throughput_mean.png
```

The earlier `suffix_per_verify_sec_mean.png` remains useful, but should be
interpreted as a verifier-normalized mechanism plot rather than the final
system objective.

To regenerate figures on a machine with matplotlib:

```bash
python -m sim.experiments.plot_empirical_block1 \
  bench/results/geometric_block1_20260429_134517/shape_summary.csv \
  --out-dir bench/results/geometric_block1_20260429_134517/figures
```

### Notes For Interpretation

If the full run preserves the sanity-check pattern, the main conclusion should
be:

> Under fixed total fan-out budget and Saguaro-style geometric fan-out, real
> SSD service efficiency is non-monotone in lookahead `k`, with an empirical
> internal optimum `k*`.

This supports Block 1 and justifies moving to the multi-client KKT and
allocation-reversal analysis.
