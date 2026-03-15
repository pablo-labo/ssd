import math

from sim.policy import linear_service, unified_service
from sim.types import ClientConfig, ClientSnapshot


class SimClient:
    def __init__(self, config: ClientConfig):
        self.name = config.name
        self.arrival_rate = config.arrival_rate
        self.base_acceptance = config.base_acceptance
        self.frontier_quality = config.frontier_quality
        self.frontier_state = config.frontier_quality
        self.expansion_policy = config.expansion_policy
        self.backlog = float(config.initial_backlog)
        self.freshness_age = 0
        self.total_accepted = 0.0
        self.total_utility = 0.0
        self.total_wasted_budget = 0.0

    def snapshot(self) -> ClientSnapshot:
        return ClientSnapshot(
            name=self.name,
            backlog=self.backlog,
            freshness_age=self.freshness_age,
            frontier_quality=self.frontier_quality,
            frontier_state=self.frontier_state,
        )

    def arrive(self) -> None:
        self.backlog += self.arrival_rate
        if self.backlog > 0:
            self.freshness_age += 1
        self._recover_frontier()

    def _service(self, budget: int, mode: str) -> float:
        if mode == "linear":
            return linear_service(self.backlog, self.base_acceptance, budget)
        if mode == "unified":
            return unified_service(
                self.backlog,
                self.base_acceptance,
                self.frontier_quality,
                self.frontier_state,
                budget,
                self.expansion_policy,
            )
        raise ValueError(f"Unknown service mode: {mode}")

    def estimate_gain(self, budget: int, estimate_mode: str, freshness_lambda: float, enable_freshness: bool) -> float:
        accepted = self._service(budget, estimate_mode)
        utility = self._apply_freshness(accepted, freshness_lambda, enable_freshness)
        return utility

    def marginal_gain(self, budget: int, estimate_mode: str, freshness_lambda: float, enable_freshness: bool) -> float:
        return self.estimate_gain(budget, estimate_mode, freshness_lambda, enable_freshness) - self.estimate_gain(
            budget - 1, estimate_mode, freshness_lambda, enable_freshness
        )

    def consume_budget(self, budget: int, world_mode: str, freshness_lambda: float, enable_freshness: bool) -> tuple[float, float, float]:
        accepted = self._service(budget, world_mode)
        utility = self._apply_freshness(accepted, freshness_lambda, enable_freshness)
        wasted_budget = max(0.0, float(budget) - accepted)

        self.backlog = max(0.0, self.backlog - accepted)
        if self.backlog == 0:
            self.freshness_age = 0
        self._update_frontier_after_service(budget, accepted, world_mode)

        self.total_accepted += accepted
        self.total_utility += utility
        self.total_wasted_budget += wasted_budget
        return accepted, utility, wasted_budget

    def _apply_freshness(self, accepted: float, freshness_lambda: float, enable_freshness: bool) -> float:
        if not enable_freshness:
            return accepted
        freshness = math.exp(-freshness_lambda * self.freshness_age)
        return accepted * freshness

    def _recover_frontier(self) -> None:
        if self.backlog <= 0:
            self.frontier_state = min(1.0, self.frontier_state + 0.03)
            return

        # Backlogged clients recover some frontier quality as new useful branches arrive,
        # but recovery is partial so persistent overuse still matters.
        pressure = min(1.0, self.backlog / max(1.0, self.arrival_rate * 3.0))
        self.frontier_state = min(1.0, self.frontier_state + 0.06 + 0.04 * pressure)

    def _update_frontier_after_service(self, budget: int, accepted: float, world_mode: str) -> None:
        if world_mode != "unified":
            return

        if accepted <= 0:
            self.frontier_state = max(0.05, self.frontier_state - 0.02)
            return

        # Spending verifier budget explores the frontier. Moderate budgets can improve the
        # frontier slightly, but over-allocation consumes easy branches and reduces future value.
        exploration_gain = 0.015 * min(accepted, 4.0)
        overuse_penalty = 0.05 * max(0.0, budget - 3.0)
        self.frontier_state = min(
            1.0,
            max(0.05, self.frontier_state + exploration_gain - overuse_penalty),
        )
