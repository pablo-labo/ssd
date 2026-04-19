# Toward a Top-Tier Conference Paper: Execution Plan

## 0. Current Position

This project is currently at the **problem-framing plus toy-simulator stage**.

What we already have:

- A strong research framing in `paper/idea.md`.
- A working deterministic simulator in `sim/`.
- A clean first comparison between:
  - `LinearBudgetScheduler`: allocates verifier budget as if `S_i` were linear speculative length.
  - `UnifiedBudgetScheduler`: allocates verifier budget using SSD/tree-aware service semantics.
- Initial sweep evidence:
  - `evaluated_cases=81`
  - `unified_win_rate=60/81 (74.1%)`
  - `allocation_reversal_rate=60/81 (74.1%)`
  - `utility_reversal_rate=3/81 (3.7%)`
- A plausible next bridge to real SSD metrics through `bench/bench.py` and the existing engine metrics.

What we do not yet have:

- A calibrated service model grounded in real SSD runs.
- A theory result showing when linear-budget scheduling provably misallocates.
- A full online scheduler with a clear algorithmic contribution beyond "use the unified service curve".
- Strong real-system experiments showing meaningful gains under realistic multi-client workloads.
- A polished paper narrative with figures, ablations, baselines, and reviewer-proof threat analysis.

The current state is promising but not yet paper-grade. The idea is valuable only if we can show that the linear interpretation of `S_i` genuinely fails in SSD/tree regimes, and that a unified-budget scheduler fixes this failure in a measurable and principled way.

## 1. Target Paper Thesis

The paper should not be framed as "we add freshness to SSD" or "we tune a simulator".

The top-level thesis should be:

> In multi-client speculative serving, existing scheduling methods implicitly treat verifier-side budget `S_i` as linear draft length. This abstraction breaks in SSD/tree speculation, where the same verifier budget can be mapped to structurally different frontier expansions. We introduce unified speculative budget scheduling, characterize when linear-budget scheduling misallocates resources, and show that SSD-aware scheduling improves fresh accepted utility under realistic serving workloads.

The contribution stack should be:

1. **Problem abstraction**
   - Define unified speculative budget.
   - Show that GoodSpeed/G-FAST-style linear service models are special cases.

2. **Structural result**
   - Show that tree/frontier service curves can reverse the optimal allocation order induced by linear service curves.
   - This must be more than an empirical observation.

3. **Scheduling algorithm**
   - Design a freshness-aware unified-budget scheduler using online estimates of SSD service efficiency and frontier state.

4. **Empirical validation**
   - Calibrate the service model with real SSD measurements.
   - Evaluate simulator-scale multi-client regimes.
   - Validate selected cases in the real SSD engine or a trace-driven serving harness.

## 2. Main Scientific Questions

The paper must answer four questions clearly.

### Q1. Is `S_i` still a linear length budget in SSD/tree speculation?

Expected answer:

No. In SSD/tree regimes, `S_i` is better understood as verifier-side speculative budget. The client can spend that budget across depth, width, frontier refresh, or mixed expansion.

Evidence needed:

- Formal definition of linear budget vs unified budget.
- Real SSD measurements showing that different speculative shapes with comparable verifier cost produce different accepted-token curves.

### Q2. Does the old abstraction cause real scheduling errors?

Expected answer:

Yes. Linear-budget scheduling can assign budget to clients with high linear acceptance but poor frontier efficiency, while under-allocating clients with better SSD/tree expansion efficiency.

Evidence needed:

- A clean two-client theorem or proposition.
- Simulator allocation reversal results.
- Real-data-calibrated examples showing the same reversal.

### Q3. Does unified-budget scheduling improve the objective?

Expected answer:

Yes, especially under heterogeneous clients, constrained verifier budgets, high load, and freshness-sensitive workloads.

Evidence needed:

- Fresh accepted utility gains.
- Accepted tokens per verifier time.
- Backlog and fairness analysis.
- Ablations over freshness, load, client heterogeneity, and expansion policy.

### Q4. Is the result robust enough for a top-tier systems/ML venue?

Expected answer:

Only if we move beyond the current hand-designed simulator curves.

Evidence needed:

- Calibration with real SSD metrics.
- Strong baselines.
- Sensitivity analysis.
- Clear limitations.

## 3. Where We Are on the Evidence Ladder

### Level 1: Conceptual framing

Status: **mostly complete**.

`paper/idea.md` already explains:

- why verifier budget is the scarce resource;
- why `S_i` is currently treated as linear speculative length;
- why SSD/tree speculation changes the meaning of `S_i`;
- why freshness-aware scheduling should use an SSD-aware service model.

Remaining work:

- Compress this into a one-page problem statement.
- Convert notation into paper-ready math.
- Decide the exact target venue and paper style.

### Level 2: Toy simulator evidence

Status: **partially complete**.

Current simulator demonstrates:

- unified scheduling often changes allocation order;
- unified scheduling wins in most swept toy regimes;
- gains are present but currently modest;
- structural reversal is much stronger than utility reversal.

Main weakness:

- The unified service model is hand-designed.
- The simulator currently proves plausibility, not realism.

Immediate improvement:

- Add a minimal "structural separation" experiment with two clients.
- Make the simulator output service curves and marginal utility curves.
- Add confidence-style summaries over randomized client populations.

### Level 3: Theoretical evidence

Status: **missing**.

Minimum acceptable theory target:

- A two-client finite-budget proposition showing that linear and tree-aware service models can induce opposite optimal allocation orders.

Possible theorem shape:

Let client A have higher linear acceptance parameter than client B:

```text
alpha_A > alpha_B
```

Under a linear service model, the greedy marginal scheduler allocates more budget to A.

But under an SSD/tree service model:

```text
mu_i^SSD(S, xi_i) = g_i(S) * h_i(xi_i)
```

there exist frontier states `xi_A, xi_B` and expansion efficiencies such that:

```text
Delta_B^SSD(S) > Delta_A^SSD(S)
```

for the relevant marginal budget units, so the optimal unified allocation gives more budget to B.

The theorem does not need to be grand. It only needs to formalize the structural mismatch cleanly.

### Level 4: Real SSD metric calibration

Status: **not started, but paths exist**.

Relevant real metrics already mentioned in `sim/README.md`:

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

Goal:

Fit empirical service curves:

```text
mu_i^SSD(S, xi; pi)
```

from real SSD runs instead of relying on hand-designed curves in `sim/policy.py`.

First real-run matrix:

- Hardware: RTX A4500 first, H100 later if available.
- Target: `Qwen/Qwen3-8B`.
- Draft: `Qwen/Qwen3-0.6B`.
- Dataset: `gsm` first, then code/math/chat mixes.
- Temperature: `0` first, then nonzero temperature.
- Async SSD shapes:
  - `(k=4, f=2)`
  - `(k=6, f=3)`
  - `(k=8, f=4)`
- Optional later:
  - varied `fan_out_list`;
  - longer output lengths;
  - different prompt distributions.

Required artifact:

- A CSV or JSONL export per run containing:
  - model setup;
  - dataset;
  - speculative shape;
  - accepted suffix stats;
  - cache hit stats;
  - target verify times;
  - accepted tokens per verifier second;
  - prompt/output length metadata.

### Level 5: Trace-driven or real serving validation

Status: **missing**.

Minimum viable version:

- Use real SSD measurements to build per-client empirical service profiles.
- Feed those profiles into the simulator.
- Evaluate multi-client scheduling over synthetic arrivals and freshness deadlines.

Stronger version:

- Build a trace-driven serving harness where multiple client streams choose requests from different datasets.
- Scheduler selects per-client budget/shape decisions.
- The engine executes representative SSD configurations or replays measured profiles.

Best version:

- Real online multi-client SSD serving loop.
- This is probably too expensive for the first paper unless the engine already supports most of it cleanly.

Recommended path:

Start with trace-driven validation. It gives most of the paper value with much less engineering risk.

## 4. Concrete Work Plan

### Phase A: Make the claim crisp

Deliverables:

- `paper/problem_statement.md`
- 1-page figure sketch:
  - left: linear speculative budget as a chain;
  - right: unified speculative budget as a tree/frontier;
  - bottom: same `S_i`, different marginal service curves.
- Paper contribution list.

Acceptance criteria:

- A collaborator can explain the paper in 60 seconds.
- The difference from GoodSpeed/G-FAST is obvious.
- The role of SSD is essential, not decorative.

### Phase B: Strengthen the simulator

Deliverables:

- Structural separation experiment.
- Randomized regime sweep.
- Service curve plotting script.
- Cleaner metrics:
  - accepted tokens;
  - fresh accepted utility;
  - accepted tokens per verifier budget;
  - final backlog;
  - allocation reversal;
  - marginal curve reversal;
  - fairness;
  - wasted verifier budget with consistent units.

Acceptance criteria:

- We can produce a figure where linear and unified schedulers make visibly different choices.
- Gains are not only from one hand-picked regime.
- There are ablations showing when unified scheduling helps and when it does not.

### Phase C: Add the minimal theory

Deliverables:

- One proposition about allocation-order reversal.
- One proof sketch in paper notation.
- Optional corollary connecting freshness decay to larger loss under stale allocation.

Acceptance criteria:

- The theorem is simple enough to fit in the main paper.
- It directly explains a simulator or trace result.
- It does not require unrealistic assumptions that contradict the experiments.

### Phase D: Collect real SSD calibration data

Deliverables:

- Metrics export path from `bench/bench.py`.
- Real-run matrix for Qwen3-8B/Qwen3-0.6B.
- CSV/JSONL result files.
- Fitting script mapping real runs to service profiles.

Acceptance criteria:

- We can plot accepted suffix length and verifier efficiency versus speculative shape.
- We can fit or tabulate `mu^SSD(S, xi, pi)` for at least a few client/workload classes.
- The fitted curves differ enough from linear curves to support the paper's premise.

### Phase E: Build trace-driven evaluation

Deliverables:

- Multi-client workload generator:
  - interactive;
  - search/batch;
  - code/math;
  - commodity chat.
- Trace-driven scheduler comparison:
  - linear-budget baseline;
  - GoodSpeed-style marginal scheduler;
  - G-FAST-style freshness scheduler;
  - unified-budget scheduler;
  - oracle upper bound if feasible.
- Full sweep over:
  - verifier budget;
  - load;
  - freshness decay;
  - client heterogeneity;
  - frontier quality;
  - service curve noise.

Acceptance criteria:

- Unified scheduling wins in the regimes predicted by the theory.
- The result is robust to reasonable parameter changes.
- Baselines are strong enough that the gain is credible.

### Phase F: Paper assembly

Deliverables:

- Abstract.
- Introduction.
- Related work.
- System model.
- Structural mismatch theorem.
- Scheduler algorithm.
- Experimental setup.
- Results.
- Limitations.

Target figures:

1. Motivation figure: linear chain budget vs unified tree/frontier budget.
2. Service curve figure: real SSD accepted utility vs budget/shape.
3. Structural reversal figure: two-client allocation reversal.
4. Main result: fresh accepted utility under load.
5. Ablation: freshness/load/heterogeneity.
6. Calibration figure: simulator predictions vs real SSD metrics.
7. Fairness/backlog figure.

## 5. Scheduler Design Direction

The scheduler should be more than "greedy over a hand-written unified curve".

Recommended algorithm:

1. Maintain an online estimate for each client:

```text
hat_mu_i(S, xi_i, pi_i)
```

2. Track freshness:

```text
Phi(Delta_i)
```

3. Estimate marginal fresh utility:

```text
Delta_i(S) =
  U_i'(bar_y_i) *
  [hat_mu_i(S + 1, xi_i, pi_i) - hat_mu_i(S, xi_i, pi_i)] *
  Phi(Delta_i)
```

4. Greedily allocate verifier budget units to the highest marginal fresh utility.

5. Update service estimates from observed accepted suffix lengths, cache hits, and verifier times.

Possible names:

- FUSION: Fresh Unified Speculative Inference schedulON.
- FUSE: Fresh Unified Speculative Expansion.
- UBS: Unified Budget Scheduling.

Use a restrained name unless the acronym genuinely helps.

## 6. Baselines

Minimum baselines:

- Static equal budget.
- Linear speculative budget scheduler.
- GoodSpeed-style goodput scheduler.
- G-FAST-style freshness scheduler.
- Unified scheduler without freshness.
- Unified scheduler with freshness.

Useful ablations:

- No frontier state.
- No cache-hit signal.
- No online adaptation.
- Oracle service curve.
- Miscalibrated service curve.

Important:

The strongest baseline is probably a G-FAST-like freshness scheduler using the best linear service estimate. We must beat that, not only equal allocation.

## 7. Metrics

Primary metric:

- Fresh accepted utility.

Secondary metrics:

- Accepted tokens per verifier second.
- Accepted tokens per verifier budget.
- Mean and tail freshness age.
- Final backlog.
- Jain fairness over per-client utility.
- Allocation reversal rate.
- Marginal curve reversal rate.
- Wasted verifier budget.
- Cache hit rate.
- Accepted suffix length on hit and miss.

For top-tier credibility, every gain should be connected to one of:

- better verifier efficiency;
- lower staleness;
- lower backlog;
- better fairness at comparable throughput.

## 8. Risks and Kill Criteria

### Risk 1: Real SSD curves look almost linear

Consequence:

The unified-budget framing becomes weak.

Mitigation:

- Test diverse datasets and speculative shapes.
- Look for heterogeneity across workloads, not only average gain.

Kill criterion:

If real SSD service curves do not produce allocation reversals in any realistic regime, the top-tier version should be abandoned or reframed.

### Risk 2: Gains are too small

Consequence:

The paper may read as a modeling refinement with limited practical value.

Mitigation:

- Focus on high-load, freshness-sensitive, heterogeneous-client regimes.
- Use accepted utility and latency/freshness metrics, not only throughput.

Kill criterion:

If calibrated trace-driven gains stay below roughly 3-5% and are not robust, the result is probably not enough for a systems/ML top-tier paper.

### Risk 3: The scheduler is just an oracle over fitted curves

Consequence:

Reviewers may say the algorithm assumes the hard part away.

Mitigation:

- Use online estimation.
- Include miscalibration and cold-start experiments.
- Show the scheduler adapts from observable engine metrics.

### Risk 4: Real online implementation becomes too expensive

Consequence:

Engineering can consume the project.

Mitigation:

- Use trace-driven evaluation first.
- Only implement real online scheduling if the trace-driven story is already strong.

## 9. Near-Term Checklist

Next 1 week:

- Write `paper/problem_statement.md`.
- Add structural separation experiment in `sim/experiments/`.
- Add plotting/export for marginal service curves.
- Decide exact real-run metrics schema.

Next 2-3 weeks:

- Patch `bench/bench.py` to export SSD metrics.
- Run Qwen3-8B/Qwen3-0.6B calibration matrix.
- Fit first empirical service profiles.
- Replace or augment hand-designed simulator curves with empirical profiles.

Next 4-6 weeks:

- Implement trace-driven evaluation.
- Add GoodSpeed/G-FAST-style baselines.
- Run full sweeps and ablations.
- Draft theorem and proof sketch.

Next 6-8 weeks:

- Freeze main claims.
- Produce paper figures.
- Write the first full draft.
- Identify weak claims and remove them.

## 10. Immediate Recommendation

The most important next step is **not** to build a full online serving system.

The most important next step is to close the evidence loop:

```text
real SSD metrics -> calibrated service curves -> trace-driven scheduling gains
```

Once that loop exists, we can judge whether this is a top-tier paper, a workshop paper, or a useful internal research note.

Right now, the project is promising because the abstraction is sharp and the toy simulator already shows structural mismatch. It is not yet top-tier-ready because the central service model is not empirically grounded.
