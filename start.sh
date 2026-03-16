#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ROOT="${MODEL_ROOT:-$ROOT_DIR/models}"
HF_HOME_DIR="${HF_HOME_DIR:-$MODEL_ROOT/huggingface}"
HF_HUB_DIR="${HF_HUB_DIR:-$HF_HOME_DIR/hub}"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"

mkdir -p "$HF_HUB_DIR"

export HF_HOME="$HF_HOME_DIR"
export SSD_HF_CACHE="$HF_HUB_DIR"
export UV_PROJECT_ENVIRONMENT="$VENV_DIR"

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

verify_model_snapshot() {
  local repo_id="$1"
  local org model cache_base snapshot_dir
  org="${repo_id%%/*}"
  model="${repo_id##*/}"
  cache_base="$SSD_HF_CACHE/models--${org}--${model}"

  if [[ ! -d "$cache_base" ]]; then
    echo "Model cache directory missing: $cache_base" >&2
    return 1
  fi

  snapshot_dir="$(find "$cache_base" -maxdepth 3 -type f -name config.json -print -quit 2>/dev/null || true)"
  if [[ -z "$snapshot_dir" ]]; then
    echo "Model snapshot incomplete for $repo_id: no config.json found under $cache_base" >&2
    return 1
  fi

  return 0
}

download_models() {
  . "$VENV_DIR/bin/activate"
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

print_retry_hint() {
  local repo_id="$1"
  cat <<EOF >&2
Retry just this model with:
  cd "$ROOT_DIR"
  source "$VENV_DIR/bin/activate"
  export HF_HOME="$HF_HOME_DIR"
  export SSD_HF_CACHE="$HF_HUB_DIR"
  python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="$repo_id",
    cache_dir="$HF_HUB_DIR",
    resume_download=True,
)
PY
EOF
}

ensure_uv
uv sync --extra scripts
test -x "$VENV_DIR/bin/python" || {
  echo "Expected virtualenv at $VENV_DIR but it was not created" >&2
  exit 1
}
download_models

models=(
  "Qwen/Qwen3-8B"
  "Qwen/Qwen3-0.6B"
)

for repo_id in "${models[@]}"; do
  if ! verify_model_snapshot "$repo_id"; then
    print_retry_hint "$repo_id"
    exit 1
  fi
done

cat <<EOF
Setup complete.
SSD_HF_CACHE=$SSD_HF_CACHE
Virtualenv: $VENV_DIR
Downloaded models:
  - Qwen/Qwen3-8B
  - Qwen/Qwen3-0.6B

Next steps:
  source "$VENV_DIR/bin/activate"
  cd "$ROOT_DIR/bench"
  python -O bench.py --qwen --size 8 --b 1 --temp 0 --numseqs 8 --output_len 64
EOF
