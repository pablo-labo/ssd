# Async SSD Shape Grid Plan

## Purpose

The current real-data result covers only three shapes:

```text
(k=4, f=2), (k=6, f=3), (k=8, f=4)
```

This is enough to show the calibration pipeline works, but not enough to fit a stable empirical service model. The next experiment expands the shape space and repeats each shape over multiple prompt offsets.

## Default Grid

The one-command script runs:

```text
shapes:
  (4,1), (4,2), (4,4)
  (6,1), (6,2), (6,3)
  (8,1), (8,2), (8,4)

prompt offsets:
  0, 4, 8

scale:
  numseqs=4
  output_len=64
  max_model_len=1024
  block_sz=128
```

This produces 27 async SSD runs by default.

## Command

From the repo root on the remote machine:

```bash
source .venv/bin/activate
bash scripts/run_async_shape_grid.sh
```

The script writes:

```text
bench/results/async_shape_grid_<timestamp>/per_run_summary.csv
bench/results/async_shape_grid_<timestamp>/shape_summary.csv
bench/results/async_shape_grid_<timestamp>/empirical_profiles.json
```

`shape_summary.csv` is the table for group-meeting slides. `empirical_profiles.json` is the first artifact to feed back into the simulator.

## Smaller Run

For a faster 12-run version:

```bash
source .venv/bin/activate
SHAPES="4:1 4:2 4:4 8:1 8:2 8:4" \
PROMPT_OFFSETS="0 4" \
NUMSEQS=4 \
OUTPUT_LEN=64 \
bash scripts/run_async_shape_grid.sh
```

## Larger Run

For a more stable run:

```bash
source .venv/bin/activate
PROMPT_OFFSETS="0 4 8 12" \
NUMSEQS=8 \
OUTPUT_LEN=64 \
bash scripts/run_async_shape_grid.sh
```

## What To Look For

Use the grouped summary columns:

```text
avg_suffix_mean
cache_hit_mean
verify_ms_mean
suffix_per_verify_sec_mean
decode_tokens_per_verify_sec_mean
```

The key question is not simply which shape is fastest. The key question is whether the empirical service curve is shape-dependent and non-linear enough to change scheduler marginal-gain estimates.

## Next Step After This Grid

Use `empirical_profiles.json` to replace hand-written service curves in `sim/policy.py` or to add a new empirical service mode.

The immediate scheduling test should be:

```text
linear-budget scheduler
  vs
empirical unified-budget scheduler
```

using the measured shape-level service profiles.
