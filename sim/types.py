from dataclasses import dataclass, field


@dataclass
class ClientConfig:
    name: str
    arrival_rate: int
    base_acceptance: float
    frontier_quality: float
    expansion_policy: str
    initial_backlog: float = 0.0
    empirical_f: int | None = None


@dataclass
class ClientSnapshot:
    name: str
    backlog: float
    freshness_age: int
    frontier_quality: float
    frontier_state: float


@dataclass
class SlotAllocation:
    budgets: dict[str, int]
    predicted_marginals: dict[str, list[float]]


@dataclass
class SlotResult:
    slot: int
    allocations: dict[str, int]
    accepted_tokens: dict[str, float]
    utilities: dict[str, float]
    wasted_budget: dict[str, float]
    backlogs: dict[str, float]
    freshness: dict[str, int]


@dataclass
class RunSummary:
    scheduler: str
    world_mode: str
    total_accepted_tokens: float
    total_utility: float
    total_wasted_budget: float
    fairness: float
    per_client_utility: dict[str, float] = field(default_factory=dict)
    per_client_accepted_tokens: dict[str, float] = field(default_factory=dict)
    final_backlogs: dict[str, float] = field(default_factory=dict)
