import argparse
import time

from bench_helpers import generate_benchmark_inputs, get_model_paths
from project_pkg.paths import DATASET_DIR, HF_CACHE_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark a research inference engine")

    parser.add_argument("--size", choices=["8", "32", "70"], default="8")
    parser.add_argument("--llama", action="store_true", default=True)
    parser.add_argument("--qwen", action="store_true")
    parser.add_argument("--draft", type=str, default=None)

    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--eager", action="store_true")

    parser.add_argument("--spec", action="store_true")
    parser.add_argument("--async", dest="async_spec", action="store_true")
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--f", type=int, default=2)

    parser.add_argument("--b", type=int, default=1)
    parser.add_argument("--input_len", type=int, default=128)
    parser.add_argument("--output_len", type=int, default=512)
    parser.add_argument("--numseqs", type=int, default=128)
    parser.add_argument("--temp", type=float, default=0.0)

    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()
    if args.qwen:
        args.llama = False
    return args


def create_run_name(args: argparse.Namespace) -> str:
    mode = "spec" if args.spec else "ar"
    if args.async_spec:
        mode += "-async"
    family = "qwen" if args.qwen else "llama"
    return f"{family}-{args.size}-{mode}-b{args.b}-temp{args.temp}"


def main() -> None:
    args = parse_args()
    run_name = create_run_name(args)
    model_name, model_path, draft_path = get_model_paths(args, HF_CACHE_DIR)
    dataset_path = f"{DATASET_DIR}/{args.dataset}.jsonl" if args.dataset else None
    prompts = generate_benchmark_inputs(dataset_path, args.numseqs, args.input_len)

    if args.verbose:
        print(f"run_name={run_name}")
        print(f"model={model_name}")
        print(f"model_path={model_path}")
        print(f"draft_path={draft_path}")
        print(f"num_prompts={len(prompts)}")

    start = time.time()
    # Replace this block with the project's real engine invocation.
    total_tokens = len(prompts) * args.output_len
    total_time = max(time.time() - start, 1e-6)
    print(
        {
            "run_name": run_name,
            "total_tokens": total_tokens,
            "total_time": total_time,
            "throughput": total_tokens / total_time,
        }
    )


if __name__ == "__main__":
    main()
