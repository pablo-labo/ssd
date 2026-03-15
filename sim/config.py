from dataclasses import dataclass, field, replace

from sim.types import ClientConfig


@dataclass
class SimConfig:
    num_slots: int = 12
    verifier_budget: int = 10
    enable_freshness: bool = True
    freshness_lambda: float = 0.18
    world_mode: str = "unified"
    unit_budget: int = 1
    clients: list[ClientConfig] = field(default_factory=list)


def make_default_config() -> SimConfig:
    return SimConfig(
        num_slots=12,
        verifier_budget=10,
        enable_freshness=True,
        freshness_lambda=0.18,
        world_mode="unified",
        clients=[
            ClientConfig(
                name="interactive_depth",
                arrival_rate=4,
                base_acceptance=0.62,
                frontier_quality=0.92,
                expansion_policy="depth_heavy",
                initial_backlog=6,
            ),
            ClientConfig(
                name="search_width",
                arrival_rate=5,
                base_acceptance=0.48,
                frontier_quality=0.88,
                expansion_policy="width_heavy",
                initial_backlog=6,
            ),
            ClientConfig(
                name="commodity_linear",
                arrival_rate=6,
                base_acceptance=0.70,
                frontier_quality=0.45,
                expansion_policy="linear",
                initial_backlog=6,
            ),
        ],
    )


def with_load_multiplier(config: SimConfig, multiplier: float) -> SimConfig:
    clients = [
        replace(client, arrival_rate=max(1, round(client.arrival_rate * multiplier)))
        for client in config.clients
    ]
    return replace(config, clients=clients)


def with_freshness(config: SimConfig, freshness_lambda: float, enable_freshness: bool = True) -> SimConfig:
    return replace(
        config,
        freshness_lambda=freshness_lambda,
        enable_freshness=enable_freshness,
    )


def with_budget(config: SimConfig, verifier_budget: int) -> SimConfig:
    return replace(config, verifier_budget=verifier_budget)


def with_policy_mix(config: SimConfig, mix_name: str) -> SimConfig:
    if mix_name == "balanced":
        return config

    if mix_name == "tree_skewed":
        clients = [
            replace(config.clients[0], frontier_quality=0.98, expansion_policy="depth_heavy"),
            replace(config.clients[1], frontier_quality=0.95, expansion_policy="quality_aware"),
            replace(config.clients[2], frontier_quality=0.30, expansion_policy="linear"),
        ]
        return replace(config, clients=clients)

    if mix_name == "linear_skewed":
        clients = [
            replace(config.clients[0], frontier_quality=0.55, expansion_policy="mixed"),
            replace(config.clients[1], frontier_quality=0.45, expansion_policy="linear"),
            replace(config.clients[2], frontier_quality=0.70, expansion_policy="linear"),
        ]
        return replace(config, clients=clients)

    raise ValueError(f"Unknown policy mix: {mix_name}")
