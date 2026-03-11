# Minimal Research Inference Repo Template

This template captures the stable outer shell of an SSD-style research repository:
- `project_pkg/config.py`: one dataclass-based config surface
- `project_pkg/paths.py`: environment-driven path resolution
- `bench/bench.py`: one main benchmark CLI
- `bench/bench_helpers.py`: model and prompt resolution helpers

Adapt the names, model IDs, and engine callsites to the target project. Keep the structure.
