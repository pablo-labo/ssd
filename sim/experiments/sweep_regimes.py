from dataclasses import dataclass

from sim.config import (
    make_default_config,
    with_budget,
    with_freshness,
    with_load_multiplier,
    with_policy_mix,
)
from sim.runner import SimulationRunner
from sim.scheduler import LinearBudgetScheduler, UnifiedBudgetScheduler


@dataclass
class SweepCaseResult:
    case_id: str
    budget: int
    load_multiplier: float
    freshness_lambda: float
    policy_mix: str
    linear_utility: float
    unified_utility: float
    utility_delta: float
    linear_fairness: float
    unified_fairness: float
    fairness_delta: float
    linear_backlog: float
    unified_backlog: float
    backlog_delta: float
    linear_avg_allocations: dict[str, float]
    unified_avg_allocations: dict[str, float]
    linear_allocation_order: list[str]
    unified_allocation_order: list[str]
    linear_utility_order: list[str]
    unified_utility_order: list[str]
    allocation_reversal_pairs: list[str]
    utility_reversal_pairs: list[str]
    per_client_utility_delta: dict[str, float]


def _average_allocations(slot_results) -> dict[str, float]:
    if not slot_results:
        return {}
    totals: dict[str, float] = {}
    for result in slot_results:
        for name, budget in result.allocations.items():
            totals[name] = totals.get(name, 0.0) + budget
    num_slots = len(slot_results)
    return {name: value / num_slots for name, value in totals.items()}


def _sort_desc(values: dict[str, float]) -> list[str]:
    return sorted(values, key=lambda name: (-values[name], name))


def _reversal_pairs(order_a: list[str], order_b: list[str]) -> list[str]:
    pos_a = {name: idx for idx, name in enumerate(order_a)}
    pos_b = {name: idx for idx, name in enumerate(order_b)}
    names = list(order_a)
    reversals = []
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            if (pos_a[left] - pos_a[right]) * (pos_b[left] - pos_b[right]) < 0:
                reversals.append(f"{left}<->{right}")
    return reversals


def _run_case(budget: int, load_multiplier: float, freshness_lambda: float, policy_mix: str) -> SweepCaseResult:
    config = make_default_config()
    config = with_budget(config, budget)
    config = with_load_multiplier(config, load_multiplier)
    config = with_freshness(config, freshness_lambda, enable_freshness=freshness_lambda > 0)
    config = with_policy_mix(config, policy_mix)

    runner = SimulationRunner(config)
    linear_summary, linear_slots = runner.run(LinearBudgetScheduler())
    unified_summary, unified_slots = runner.run(UnifiedBudgetScheduler())

    linear_backlog = sum(linear_summary.final_backlogs.values())
    unified_backlog = sum(unified_summary.final_backlogs.values())
    linear_avg_allocations = _average_allocations(linear_slots)
    unified_avg_allocations = _average_allocations(unified_slots)
    linear_allocation_order = _sort_desc(linear_avg_allocations)
    unified_allocation_order = _sort_desc(unified_avg_allocations)
    linear_utility_order = _sort_desc(linear_summary.per_client_utility)
    unified_utility_order = _sort_desc(unified_summary.per_client_utility)
    allocation_reversal_pairs = _reversal_pairs(linear_allocation_order, unified_allocation_order)
    utility_reversal_pairs = _reversal_pairs(linear_utility_order, unified_utility_order)
    per_client_utility_delta = {
        name: unified_summary.per_client_utility.get(name, 0.0) - linear_summary.per_client_utility.get(name, 0.0)
        for name in linear_summary.per_client_utility
    }

    return SweepCaseResult(
        case_id=(
            f"budget={budget}|load={load_multiplier:.2f}|"
            f"fresh={freshness_lambda:.2f}|mix={policy_mix}"
        ),
        budget=budget,
        load_multiplier=load_multiplier,
        freshness_lambda=freshness_lambda,
        policy_mix=policy_mix,
        linear_utility=linear_summary.total_utility,
        unified_utility=unified_summary.total_utility,
        utility_delta=unified_summary.total_utility - linear_summary.total_utility,
        linear_fairness=linear_summary.fairness,
        unified_fairness=unified_summary.fairness,
        fairness_delta=unified_summary.fairness - linear_summary.fairness,
        linear_backlog=linear_backlog,
        unified_backlog=unified_backlog,
        backlog_delta=linear_backlog - unified_backlog,
        linear_avg_allocations=linear_avg_allocations,
        unified_avg_allocations=unified_avg_allocations,
        linear_allocation_order=linear_allocation_order,
        unified_allocation_order=unified_allocation_order,
        linear_utility_order=linear_utility_order,
        unified_utility_order=unified_utility_order,
        allocation_reversal_pairs=allocation_reversal_pairs,
        utility_reversal_pairs=utility_reversal_pairs,
        per_client_utility_delta=per_client_utility_delta,
    )


def _print_case(case: SweepCaseResult) -> None:
    print(case.case_id)
    print(
        "  utility: "
        f"linear={case.linear_utility:.2f} unified={case.unified_utility:.2f} "
        f"delta={case.utility_delta:.2f}"
    )
    print(
        "  fairness: "
        f"linear={case.linear_fairness:.4f} unified={case.unified_fairness:.4f} "
        f"delta={case.fairness_delta:.4f}"
    )
    print(
        "  final_backlog: "
        f"linear={case.linear_backlog:.2f} unified={case.unified_backlog:.2f} "
        f"delta={case.backlog_delta:.2f}"
    )
    print(
        "  allocation_order: "
        f"linear={case.linear_allocation_order} unified={case.unified_allocation_order}"
    )
    print(
        "  utility_order: "
        f"linear={case.linear_utility_order} unified={case.unified_utility_order}"
    )
    print(f"  allocation_reversals={case.allocation_reversal_pairs or ['none']}")
    print(f"  utility_reversals={case.utility_reversal_pairs or ['none']}")
    print("  avg_allocations:")
    for name in case.linear_allocation_order:
        print(
            f"    {name}: linear={case.linear_avg_allocations.get(name, 0.0):.2f} "
            f"unified={case.unified_avg_allocations.get(name, 0.0):.2f}"
        )
    print("  per_client_utility_delta:")
    for name, delta in sorted(case.per_client_utility_delta.items(), key=lambda item: (-abs(item[1]), item[0])):
        print(f"    {name}: {delta:+.2f}")


def main() -> None:
    budgets = [6, 10, 14]
    load_multipliers = [0.80, 1.00, 1.30]
    freshness_levels = [0.00, 0.18, 0.35]
    policy_mixes = ["balanced", "tree_skewed", "linear_skewed"]

    cases: list[SweepCaseResult] = []
    for budget in budgets:
        for load_multiplier in load_multipliers:
            for freshness_lambda in freshness_levels:
                for policy_mix in policy_mixes:
                    cases.append(_run_case(budget, load_multiplier, freshness_lambda, policy_mix))

    unified_wins = [case for case in cases if case.utility_delta > 0]
    allocation_reversal_cases = [case for case in cases if case.allocation_reversal_pairs]
    utility_reversal_cases = [case for case in cases if case.utility_reversal_pairs]
    worst_losses = sorted(cases, key=lambda case: case.utility_delta)[:3]
    best_gains = sorted(cases, key=lambda case: case.utility_delta, reverse=True)[:5]
    strongest_reversals = sorted(
        allocation_reversal_cases,
        key=lambda case: (len(case.allocation_reversal_pairs), abs(case.utility_delta), abs(case.backlog_delta)),
        reverse=True,
    )[:5]

    print(f"evaluated_cases={len(cases)}")
    print(
        "unified_win_rate="
        f"{len(unified_wins)}/{len(cases)} "
        f"({len(unified_wins) / len(cases):.1%})"
    )
    print(
        "allocation_reversal_rate="
        f"{len(allocation_reversal_cases)}/{len(cases)} "
        f"({len(allocation_reversal_cases) / len(cases):.1%})"
    )
    print(
        "utility_reversal_rate="
        f"{len(utility_reversal_cases)}/{len(cases)} "
        f"({len(utility_reversal_cases) / len(cases):.1%})"
    )
    print()

    print("top_gain_cases")
    for case in best_gains:
        _print_case(case)
    print()

    print("strongest_allocation_reversal_cases")
    for case in strongest_reversals:
        _print_case(case)
    print()

    print("worst_cases")
    for case in worst_losses:
        _print_case(case)


if __name__ == "__main__":
    main()
