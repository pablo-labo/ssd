import os
from pathlib import Path


def required_env(var_name: str, note: str) -> str:
    value = os.environ.get(var_name)
    if value:
        return value
    raise RuntimeError(f"Missing required env var {var_name}. {note}")


def resolve_snapshot(path: str) -> str:
    base = Path(path)
    if (base / "config.json").exists():
        return str(base)
    snapshots = base / "snapshots"
    if snapshots.is_dir():
        for child in snapshots.iterdir():
            if child.is_dir() and (child / "config.json").exists():
                return str(child)
    for child in base.iterdir() if base.is_dir() else []:
        if child.is_dir() and (child / "config.json").exists():
            return str(child)
    raise FileNotFoundError(f"No snapshot with config.json found under {path}")


HF_CACHE_DIR = required_env(
    "PROJECT_HF_CACHE",
    "Set it to your HuggingFace hub directory.",
)

DATASET_DIR = required_env(
    "PROJECT_DATASET_DIR",
    "Set it to the directory containing processed benchmark datasets.",
)

CUDA_ARCH = os.environ.get("PROJECT_CUDA_ARCH", "9.0")
os.environ.setdefault("TORCH_CUDA_ARCH_LIST", CUDA_ARCH)
