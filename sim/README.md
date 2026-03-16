# Simulator Design

## Current Status

This directory already contains a working deterministic simulator and two
experiment entrypoints:

- `python3 -m sim.experiments.baseline_grid`
- `python3 -m sim.experiments.sweep_regimes`

The simulator is not a real SSD runtime. It is a research prototype used to
test whether changing the meaning of verifier-side budget `S_i` changes the
multi-client allocation structure.

## How To Use

Run from the repo root:

```bash
python3 -m sim.experiments.baseline_grid
python3 -m sim.experiments.sweep_regimes
```

What each command does:

- `baseline_grid`: runs one default configuration and prints summary metrics for
  `LinearBudgetScheduler` and `UnifiedBudgetScheduler`.
- `sweep_regimes`: sweeps verifier budget, load, freshness, and policy mix, and
  reports:
  - win rate of unified over linear;
  - allocation-order reversal rate;
  - utility-order reversal rate;
  - representative best and worst cases.

## What "Unified" Means Here

The current simulator does not execute real tree decoding. Instead it models
two different service semantics:

- `linear`
  - budget behaves like linear speculative length.
- `unified`
  - budget behaves like a unified speculative resource that a client can spend
    through an expansion policy and a dynamic frontier state.

Implementation notes:

- `linear_service` and `unified_service` live in
  [`sim/policy.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/sim/policy.py).
- dynamic frontier state lives in
  [`sim/client.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/sim/client.py).
- the environment currently runs with `world_mode="unified"`, meaning the
  ground-truth service model is unified, while the linear scheduler still
  allocates as if budget were linear.

This is intentional: it directly tests the hypothesis that old schedulers may
misallocate budget when SSD/tree-style client-side expansion changes the true
service semantics of `S_i`.

## Current Results

Latest baseline run:

- `linear_budget`
  - total accepted tokens: `184.34`
  - total utility: `70.62`
  - fairness: `0.9923`
- `unified_budget`
  - total accepted tokens: `184.83`
  - total utility: `70.90`
  - fairness: `0.9904`

Latest sweep run:

- `evaluated_cases=81`
- `unified_win_rate=60/81 (74.1%)`
- `allocation_reversal_rate=60/81 (74.1%)`
- `utility_reversal_rate=3/81 (3.7%)`

Representative gain case:

- `budget=14|load=1.30|fresh=0.00|mix=linear_skewed`
- `linear utility=221.59`
- `unified utility=225.53`
- allocation order changes from
  `['interactive_depth', 'search_width', 'commodity_linear']`
  to
  `['commodity_linear', 'search_width', 'interactive_depth']`

Representative neutral case:

- `budget=6|load=0.80|fresh=0.00|mix=linear_skewed`
- linear and unified produce the same allocation and utility

## Current Conclusions

What the current simulator already supports:

- changing the service semantics of `S_i` frequently changes budget allocation
  order;
- structural mismatch appears more often than utility-order reversal;
- the current model is conservative enough that unified is not trivially or
  dramatically better in every regime;
- the idea is strong enough for an internal group-meeting demo.

What the current simulator does **not** prove:

- that real SSD serving will exhibit the same magnitude of gains;
- that the current unified service curve is faithful to real LLM behavior;
- that a full online multi-client LLM scheduler is already validated.

The right interpretation is:

- this simulator is evidence that the problem framing is operational and can
  produce structural mismatches;
- the next major step is to calibrate the simulator with real SSD metrics such
  as accepted suffix length, cache hits, and verifier-side efficiency.

## Preparing Real LLM Integration

The next step is **not** to build a full online multi-client scheduler inside
the SSD engine. The right next step is to collect real SSD metrics and use them
to calibrate the simulator.

### 1. Metrics To Collect From Real SSD Runs

These metrics already exist in the current engine and benchmark code:

- `accepted_suffix_lens_with_recovery`
- `accepted_suffix_lens_on_hit`
- `accepted_suffix_lens_on_miss`
- `cache_hits`
- `target_step_times`
- `target_verify_times`
- `prefill_total_time`
- `decode_total_time`
- `prefill_total_tokens`
- `decode_total_tokens`

They are surfaced through:

- [`ssd/engine/llm_engine.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/ssd/engine/llm_engine.py)
- [`ssd/engine/verifier.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/ssd/engine/verifier.py)
- [`bench/bench.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/bench/bench.py)

### 2. Why These Metrics Matter

They give us the first empirical bridge from SSD to the simulator:

- accepted suffix lengths:
  proxy for per-step accepted utility under a given speculative shape;
- cache hits:
  proxy for whether a client is operating in an efficient frontier regime;
- target verify times:
  proxy for verifier-side cost;
- accepted tokens divided by verifier time:
  proxy for service efficiency under a given budget shape.

This is enough to start fitting simulator service curves without claiming that
the simulator is already a faithful execution model.

### 3. Minimal Real-Run Matrix

The first real-LLM collection pass should stay small.

Use one model family and one workload family first.

Recommended first pass:

- remote hardware:
  - `NVIDIA RTX A4500`;
- one target model family:
  - `qwen`;
- one target model:
  - `Qwen3-8B`;
- one draft setup:
  - `Qwen3-0.6B`;
- one dataset family:
  - `gsm` first;
- fixed temperature:
  - `temp=0` first to reduce variance;
- sweep only a few speculative shapes:
  - `k in {4, 6, 8}`
  - `f in {2, 3, 4}` for async mode
  - optional `fan_out_list` variants later

### 4. Minimal Benchmark Commands

Run from `bench/` after normal SSD setup.

Examples:

```bash
python -O bench.py --qwen --size 8 --spec --async --draft 0.6 --k 4 --f 2 --b 1 --temp 0 --numseqs 32 --output_len 128
python -O bench.py --qwen --size 8 --spec --async --draft 0.6 --k 6 --f 3 --b 1 --temp 0 --numseqs 32 --output_len 128
python -O bench.py --qwen --size 8 --spec --async --draft 0.6 --k 8 --f 4 --b 1 --temp 0 --numseqs 32 --output_len 128
```

These commands match the current plan: `RTX A4500`, `Qwen3-8B` target,
`Qwen3-0.6B` draft, and a small `gsm`-style first-pass collection sweep. The
goal of this stage is data collection, not leaderboard benchmarking.

### 5. Mapping Real SSD Metrics Back To The Simulator

The first mapping does not need to be perfect. It only needs to be explicit.

Recommended initial mapping:

- `base_acceptance`
  - fit from average accepted suffix length under a fixed `(k, f)` setting;
- `frontier_quality`
  - initialize from cache-hit-heavy regimes or from accepted suffix length on
    cache hits;
- `frontier_state`
  - evolve according to recent cache hit rate or recent accepted suffix trend;
- verifier budget proxy
  - start with one of:
    - `k`
    - `f`
    - `sum(fan_out_list)`
  - later replace with a better verifier-cost estimate using target verify time.

### 6. What Must Be Prepared Before Writing New Engine Code

Before touching the SSD runtime for online unified-budget scheduling, prepare:

1. a metrics table for each real run:
   - model, dataset, `k`, `f`, fan-out settings, batch size;
   - accepted suffix stats;
   - cache-hit stats;
   - verifier-time stats.
2. a documented mapping from real metrics to simulator parameters.
3. one or two calibrated simulator cases showing that the structural mismatch
   signal survives after calibration.

If these three pieces are missing, it is too early to claim that the idea has
crossed from abstract simulator evidence into real-system evidence.

### 7. Practical Readiness Check

We are ready to start real-LLM integration when:

- simulator results are stable enough to show in a meeting;
- we know exactly which engine metrics we need;
- we have a small benchmark matrix that is feasible on available hardware;
- we are treating the first real runs as calibration data, not as final proof.

That is the current stage of the project.

## Goal

This simulator is the minimum validation harness for the idea in
[`paper/idea.md`](/Users/ruben/Documents/Git docs/specdiff/ssd/paper/idea.md):

- test whether `linear budget` and `unified speculative budget` induce
  different allocation behavior;
- identify regime changes rather than only small average gains;
- do this before modifying the real SSD engine.

The simulator should model a `multi-client, single-verifier` system with
lightweight client-side speculation abstractions. It is not meant to reproduce
the full GPU runtime of SSD. It is meant to isolate the scheduling question.

## Research Questions

The simulator should answer these first:

1. Does treating `S_i` as linear draft length become systematically suboptimal
   when client-side expansion is tree/frontier-based?
2. Under what regimes does a unified-budget scheduler outperform a linear-budget
   scheduler?
3. Are gains explained by better verifier-budget allocation, not by simply
   spending more total speculative compute?

## Scope

The first version should simulate:

- discrete time slots;
- `N` clients;
- one verifier bottleneck with total budget `C` per slot;
- per-client queue/backlog and freshness age;
- per-client internal expansion policy;
- realized accepted utility from verifier budget.

The first version should not simulate:

- actual token logits;
- actual draft/verify kernels;
- GPU memory layout or NCCL behavior;
- exact SSD tree execution traces.

## Core Abstraction

Each client receives verifier-side budget `S_i(t)` with:

`sum_i S_i(t) <= C`

Under the old abstraction:

- `S_i(t)` means linear speculative length;
- client service is `mu_i_linear(S_i, state_i)`.

Under the new abstraction:

- `S_i(t)` means unified speculative budget;
- client converts budget into a structured frontier via policy `pi_i`;
- service is `mu_i_unified(S_i, xi_i, pi_i)`.

The key comparison is not "better heuristic A vs heuristic B", but:

- `Linear-Budget Scheduler`: allocates as if service is linear;
- `Unified-Budget Scheduler`: allocates using the true structured service model.

## Simulator Entities

### 1. Client

Minimal state:

- `client_id`
- `backlog_tokens`
- `freshness_age`
- `acceptance_profile`
- `expansion_policy`
- `frontier_state`
- `arrival_process`
- `stats`

Minimal methods:

- `arrive(t) -> new_work`
- `estimate_linear_gain(S) -> expected_utility`
- `estimate_unified_gain(S) -> expected_utility`
- `consume_budget(S, mode) -> realized_service`
- `advance_freshness()`

### 2. Verifier

Minimal state:

- `total_budget_per_slot = C`

Minimal role:

- accepts budget allocation vector `S(t)`;
- checks feasibility;
- returns per-client realized accepted utility.

### 3. Scheduler

Common interface:

- `allocate(clients, budget, t) -> list[int]`

Initial scheduler variants:

1. `LinearBudgetScheduler`
   - assumes each client has linear service.
   - ignores internal frontier structure.

2. `UnifiedBudgetScheduler`
   - allocates using the true structured gain estimate.
   - can still be heuristic at first.

3. Optional later: `FreshnessAwareUnifiedScheduler`
   - multiplies gain by freshness utility or queue urgency.

### 4. Expansion Policy

This is the key client-side abstraction.

Each policy maps a unified budget to a speculative frontier shape.

Initial policies:

- `linear`
  - baseline equivalent to chain speculation.
- `depth_heavy`
  - spends budget to extend deeper paths.
- `width_heavy`
  - spends budget on broader frontier exploration.
- `mixed`
  - balances depth and width.
- `quality_aware`
  - allocates more budget to high-quality frontier regions.

The simulator does not need to materialize full trees initially. A compact
policy-dependent service curve is enough.

## Service Model

We need a simple model that is expressive enough to produce structural
differences.

### Linear Service

For client `i`:

`mu_i_linear(S) = expected accepted tokens from a chain of length S`

Possible approximation:

- acceptance parameter `alpha_i in (0, 1)`;
- `mu_i_linear(S)` increases with diminishing returns.

Examples:

- geometric acceptance style;
- capped concave curve;
- empirical table indexed by `S`.

### Unified Service

For client `i`:

`mu_i_unified(S, xi_i, pi_i)`

where:

- `xi_i` is frontier quality/state;
- `pi_i` determines how budget is split across depth/width;
- service can dominate or underperform linear service depending on regime.

The first version should use table-driven or analytic service curves rather than
simulate full token trees. The important part is to encode:

- heterogeneity across clients;
- policy-dependent gains;
- diminishing returns;
- interaction with freshness.

## Freshness Model

Freshness should be optional in v1, but built into the design.

Per client, define:

- `Delta_i(t)` as age or staleness;
- `Phi(Delta_i)` as freshness decay.

Examples:

- exponential decay;
- piecewise linear decay;
- hard deadline then zero utility.

Realized utility:

`y_i(t) = accepted_i(t) * Phi(Delta_i(t))`

If freshness is disabled:

`y_i(t) = accepted_i(t)`

## Slot Execution

Each simulation slot should run:

1. New work arrives per client.
2. Freshness age updates.
3. Scheduler computes budget allocation `S_i(t)`.
4. Clients consume budget under either linear or unified semantics.
5. Accepted utility is realized.
6. Backlog and frontier state are updated.
7. Metrics are logged.

This makes the simulator usable for both GoodSpeed-style and G-FAST-style
experiments.

## Metrics

The simulator should log at least:

- `accepted_tokens`
- `accepted_tokens_per_verifier_budget`
- `fresh_accepted_utility`
- `wasted_verifier_budget`
- `wasted_speculative_expansion`
- `backlog`
- `mean_latency_proxy`
- `per-client served utility`
- `Jain_fairness`

Important derived comparisons:

- unified vs linear total utility;
- unified vs linear fairness;
- allocation difference by regime;
- budget efficiency at equal verifier budget.

## Minimal Experiment Matrix

The first experiment suite should sweep:

- number of clients `N`;
- total verifier budget `C`;
- load level;
- acceptance heterogeneity;
- freshness decay strength;
- expansion policy mix.

The first regime-change checks should focus on:

1. Low load vs high load.
2. Homogeneous vs heterogeneous clients.
3. Weak freshness vs strong freshness.
4. Mostly linear-friendly vs mostly tree-friendly policy mix.

## Success Criteria

The simulator is useful only if it can reveal one of these:

- unified-budget scheduling changes allocation ordering;
- unified-budget scheduling wins significantly in certain regimes;
- linear-budget scheduling wastes verifier budget in a systematic pattern.

If results only show small uniform gains, the framing is weaker.

## Proposed File Layout

Initial layout:

```text
sim/
  README.md
  config.py
  types.py
  client.py
  policy.py
  scheduler.py
  metrics.py
  runner.py
  experiments/
    baseline_grid.py
```

Suggested responsibilities:

- `config.py`: simulation parameters and presets.
- `types.py`: dataclasses for state and outputs.
- `client.py`: client state transitions and service realization.
- `policy.py`: expansion policies and service curve helpers.
- `scheduler.py`: linear and unified schedulers.
- `metrics.py`: utility, fairness, efficiency metrics.
- `runner.py`: slot loop and result aggregation.

## Implementation Plan

### Phase 1: Deterministic Minimal Core

Build a deterministic simulator with:

- fixed arrivals;
- fixed client service curves;
- no randomness except optional seeded perturbation.

Deliverable:

- reproduce one clear linear-vs-unified separation plot or table.

### Phase 2: Add Stochasticity

Add:

- random arrivals;
- noisy realized service around expected service;
- repeated trials with confidence intervals.

Deliverable:

- robust regime map, not a single cherry-picked run.

### Phase 3: Add Freshness

Add:

- freshness decay;
- queue-age-aware utility;
- freshness-aware unified scheduler.

Deliverable:

- timely goodput comparison under load.

## Recommended First Heuristic Pair

To get the first result quickly:

- linear scheduler allocates by marginal gain from `mu_i_linear(S)`;
- unified scheduler allocates by marginal gain from
  `mu_i_unified(S, xi_i, pi_i)`.

Use a greedy allocator:

- repeatedly assign one budget unit to the client with highest current
  marginal utility until budget `C` is exhausted.

This is simple, interpretable, and enough to test whether the two abstractions
lead to different allocation orderings.

## What We Need to Prove Early

Before adding complexity, the simulator should establish at least one of:

- a client preferred by linear scheduling is not preferred by unified
  scheduling;
- the preference reversal is amplified by freshness;
- the reversal comes from structured budget usage, not from arbitrary curve
  tuning.

That is the first real checkpoint for the research idea.
