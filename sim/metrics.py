from sim.types import RunSummary, SlotResult


def jain_fairness(values: list[float]) -> float:
    if not values:
        return 0.0
    total = sum(values)
    squared = sum(v * v for v in values)
    if squared == 0:
        return 0.0
    return (total * total) / (len(values) * squared)


def summarize_run(
    scheduler_name: str,
    world_mode: str,
    slot_results: list[SlotResult],
) -> RunSummary:
    accepted_totals: dict[str, float] = {}
    utility_totals: dict[str, float] = {}
    wasted_totals: dict[str, float] = {}
    final_backlogs: dict[str, float] = {}

    for result in slot_results:
        for name, value in result.accepted_tokens.items():
            accepted_totals[name] = accepted_totals.get(name, 0.0) + value
        for name, value in result.utilities.items():
            utility_totals[name] = utility_totals.get(name, 0.0) + value
        for name, value in result.wasted_budget.items():
            wasted_totals[name] = wasted_totals.get(name, 0.0) + value
        final_backlogs = result.backlogs

    return RunSummary(
        scheduler=scheduler_name,
        world_mode=world_mode,
        total_accepted_tokens=sum(accepted_totals.values()),
        total_utility=sum(utility_totals.values()),
        total_wasted_budget=sum(wasted_totals.values()),
        fairness=jain_fairness(list(utility_totals.values())),
        per_client_utility=utility_totals,
        per_client_accepted_tokens=accepted_totals,
        final_backlogs=final_backlogs,
    )

