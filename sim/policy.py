import math
import json
from functools import lru_cache
from pathlib import Path


POLICY_PARAMS = {
    "linear": {"boost": 1.00, "curvature": 0.55, "quality_weight": 0.08, "budget_penalty": 0.14},
    "depth_heavy": {"boost": 1.12, "curvature": 0.72, "quality_weight": 0.28, "budget_penalty": 0.18},
    "width_heavy": {"boost": 1.16, "curvature": 0.60, "quality_weight": 0.34, "budget_penalty": 0.22},
    "mixed": {"boost": 1.10, "curvature": 0.66, "quality_weight": 0.22, "budget_penalty": 0.18},
    "quality_aware": {"boost": 1.20, "curvature": 0.70, "quality_weight": 0.42, "budget_penalty": 0.20},
}

DEFAULT_EMPIRICAL_PROFILE = Path(__file__).parent / "empirical_profiles" / "qwen8b_gsm_async.json"


def _policy_params(policy: str) -> dict[str, float]:
    try:
        return POLICY_PARAMS[policy]
    except KeyError as exc:
        raise ValueError(f"Unknown expansion policy: {policy}") from exc


def linear_service(backlog: float, base_acceptance: float, budget: int) -> float:
    if backlog <= 0 or budget <= 0:
        return 0.0
    exposure = 1.0 - math.exp(-base_acceptance * math.sqrt(budget))
    budget_penalty = max(0.65, 1.0 - 0.10 * max(0.0, budget - 1.0))
    return min(backlog, backlog * exposure * budget_penalty)


def unified_service(
    backlog: float,
    base_acceptance: float,
    frontier_quality: float,
    frontier_state: float,
    budget: int,
    expansion_policy: str,
) -> float:
    if backlog <= 0 or budget <= 0:
        return 0.0

    params = _policy_params(expansion_policy)
    effective_frontier = max(0.05, min(1.0, 0.45 * frontier_quality + 0.55 * frontier_state))
    quality_term = 1.0 + params["quality_weight"] * effective_frontier
    exposure = 1.0 - math.exp(-base_acceptance * params["curvature"] * math.sqrt(budget))
    budget_penalty = max(0.55, 1.0 - params["budget_penalty"] * max(0.0, math.sqrt(budget) - 1.0))
    accepted = backlog * exposure * params["boost"] * quality_term * budget_penalty
    return min(backlog, accepted)


@lru_cache(maxsize=8)
def load_empirical_profiles(path: str = str(DEFAULT_EMPIRICAL_PROFILE)) -> dict[tuple[int, int], dict[str, float]]:
    with open(path) as f:
        payload = json.load(f)

    profiles = {}
    for profile in payload["profiles"]:
        key = (int(profile["k"]), int(profile["f"]))
        metrics = profile["metrics"]
        profiles[key] = {
            "accepted_suffix": float(metrics["accepted_suffix_mean"]),
            "verify_ms": float(metrics["target_verify_time_ms_mean"]),
            "suffix_per_verify_sec": float(metrics["accepted_suffix_per_verify_sec_mean"]),
            "cache_hit_rate": float(metrics["cache_hit_rate_mean"]),
        }
    return profiles


def _nearest_profile(profiles: dict[tuple[int, int], dict[str, float]], k: int, f: int) -> dict[str, float]:
    best_key = min(profiles, key=lambda key: (abs(key[0] - k), abs(key[1] - f), key[0], key[1]))
    return profiles[best_key]


def _interpolate_empirical_suffix(profiles: dict[tuple[int, int], dict[str, float]], budget: int, f: int) -> float:
    if budget <= 0:
        return 0.0

    available_k = sorted({k for k, _ in profiles})
    min_k = available_k[0]
    max_k = available_k[-1]

    if budget <= min_k:
        anchor = _nearest_profile(profiles, min_k, f)["accepted_suffix"]
        return anchor * budget / min_k

    if budget >= max_k:
        last = _nearest_profile(profiles, max_k, f)["accepted_suffix"]
        prev_k = available_k[-2]
        prev = _nearest_profile(profiles, prev_k, f)["accepted_suffix"]
        slope = max(0.0, (last - prev) / (max_k - prev_k))
        return last + 0.35 * slope * (budget - max_k)

    lower = max(k for k in available_k if k <= budget)
    upper = min(k for k in available_k if k >= budget)
    if lower == upper:
        return _nearest_profile(profiles, lower, f)["accepted_suffix"]

    lower_value = _nearest_profile(profiles, lower, f)["accepted_suffix"]
    upper_value = _nearest_profile(profiles, upper, f)["accepted_suffix"]
    weight = (budget - lower) / (upper - lower)
    return lower_value * (1.0 - weight) + upper_value * weight


def empirical_service(
    backlog: float,
    base_acceptance: float,
    frontier_quality: float,
    frontier_state: float,
    budget: int,
    empirical_f: int,
) -> float:
    if backlog <= 0 or budget <= 0:
        return 0.0

    profiles = load_empirical_profiles()
    suffix = _interpolate_empirical_suffix(profiles, budget, empirical_f)

    # The measured profile is from one GSM setup. Client-specific acceptance and
    # frontier state adjust it into a multi-client scheduling proxy.
    acceptance_scale = 0.65 + 0.70 * base_acceptance
    frontier_scale = 0.75 + 0.30 * max(0.05, min(1.0, 0.45 * frontier_quality + 0.55 * frontier_state))
    accepted = suffix * acceptance_scale * frontier_scale
    return min(backlog, accepted)
