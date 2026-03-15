# Real LLM Runbook

## Goal

This runbook turns the "Preparing Real LLM Integration" checklist into an
execution sequence.

The purpose of the first real-LLM stage is not to implement online scheduling.
It is to collect real SSD metrics that can calibrate the simulator.

## Execution Model

This runbook assumes the actual SSD benchmarks will be run on a rented remote
server, not on the local machine where this repository is being edited.

So the correct workflow is:

1. prepare the runbook and command set locally;
2. log in to the remote server;
3. verify server environment and caches;
4. run a minimal SSD collection sweep remotely;
5. bring the metrics back and calibrate the simulator.

## Step 1: Verify The Remote Server Environment

After logging in to the server, confirm all of the following:

1. Python environment is activated.
2. `torch` imports successfully.
3. `transformers` imports successfully.
4. `SSD_HF_CACHE` points to the HuggingFace `hub/` directory.
5. `SSD_DATASET_DIR` points to the processed dataset directory.
6. target and draft model snapshots exist in the HF cache.
7. enough GPUs are available for the chosen mode.
8. CUDA version is compatible with the project.

Suggested checks:

```bash
python --version
python -c "import torch, transformers; print(torch.__version__)"
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
nvidia-smi
echo $SSD_HF_CACHE
echo $SSD_DATASET_DIR
echo $SSD_CUDA_ARCH
```

If SSD dependencies are not installed yet:

```bash
uv sync
source .venv/bin/activate
python -c "from ssd import LLM; print('ok')"
```

## Step 1.5: Set Remote Environment Variables

If the server shell does not already export these, set them explicitly:

```bash
export SSD_HF_CACHE=/path/to/huggingface/hub
export SSD_DATASET_DIR=/path/to/processed_datasets
export SSD_CUDA_ARCH=9.0
```

Notes:

- `SSD_HF_CACHE` must point to the HuggingFace `hub/` directory that contains
  entries like `models--meta-llama--...`.
- `SSD_DATASET_DIR` must point to the processed dataset directory containing
  folders such as `gsm8k/`, `alpaca/`, and `humaneval/`.
- `SSD_CUDA_ARCH=9.0` is appropriate for H100; adjust for the actual server GPU.

## Step 2: Choose a Minimal Real Collection Matrix

Do not start with many models or many datasets.

Use one model family, one dataset family, and a small speculative sweep.

Recommended first pass:

- model family:
  - `llama`
- size:
  - use the smallest feasible size that still exercises SSD mechanics on the
    available remote hardware
- dataset:
  - `gsm` first
- generation:
  - `temp=0`
  - `numseqs=32`
  - `output_len=128`
- async SSD sweep:
  - `(k, f) in {(4,2), (6,3), (8,4)}`

If hardware is tight, reduce `numseqs` and `output_len` before changing the
logic of the collection pass.

For a first server pass, it is acceptable to start with a smaller target model
than 70B if that gets you to clean metrics faster.

## Step 3: Record a Fixed Metrics Table

For every run, record at least:

- model family
- model size
- dataset
- `k`
- `f`
- `fan_out_list`
- `fan_out_list_miss`
- `numseqs`
- `output_len`
- average accepted suffix length with recovery
- average accepted suffix length on hit
- average accepted suffix length on miss
- average cache hit rate
- average target step time
- average target verify time
- decode throughput

These metrics are already exposed through the engine and benchmark flow:

- [`ssd/engine/llm_engine.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/ssd/engine/llm_engine.py)
- [`ssd/engine/verifier.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/ssd/engine/verifier.py)
- [`bench/bench.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/bench/bench.py)

## Step 4: Run The First Three Real Collection Jobs On The Server

Run from `bench/`.

Template:

```bash
python -O bench.py --llama --size 70 --spec --async --k K --f F --b 1 --temp 0 --numseqs 32 --output_len 128
```

First three runs:

```bash
python -O bench.py --llama --size 70 --spec --async --k 4 --f 2 --b 1 --temp 0 --numseqs 32 --output_len 128
python -O bench.py --llama --size 70 --spec --async --k 6 --f 3 --b 1 --temp 0 --numseqs 32 --output_len 128
python -O bench.py --llama --size 70 --spec --async --k 8 --f 4 --b 1 --temp 0 --numseqs 32 --output_len 128
```

If 70B is not feasible on the server, substitute a smaller supported target
model and keep the same collection logic.

Recommended execution practice:

- keep a text log for each run;
- copy the exact command line into the log;
- record the server GPU type and count once at the top of the log;
- do not start with `--wandb`; plain terminal output is enough for the first
  pass.

## Step 5: Map Real Metrics Into Simulator Parameters

After the first collection pass, fit only a coarse first mapping.

Initial mapping:

- simulator `base_acceptance`
  - from average accepted suffix length under fixed `(k, f)`
- simulator `frontier_quality`
  - from cache-hit-heavy regimes or accepted suffix on hit
- simulator `frontier_state`
  - from recent cache-hit trend or recent accepted suffix trend
- simulator verifier budget
  - initially from `k`, `f`, or `sum(fan_out_list)`
  - later refined using target verify time

At this stage, an explicit rough mapping is better than an implicit vague one.

## Step 6: Re-run The Simulator With Calibrated Parameters

Once the first mapping exists:

1. update simulator presets from real data;
2. rerun:

```bash
python3 -m sim.experiments.baseline_grid
python3 -m sim.experiments.sweep_regimes
```

3. compare:
   - whether allocation reversals remain;
   - whether unified still wins in some regimes;
   - whether the magnitude becomes more realistic.

## Step 7: Decide Whether To Touch The Real Engine

Only after the calibrated simulator still shows a structural mismatch should we
move to engine-side intervention.

That intervention should remain minimal at first:

- per-run or per-request budget class selection;
- small policy changes to `k`, `f`, or `fan_out_list`;
- no full online multi-client scheduler yet.

## Practical Next Action

The immediate next action is Step 1.

Concretely:

1. log in to the remote server;
2. activate the SSD Python environment there;
3. verify imports, CUDA, GPUs, and env vars;
4. verify that at least one target+draft model pair and one dataset are
   available on the server;
5. only then launch the first three collection runs.

Nothing else should happen before those checks pass.
