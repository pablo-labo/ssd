# Chapter 3: Problem Formulation

> Draft status: complete first draft. Source assets: `paper/proposal_en.md` §3, `paper/math/block1a2.md` §1–4, `sim/types.py`. Notation follows `thesis_outline.md` §0.2. Equation numbers are local to this chapter and will be re-keyed at integration.

This chapter formalizes the object of study. We first describe the single-client speculative-decoding model on which the rest of the thesis builds (§3.1), state the four modelling assumptions and their empirical justification (§3.2), and derive the single-client service curve as a function of the verifier lookahead $k$ (§3.3). We then lift the model to the multi-client setting, where a shared verifier budget couples the clients (§3.4), and close by placing the formulation side-by-side with the GoodSpeed multi-client model to make the structural difference precise (§3.5). No theoretical result is proved here; lemmas and theorems are deferred to Chapter 4.

## 3.1 System model

We consider speculative speculative decoding (SSD) in the sense of the Saguaro engine: a *drafter* model proposes a tree of candidate continuations while a larger *verifier* model checks them in parallel. The two models share the same accelerator, so the drafter runs inside the wall-clock window during which the verifier is occupied. A single decoding step is organized around the verifier's lookahead $k$, the length of the speculative chain the verifier is asked to validate in one round.

For a fixed client, the relevant quantities per step are: the verifier wall time $T_V$ spent on one validation round; the drafter fan-out budget $B$, the number of candidate continuations the drafter can prepare within that window; and the token acceptance rate $\alpha \in (0,1)$, the probability that a single drafted token is accepted by the verifier. Following Saguaro, the drafter allocates its budget across the $k$ levels of the speculation tree as a *capped geometric* fan-out shape (Assumption A2 below), and the cache-hit probability at a level with fan-out $F$ follows a power law (Assumption A1).

The decision variable is $k$. The fan-out budget $B$ is *not* an independent control: it is induced by $k$ through the shared timing, because every unit of verifier lookahead consumes drafter wall time that would otherwise have widened the tree. This induced dependence $B = \phi(k)$ is the structural feature that distinguishes our model from prior multi-client speculative-decoding scheduling and is made explicit next.

## 3.2 Modelling assumptions

We adopt four working assumptions. Each is a deliberate simplification made to keep the model analytically tractable; Chapter 5 reports the calibration evidence that supports them on real LLM executions, and Chapter 7 records their limitations.

**A1 (Power-law cache hit).** At a tree level with fan-out $F \ge 1$, the cache-miss probability is
$$
1 - p_{\mathrm{hit}}(F) = F^{-r}, \qquad r > 0. \tag{3.1}
$$
This is the Saguaro cache model; the exponent $r$ summarizes how quickly additional fan-out buys down miss probability. The model is only meaningful for $F \ge 1$, which constrains the effective domain of $k$ (§3.3).

**A2 (Capped geometric fan-out).** Under A1 and a fixed budget, Saguaro's optimal fan-out shape is a capped geometric series. With $\beta := \alpha^{1/(1+r)}$, the per-level fan-outs are
$$
F_j = F_0 \,\beta^{\,j} \;\; (j < k), \qquad F_k = F_0\, \beta^{\,k}\,(1-\alpha)^{-1/(1+r)}. \tag{3.2}
$$

**A3 (Drafter timing).** The drafter wall time to prepare a depth-$k$, budget-$B$ tree is affine in both depth and total work,
$$
\mathrm{draft\_ms} = a\,k + b\,k\,B, \qquad a, b > 0, \tag{3.3}
$$
with $a$ a per-depth cost and $b$ a per-(depth$\times$fan-out) cost.

**A4 (Verifier timing).** The verifier wall time is approximately affine in lookahead,
$$
T_V(k) = T_0 + \tau\,k. \tag{3.4}
$$
In much of the single-client analysis we treat $T_V$ as a fixed scale; §3.4 reinstates the $k$-dependence because it is the source of the multi-client coupling.

Equating the drafter's available window $T_V$ with its spend (3.3) gives the induced fan-out budget
$$
B(k) = \left\lfloor \frac{T_V - a\,k}{b\,k} \right\rfloor_{+}, \tag{3.5}
$$
which is positive only on $0 < k < T_V/a$. This, together with the $F_0(k) \ge 1$ requirement from A1, defines the **effective interval** $\mathcal{I}$ on which the model is well posed (developed in §3.3).

## 3.3 Single-client formulation

Fix one client. The decision variable is the lookahead $k$; the induced budget is $B(k)$ from (3.5). Substituting the capped-geometric shape (3.2) into the power-law miss model (3.1) and summing over tree levels yields a closed form for the aggregate cache-miss probability. Defining
$$
N(k) = (1-\alpha)^{-1/(1+r)}\beta^{k} + \frac{1-\beta^{k}}{1-\beta}, \qquad
D(k) = (1-\alpha)^{r/(1+r)}\beta^{k} + (1-\alpha)\frac{1-\beta^{k}}{1-\beta}, \tag{3.6}
$$
and $G(k) = N(k)^{r} D(k)$, the miss probability separates into a Saguaro cache-shape factor and a drafter-timing penalty:
$$
q(k) \;=\; G(k)\left(\frac{b\,k}{T_V - a\,k}\right)^{\!r}. \tag{3.7}
$$
The full derivation of (3.6)–(3.7) is reproduced in Appendix A; here we treat (3.7) as the definition of $q(k)$.

The effective interval is
$$
\mathcal{I} = \Big\{\, k \in (0,\,T_V/a) \;:\; F_0(k) \ge 1 \,\Big\}, \qquad F_0(k) = \frac{B(k)}{N(k)}, \tag{3.8}
$$
i.e. the set of lookaheads for which the budget is positive *and* the base fan-out is at least one, so that (3.1) returns a valid probability.

With expected accepted-suffix length $E(k) = (1-\alpha^{k+1})/(1-\alpha)$ and the first-order latency normalization ($l_{\mathrm{hit}}=1$, miss latency $1+T_b$), the SSD service curve is
$$
\tilde\mu^{\mathrm{SSD}}(k) \;=\; E(k) - q(k)\,\big(E(k) - 1\big), \tag{3.9}
$$
which reads as *ideal hit benefit minus miss-probability-weighted loss*. The central single-client question is whether (3.9) is monotone in $k$ or has an interior maximizer $k^\ast$; this is answered in Chapter 4.

## 3.4 Multi-client formulation

Now consider $N$ clients sharing one verifier. Client $i$ has parameters $(\alpha_i, r_i, a_i, b_i)$ and chooses lookahead $k_i$. The verifier serves the clients within a shared wall-clock budget, modelled as the capacity constraint
$$
\sum_{i=1}^{N} k_i \;\le\; C. \tag{3.10}
$$
Because the verifier wall time depends on the *total* lookahead it must validate, the per-client window — and therefore each client's induced fan-out budget — is a function of the entire allocation $\{k_j\}$:
$$
B_i(\{k_j\}) = \left\lfloor \frac{T_V\!\left(\textstyle\sum_j k_j\right) - a_i k_i}{b_i\, k_i} \right\rfloor_{+}. \tag{3.11}
$$
This is the crux of the thesis: $B_i$ is a *derived* quantity, not a free control, and it couples client $i$ to every other client through the shared $T_V(\sum_j k_j)$. We write $B_i = \phi_i(\{k_j\})$ and carry $\phi_i$ as a first-class object through the remaining chapters.

The scheduler chooses $\{k_i\}$ to maximize aggregate utility. We study two objectives: sum-throughput $\sum_i \mu_i^{\mathrm{SSD}}(k_i, B_i)$ (primary), and proportional fairness $\sum_i \log \mu_i^{\mathrm{SSD}}(k_i, B_i)$ (secondary). Both reduce to allocating a shared integer budget across clients whose per-client service is the single-peaked curve (3.9), evaluated at the induced budget (3.11).

## 3.5 Relation to the GoodSpeed formulation

GoodSpeed, the closest multi-client speculative-decoding scheduler, optimizes
$$
\max_{\{k_i\}} \;\sum_i \log \mu_i^{\mathrm{GS}}(k_i), \qquad
\mu_i^{\mathrm{GS}}(k_i) = \frac{1 - \alpha_i^{\,k_i+1}}{1 - \alpha_i}, \tag{3.12}
$$
subject to the same capacity constraint (3.10). The two formulations differ in exactly two places. First, GoodSpeed's per-client service $\mu^{\mathrm{GS}}$ is the bare expected accepted suffix $E(k)$: it is *monotone-saturating* in $k$, so more lookahead is never harmful. Our $\mu^{\mathrm{SSD}}$ (3.9) subtracts the miss-cost term $q(k)(E(k)-1)$, which grows with $k$ through the induced budget squeeze and eventually dominates — making the curve non-monotone. Second, GoodSpeed has no analogue of the coupling $\phi_i$: its per-client service depends only on $k_i$, whereas ours depends on $\{k_j\}$ through (3.11).

Setting the miss term to zero and decoupling the budget ($\partial B_i/\partial k_j = 0$) recovers (3.12) exactly. GoodSpeed is therefore the *decoupled, monotone limit* of our model. The remainder of the thesis quantifies what is lost in that limit: a scheduler that assumes monotone service (3.12) pushes each client's lookahead as high as the budget allows, overshooting the interior optimum $k_i^\ast$ of the true curve (3.9) and degrading realized throughput. Chapter 4 establishes the structural facts behind this claim; Chapter 6 measures its consequences.
