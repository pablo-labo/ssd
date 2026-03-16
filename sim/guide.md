# Real Sampling Guide

This guide records the correct sampling workflow for the current remote setup:

- machine: `2 x NVIDIA RTX A4500`
- target model: `Qwen/Qwen3-8B`
- draft model: `Qwen/Qwen3-0.6B`
- current prompt mode: `--random`

## One-Time Setup

Run once on the remote machine:

```bash
cd /workspace/ssd

apt-get update
apt-get install -y libnuma1 libnuma-dev

bash start.sh

mkdir -p /workspace/ssd/processed_datasets
```

## Per-Shell Setup

Run these commands in every new shell before sampling:

```bash
cd /workspace/ssd
source .venv/bin/activate

export HF_HOME=/workspace/ssd/models/huggingface
export SSD_HF_CACHE=/workspace/ssd/models/huggingface/hub
export SSD_CUDA_ARCH=8.6
export SSD_DATASET_DIR=/workspace/ssd/processed_datasets
```

## Sanity Check

Run from:

```bash
cd /workspace/ssd/bench
```

Then execute:

```bash
python -O bench.py \
  --qwen \
  --size 8 \
  --gpus 1 \
  --b 1 \
  --temp 0 \
  --numseqs 8 \
  --output_len 64 \
  --random \
  --wandb \
  --group qwen8b-2xa4500-random \
  --name qwen8b_ar_sanity_random
```

## Sampling Commands

Run from:

```bash
cd /workspace/ssd/bench
```

### AR Baseline

```bash
python -O bench.py \
  --qwen \
  --size 8 \
  --gpus 1 \
  --b 1 \
  --temp 0 \
  --numseqs 32 \
  --output_len 128 \
  --random \
  --wandb \
  --group qwen8b-2xa4500-random \
  --name qwen8b_ar_random_b1_n32_o128
```

### Sync Speculative Baseline

```bash
python -O bench.py \
  --qwen \
  --size 8 \
  --gpus 2 \
  --spec \
  --draft 0.6 \
  --k 6 \
  --b 1 \
  --temp 0 \
  --numseqs 32 \
  --output_len 128 \
  --random \
  --wandb \
  --group qwen8b-2xa4500-random \
  --name qwen8b_sync_k6_draft06_random_b1_n32_o128
```

### Async SSD Sweep

These runs use both GPUs.

```bash
python -O bench.py \
  --qwen \
  --size 8 \
  --gpus 2 \
  --spec \
  --async \
  --draft 0.6 \
  --k 4 \
  --f 2 \
  --b 1 \
  --temp 0 \
  --numseqs 32 \
  --output_len 128 \
  --random \
  --wandb \
  --group qwen8b-2xa4500-random \
  --name qwen8b_async_k4_f2_draft06_random_b1_n32_o128

python -O bench.py \
  --qwen \
  --size 8 \
  --gpus 2 \
  --spec \
  --async \
  --draft 0.6 \
  --k 6 \
  --f 3 \
  --b 1 \
  --temp 0 \
  --numseqs 32 \
  --output_len 128 \
  --random \
  --wandb \
  --group qwen8b-2xa4500-random \
  --name qwen8b_async_k6_f3_draft06_random_b1_n32_o128

python -O bench.py \
  --qwen \
  --size 8 \
  --gpus 2 \
  --spec \
  --async \
  --draft 0.6 \
  --k 8 \
  --f 4 \
  --b 1 \
  --temp 0 \
  --numseqs 32 \
  --output_len 128 \
  --random \
  --wandb \
  --group qwen8b-2xa4500-random \
  --name qwen8b_async_k8_f4_draft06_random_b1_n32_o128
```

## Recommended Order

Run in this order:

1. sanity check
2. AR baseline
3. sync speculative baseline
4. async `k=4, f=2`
5. async `k=6, f=3`
6. async `k=8, f=4`

## WandB Metrics To Check

Check these fields after each run:

- `official_end_to_end_throughput`
- `metrics_decode_throughput`
- `metrics_avg_target_step_time_ms`
- `metrics_avg_target_verify_time_ms`
- `metrics_avg_cache_hits`
- `metrics_avg_accepted_suffix_lens_with_recovery`
- `metrics_avg_accepted_suffix_lens_on_hit`
- `metrics_avg_accepted_suffix_lens_on_miss`
