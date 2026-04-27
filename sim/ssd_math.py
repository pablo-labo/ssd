from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite

import numpy as np


@dataclass(frozen=True)
class Block1Params:
    alpha: float
    r: float
    a: float
    b: float
    t_v: float
    t_b: float = 1.0
    e_miss: float = 1.0
    l_hit: float = 1.0


@dataclass(frozen=True)
class CurvePoint:
    k: int
    budget: float
    f0: float
    min_fanout: float
    phit: float
    e_hit: float
    mu: float
    valid: bool
    invalid_reason: str = ""


def beta(alpha: float, r: float) -> float:
    _validate_alpha_r(alpha, r)
    return alpha ** (1.0 / (1.0 + r))


def budget_b(k: int | float, t_v: float, a: float, b: float) -> float:
    if k <= 0 or b <= 0:
        return float("nan")
    return (t_v - a * k) / (b * k)


def fanout_denominator(k: int | float, alpha: float, r: float) -> float:
    bt = beta(alpha, r)
    return bt**k * (1.0 - alpha) ** (-1.0 / (1.0 + r)) + (1.0 - bt**k) / (1.0 - bt)


def fanout_f0(k: int | float, budget: float, alpha: float, r: float) -> float:
    if budget <= 0:
        return float("nan")
    return budget / fanout_denominator(k, alpha, r)


def fanouts(k: int, budget: float, alpha: float, r: float) -> np.ndarray:
    f0 = fanout_f0(k, budget, alpha, r)
    if not isfinite(f0) or f0 <= 0:
        return np.array([], dtype=float)
    bt = beta(alpha, r)
    values = [f0 * bt**j for j in range(k)]
    values.append(f0 * bt**k * (1.0 - alpha) ** (-1.0 / (1.0 + r)))
    return np.array(values, dtype=float)


def phit_primary(k: int | float, budget: float, alpha: float, r: float) -> float:
    f0 = fanout_f0(k, budget, alpha, r)
    if not isfinite(f0) or f0 <= 0:
        return float("nan")

    bt = beta(alpha, r)
    miss_weight = (1.0 - alpha) ** (r / (1.0 + r)) * bt**k
    miss_weight += (1.0 - alpha) * (1.0 - bt**k) / (1.0 - bt)
    return 1.0 - f0 ** (-r) * miss_weight


def e_hit(k: int | float, alpha: float) -> float:
    if not 0.0 < alpha < 1.0:
        return float("nan")
    return (1.0 - alpha ** (k + 1.0)) / (1.0 - alpha)


def mu_ssd_from_parts(
    phit: float,
    e_hit_value: float,
    e_miss: float = 1.0,
    l_hit: float = 1.0,
    l_miss: float = 2.0,
) -> float:
    if not all(isfinite(value) for value in (phit, e_hit_value, e_miss, l_hit, l_miss)):
        return float("nan")
    if l_hit <= 0 or l_miss <= 0:
        return float("nan")

    numerator = phit * e_hit_value + (1.0 - phit) * e_miss
    latency = phit * l_hit + (1.0 - phit) * l_miss
    if latency <= 0:
        return float("nan")
    return numerator / latency


def curve_point(k: int, params: Block1Params, require_integer_fanout: bool = True) -> CurvePoint:
    budget = budget_b(k, params.t_v, params.a, params.b)
    if not isfinite(budget) or budget <= 0:
        return CurvePoint(k, budget, float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), False, "budget")

    f0 = fanout_f0(k, budget, params.alpha, params.r)
    fs = fanouts(k, budget, params.alpha, params.r)
    min_fanout = float(np.min(fs)) if fs.size else float("nan")
    if require_integer_fanout and (not isfinite(min_fanout) or min_fanout < 1.0):
        return CurvePoint(k, budget, f0, min_fanout, float("nan"), float("nan"), float("nan"), False, "fanout")

    phit = phit_primary(k, budget, params.alpha, params.r)
    if not isfinite(phit) or phit < -1e-9 or phit > 1.0 + 1e-9:
        return CurvePoint(k, budget, f0, min_fanout, phit, float("nan"), float("nan"), False, "phit")

    phit = min(1.0, max(0.0, phit))
    e_hit_value = e_hit(k, params.alpha)
    mu = mu_ssd_from_parts(
        phit=phit,
        e_hit_value=e_hit_value,
        e_miss=params.e_miss,
        l_hit=params.l_hit,
        l_miss=params.l_hit + params.t_b,
    )
    valid = isfinite(mu) and mu >= 0.0
    return CurvePoint(k, budget, f0, min_fanout, phit, e_hit_value, mu, valid, "" if valid else "mu")


def curve(
    params: Block1Params,
    max_k: int | None = None,
    require_integer_fanout: bool = True,
) -> list[CurvePoint]:
    if max_k is None:
        if params.a <= 0:
            max_k = 80
        else:
            max_k = min(80, max(1, floor((params.t_v - 1e-9) / params.a)))
    return [curve_point(k, params, require_integer_fanout) for k in range(1, max_k + 1)]


def is_discrete_unimodal(values: list[float], tol: float = 1e-8) -> bool:
    finite_values = [value for value in values if isfinite(value)]
    if len(finite_values) < 3:
        return False

    seen_negative = False
    for left, right in zip(finite_values, finite_values[1:]):
        diff = right - left
        if abs(diff) <= tol:
            continue
        if diff < 0:
            seen_negative = True
        elif seen_negative:
            return False
    return True


def curve_summary(points: list[CurvePoint], tol: float = 1e-8) -> dict[str, float | int | bool | str]:
    valid_points = [point for point in points if point.valid]
    if not valid_points:
        reasons = sorted({point.invalid_reason for point in points if point.invalid_reason})
        return {
            "num_valid_k": 0,
            "is_unimodal": False,
            "best_k": -1,
            "best_mu": float("nan"),
            "first_valid_k": -1,
            "last_valid_k": -1,
            "invalid_reasons": ",".join(reasons),
        }

    best = max(valid_points, key=lambda point: (point.mu, -point.k))
    return {
        "num_valid_k": len(valid_points),
        "is_unimodal": is_discrete_unimodal([point.mu for point in valid_points], tol=tol),
        "best_k": best.k,
        "best_mu": best.mu,
        "first_valid_k": valid_points[0].k,
        "last_valid_k": valid_points[-1].k,
        "invalid_reasons": ",".join(sorted({point.invalid_reason for point in points if point.invalid_reason})),
    }


def _validate_alpha_r(alpha: float, r: float) -> None:
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if r <= 0.0:
        raise ValueError(f"r must be positive, got {r}")
