#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ROOT="${MODEL_ROOT:-$ROOT_DIR/models}"
HF_HOME_DIR="${HF_HOME_DIR:-$MODEL_ROOT/huggingface}"
HF_HUB_DIR="${HF_HUB_DIR:-$HF_HOME_DIR/hub}"

mkdir -p "$HF_HUB_DIR"

export HF_HOME="$HF_HOME_DIR"
export SSD_HF_CACHE="$HF_HUB_DIR"

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi

  curl -LsSf https://astral.sh/uv/install.sh | sh

  if [[ -x "$HOME/.local/bin/uv" ]]; then
    export PATH="$HOME/.local/bin:$PATH"
  fi

  command -v uv >/dev/null 2>&1 || {
    echo "uv install failed or is not on PATH" >&2
    exit 1
  }
}

download_models() {
  . .venv/bin/activate
  python - <<'PY'
from huggingface_hub import snapshot_download
import os

cache_dir = os.environ["SSD_HF_CACHE"]
models = [
    "Qwen/Qwen3-8B",
    "Qwen/Qwen3-0.6B",
]

for repo_id in models:
    print(f"Downloading {repo_id} into {cache_dir}...")
    snapshot_download(repo_id=repo_id, cache_dir=cache_dir, resume_download=True)
PY
}

ensure_uv
uv sync --extra scripts
download_models

cat <<EOF
Setup complete.
SSD_HF_CACHE=$SSD_HF_CACHE
Downloaded models:
  - Qwen/Qwen3-8B
  - Qwen/Qwen3-0.6B
EOF
