# Real LLM Calibration Plan

## Goal

Use real SSD runs to estimate the verifier-side service curve:

```text
S_i / speculative shape -> accepted tokens, cache behavior, verifier time
```

This is the missing evidence between the toy simulator and the paper claim. We are not trying to prove "SSD is fast" here. We are trying to test whether real SSD shapes produce different marginal service curves, which would make linear-budget scheduling structurally unreliable.

## What To Run First

Recommended first setup:

```text
target model: Qwen/Qwen3-8B
draft model:  Qwen/Qwen3-0.6B
dataset:      gsm
temperature:  0
batch size:   1
numseqs:      32 after smoke test
output_len:   128 after smoke test
```

Important:

Async SSD requires at least two GPUs in this engine because target and draft run on separate devices. If the remote machine has only one GPU, run AR and sync SD first, then use a multi-GPU machine for async SSD calibration.

## Smoke Test

Run this first on the remote machine:

```bash
source .venv/bin/activate
cd bench

python -O bench.py \
  --qwen --size 8 \
  --gpus 2 \
  --spec --async --draft 0.6 --k 4 --f 2 \
  --b 1 --temp 0 --numseqs 4 --output_len 64 \
  --calibration-json results/smoke_async_ssd_k4_f2.json
```

If only one GPU is available:

```bash
python -O bench.py \
  --qwen --size 8 \
  --gpus 1 \
  --spec --draft 0.6 --k 6 \
  --b 1 --temp 0 --numseqs 4 --output_len 64 \
  --calibration-json results/smoke_sync_sd_k6.json
```

## Full First Matrix

From repo root:

```bash
source .venv/bin/activate
NUMSEQS=32 OUTPUT_LEN=128 ASYNC_GPUS=2 bash scripts/run_real_calibration.sh
```

For a faster dry run:

```bash
source .venv/bin/activate
NUMSEQS=4 OUTPUT_LEN=64 ASYNC_GPUS=2 bash scripts/run_real_calibration.sh
```

The script writes:

```text
bench/results/calibration_<timestamp>/*.json
bench/results/calibration_<timestamp>/summary.csv
```

## Metrics Exported

Each `--calibration-json` file includes:

- run/model/dataset/shape metadata;
- raw engine metrics;
- summary statistics for:
  - `accepted_suffix_lens_with_recovery`;
  - `accepted_suffix_lens_on_hit`;
  - `accepted_suffix_lens_on_miss`;
  - `cache_hits`;
  - `target_step_times`;
  - `target_verify_times`;
- derived efficiency metrics:
  - `metrics_decode_tokens_per_target_verify_second`;
  - `metrics_accepted_suffix_tokens_per_target_verify_second`;
  - `metrics_decode_throughput`;
  - `metrics_avg_target_verify_time_ms`.

The most important fields for this project are:

```text
metrics_avg_accepted_suffix_lens_with_recovery
metrics_avg_cache_hits
metrics_avg_target_verify_time_ms
metrics_accepted_suffix_tokens_per_target_verify_second
metrics_decode_tokens_per_target_verify_second
```

## How To Summarize Results

After any set of runs:

```bash
cd bench
python summarize_calibration.py results/calibration_<timestamp> --csv results/calibration_<timestamp>/summary.csv
```

The markdown table printed by this script is suitable for a group-meeting slide.

## How To Interpret

We are looking for these signals:

1. Accepted suffix length changes nonlinearly across `(k, f)`.
2. Verifier efficiency is not monotonic in larger speculative shapes.
3. Cache hit behavior changes across shapes.
4. Different workloads later prefer different shapes.

If these signals appear, the real model supports the core claim:

```text
S_i is not just linear draft length in SSD/tree speculation.
```

The next step after this calibration is to plug empirical service curves into the simulator and test whether real-data-driven curves cause allocation reversal.
