# SSD Research Repo Patterns

## Project fingerprint

This repository is a research inference engine, not a production serving stack.

Its stable shape is:
- `ssd/`: native inference engine, model code, kernels, schedulers, and runtime utilities
- `bench/`: experiment harnesses and comparisons against SSD, SGLang, and vLLM
- `scripts/`: data and model acquisition helpers
- `skills/`: local Codex skills that document reusable repository knowledge

The code optimizes for:
- algorithm iteration speed
- explicit benchmarking
- hardware-aware path and cache configuration
- separation between engine code and experiment code

It does not optimize for:
- deployment APIs
- broad platform compatibility
- zero-setup onboarding

## Architecture to preserve

### 1. Thin public API

`ssd/llm.py` exposes `LLM` as a light subclass of `LLMEngine`.

Pattern to reuse:
- keep the import surface small
- let advanced behavior live in deeper modules
- expose a minimal object model at package top level

### 2. Config as the engine control plane

`ssd/config.py` uses a dataclass as the canonical engine configuration surface.

Pattern to reuse:
- collect runtime options in one dataclass
- validate hardware and model invariants in `__post_init__`
- keep defaults close to the engine, not scattered across CLIs
- derive computed limits as properties

Good examples from this repo:
- cap `max_model_len` against model configs
- assert GPU-count constraints for async draft mode
- resolve fan-out defaults only when async speculation is enabled

### 3. Environment-driven path resolution

`ssd/paths.py` and `bench/bench_paths.py` are explicit path modules.

Pattern to reuse:
- require env vars for essential external state
- document each env var with an exact directory expectation
- centralize model aliases and dataset file locations
- resolve HuggingFace snapshot directories in helpers, not at callsites

Canonical env vars in this repo:
- `SSD_HF_CACHE`
- `SSD_DATASET_DIR`
- `SSD_CUDA_ARCH`
- optional model overrides such as `SSD_TARGET_MODEL`, `SSD_DRAFT_MODEL`, `BENCH_LLAMA_70B`

### 4. Engine internals split by concern

`ssd/engine/` is divided into orthogonal runtime units:
- `llm_engine.py`: top-level orchestration and lifecycle
- `scheduler.py`: request scheduling and cache-allocation decisions
- `model_runner.py`: target-model execution
- `draft_runner.py`: draft-model execution for speculative decoding
- `step.py`: inference-mode policy (`AutoRegressiveStep`, `SpecDecodeStep`)
- `verifier.py`, `speculator_sync.py`, `speculator_async.py`: algorithm-specific logic
- `block_manager.py`, `sequence.py`: state and memory bookkeeping
- `helpers/`: lower-level tensor, mask, and cudagraph helpers

Pattern to reuse:
- separate orchestration from algorithm policy
- separate state containers from compute runners
- put hot-path helper logic in focused utility modules

### 5. Benchmarks as first-class entrypoints

`bench/bench.py` is not an afterthought; it is the main experiment surface.

Pattern to reuse:
- make benchmark CLIs broad enough to express the real ablation matrix
- group CLI args by concern: model, execution, speculation, batching, generation, datasets, logging
- keep repeated resolution logic in `bench_helpers.py`
- support both exact dataset-driven prompts and synthetic fallbacks

This repo also keeps external baseline scripts separate:
- `bench/run_sglang_bench.py`
- `bench/run_vllm_bench.py`
- `bench/chat.py`

That split matters because dependency stacks conflict.

## Invocation conventions to preserve

### General runtime rules

- Run from repo root for setup.
- Run benchmark commands from inside `bench/`.
- Use `python -O` for benchmark and chat runs to avoid debug overhead.
- Expect large-model warmup and compile time before steady-state generation.

### Setup pattern

```bash
uv sync
source .venv/bin/activate
python -c "from ssd import LLM; print('ok')"
```

Optional scripts dependencies:

```bash
uv sync --extra scripts
```

### Required environment pattern

```bash
export SSD_HF_CACHE=/path/to/huggingface/hub
export SSD_DATASET_DIR=/path/to/processed_datasets
export SSD_CUDA_ARCH=9.0
```

### Canonical benchmark commands

All of these run from `bench/`.

Autoregressive baseline:

```bash
python -O bench.py --llama --size 70 --gpus 4 --b 1 --temp 0 --numseqs 128 --output_len 512 --all
```

Synchronous speculative decoding:

```bash
python -O bench.py --llama --size 70 --gpus 4 --spec --k 6 --b 1 --temp 0 --numseqs 128 --output_len 512 --all
```

Asynchronous SSD:

```bash
python -O bench.py --llama --size 70 --gpus 5 --spec --async --k 7 --f 3 --b 1 --temp 0 --numseqs 128 --output_len 512 --all
```

### Baseline comparison pattern

Keep third-party systems in separate environments when low-level deps conflict.

This repo uses:
- native SSD in the repo environment
- SGLang in its own conda env
- vLLM in its own conda env

Preserve that pattern in future projects if FlashInfer, Triton, or CUDA package versions diverge.

## CLI design conventions extracted from `bench.py`

The benchmark CLI is organized well enough to treat it as a template.

Reuse these flag groups:
- model identity: `--llama`, `--qwen`, `--size`, `--draft`
- execution mode: `--gpus`, `--eager`
- speculative controls: `--spec`, `--async`, `--k`, `--f`, `--backup`, `--fl`, `--flh`, `--flm`
- memory and batching: `--block_sz`, `--b`, `--max_model_len`
- generation: `--input_len`, `--output_len`, `--numseqs`, `--temp`, `--dtemp`, `--x`
- prompt source: `--example`, dataset selectors, `--all`, `--chat_template`
- observability: `--verbose`, `--debug`, `--max-steps`, `--wandb`, `--group`, `--name`

Design rules worth reusing:
- define mutually exclusive model-family switches clearly
- derive implied flags when a mode requires them
- generate a descriptive run name automatically
- keep sweep support in the main benchmark entrypoint if repeated reinitialization is expensive

## Helper-module conventions extracted from `bench_helpers.py`

Patterns worth copying:
- resolve HuggingFace cache dirs to real snapshot dirs
- map abstract model sizes to concrete model IDs in one place
- centralize draft-model auto-selection
- keep dataset tokenization and fallback logic outside the benchmark main loop
- allow both string prompts and token-id prompts

This style reduces churn in the main benchmark scripts and makes model swaps cheap.

## Standard template for future research repos

When building a new inference or systems research project, start with this structure:

```text
project/
├── README.md
├── pyproject.toml
├── scripts/
│   ├── download_models.py
│   └── prepare_datasets.py
├── project_pkg/
│   ├── __init__.py
│   ├── api.py
│   ├── config.py
│   ├── paths.py
│   ├── models/
│   ├── engine/
│   └── utils/
├── bench/
│   ├── README.md
│   ├── bench.py
│   ├── bench_helpers.py
│   ├── run_baseline_a.py
│   └── run_baseline_b.py
└── skills/
```

Map the SSD repo into that template like this:
- `ssd/llm.py` -> `project_pkg/api.py`
- `ssd/config.py` -> `project_pkg/config.py`
- `ssd/paths.py` -> `project_pkg/paths.py`
- `ssd/engine/*` -> `project_pkg/engine/*`
- `bench/bench.py` -> `bench/bench.py`
- `bench/bench_helpers.py` -> `bench/bench_helpers.py`

The skill also ships a concrete starter shell under `assets/minimal-repo-template/`.
Use that asset when you want to bootstrap a new repo quickly without re-deriving these outer-layer files.

## What to standardize when porting this style

Keep these invariants:
- one minimal public API
- one explicit config dataclass
- one explicit env-driven paths module
- one main benchmark CLI
- one helper module for benchmark resolution logic
- one benchmark README for backend-specific notes
- setup commands that are copy-pasteable

Do not over-copy these repo-specific details:
- exact model names
- exact dataset list
- exact async-speculation parameters
- assumptions about H100-only validation

Port the structure, not the incidental constants.

## Quick checklist

Before calling a new research repo "SSD-style", verify that it has:
- engine code separated from experiment code
- environment variables for model and dataset roots
- benchmark entrypoints with explicit flags
- helper modules for path and prompt resolution
- a thin public API over deeper runtime internals
- README commands that match the actual folder layout
