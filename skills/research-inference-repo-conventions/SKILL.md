---
name: research-inference-repo-conventions
description: Capture and reuse the architecture, CLI patterns, config surfaces, and benchmark workflows of an SSD-style LLM inference research repository. Use when Codex needs to analyze a research inference codebase, standardize its conventions into a reusable template, or build a new speculative decoding / serving / benchmarking project that should preserve the same separation between engine code, benchmark harnesses, scripts, and environment-driven paths.
---

# Research Inference Repo Conventions

Extract stable project patterns first, then preserve them when adding features or creating a new research repository.

Keep the skill focused on reproducible engineering structure, not on copying one algorithm verbatim.

## Workflow

1. Read the repo surface area in this order:
- `README.md`
- Dependency manifest such as `pyproject.toml`
- Benchmark entrypoints under `bench/`
- Environment and path modules such as `ssd/paths.py` or `bench/bench_paths.py`
- Engine entrypoints such as `ssd/llm.py`, `ssd/config.py`, and `ssd/engine/`

2. Classify the repository into these layers:
- Public package API
- Engine/runtime internals
- Experiment and benchmark harnesses
- Data or model acquisition scripts
- Project-local skills or references

3. Preserve the conventions that make the repo easy to operate:
- Environment variables fail fast for required paths
- One thin public API layer over a deeper engine
- CLI flags grouped by concern
- Benchmark helpers separated from benchmark entrypoints
- Baseline integrations isolated from native engine code

4. When building a new research repo, reproduce the same shape unless there is a clear reason not to:
- `package/` or `src/` for engine code
- `bench/` for experiments and cross-system comparisons
- `scripts/` for model or dataset preparation
- Root `README.md` with exact commands
- One config module and one path module as stable control planes
- Reusable template assets for the minimal outer shell

## Standardization Rules

- Keep model-path and dataset-path resolution in dedicated modules, not inline in benchmark scripts.
- Use environment variables as the primary portability layer. Raise immediately if required paths are missing.
- Keep the top-level API minimal. A thin wrapper like `LLM` over `LLMEngine` is preferred.
- Put orchestration in `engine/` and keep model-family implementations in `models/`.
- Separate native benchmarking from external-baseline benchmarking when dependencies conflict.
- Prefer helper modules for prompt loading, snapshot resolution, and dataset fallback logic.
- Make benchmark CLIs expose the experiment matrix explicitly through flags, not hidden constants.
- Put user-facing invocation examples in the root `README.md`, and backend-specific notes in `bench/README.md`.

## Reference File

Read [references/ssd-patterns.md](./references/ssd-patterns.md) when you need:
- The concrete architecture extracted from this SSD repository
- The canonical benchmark and chat command patterns
- A reusable template for future inference research repos
- The specific conventions around env vars, config dataclasses, and entrypoint layout

Copy from [assets/minimal-repo-template](./assets/minimal-repo-template) when you need:
- A starter `config.py` with dataclass validation
- A starter `paths.py` with environment-driven path resolution
- A benchmark CLI skeleton with grouped flags
- A benchmark helper module for snapshot and dataset resolution

## Output Pattern

When asked to analyze or replicate a repo, answer in this order:

1. Repository shape
2. Invocation surface
3. Stable conventions worth preserving
4. Proposed standardized template for the next project
