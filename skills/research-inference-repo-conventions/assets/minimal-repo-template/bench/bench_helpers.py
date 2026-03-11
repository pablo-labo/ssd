import json
from pathlib import Path
from random import randint


def get_model_paths(args, hf_cache_dir: str) -> tuple[str, str, str | None]:
    family_map = {
        "llama": {
            "8": "meta-llama/Llama-3.1-8B-Instruct",
            "70": "meta-llama/Llama-3.1-70B-Instruct",
        },
        "qwen": {
            "8": "Qwen/Qwen3-8B",
            "32": "Qwen/Qwen3-32B",
        },
    }
    family = "qwen" if args.qwen else "llama"
    model_id = family_map[family][args.size]
    model_base = Path(hf_cache_dir) / f"models--{model_id.replace('/', '--')}"
    draft_base = None
    if args.spec:
        draft_id = args.draft or ("meta-llama/Llama-3.2-1B-Instruct" if family == "llama" else "Qwen/Qwen3-0.6B")
        draft_base = Path(hf_cache_dir) / f"models--{draft_id.replace('/', '--')}"
    return model_id, str(model_base), str(draft_base) if draft_base else None


def load_jsonl_prompts(dataset_path: str, num_prompts: int, input_len: int) -> list[list[int]] | None:
    path = Path(dataset_path)
    if not path.exists():
        return None
    prompts: list[list[int]] = []
    with path.open() as f:
        for line in f:
            if len(prompts) >= num_prompts:
                break
            text = json.loads(line)["text"]
            prompts.append([ord(ch) % 256 for ch in text[:input_len]])
    return prompts


def generate_benchmark_inputs(dataset_path: str | None, num_prompts: int, input_len: int) -> list[list[int]]:
    if dataset_path:
        prompts = load_jsonl_prompts(dataset_path, num_prompts, input_len)
        if prompts is not None:
            return prompts
    return [[randint(0, 10000) for _ in range(input_len)] for _ in range(num_prompts)]
