# Multi-Client SSD Scheduling: Execution Plan

## 0. Current Position

This project is now centered on the thesis stated in:

- `paper/proposal_cn.md`
- `paper/proposal_en.md`
- `paper/math_roadmap_v2.pdf`
- `paper/idea.md`

Older material built around "real-LLM calibration first" or a two-level
`S_i -> (k_i, f_i)` scheduler is no longer the active direction.

The active framing is:

- decision variable: verifier-side lookahead `k_i`;
- implicit coupled variable: drafter budget `B_i({k_j})`;
- objective: analyze the resulting SSD service curve and multi-client
  allocation structure;
- method: theory first, simulator second, paper-based calibration third.

The thesis does not require a real multi-client SSD system implementation in
its core path.

## 1. Target Thesis

The paper should be framed around the structural gap between:

- GoodSpeed: multi-client speculative decoding with monotone service in `k_i`;
- Saguaro: single-client SSD with fixed `k` and optimized fan-out shape.

The key thesis is:

> In multi-client SSD serving, the effective service curve is no longer a
> monotone function of verifier lookahead alone. Because each client's drafter
> budget is induced by shared verifier wall time, the service curve becomes
> non-monotone in `k_i` and non-locally coupled across clients. This creates
> positive externalities, possible allocation reversal relative to GoodSpeed,
> and potentially non-binding verifier optima.

## 2. Core Scientific Questions

### Q1. Single-client structure

Does `tilde(mu)_SSD(k)` exhibit the predicted unimodal shape, and how does the
internal optimum `k*` move with `alpha`, `r`, `a`, `b`, and `T_V`?

### Q2. Multi-client coupling

When `B_i` is written as a function of all lookaheads `{k_j}`, does the KKT
system expose the predicted positive externality term?

### Q3. Allocation reversal

Is there a non-trivial parameter region `R` where GoodSpeed's preferred
allocation order differs from the SSD-aware optimum?

### Q4. Non-binding verifier regime

Are there meaningful parameter settings where the SSD-aware optimum satisfies
`sum_i k_i < C`?

## 3. Experimental Strategy

The experiment stack has three layers:

1. symbolic and numerical sanity checks for the mathematical model;
2. deterministic simulator experiments on synthetic parameter grids;
3. realistic-parameter reruns calibrated from published Saguaro figures and
   appendix data.

Real online serving experiments are not a core dependency for this thesis.

## 4. Experiment Blocks

### Block A. Single-Client Shape Validation

Goal:

- validate the Block 1 claim that `tilde(mu)_SSD(k)` is unimodal;
- estimate `k*`;
- verify monotonicity trends of `k*`.

Model:

- use Saguaro's geometric fan-out and power-law cache-hit assumptions;
- use `B(k) = floor((T_V - a k) / (b k))_+`;
- start with constant timing simplifications:
  - `E_miss ~= 1`
  - hit latency normalized to `1`
  - miss latency `1 + T_b`

Outputs:

- `mu(k)` curves;
- `k*` heatmaps;
- a table of non-unimodal or degenerate cases.

Gate A:

- if most valid curves are unimodal, proceed;
- otherwise revise the service model before moving on.

### Block B. Two-Client KKT and Externality Validation

Goal:

- numerically verify the sign and scale of the externality term;
- separate own direct effect, own indirect effect, and cross-client effect.

Setup:

- two clients;
- shared verifier budget `k_1 + k_2 <= C`;
- objective `log mu_1 + log mu_2`.

Outputs:

- finite-difference sign checks for `partial mu_j / partial k_i`;
- representative sign maps over `(k_1, k_2)`;
- one figure illustrating binding versus non-binding regimes.

Gate B:

- if the cross term is positive and material in the intended regime, proceed;
- otherwise weaken the paper toward a single-client structural result.

### Block C. Allocation-Reversal Mapping

Goal:

- test the central claim that allocation ordering can reverse relative to
  GoodSpeed.

Setup:

- compare GoodSpeed allocation `k^GS` with SSD-aware optimum `k*`;
- scan two-client parameter grids over `(alpha_1, alpha_2)`, `(b_1, b_2)`, and
  later `r_i`.

Metrics:

- reversal indicator;
- utility gap `U(k*) - U(k^GS)`;
- reversal-region size under the scanned distribution.

Outputs:

- reversal heatmaps;
- utility-gap heatmaps;
- a canonical two-client reversal case.

Gate C:

- if reversal region is non-trivial, it becomes the signature result;
- if reversal exists but is tiny, it becomes supporting evidence rather than the
  headline claim.

### Block D. Non-Binding Verifier Regime

Goal:

- test whether the SSD-aware optimum can satisfy `sum_i k_i < C`.

Metrics:

- fraction of regimes with positive slack;
- average slack when slack is positive;
- utility difference between unconstrained-up-to-`C` and forced-binding
  optimization.

This is a stretch result, not a dependency for the paper's core story.

### Block E. N-Client Simulator

Goal:

- show that the structural effect persists beyond hand-picked two-client cases.

Setup:

- `N in {4, 8, 16}`;
- parameters sampled from synthetic distributions first;
- compare GoodSpeed-style monotone allocation, equal split, and SSD-aware
  heuristic or oracle allocations.

Role:

- supporting evidence only;
- the main structural story should remain in 2-client form.

### Block F. Realistic-Parameter Calibration from Published Saguaro Data

Goal:

- move from synthetic scans to realistic parameter ranges without making new
  real-LLM collection a prerequisite.

Data source:

- published Saguaro figures;
- appendix timing data;
- coarse extraction of empirical ranges for `alpha`, `r`, verifier wall-time
  scale, and drafter timing proxies.

Outputs:

- calibrated parameter table;
- synthetic-versus-calibrated comparison plots;
- final decision on whether the reversal story survives realistic settings.

Gate F:

- if reversal survives, keep the positive-result framing;
- otherwise pivot to a structural-limits or negative-result framing.

## 5. Concrete Deliverables

Minimum deliverables:

- a technical note for Block A and Block B formulas;
- one script for single-client unimodality scans;
- one script for two-client KKT and reversal scans;
- one script for calibrated reruns using paper-derived parameter ranges;
- one summary table of all gate decisions.

Nice-to-have deliverables:

- a lightweight `N`-client heuristic scheduler demo;
- a robustness appendix for `T_V(k) = T_0 + tau k`;
- a short note on conditions for non-binding verifier optima.

## 6. Execution Order

Week 1:

- finalize notation;
- implement Block A scans;
- run Gate A.

Week 2:

- implement Block B and Block C;
- produce first reversal maps;
- run Gate C.

Week 3:

- implement Block D and lightweight Block E;
- stabilize core figures and notes.

Week 4:

- calibrate from published Saguaro data;
- rerun core scans;
- decide between:
  - positive reversal framing;
  - negative-result structural framing.

## 7. Kill Criteria

### Risk 1. Unimodality is not robust

If `tilde(mu)_SSD(k)` is often bimodal or monotone in the intended parameter
range, revise the service model before pushing further.

### Risk 2. Externality is negligible

If the cross-client term is numerically tiny in realistic settings, reduce the
paper to a single-client or weak-coupling structural result.

### Risk 3. Reversal region is too small

If calibrated reversal regions are near-empty or the utility gap is negligible,
reframe the paper as a negative result on the structural limits of multi-client
SSD scheduling.
