from __future__ import annotations

import argparse
import json
import math

from sim.ssd_math import beta


def capped_geometric_weights(k: int, alpha: float, r: float) -> list[float]:
    if k < 0:
        raise ValueError("k must be non-negative")
    bt = beta(alpha, r)
    weights = [bt**j for j in range(k)]
    weights.append(bt**k * (1.0 - alpha) ** (-1.0 / (1.0 + r)))
    return weights


def capped_geometric_fanouts(k: int, budget: int, alpha: float, r: float, min_fanout: int = 1) -> list[int]:
    if budget < min_fanout * (k + 1):
        raise ValueError(f"budget={budget} is too small for k={k} with min_fanout={min_fanout}")

    weights = capped_geometric_weights(k, alpha, r)
    total_weight = sum(weights)
    continuous = [budget * weight / total_weight for weight in weights]

    fanouts = [max(min_fanout, int(math.floor(value))) for value in continuous]
    while sum(fanouts) > budget:
        candidates = [idx for idx, value in enumerate(fanouts) if value > min_fanout]
        if not candidates:
            raise ValueError("could not round fanouts without violating min_fanout")
        idx = min(candidates, key=lambda item: continuous[item] - math.floor(continuous[item]))
        fanouts[idx] -= 1

    remaining = budget - sum(fanouts)
    order = sorted(range(len(fanouts)), key=lambda idx: continuous[idx] - math.floor(continuous[idx]), reverse=True)
    for idx in order[:remaining]:
        fanouts[idx] += 1

    return fanouts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Saguaro capped-geometric integer fan-out lists.")
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--budget", type=int, required=True, help="Total cache budget B=sum_j F_j")
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--r", type=float, required=True)
    parser.add_argument("--min-fanout", type=int, default=1)
    parser.add_argument("--format", choices=["space", "json"], default="space")
    args = parser.parse_args()

    fanouts = capped_geometric_fanouts(
        k=args.k,
        budget=args.budget,
        alpha=args.alpha,
        r=args.r,
        min_fanout=args.min_fanout,
    )
    if args.format == "json":
        print(json.dumps(fanouts))
    else:
        print(" ".join(str(value) for value in fanouts))


if __name__ == "__main__":
    main()
