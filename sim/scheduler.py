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

    # When True, stop allocating once the best available marginal gain is
    # non-positive (<= cap_tolerance), leaving any remaining budget unspent.
    # This is the peak cap / unimodal correction: it refuses to push a client
    # past its service peak. When False (default) the full budget is always
    # spent, which is the GoodSpeed-style "always allocate" behavior.
    cap_at_peak = False
    cap_tolerance = 0.0

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
            if self.cap_at_peak and gain <= self.cap_tolerance:
                # No client converts another unit into positive marginal
                # utility; spending more would push past the service peak.
                break
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


class CappedGreedyMarginalScheduler(GreedyMarginalScheduler):
    """G1: marginal greedy with peak cap ("F" in paper/scheduler_design.md).

    Pours capacity into the client with the highest marginal gain and stops
    once no client offers a positive marginal, leaving spare budget unspent
    instead of overcommitting past the service peak. With a monotone service
    (e.g. ``goodspeed``) the cap never triggers and this matches the uncapped
    greedy; the cap only bites when the service curve is unimodal.
    """

    name = "capped_greedy"
    cap_at_peak = True


class CappedEmpiricalScheduler(CappedGreedyMarginalScheduler):
    name = "capped_empirical"
    estimate_mode = "empirical"


class GoodSpeedScheduler(GreedyMarginalScheduler):
    """G2: GoodSpeed baseline.

    Uncapped greedy on the monotone service ``mu^GS = (1 - alpha^(k+1))/(1 -
    alpha)``. The marginal of a monotone-saturating curve never turns negative,
    so this never stops early and always spends the full budget -- the
    structural source of overcommit relative to the capped scheduler.
    """

    name = "goodspeed"
    estimate_mode = "goodspeed"
    cap_at_peak = False


class CappedSSDScheduler(CappedGreedyMarginalScheduler):
    """G5 / "F" on the calibrated curve.

    Marginal greedy with peak cap, running on the unimodal ``ssd`` service
    (mu^SSD from sim.ssd_math). The cap binds at each client's interior optimum
    k*, leaving spare capacity unspent rather than overcommitting.
    """

    name = "capped_ssd"
    estimate_mode = "ssd"


class SSDGreedyScheduler(GreedyMarginalScheduler):
    """Uncapped greedy on the same unimodal ``ssd`` service.

    Identical to CappedSSDScheduler except the cap is removed, so it must spend
    the full budget and is forced past the peak. Pairing it against
    CappedSSDScheduler isolates the effect of the cap alone (same service
    curve), separate from the GoodSpeed monotone-service baseline.
    """

    name = "ssd_greedy"
    estimate_mode = "ssd"
    cap_at_peak = False
