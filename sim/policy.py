import math


POLICY_PARAMS = {
    "linear": {"boost": 1.00, "curvature": 0.55, "quality_weight": 0.08, "budget_penalty": 0.14},
    "depth_heavy": {"boost": 1.12, "curvature": 0.72, "quality_weight": 0.28, "budget_penalty": 0.18},
    "width_heavy": {"boost": 1.16, "curvature": 0.60, "quality_weight": 0.34, "budget_penalty": 0.22},
    "mixed": {"boost": 1.10, "curvature": 0.66, "quality_weight": 0.22, "budget_penalty": 0.18},
    "quality_aware": {"boost": 1.20, "curvature": 0.70, "quality_weight": 0.42, "budget_penalty": 0.20},
}


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
