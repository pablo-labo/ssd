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

## 2026-04-30: GSM8K Fine-Grained Block 1 A3 Result

### Motivation

After the first real-LLM A3 run, we used the measured acceptance/cache behavior
to update the capped-geometric fan-out prior. The previous values
`alpha=0.8, r=0.8` appeared optimistic. A rough empirical calibration from the
Alpaca run suggested:

```text
alpha ~= 0.735
r ~= 0.6
```

The goal of this follow-up run was to check whether the fixed-budget
unimodality remains visible under a more realistic shape prior and a finer
grid of `k`.

### Configuration

Remote run configuration:

```text
dataset: GSM8K
model: Qwen3-8B target, Qwen3-0.6B draft
hardware: 2 x RTX 4090
fixed budget: B = 36
shape prior: alpha = 0.735, r = 0.6
k values: {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
prompt offsets: {0, 4}
runs: 22 total
```

Each plotted point is the mean over two prompt offsets for the same `(B, k,
fanout)` setting.

The intended command shape was:

```bash
export SSD_CUDA_ARCH=8.9
export CUDA_VISIBLE_DEVICES=0,1
export ASYNC_GPUS=2
export DATASET_FLAG=""
export BUDGETS="36"
export ALPHA="0.735"
export R="0.6"
export K_VALUES="2 3 4 5 6 7 8 9 10 11 12"
export PROMPT_OFFSETS="0 4"
export NUMSEQS=4
export OUTPUT_LEN=64
export INPUT_LEN=128
export MAX_MODEL_LEN=1024
export BLOCK_SZ=128
export BATCH_SIZE=1
bash scripts/run_geometric_block1_grid.sh
```

Note: use an absolute `OUT_DIR` on the remote machine. A relative `OUT_DIR`
such as `bench/results/...` can be interpreted under `bench/` after the script
changes directory, which places results in `bench/bench/results/...` and causes
the final plotting step to miss `shape_summary.csv`.

### Key Result

The primary metric `decode_throughput_mean` shows a clear internal optimum:

```text
k=2:  about 94 tokens/s
k=3:  about 110 tokens/s
k=4:  about 129 tokens/s
k=5:  about 140 tokens/s  <-- best observed point
k=6:  about 130 tokens/s
k=7:  about 122 tokens/s
k=8:  about 113 tokens/s
k=9:  about 103 tokens/s
k=10: about 98 tokens/s
k=11: about 91 tokens/s
k=12: about 85 tokens/s
```

This is stronger than the earlier coarse grid because the peak is now resolved
at integer granularity. Under `B=36`, the best observed lookahead is:

```text
k* ~= 5
```

### Interpretation

This supports the Block 1 A3 claim on real LLM execution:

- small `k` underuses the speculative lookahead opportunity;
- increasing `k` initially improves accepted work per decoding step;
- after the optimum, the fixed budget `B` is spread across too many positions,
  reducing cache/fan-out effectiveness and lowering end-to-end decode
  throughput;
- the resulting service curve is empirically unimodal in `k`.

The first Alpaca run established the same qualitative pattern across multiple
budgets (`B in {16, 24, 36}`). The GSM8K follow-up fixes `B=36` and gives a
cleaner fine-grained estimate of the optimum.

### Next Checks

For the GSM8K run, collect or regenerate the supporting mechanism plots:

```text
avg_suffix_mean.png
cache_hit_mean.png
verify_ms_mean.png
official_throughput_mean.png
```

These should be used to explain the mechanism behind the primary
`decode_throughput_mean` curve. The final paper figure should likely use
`decode_throughput_mean` as the main panel and the mechanism metrics as
secondary panels.

## 2026-05-03: Block 1 A2 Math-To-Experiment Alignment

### Source Note

Today we connected the current Block 1 experiments to the detailed A2
derivation in:

```text
paper/math/block1a2.md
```

The A2 note reframes the single-client problem as a service-curve structure
result for `tilde(mu)^SSD(k)`. The central question is whether increasing
lookahead `k` is always beneficial. The answer is no: hit-side payoff improves
with `k`, but miss probability and drafter-budget pressure also increase.

### Mathematical Claims To Support

The A2 note organizes the result around four claims:

```text
Lemma 1:
  Miss probability q(k) is increasing on the effective interval I.

Proposition 1:
  Any interior maximizer k* satisfies the FOC
  marginal hit benefit = marginal miss cost.

Theorem 1:
  Under the finite-T_V regularity assumption q''(k) >= 0,
  tilde(mu)^SSD(k) is single-peaked on I.

Theorem 2:
  In the large-T_V unsaturated regime,
  k* = r log(T_V) / log(1/alpha) + O(log log T_V).
```

The key FOC from the note is:

```text
alpha^k* log(1/alpha) p_hit(k*) = q'(k*) (1 - alpha^k*)
```

Interpretation:

```text
left side:  marginal hit benefit from extending lookahead;
right side: marginal miss cost from increasing miss probability.
```

This gives the clean story for experiments: a peak in throughput should occur
where the hit-side gain from larger `k` is overtaken by the cache-miss/fan-out
cost.

### What The Current Experiments Validate

The current real-LLM evidence validates the qualitative A2 mechanism:

```text
Alpaca coarse run:
  B in {16, 24, 36}
  k in {2, 4, 6, 8, 10}
  decode_throughput_mean peaks internally, around k = 4 to 6.

GSM8K fine run:
  B = 36
  k in {2, 3, ..., 12}
  alpha-prior = 0.735, r-prior = 0.6
  decode_throughput_mean peaks clearly around k = 5.
```

This directly supports Theorem 1's empirical content:

```text
tilde(mu)^SSD(k) is not monotone increasing in realistic SSD execution;
it is empirically single-peaked over the tested interval.
```

The GSM8K fine-grained result is especially useful because the integer peak is
resolved:

```text
k=2:  about 94 tokens/s
k=3:  about 110 tokens/s
k=4:  about 129 tokens/s
k=5:  about 140 tokens/s  <-- best observed point
k=6:  about 130 tokens/s
k>6:  steadily decreases through k=12
```

### How The Existing Metrics Map To A2 Variables

The experiments do not directly observe all A2 symbols, but several metrics map
onto the theory:

```text
alpha:
  estimated from accepted suffix statistics.
  The previous Alpaca run suggested an empirical center around alpha ~= 0.735.

r:
  estimated from cache-hit decay across fan-out budgets.
  The previous Alpaca run suggested a rough center around r ~= 0.6.

q(k):
  represented empirically by 1 - cache_hit_mean.

tilde(mu)^SSD(k):
  represented primarily by decode_throughput_mean.

k*:
  measured as the k that maximizes decode_throughput_mean for a fixed
  configuration.
```

The most important mechanism plots to keep with the A2 story are:

```text
decode_throughput_mean.png  primary service curve
avg_suffix_mean.png         hit-side payoff proxy
cache_hit_mean.png          miss/cache proxy
verify_ms_mean.png          verifier-side timing proxy
```

### What Is Not Yet Fully Validated

The experiments so far are strong evidence for conditional single-peakedness,
but they do not yet validate every A2 corollary.

Still pending:

```text
q''(k) >= 0:
  The A2 note uses this as a finite-T_V assumption. We need numerical checks on
  the measured or model-implied q(k) curves.

k* monotonicity in alpha:
  The A2 note predicts partial k*/partial alpha > 0. We need dataset/workload
  or synthetic-profile sweeps that produce different measured alpha values.

k* monotonicity in T_V:
  The A2 note predicts partial k*/partial T_V > 0. Current B sweeps are useful,
  but we still need a cleaner bridge from B to the A2 budget formula
  B(k) = (T_V - a k)/(b k).

k* monotonicity in r:
  The A2 note predicts partial k*/partial r > 0. We have only a rough estimate
  of r from the existing B sweep.

k* monotonicity in b:
  The A2 note predicts partial k*/partial b < 0 through second-order terms. We
  need draft/tree timing calibration before claiming this empirically.
```

### Next Experiment Plan For A2

The next phase should explicitly target the A2 corollaries rather than only
showing another single-peaked curve.

Recommended runs:

```text
1. Workload/alpha sweep
   Run the fine k grid on GSM8K, Alpaca, HumanEval, and C4.
   Estimate alpha for each workload and test whether higher-alpha workloads
   have larger observed k*.

2. Budget/T_V proxy sweep
   Repeat fine k grids for B in {24, 36, 48} under the calibrated
   alpha/r priors. Check whether k* shifts upward as budget increases.

3. Convexity check for q(k)
   For each fixed configuration, plot q(k)=1-cache_hit_mean and finite
   differences of q'(k). This directly tests the A2.1 assumption q''(k)>=0.

4. Timing calibration
   Extract draft/tree timing terms to estimate a and b. This is required before
   validating the predicted negative dependence of k* on b.
```

### Current Research Status

Current status relative to A2:

```text
Lemma-level direction q'(k)>0:
  qualitatively consistent with observed cache-hit degradation as k grows.

FOC mechanism:
  supported qualitatively by the observed transition from increasing to
  decreasing throughput.

Conditional single-peakedness:
  strongly supported by real-LLM Alpaca and GSM8K runs.

Large-T_V scaling and monotonicity corollaries:
  not yet experimentally validated; these define the next targeted sweeps.
```

For slides, the clean statement is:

```text
We now have real-system evidence for the single-peaked service curve predicted
by Block 1 A2. The remaining A2 work is to validate the parameter movement of
k*, especially with respect to alpha, effective budget T_V/B, and drafter cost
b.
```

## 2026-05-05: Block 3 Allocation-Reversal Scan

### Motivation

After Block 1 established a single-client SSD service curve with an internal
optimum, we moved to the roadmap's Block 3 question:

```text
Does there exist a non-trivial parameter region R where GoodSpeed's allocation
order differs from the SSD-aware optimum?
```

The implemented scanner is:

```bash
python -m sim.experiments.block3_reversal_scan
```

The scanner compares:

```text
GoodSpeed baseline:
  maximize log(mu_GS_1(k1)) + log(mu_GS_2(k2))
  where mu_GS_i(k) = (1 - alpha_i^(k+1)) / (1 - alpha_i)

SSD-aware oracle:
  maximize log(mu_SSD_1(k1,k2)) + log(mu_SSD_2(k2,k1))
  where B_i = floor_+((T_V(k1+k2) - a_i k_i) / (b_i k_i))
```

Both optimizations use integer grid search under:

```text
k1 >= 1, k2 >= 1, k1 + k2 <= C.
```

The utility comparison is not made in two different models. GoodSpeed first
chooses `(k1^GS, k2^GS)` using its own monotone service curve, then that
allocation is evaluated under the same SSD model as the SSD-aware oracle. The
reported gap is:

```text
U_SSD(k^SSD) - U_SSD(k^GS).
```

### Outputs

Default scan:

```text
sim/experiments/results/block3_reversal/
```

Wider `b`-heterogeneity scan:

```text
sim/experiments/results/block3_reversal_wide_b/
```

Semi-calibrated scan centered on the Block 1 rough estimates
`alpha ~= 0.735` and `r ~= 0.6`:

```text
sim/experiments/results/block3_reversal_semi_calibrated/
```

Cross-scenario summary:

```text
sim/experiments/results/block3_summary/gate3_summary.csv
sim/experiments/results/block3_summary/b_ratio_summary.csv
sim/experiments/results/block3_summary/b_ratio_reversal_rate.png
sim/experiments/results/block3_summary/b_ratio_reversal_gap.png
```

### Gate 3 Summary

```text
scenario          valid cases   reversal rate   avg reversal gap   top gap
default           1600/1600      5.8%            5.6%               11.0%
wide_b            3976/4900      9.9%            13.5%              35.5%
semi_calibrated    625/625      10.6%            10.5%              19.3%
```

Under the roadmap's strict global Gate 3 criterion:

```text
R share >= 20%
average gap inside R >= 15%
```

none of the three full-scenario scans passes both conditions. However, the
wide-b and semi-calibrated scans show that the reversal mechanism is not a
single isolated toy point.

### b-Ratio Scaling Result

The strongest signal is drafter-cost heterogeneity. Grouping by:

```text
b_ratio = max(b1,b2) / min(b1,b2)
```

shows a clear increase in reversal frequency and gap as the ratio grows.

Representative wide-b groups:

```text
b_ratio = 20:
  reversal rate = 26.5%
  avg reversal gap = 14.4%

b_ratio = 40:
  reversal rate = 32.3%
  avg reversal gap = 20.4%
```

Representative semi-calibrated groups:

```text
b_ratio = 10:
  reversal rate = 24.0%
  avg reversal gap = 10.9%

b_ratio = 20:
  reversal rate = 24.0%
  avg reversal gap = 17.5%
```

This supports the qualitative Block 3 mechanism:

```text
GoodSpeed orders clients mainly by acceptance behavior.
SSD-aware allocation also sees drafter cost.
When acceptance ordering conflicts with drafter-cost ordering, allocation
reversal becomes likely.
```

### Interpretation

The safe current claim is:

```text
The closed-form SSD model produces non-empty allocation-reversal regions.
Reversal is concentrated in high drafter-cost heterogeneity regimes, and the
gap can exceed 15% locally.
```

The unsafe claim is:

```text
Reversal is already proven to be large under realistic production parameters.
```

That still requires timing calibration for realistic `a`, `b`, and
`T_V(sum k)` ranges.

### Next Checks

1. Calibrate `b` from draft/tree timing measurements rather than synthetic
   ratios.
2. Replace the linear verifier-time proxy
   `T_V = t_v_base + t_v_slope * sum k` with a measured or paper-derived
   curve.
3. Re-run the semi-calibrated scan using a joint `(alpha,r)` distribution
   rather than a small independent grid around `alpha ~= 0.735, r ~= 0.6`.
4. If calibrated `b_ratio` rarely exceeds the high-heterogeneity regime, frame
   reversal as a conditional structural result and make the externality term
   the main signature.

## 2026-05-05: Block 3 Real-LLM Timing Run Setup

### Goal

The next real-LLM run is meant to calibrate the quantities that synthetic
Block 3 currently treats as free parameters:

```text
draft timing:   draft_ms ~= k*a + k*b*B
verifier time:  verify_ms ~= T0 + tau*k
```

The run wrapper added for this purpose is:

```bash
bash scripts/run_block3_timing_grid.sh
```

It wraps the existing geometric fan-out benchmark, enables draft-side profiling
with:

```text
SSD_PROFILE_DRAFT=1
```

and then parses the log into:

```text
draft_profile_summary.csv
```

using:

```bash
python bench/summarize_draft_profile_log.py <run.log> --csv <out>/draft_profile_summary.csv
```

### Dataset Issue Found

The first attempted Alpaca run still printed garbage-looking prompts. This was
not a model issue. It happened because the remote shell had:

```text
DATASET_FLAG=--alpaca
SSD_DATASET_DIR=
```

With `SSD_DATASET_DIR` empty or pointing at a missing directory, the benchmark
could not find:

```text
alpaca/alpaca_data_10000.jsonl
```

and silently fell back to random token prompts. Those random token ids decode
as mixed code-like / garbage text, which polluted the displayed prompts.

### Alpaca Data Fix

On the AutoDL machine, HuggingFace direct access initially timed out. The
dataset was downloaded successfully by setting the mirror endpoint:

```bash
export PYTHONPATH=/root/autodl-tmp/ssd:$PYTHONPATH
export HF_ENDPOINT=https://hf-mirror.com
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_datasets_cache

python - <<'PY'
from scripts.get_data_from_hf import download_alpaca_data
print(download_alpaca_data(10000))
PY
```

This produced:

```text
/root/autodl-tmp/hf_datasets_cache/processed_datasets/alpaca/alpaca_data_10000.jsonl
```

The critical environment variable for the benchmark is the parent
`processed_datasets` directory:

```bash
export SSD_DATASET_DIR=/root/autodl-tmp/hf_datasets_cache/processed_datasets
```

Before launching an overnight run, always check:

```bash
echo "DATASET_FLAG=$DATASET_FLAG"
echo "SSD_DATASET_DIR=$SSD_DATASET_DIR"
ls -lh "$SSD_DATASET_DIR/alpaca/alpaca_data_10000.jsonl"
head -n 2 "$SSD_DATASET_DIR/alpaca/alpaca_data_10000.jsonl"
```

Expected:

```text
DATASET_FLAG=--alpaca
SSD_DATASET_DIR=/root/autodl-tmp/hf_datasets_cache/processed_datasets
```

and the `head` output should contain natural-language Alpaca instructions, not
random token gibberish.

### Recommended Full Alpaca Timing Run

Use a fresh output directory so earlier fallback/random-token runs do not mix
with the corrected Alpaca run:

```bash
export PYTHONPATH=/root/autodl-tmp/ssd:$PYTHONPATH
export MPLCONFIGDIR=/tmp/mpl_block3_timing
export SSD_CUDA_ARCH=8.9
export CUDA_VISIBLE_DEVICES=0,1
export ASYNC_GPUS=2
export SSD_DATASET_DIR=/root/autodl-tmp/hf_datasets_cache/processed_datasets
export DATASET_FLAG="--alpaca"

export OUT_DIR=/root/autodl-tmp/ssd/bench/results/block3_timing_alpaca_full_v2

K_VALUES="2 3 4 5 6 7 8 9 10 11 12" \
BUDGETS="16 24 36 48 64" \
PROMPT_OFFSETS="0 8 16" \
NUMSEQS=4 \
OUTPUT_LEN=64 \
INPUT_LEN=128 \
MAX_MODEL_LEN=1024 \
BLOCK_SZ=128 \
BATCH_SIZE=1 \
bash scripts/run_block3_timing_grid.sh
```

Expected scale:

```text
11 k values * 5 budgets * 3 prompt offsets = 165 runs
```

If the observed rate is about 30 seconds per run, this should finish in roughly
1.5--2 hours including summarization and plotting overhead.

### Acceptance Criteria For The Run

The run is usable only if:

```text
dataset flag: --alpaca
```

appears in the wrapper banner and the log contains no fallback warning:

```text
falling back to random tokens
```

After completion, inspect:

```bash
head -n 5 /root/autodl-tmp/ssd/bench/results/block3_timing_alpaca_full_v2/shape_summary.csv
head -n 5 /root/autodl-tmp/ssd/bench/results/block3_timing_alpaca_full_v2/draft_profile_summary.csv
```

The follow-up analysis should use:

```text
shape_summary.csv          for cache hit, accepted suffix, verify_ms, throughput
draft_profile_summary.csv  for draft/tree timing and b calibration
run.log                    for raw profiling/debug checks
```

## 2026-05-05: Block 3 Alpaca Full Timing Result

### Result Directory

The corrected Alpaca run was placed under:

```text
bench/results/block3_timing_alpaca_full_v2/
```

Key files:

```text
shape_summary.csv
draft_profile_summary.csv
per_run_summary.csv
run.log
figures/
```

An additional merged analysis table was generated:

```text
bench/results/block3_timing_alpaca_full_v2/block3_timing_analysis_summary.csv
```

Each row in that merged table corresponds to one `(B,k)` pair and combines:

```text
throughput / cache / verify metrics from shape_summary.csv
draft-side timing metrics from draft_profile_summary.csv
```

### Data Quality Check

The run is usable:

```text
shape rows: 55 = 5 budgets * 11 k values
draft rows: 165 = 5 budgets * 11 k values * 3 prompt offsets
dataset: alpaca
runs per shape point: 3
fallback count in run.log: 0
```

Prompt samples in `run.log` are real Alpaca prompts, for example:

```text
Give three tips for staying healthy.
Render a 3D model of a house
Describe the function of a computer motherboard
```

This confirms that the earlier random-token / garbage-prompt issue was fixed.

### Service-Curve Result

The Alpaca full run preserves the Block 1 single-peaked pattern. Best observed
lookahead by budget:

```text
B=16: best decode k=4, best official k=4
B=24: best decode k=5, best official k=4
B=36: best decode k=5, best official k=5
B=48: best decode k=4, best official k=4
B=64: best decode k=4, best official k=4
```

Cache hit rate decreases with `k`, while larger `B` raises cache hit rate:

```text
B=16: cache hit k=2 -> k=12: 0.824 -> 0.433
B=24: cache hit k=2 -> k=12: 0.853 -> 0.575
B=36: cache hit k=2 -> k=12: 0.879 -> 0.667
B=48: cache hit k=2 -> k=12: 0.896 -> 0.711
B=64: cache hit k=2 -> k=12: 0.908 -> 0.736
```

This is consistent with the proposed mechanism:

```text
larger k improves hit-side payoff,
but larger k also spreads fan-out/cache budget over more positions,
so throughput peaks internally.
```

### Timing Calibration

Do not use `draft_total_ms_mean` directly for Block 3 `b` calibration. It mixes
service/build/populate/communication overhead and gives an unphysical negative
`b` in the linear fit.

The cleaner draft timing targets are:

```text
draft_detail_total_ms_mean
draft_decode_tree_ms_mean
```

Fitting:

```text
draft_ms ~= c + a*k + b*k*B
```

gives:

```text
draft_detail_total_ms_mean:
  c  = -0.0035 ms
  a  =  2.6285 ms per draft depth step
  b  =  0.007689 ms per depth-step fanout unit
  R2 =  0.9966
  RMSE = 0.541 ms

draft_decode_tree_ms_mean:
  c  =  1.1488 ms
  a  =  2.9567 ms per draft depth step
  b  =  0.008456 ms per depth-step fanout unit
  R2 =  0.9970
  RMSE = 0.570 ms
```

For first calibrated Block 3 runs, use:

```text
a ~= 2.6--3.0 ms
b ~= 0.0077--0.0085 ms
```

Verifier timing is nearly linear in `k` and only weakly affected by `B`:

```text
verify_ms_mean ~= 19.613 + 0.0944*k - 0.00239*B
R2 = 0.8726
RMSE = 0.115 ms
```

For the first calibrated scheduler scan, the simplest proxy is:

```text
T_V(k) ~= 19.6 + 0.094*k ms
```

### Interpretation For Block 3

This run provides a real-system anchor for the absolute scale of `a`, `b`, and
`T_V`.

However, it uses a single target/draft pair:

```text
Qwen3-8B target, Qwen3-0.6B draft
```

so it calibrates the absolute timing scale but not the multi-client
heterogeneity distribution of `b`. To decide whether allocation reversal is a
common realistic regime, we still need either:

```text
multiple draft model sizes / hardware settings,
or multiple measured workload profiles that induce materially different draft
cost coefficients.
```

The immediate next step is to feed the fitted `(a,b,T_V)` into the Block 3 scan
as a calibrated single-profile baseline, then run sensitivity around measured
`b` to determine how much heterogeneity is required for reversal under real
timing scale.

## 2026-05-05: Block 3 Alpaca-Calibrated Reversal Scan

### Reproducible Entry Point

The real Alpaca timing fit was connected back into the Block 3 reversal scanner
through:

```bash
CONDA_ENV=crypto_ml \
MPLCONFIGDIR=/private/tmp/mpl_block3_calibrated \
scripts/run_block3_alpaca_calibrated_scan.sh
```

The script runs:

```text
sim.experiments.block3_reversal_scan
sim.experiments.block3_summarize_results
```

and writes:

```text
sim/experiments/results/block3_reversal_alpaca_calibrated/
sim/experiments/results/block3_summary/
```

### Calibration Used

The scan uses the fitted timing model from the corrected Alpaca run:

```text
draft_detail_total_ms ~= -0.003456 + 2.628523*k + 0.007689*k*B
verify_ms             ~= 19.613020 + 0.094370*k
```

For the two-client scanner this becomes:

```text
a = 2.628523 ms
T_V(k1+k2) = 19.613020 + 0.094370*(k1+k2) ms
```

and `b` is swept around the measured value:

```text
b values =
0.0038445 0.005126 0.007689 0.0115335 0.015378
0.023067 0.030756 0.061512 0.07689
```

This is a sensitivity scan around the measured single-profile value. The
single Qwen3-8B/Qwen3-0.6B run does not by itself identify a population
distribution over `b`; it only anchors the real timing scale.

### Result

The calibrated scan evaluated:

```text
8 alpha values * 8 alpha values * 9 b values * 9 b values = 5184 cases
```

with:

```text
valid cases:                    2754 / 5184 = 53.1%
positive SSD-over-GS gap cases: 2749 / 2754 = 99.8%
reversal cases:                   56 / 2754 = 2.0%
strong reversal cases:            54 / 2754 = 2.0%
average reversal gap:                      37.4%
top reversal gap:                          48.5%
```

The summary table now includes:

```text
scenario            valid cases   reversal rate   avg reversal gap   gate pass
default             1600/1600      5.8%            5.6%               no
wide_b              3976/4900      9.9%            13.5%              no
semi_calibrated      625/625       10.6%           10.5%              no
alpaca_calibrated   2754/5184      2.0%            37.4%              no
```

Representative top calibrated reversal cases:

```text
alpha=(0.65,0.8),  b=(0.0038445,0.023067):
  GoodSpeed k=(5,7), SSD k=(5,4), gap=48.5%

alpha=(0.735,0.8), b=(0.0038445,0.023067):
  GoodSpeed k=(5,7), SSD k=(5,4), gap=48.5%

alpha=(0.8,0.735), b=(0.023067,0.005126):
  GoodSpeed k=(7,5), SSD k=(4,5), gap=48.5%
```

### Interpretation

The real-timing scale narrows the reversal region substantially. In this
calibrated scan, reversal is not a broad default behavior: it appears in about
2% of valid cases.

However, the surviving reversal cases are not numerical noise. Their utility
gaps are large, usually above the 15% strong-reversal threshold. The mechanism
appears when:

```text
one client has better acceptance/cache structure,
but the other client has materially cheaper or more expensive draft fanout cost.
```

GoodSpeed still allocates deeper `k` mainly according to acceptance quality,
while the SSD-aware objective accounts for how `k` changes the feasible fanout
budget through the measured drafter timing model.

The right paper framing after this result is:

```text
allocation reversal survives real timing calibration,
but as a conditional high-heterogeneity phenomenon rather than a common-case
claim under one measured draft profile.
```

The broader empirical claim should now move toward:

```text
1. positive SSD-over-GoodSpeed utility gap is very common in the calibrated scan;
2. allocation reversal is a sharp diagnostic case that exposes the structural
   mismatch in GoodSpeed-style allocation;
3. the next required measurement is a population of b values from multiple
   draft sizes, batch/workload regimes, or hardware placements.
```

### Slide Figures

Slide-friendly figures were generated with:

```bash
MPLCONFIGDIR=/private/tmp/mpl_block3_slide \
conda run -n crypto_ml python -m sim.experiments.block3_make_slide_figures
```

Output directory:

```text
sim/experiments/results/block3_slide_figures/
```

The script writes PNG, SVG, and PDF versions of each figure:

```text
calibrated_scenario_summary
alpaca_calibrated_b_ratio
alpaca_calibrated_reversal_case
```

Figure usage:

```text
calibrated_scenario_summary:
  compare reversal region size against average reversal gap across default,
  wide-b, semi-calibrated, and Alpaca-calibrated scans.

alpaca_calibrated_b_ratio:
  show that calibrated reversal requires draft-cost heterogeneity; the x-axis
  is max(b1,b2)/min(b1,b2), the left y-axis is reversal rate, and the right
  y-axis is average gap among reversal cases.

alpaca_calibrated_reversal_case:
  show a representative concrete case where GoodSpeed allocates k=(5,7), while
  the SSD-aware objective allocates k=(5,4), producing a 48.5% geomean utility
  gain under the calibrated timing model.
```

Suggested slide text:

```text
Real timing calibration narrows the reversal region, but does not eliminate it.
Under Alpaca-calibrated Qwen3 timing, allocation reversal appears in 2.0% of
valid cases; however, surviving reversal cases have large utility gaps
(avg. 37.4%, max 48.5%). This suggests reversal is a conditional
high-heterogeneity phenomenon, while the broader and more stable signal is the
SSD-aware utility advantage over GoodSpeed allocation.
```

## 2026-05-05: Scheduler-Native Reversal Decomposition

### Motivation

The first calibrated reversal report used a very conservative validity filter:

```text
GoodSpeed's allocation must also be executable under the SSD timing model.
```

This was useful for computing a direct SSD-utility gap:

```text
U_SSD(k_SSD) - U_SSD(k_GoodSpeed)
```

but it is not the right definition for measuring whether two schedulers choose
the same allocation order. GoodSpeed and the SSD-aware scheduler are different
schedulers; each should be allowed to produce its native allocation.

For scheduler-native order comparison, use:

```text
GoodSpeed allocation:    k_GS from the GoodSpeed objective
SSD-aware allocation:    k_SSD from the SSD-aware objective
```

and compare only the relative order:

```text
order(k1, k2) in {-1, 0, +1}
```

where:

```text
-1: k1 < k2
 0: k1 = k2
+1: k1 > k2
```

### Do Not Collapse All Mismatch Into Reversal

Under this scheduler-native definition, the broad order-mismatch rate at
`C=12` is:

```text
order mismatch including ties: 2674 / 5184 = 51.6%
```

However, this 51.6% number should not be reported as "reversal." It mixes three
mechanistically different phenomena:

```text
GS-blindness   (GS tie     -> SSD non-tie): 1180 / 5184 = 22.8%
GS-overcommit  (GS non-tie -> SSD tie):      934 / 5184 = 18.0%
Strict reversal:                              560 / 5184 = 10.8%
```

The tie/non-tie components are real findings, but they are not the same as
strict allocation reversal.

### Mechanism 1: GoodSpeed Blindness

GoodSpeed allocation is effectively driven by the acceptance parameter:

```text
GoodSpeed allocation: k_i determined from alpha_i
```

The SSD-aware scheduler depends on the joint profile:

```text
SSD-aware allocation: k_i = arg max U_SSD(alpha_i, a_i, b_i, {k_j})
```

Therefore, when the scan contains points such as:

```text
alpha1 = alpha2, but b1 != b2
```

GoodSpeed necessarily ties the two clients, while SSD can break the tie because
the draft fanout cost `b` changes the feasible fanout budget. This is not a
definition artifact. It is direct evidence that GoodSpeed is blind to drafter
cost heterogeneity.

Suggested finding wording:

```text
Finding 1 (blindness):
GoodSpeed's alpha-only allocation is structurally blind to drafter-cost
heterogeneity. When alpha1 = alpha2 but b1 != b2, GoodSpeed gives identical k
while SSD-aware scheduling differentiates the clients.
Rate at C=12: 22.8%.
```

### Mechanism 2: GoodSpeed Overcommit

The reverse tie/non-tie transition also matters:

```text
GS non-tie -> SSD tie
```

Here GoodSpeed sees an acceptance difference and assigns a strict order, but the
SSD-aware objective finds that the two clients should receive the same depth.
This happens when the SSD utility is near the unimodal peak and marginal depth
differences are no longer worth the extra draft/fanout cost.

Suggested finding wording:

```text
Finding 2 (overcommit):
Where alpha differs but the SSD utility is near-flat around its unimodal peak,
GoodSpeed over-discriminates between clients while SSD-aware scheduling prefers
a tie.
Rate at C=12: 18.0%.
```

### Mechanism 3: Strict Reversal

Strict reversal should be reserved for the strongest form of disagreement:

```text
GoodSpeed: k1 < k2, SSD-aware: k1 > k2
or
GoodSpeed: k1 > k2, SSD-aware: k1 < k2
```

Under scheduler-native comparison:

```text
old comparable-only strict reversal:  56 / 2754 = 2.0%
new scheduler-native strict reversal: 560 / 5184 = 10.8%
```

The difference:

```text
504 additional strict reversal cases
```

is the real effect of removing the cross-model validity filter. This is the
number that should be used when discussing the expansion of the reversal
region.

Strict reversal also increases under more aggressive capacity:

```text
C=8:   352 / 5184 =  6.8%
C=10:  478 / 5184 =  9.2%
C=12:  560 / 5184 = 10.8%
C=14:  732 / 5184 = 14.1%
C=16:  770 / 5184 = 14.9%
C=20:  814 / 5184 = 15.7%
```

Suggested finding wording:

```text
Finding 3 (strict reversal):
When non-local coupling and the SSD unimodal peak shift the optimal depth order
across the GoodSpeed ordering boundary, the two schedulers strictly disagree on
direction.
Rate at C=12: 10.8%; rate at C=20: 15.7%.
```

### Implication For Gate 3

The roadmap Gate 3 asks whether the reversal region is large enough under
realistic parameters:

```text
R in realistic parameter space >= 20%
average GoodSpeed-vs-SSD utility gap >= 15%
```

If `R` is defined as strict reversal over the full calibrated grid, then:

```text
C=12 strict reversal: 10.8%
C=20 strict reversal: 15.7%
```

so the full-grid strict reversal frequency is below the 20% gate.

There are two important follow-ups:

```text
1. Conditional heterogeneity:
   In high b-ratio subsets, strict reversal is around or above 30%.
   The reversal region may need to be stated as a heterogeneous-regime result.

2. Utility impact:
   The scheduler-native strict reversal cases still need utility-gap evaluation.
   If these cases have average utility loss >= 15%, then strict reversal remains
   a high-impact finding even if the full-grid frequency is below 20%.
```

### Revised Framing

Do not report:

```text
51.6% reversal
```

Instead report the decomposition:

```text
At C=12, scheduler-native allocation disagreement decomposes into:

GoodSpeed blindness:   22.8%
GoodSpeed overcommit:  18.0%
Strict reversal:       10.8%
```

Recommended one-sentence summary:

```text
The 51.6% scheduler-native mismatch is not a single reversal rate; it is the
sum of three structural failures. Blindness and overcommit reveal GoodSpeed's
missing drafter-cost and unimodal-depth dimensions, while strict reversal is the
signature region where the two schedulers prefer opposite clients.
```
