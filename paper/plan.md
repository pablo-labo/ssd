# Toward a Paper: Execution Plan

## 0. Current Position

This project is at the problem-framing plus early-simulator stage.

What we already have:

- A working SSD codebase and benchmark harness.
- A deterministic scheduling simulator in `sim/`.
- Initial real async SSD shape measurements over several `(k, f)` settings.
- A previous unified-budget framing in `paper/idea.md`.

The framing has now changed in an important way:

- Old version: treat `S_i` as a unified verifier-side speculative budget.
- New version: treat `S_i` as an upper-level scheduler signal, then map it
  through a client policy into physical actions `(k_i, f_i)`.

This avoids forcing one variable to mean linear length, tree size, verifier work,
and drafter work at the same time.

## 1. Target Thesis

The paper should be framed around the verifier/drafter split, not around
deadline or age-aware serving objectives. Those can remain future work.

The thesis should be:

> In multi-client SSD serving, the traditional linear speculative-budget
> abstraction is too coarse because verifier and drafter bottlenecks act on
> different physical variables. The verifier sees a global linear lookahead
> constraint over `k_i`, while each drafter has a local compute/latency constraint
> over the chosen `(k_i, f_i)` frontier shape. We introduce a two-level scheduling
> model where the scheduler emits an abstract signal `S_i`, and each client maps
> it to executable SSD actions `(k_i, f_i)` under both constraints.

The contribution stack should be:

1. **Problem abstraction**
   - Define the two-level control model: scheduler signal `S_i`, execution actions
     `(k_i, f_i)`.
   - Separate global verifier constraint from local drafter constraint.

2. **Cost and service model**
   - Define `g_i(k_i, f_i; xi_i) <= c_i` for draft-side feasibility.
   - Define `mu_i^SSD(k_i, f_i, xi_i)` for realized goodput.
   - Start with a simple model such as `g_i = a_i k_i + b_i k_i f_i`.

3. **Structural result**
   - Show that linear `S_i -> k_i` scheduling can misallocate when clients have
     different draft-side costs or depth-width efficiencies.

4. **Empirical validation**
   - Calibrate `g_i` and `mu_i^SSD` from real SSD `(k, f)` shape runs.
   - Evaluate whether the calibrated curves induce allocation reversals or
     measurable goodput gains in multi-client scheduling.

## 2. Main Scientific Questions

### Q1. What is the right physical constraint?

Expected answer:

The verifier-side constraint is:

```text
sum_i k_i <= C
```

not `sum_i S_i <= C`.

`S_i` is retained as an abstract scheduling signal, but the verifier physically
executes `k_i`.

### Q2. What constrains fan-out?

Expected answer:

Fan-out is constrained by the drafter's local compute and latency window:

```text
g_i(k_i, f_i; xi_i) <= c_i
```

This is the part missing from a pure linear-budget model.

### Q3. How does `S_i` affect execution?

Expected answer:

Through a client policy:

```text
(k_i, f_i) = pi_i(S_i, xi_i)
```

The paper must give at least one executable policy. The best first version is
cost-aware:

```text
(k_i, f_i) = argmax mu_i^SSD(k, f, xi_i)
subject to g_i(k, f; xi_i) <= h_i(S_i, c_i)
```

### Q4. Does this change scheduling decisions?

Expected answer:

It should, in heterogeneous regimes. A client with high linear acceptance but
poor fan-out efficiency may receive less useful service than a client with lower
linear acceptance but better `(k, f)` frontier efficiency.

The minimum required evidence is a clean two-client allocation reversal.

## 3. Evidence Ladder

### Level 1: Problem statement

Status: in progress.

Deliverable:

- `paper/idea.md` rewritten around two-level control.

Acceptance criteria:

- `S_i`, `k_i`, and `f_i` have distinct meanings.
- The constraints are explicit.
- No deadline or age-aware serving objective is needed for the core story.

### Level 2: Toy structural simulator

Status: current simulator exists, but its variable semantics need updating.

Immediate change:

- Scheduler emits `S_i`.
- Client policy maps `S_i` to `(k_i, f_i)`.
- Environment enforces `sum k_i <= C`.
- Client feasibility uses `g_i(k_i, f_i; xi_i) <= c_i`.
- Service is `mu_i^SSD(k_i, f_i, xi_i)`.

Acceptance criteria:

- We can run linear `S_i -> k_i` baseline.
- We can run rule-based and cost-aware `(k_i, f_i)` policies.
- We can plot marginal service curves over `k` and `f`.

### Level 3: Structural separation

Status: missing.

Minimum theorem or proposition:

There exist two clients A and B such that:

```text
alpha_A > alpha_B
```

so a linear scheduler prefers A, but under SSD-aware execution:

```text
Delta_B^SSD(k, f, xi_B) > Delta_A^SSD(k, f, xi_A)
```

for the relevant budget range, so the optimal allocation prefers B.

This only needs to be a small finite-action result. The goal is to formalize the
resource mismatch, not to prove a grand asymptotic theorem.

### Level 4: Real SSD calibration

Status: early measurements exist.

Needed measurements:

- `(k, f)` shape.
- accepted suffix length.
- cache hit rate.
- draft-side timing or proxy.
- target verify time.
- accepted tokens per verifier second.
- accepted tokens per draft-cost proxy.

First fitting target:

```text
g_i(k, f) = a_i k + b_i k f
mu_i^SSD(k, f, xi_i) = empirical goodput table or smooth fit
```

Acceptance criteria:

- Different `(k, f)` shapes produce measurably different cost-service tradeoffs.
- The fitted curves are non-linear enough to affect scheduler decisions.

### Level 5: Trace-driven evaluation

Status: missing.

Minimum viable version:

- Use calibrated shape profiles from real SSD runs.
- Create heterogeneous client classes with different `a_i`, `b_i`, and service
  curves.
- Compare:
  - equal allocation;
  - linear `S_i -> k_i` scheduler;
  - fixed-shape SSD scheduler;
  - two-level SSD-aware scheduler.

Acceptance criteria:

- Show where two-level scheduling helps.
- Show where it does not help.
- Connect wins to draft-side cost or depth-width efficiency, not to arbitrary
  simulator knobs.

## 4. Concrete Work Plan

### Phase A: Clean notation and docs

Deliverables:

- Rewritten `paper/idea.md`.
- A one-page problem statement.
- Figure sketch:
  - top: old linear chain, `S_i = k_i`;
  - middle: SSD frontier with `(k_i, f_i)`;
  - bottom: two constraints, `sum k_i <= C` and `g_i <= c_i`.

### Phase B: Update simulator semantics

Deliverables:

- `ClientPolicy` returns `(k, f)` instead of direct service.
- `DrafterCostModel` abstraction.
- `VerifierBudgetProjector` or equivalent feasibility check for `sum k_i <= C`.
- Baselines:
  - linear length baseline;
  - rule-based depth/width split;
  - cost-aware policy.

### Phase C: Add structural experiment

Deliverables:

- Two-client separation script.
- Marginal curve plot over budget units.
- Table showing allocation reversal.

### Phase D: Calibrate from real runs

Deliverables:

- Shape grid summary over `(k, f)`.
- Fit or table for `g_i`.
- Fit or table for `mu_i^SSD`.
- Sensitivity over workload classes if data is available.

### Phase E: Paper skeleton

Sections:

- Introduction.
- Background: speculative decoding and SSD.
- Why linear budget fails.
- Two-level system model.
- Structural separation.
- Scheduler policy.
- Calibration and evaluation.
- Limitations.

## 5. Scheduler Design Direction

Start with a conservative algorithm:

1. For each client and candidate scheduling signal `S`, enumerate feasible
   `(k, f)` actions.
2. Remove actions violating `g_i(k, f; xi_i) <= h_i(S_i, c_i)`.
3. Estimate `mu_i^SSD(k, f, xi_i)` from a table or fitted curve.
4. Choose the best local action for each candidate `S`.
5. Allocate across clients while respecting `sum_i k_i <= C`.

The first implementation can be greedy over marginal goodput:

```text
M_i = best_gain_i(next S_i) - best_gain_i(current S_i)
```

but the actual feasibility check must be based on the resulting `k_i`, not on
`S_i` itself.

## 6. Baselines

Minimum baselines:

- Equal `k` allocation.
- Linear budget scheduler with `S_i = k_i`.
- Fixed shape scheduler, e.g. always `(k=6, f=3)`.
- Rule-based `S_i -> (k_i, f_i)` split.
- Oracle table over measured `(k, f)` profiles.

Useful ablations:

- No fan-out choice.
- No draft-side cost constraint.
- Homogeneous versus heterogeneous `c_i`.
- Hand-written curves versus empirical profiles.

## 7. Metrics

Primary metrics:

- Realized goodput.
- Accepted tokens per verifier second.
- Accepted tokens per draft-cost proxy.

Secondary metrics:

- accepted suffix length;
- cache hit rate;
- verifier budget utilization;
- drafter budget utilization;
- wasted branching work;
- allocation reversal rate;
- fairness across clients.

## 8. Risks and Kill Criteria

### Risk 1: `S_i` remains too abstract

Mitigation:

- Always define an explicit `pi_i(S_i, xi_i)`.
- Include both rule-based and cost-aware policies.

Kill criterion:

If no simple policy can make `S_i` operational, remove `S_i` and formulate the
scheduler directly over `(k_i, f_i)`.

### Risk 2: Real SSD cost is not captured by simple `g_i`

Mitigation:

- Start with `a_i k_i + b_i k_i f_i`.
- Add measured lookup tables if the linear-plus-interaction model is too weak.

Kill criterion:

If measured cost is too noisy to model or predict, keep the work as an empirical
trace scheduler rather than a clean theory paper.

### Risk 3: Scheduling gains are small

Mitigation:

- Focus on heterogeneous workloads and constrained drafter regimes.
- Report when the two-level model collapses back to the linear baseline.

Kill criterion:

If calibrated curves never change allocation decisions in realistic regimes, the
top-level claim should be reframed or abandoned.
