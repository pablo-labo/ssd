from sim.config import make_default_config
from sim.runner import SimulationRunner
from sim.scheduler import LinearBudgetScheduler, UnifiedBudgetScheduler


def _print_summary(summary) -> None:
    print(f"scheduler={summary.scheduler} world={summary.world_mode}")
    print(f"  total_accepted_tokens={summary.total_accepted_tokens:.2f}")
    print(f"  total_utility={summary.total_utility:.2f}")
    print(f"  total_wasted_budget={summary.total_wasted_budget:.2f}")
    print(f"  fairness={summary.fairness:.4f}")
    print("  per_client_utility:")
    for name, value in summary.per_client_utility.items():
        print(f"    {name}: {value:.2f}")
    print("  final_backlogs:")
    for name, value in summary.final_backlogs.items():
        print(f"    {name}: {value:.2f}")


def main() -> None:
    config = make_default_config()
    runner = SimulationRunner(config)

    for scheduler in (LinearBudgetScheduler(), UnifiedBudgetScheduler()):
        summary, _ = runner.run(scheduler)
        _print_summary(summary)
        print()


if __name__ == "__main__":
    main()
