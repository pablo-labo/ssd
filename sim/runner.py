from sim.client import SimClient
from sim.config import SimConfig
from sim.metrics import summarize_run
from sim.scheduler import Scheduler
from sim.types import SlotResult


class SimulationRunner:
    def __init__(self, config: SimConfig):
        self.config = config

    def _build_clients(self) -> list[SimClient]:
        return [SimClient(client_cfg) for client_cfg in self.config.clients]

    def run(self, scheduler: Scheduler):
        clients = self._build_clients()
        slot_results: list[SlotResult] = []

        for slot in range(self.config.num_slots):
            for client in clients:
                client.arrive()

            allocation = scheduler.allocate(
                clients,
                self.config.verifier_budget,
                self.config.freshness_lambda,
                self.config.enable_freshness,
            )

            accepted = {}
            utilities = {}
            wasted = {}
            backlogs = {}
            freshness = {}

            for client in clients:
                budget = allocation.budgets[client.name]
                accepted_tokens, utility, wasted_budget = client.consume_budget(
                    budget=budget,
                    world_mode=self.config.world_mode,
                    freshness_lambda=self.config.freshness_lambda,
                    enable_freshness=self.config.enable_freshness,
                )
                accepted[client.name] = accepted_tokens
                utilities[client.name] = utility
                wasted[client.name] = wasted_budget
                backlogs[client.name] = client.backlog
                freshness[client.name] = client.freshness_age

            slot_results.append(
                SlotResult(
                    slot=slot,
                    allocations=allocation.budgets,
                    accepted_tokens=accepted,
                    utilities=utilities,
                    wasted_budget=wasted,
                    backlogs=backlogs,
                    freshness=freshness,
                )
            )

        return summarize_run(scheduler.name, self.config.world_mode, slot_results), slot_results

