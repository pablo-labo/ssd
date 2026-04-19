from dataclasses import replace

from sim.config import make_default_config
from sim.runner import SimulationRunner
from sim.scheduler import EmpiricalBudgetScheduler, LinearBudgetScheduler


def _average_allocations(slot_results) -> dict[str, float]:
    totals: dict[str, float] = {}
    for result in slot_results:
        for name, budget in result.allocations.items():
            totals[name] = totals.get(name, 0.0) + budget
    return {name: value / len(slot_results) for name, value in totals.items()}


def _order(values: dict[str, float]) -> list[str]:
    return sorted(values, key=lambda name: (-values[name], name))


def _print_summary(summary, slots) -> None:
    avg_alloc = _average_allocations(slots)
    print(f"scheduler={summary.scheduler} world={summary.world_mode}")
    print(f"  total_accepted_tokens={summary.total_accepted_tokens:.2f}")
    print(f"  total_utility={summary.total_utility:.2f}")
    print(f"  fairness={summary.fairness:.4f}")
    print(f"  allocation_order={_order(avg_alloc)}")
    print(f"  utility_order={_order(summary.per_client_utility)}")
    print("  avg_allocations:")
    for name in _order(avg_alloc):
        print(f"    {name}: {avg_alloc[name]:.2f}")
    print("  per_client_utility:")
    for name in _order(summary.per_client_utility):
        print(f"    {name}: {summary.per_client_utility[name]:.2f}")
    print("  final_backlogs:")
    for name, value in summary.final_backlogs.items():
        print(f"    {name}: {value:.2f}")


def make_empirical_demo_config():
    config = make_default_config()
    clients = [
        replace(
            config.clients[0],
            name="depth_shape_f1",
            base_acceptance=0.58,
            frontier_quality=0.90,
            expansion_policy="depth_heavy",
            empirical_f=1,
            arrival_rate=5,
        ),
        replace(
            config.clients[1],
            name="width_shape_f4",
            base_acceptance=0.52,
            frontier_quality=0.88,
            expansion_policy="width_heavy",
            empirical_f=4,
            arrival_rate=5,
        ),
        replace(
            config.clients[2],
            name="linear_shape_f2",
            base_acceptance=0.70,
            frontier_quality=0.45,
            expansion_policy="linear",
            empirical_f=2,
            arrival_rate=6,
        ),
    ]
    return replace(
        config,
        num_slots=16,
        verifier_budget=12,
        freshness_lambda=0.12,
        world_mode="empirical",
        clients=clients,
    )


def main() -> None:
    config = make_empirical_demo_config()
    runner = SimulationRunner(config)

    results = []
    for scheduler in (LinearBudgetScheduler(), EmpiricalBudgetScheduler()):
        summary, slots = runner.run(scheduler)
        results.append((summary, slots))
        _print_summary(summary, slots)
        print()

    linear_summary, linear_slots = results[0]
    empirical_summary, empirical_slots = results[1]
    linear_alloc = _average_allocations(linear_slots)
    empirical_alloc = _average_allocations(empirical_slots)
    print("comparison")
    print(f"  utility_delta={empirical_summary.total_utility - linear_summary.total_utility:+.2f}")
    print(f"  accepted_delta={empirical_summary.total_accepted_tokens - linear_summary.total_accepted_tokens:+.2f}")
    print(f"  linear_allocation_order={_order(linear_alloc)}")
    print(f"  empirical_allocation_order={_order(empirical_alloc)}")


if __name__ == "__main__":
    main()
