# Chapter 5: Single-Client Validation

> Draft status: complete first draft. Sources: `paper/experiment_log.md` 2026-04-30 (Block 1 A3 synthetic + real-LLM) and 2026-05-05 (Block 3 Alpaca timing). Numbers below are transcribed from those log sections; figure callouts (Figure 5.x) are placeholders to be wired to `bench/results/geometric_block1_20260429_134517/` and `bench/results/block3_timing_alpaca_full_v2/figures/` at integration.
>
> **To reconcile before finalizing:** the calibration fit gives $b \approx 0.0077$ ms, but the simulator default (`sim/types.py`, used by E3b/G3) is `ssd_b = 0.0115335`. Confirm which value the multi-client chapters should quote, or document the conversion. This does not affect the qualitative results but the reported constant must be consistent.

This chapter provides the empirical backbone of the thesis. It shows that the non-monotone service curve predicted by Theorem 1 appears both on a broad synthetic parameter grid (§5.1) and in real LLM execution (§5.2–5.3), validates the underlying mechanism through the component metrics (§5.4), reports the timing calibration that fixes the absolute scale of $a$, $b$, and $T_V$ (§5.5), and honestly records a negative finding: the measured $k^\ast(B)$ is mildly non-monotone, which the simple $T_V$-proxy does not capture (§5.6).

## 5.1 Synthetic grid validation

We first checked single-peakedness on a synthetic grid spanning the model parameters $(\alpha, r, a, b, T_V)$, evaluating the closed-form service curve (3.9) at each grid point. Across the full grid, essentially all valid curves are single-peaked, consistent with Theorem 1; only a negligible fraction exhibit a monotonicity violation, attributable to boundary effects near the edge of the effective interval $\mathcal{I}$ where the integer fan-out constraint $F_0 \ge 1$ binds. This establishes that the conditional unimodality of Theorem 1 holds throughout the parameter region of interest, not just at isolated points. Figure 5.1 shows the $k^\ast$ heatmap over $(\alpha, T_V)$, and Table 5.1 records the count of valid, single-peaked, and degenerate cases.

## 5.2 Real-LLM experimental setup

The real-system validation uses a Qwen3-8B target paired with a Qwen3-0.6B drafter on a workstation with two RTX 4090 GPUs (CUDA architecture 8.9). Two datasets are used: Alpaca (open-ended instructions) and GSM8K (grade-school math). The drafter builds a Saguaro-style capped geometric fan-out tree; each run is parameterized by the acceptance prior, cache exponent prior, fan-out budget $B$, and lookahead $k$. An earlier run was contaminated by a dataset-fallback bug that substituted random tokens for real prompts; this was identified and fixed, and the corrected Alpaca run (`block3_timing_alpaca_full_v2`) logs zero fallbacks with verified real prompts. All results below are from the corrected runs.

## 5.3 Single-peakedness in real execution

The corrected Alpaca run preserves the single-peaked pattern across all five fan-out budgets. The best observed lookahead by budget (decode-throughput criterion) is
$$
B{=}16{:}\;k^\ast{=}4,\quad B{=}24{:}\;k^\ast{=}5,\quad B{=}36{:}\;k^\ast{=}5,\quad B{=}48{:}\;k^\ast{=}4,\quad B{=}64{:}\;k^\ast{=}4,
$$
and the GSM8K fine-grained sweep ($B{=}36$, $k \in \{2,\dots,12\}$) peaks at $k^\ast \approx 5$. In every case the throughput rises to an interior maximum and falls thereafter — there is no setting in which longer lookahead is uniformly better, which is the qualitative prediction of Theorem 1. Figure 5.2 (the candidate paper headline figure) overlays decode throughput versus $k$ for each budget $B$, showing the family of interior peaks.

## 5.4 Mechanism validation

The component metrics confirm that the peak arises from the predicted tension between hit benefit and miss cost rather than from an artefact. The cache-hit rate decreases monotonically with $k$ and increases with $B$: at $B{=}16$ it falls from $0.824$ at $k{=}2$ to $0.433$ at $k{=}12$, whereas at $B{=}64$ it falls only from $0.908$ to $0.736$. This is exactly the budget-squeeze mechanism of Chapter 3 — spreading a fixed fan-out budget over more levels lowers per-level fan-out and raises miss probability (Lemma 1). Simultaneously the expected accepted suffix increases with $k$ (the hit-side payoff), and verifier time rises only mildly. The product peaks internally, matching the FOC (4.4): the optimum sits where the marginal hit benefit equals the marginal miss cost. Figure 5.3 shows the four supporting panels (accepted suffix, cache hit, verify time, throughput) side by side.

## 5.5 Timing calibration

The timing model (3.3)–(3.4) was fit to the corrected Alpaca measurements. Care is needed in choosing the drafter timing target: the raw `draft_total_ms` mixes service, build, populate, and communication overhead and yields an unphysical negative $b$ in the linear fit. Using the cleaner `draft_detail_total_ms` target, the fit of $\mathrm{draft\_ms} = c + a\,k + b\,k\,B$ gives
$$
c = -0.0035~\text{ms}, \quad a = 2.6285~\text{ms/depth}, \quad b = 0.007689~\text{ms/(depth}\cdot\text{fan-out)}, \quad R^2 = 0.9966,\;\; \mathrm{RMSE}=0.541~\text{ms}.
$$
An alternative target (`draft_decode_tree_ms`) gives a consistent $a \approx 2.96$, $b \approx 0.0085$, $R^2 = 0.9970$, so we report $a \approx 2.6$–$3.0$ ms and $b \approx 0.0077$–$0.0085$ ms. The verifier time is nearly linear in $k$ and only weakly dependent on $B$,
$$
\mathrm{verify\_ms} \approx 19.613 + 0.0944\,k - 0.00239\,B \quad (R^2 = 0.8726),
$$
for which we use the proxy $T_V(k) \approx 19.6 + 0.094\,k$ ms. These constants set the absolute scale used in the multi-client simulations of Chapter 6. The lesson on the timing target — never fit $b$ against the aggregate `draft_total_ms` — is recorded here because it materially changes the sign of $b$ and hence the qualitative shape of the calibrated curve.

This calibration is from a single target/drafter pair on a single hardware setting. It fixes the absolute timing scale but not the multi-client heterogeneity distribution of $b$; the consequences of that limitation, and the synthetic $b$-heterogeneity used to probe it, are discussed in Chapter 7.

## 5.6 A2 corollary check and an honest negative finding

The monotonicity corollary (4.6) predicts $\partial k^\ast/\partial T_V > 0$, which through the proxy $B \mapsto T_V$ would make $k^\ast(B)$ non-decreasing. The measured sequence across budgets is
$$
k^\ast(B) = 4,\,5,\,5,\,4,\,4 \quad \text{for } B = 16,\,24,\,36,\,48,\,64,
$$
which is *not* monotone: it rises then falls. We report this as a negative finding rather than suppress it. The mechanism is that the corollary's leading-order term holds the cache shape fixed and varies only the timing scale, whereas at large $B$ the first-order cache-hit elasticity dominates: additional budget at high $B$ is absorbed by raising per-level hit rate rather than by supporting deeper lookahead, so the simple $T_V$-proxy ceases to track $k^\ast$. The honest statement is that the proxy $B \mapsto T_V$ is consistent with the framework only to first order; under finer measurement, cache-hit elasticity dominates and $k^\ast(B)$ shows mild non-monotonicity. This is revisited in the limitations (Chapter 7) and does not affect the single-peakedness-in-$k$ result, which is the property the scheduler relies on.
