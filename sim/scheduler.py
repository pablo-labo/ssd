from abc import ABC, abstractmethod

from sim.client import SimClient
from sim.types import SlotAllocation


class Scheduler(ABC):
    name = "scheduler"
    estimate_mode = "linear"

    @abstractmethod
    def allocate(
        self,
        clients: list[SimClient],
        total_budget: int,
        freshness_lambda: float,
        enable_freshness: bool,
    ) -> SlotAllocation:
        pass


class GreedyMarginalScheduler(Scheduler):
    name = "greedy"
    estimate_mode = "linear"

    def allocate(
        self,
        clients: list[SimClient],
        total_budget: int,
        freshness_lambda: float,
        enable_freshness: bool,
    ) -> SlotAllocation:
        budgets = {client.name: 0 for client in clients}
        marginals = {client.name: [] for client in clients}

        for _ in range(total_budget):
            best_client = max(
                clients,
                key=lambda client: client.marginal_gain(
                    budgets[client.name] + 1,
                    self.estimate_mode,
                    freshness_lambda,
                    enable_freshness,
                ),
            )
            next_budget = budgets[best_client.name] + 1
            gain = best_client.marginal_gain(
                next_budget,
                self.estimate_mode,
                freshness_lambda,
                enable_freshness,
            )
            budgets[best_client.name] = next_budget
            marginals[best_client.name].append(gain)

        return SlotAllocation(budgets=budgets, predicted_marginals=marginals)


class LinearBudgetScheduler(GreedyMarginalScheduler):
    name = "linear_budget"
    estimate_mode = "linear"


class UnifiedBudgetScheduler(GreedyMarginalScheduler):
    name = "unified_budget"
    estimate_mode = "unified"


class EmpiricalBudgetScheduler(GreedyMarginalScheduler):
    name = "empirical_budget"
    estimate_mode = "empirical"
