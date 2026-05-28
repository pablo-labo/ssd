# Thesis body — draft status (2026-05-28)

This folder contains first-draft chapters of the thesis body, written in English
markdown with LaTeX math, ready for conversion. The drafts cover the four
chapters that are not blocked by further experiments. Chapters 1, 2, 7, 8, 9 and
the appendices remain to be written; see `paper/thesis_outline.md` for the full
structure.

## Files

| File | Chapter | Length | Status |
|---|---|---|---|
| `ch3_problem_formulation.md` | Ch 3: Problem Formulation | full | complete first draft |
| `ch4_theory.md`              | Ch 4: Theoretical Analysis | full | complete first draft |
| `ch5_single_client.md`       | Ch 5: Single-Client Validation | full | complete first draft |
| `ch6_multiclient_schedulers.md` | Ch 6: Multi-Client + Schedulers | full | complete first draft, includes G3/C4 (just produced) |
| `ch7_limitations.md`         | Ch 7: Limitations | full | complete first draft (synthesis of body caveats; no new claims) |

## What landed where

- **Ch 3** restates the SSD formulation from `proposal_en.md` §3 and
  `paper/math/block1a2.md` §1–4, defines the four modelling assumptions A1–A4
  with their empirical anchors, derives the single-client service curve, and
  contrasts the multi-client formulation against GoodSpeed. No new claims.
- **Ch 4** carries Lemma 1, Proposition 1 (FOC), Assumption 1, Theorem 1
  (conditional single-peakedness), Theorem 2 (large-T_V asymptotic), and the
  parameter-monotonicity corollary, all transcribed from `block1a2.md`. The
  2-client KKT externality is stated with its sign and ties to (4.9). Full
  proofs are sketched here and deferred to Appendix A.
- **Ch 5** is grounded in the actual experiment_log numbers (4/30 + 5/5), not
  outline-rounded figures. Reports the GSM8K k*≈5, Alpaca k*(B) = 4,5,5,4,4
  (the honest non-monotone finding), and the timing calibration with the
  documented R² values. Figures are placeholders to be wired at integration.
- **Ch 6** is the contribution chapter. Lands C3 (E3b capacity-pressure sweep),
  C4 (G3 exact-optimality check, just produced today), and C5 (block3
  three-mode disagreement decomposition). Uses the *current* scheduler set
  from `sim/scheduler.py` (CappedSSD = main "F"; GoodSpeed = baseline; uncapped
  SSD-greedy = ablation); see the sync note in `progress_handoff.md` about
  the older GoodSpeed++ / Coupling-Greedy names being subsumed.

## Items the author should verify before publication

1. **`ssd_b` reconciliation.** The Alpaca timing fit (`experiment_log.md`
   5/5) reports `b ≈ 0.0077–0.0085 ms`, but `sim/types.py` defaults
   `ssd_b = 0.0115335` (used by E3b and G3). Ch 5 quotes the fitted number,
   Ch 6 uses the simulator's number implicitly via the calibration anchor.
   Pick one and document the conversion, or note the discrepancy explicitly.
   It does *not* change the qualitative results: greedy=optimum and the
   capacity-pressure dominance hold either way.
2. **Block 3 decomposition numbers in §6.3** (22.8% / 18.0% / 10.8% at C=12;
   C=8→20 trajectory; b-ratio 20 → ~30%; strict-reversal utility-gap mean
   37.4%, max 48.5%) are transcribed from the outline and the experiment_log
   2026-05-07 entry. Re-verify against the actual figures in
   `block3_native_order_figures/` and `block3_reversal_alpaca_calibrated/`
   before finalizing.
3. **GoodSpeed paper claim.** §6.4 closes with "F is GoodSpeed plus two
   lines." This was flagged in `progress_handoff.md` §7 as a model-level
   claim that has not been verified against the GoodSpeed paper's actual
   algorithm. Read the GoodSpeed paper (`paper/2512.09963v2.pdf`) and either
   sharpen the wording or replace it with an algorithmic comparison that the
   paper supports.
4. **Figure callouts** (Figure 5.1–5.3, 6.1–6.5) are placeholders. At
   integration, wire each to the actual file path:
   - 5.1: synthetic k* heatmap from `bench/results/geometric_block1_…`
   - 5.2: Alpaca decode-throughput vs k by B (the candidate headline figure)
   - 5.3: four-panel mechanism figure (suffix / cache / verify / throughput)
   - 6.1: `block3_native_order_figures/native_order_mechanisms_by_capacity.png`
   - 6.2: utility-gap CDF by mode (needs Ch 6.3.4 P0 experiment output if not
     already in figures dir)
   - 6.3: `sim/experiments/results/e3b_capacity_pressure/e3b_throughput_vs_rho.png`
   - 6.4: `…/e3b_overcommit_vs_rho.png`
   - 6.5: `sim/experiments/results/g3_exact_oracle/g3_greedy_vs_optimum.png`

## What is intentionally not drafted yet

- **Ch 1 (Introduction)** and **Ch 2 (Related Work)** are intentionally
  written last per `thesis_outline.md` §4 schedule (Week 4): they distill the
  body, so drafting them now would over-commit to wording that has to change.
- **Ch 8 (Future Work)** is a roadmap chapter; can draft from
  `paper/direction.md` and `paper/long_term_roadmap.md`.
- **Ch 9 (Conclusion)** is the very last item; trivial after Ch 1–8 are set.
- **Appendices A and B** transcribe `block1a2.md` and the simulator
  reproduction commands; these are mechanical and short.

## Honesty checklist preserved across drafts

The drafts make every explicit honesty point from `thesis_outline.md` §0.4:

- Theorem 1 is stated as conditional on Assumption 1, not unconditional.
- The k*(B) = 4,5,5,4,4 non-monotone finding is written into Ch 5.6 as a
  negative result, not buried.
- The block3 reframing (strict reversal 10.8% vs the original 20% gate) is
  written as the decomposition itself being the result, not as a passing grade.
- The G3 result is explicitly framed as conditional on (i) sum-throughput
  objective and (ii) discrete concavity, with a non-concave counterexample
  delimiting the condition.
- Single-drafter calibration and simulator-vs-real-system limits are
  flagged at end of Ch 5 and Ch 6 for explicit treatment in Ch 7.
