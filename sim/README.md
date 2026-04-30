# Simulator Notes

## Purpose

The `sim/` directory is the thesis-side validation harness for the current
paper direction:

- `paper/proposal_cn.md`
- `paper/proposal_en.md`
- `paper/math_roadmap_v2.pdf`
- `paper/idea.md`
- `paper/plan.md`

This simulator is not a production SSD runtime and is not a benchmark wrapper
for new real-LLM experiments. Its purpose is to test the structural claims of
the current multi-client SSD scheduling model.

## Current Research Role

The active simulator story is:

- each client chooses verifier-side lookahead `k_i`;
- each client's drafter budget `B_i` is an implicit function of the global
  verifier load;
- service may become non-monotone in `k_i`;
- service is non-locally coupled across clients through verifier wall time.

The simulator should therefore support experiments for:

- single-client unimodality;
- two-client KKT and positive externality checks;
- allocation-reversal mapping;
- non-binding verifier regimes;
- small-`N` supporting experiments.

## Scope Boundary

This directory is no longer organized around:

- a unified speculative budget `S_i`;
- a two-level `S_i -> (k_i, f_i)` scheduler;
- real-LLM calibration as the first required step.

If later paper-derived parameter calibration is added, it should be treated as a
third-layer refinement after the synthetic structural experiments, not as the
main story.

## Existing Code

The current simulator codebase already contains useful building blocks and early
experiments, but some naming and semantics may still reflect the older framing.

Relevant files include:

- [`sim/ssd_math.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/sim/ssd_math.py)
- [`sim/policy.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/sim/policy.py)
- [`sim/client.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/sim/client.py)
- [`sim/scheduler.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/sim/scheduler.py)
- [`sim/experiments/block1_validate.py`](/Users/ruben/Documents/Git docs/specdiff/ssd/sim/experiments/block1_validate.py)

These should now be interpreted through the proposal-and-roadmap lens rather
than the older unified-budget story.

## Immediate Priorities

1. Keep Block 1 experiments clean and reproducible.
2. Add or refine 2-client experiments for KKT and reversal analysis.
3. Separate "current code semantics" from "paper target semantics" wherever the
   old framing still leaks through.
4. Prefer deterministic, inspectable scans over premature runtime integration.

## Success Criterion

The simulator is doing its job if it helps answer the following questions:

1. Is `tilde(mu)_SSD(k)` empirically unimodal over the intended parameter
   region?
2. Does the cross-client externality term appear with the predicted sign?
3. Are there realistic parameter regions where GoodSpeed and SSD-aware
   allocation order differ?
4. Does the non-binding verifier regime exist often enough to matter?

If it can answer these clearly, it is already serving the thesis well.
