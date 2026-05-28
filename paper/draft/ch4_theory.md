# Chapter 4: Theoretical Analysis

> Draft status: complete first draft. Source: `paper/math/block1a2.md` (full derivations), `paper/proposal_en.md` §3.2 (KKT). Full proofs of Lemma 1, Proposition 1, and Theorems 1–2 are reproduced in Appendix A; this chapter states the results and gives proof sketches. Equation numbers are local to this chapter.

This chapter establishes the structural facts that motivate the rest of the thesis. Section 4.1 proves that the single-client SSD service curve is single-peaked under an explicit regularity condition, derives the first-order optimality condition, and gives the large-$T_V$ growth rate of the optimal lookahead together with its parameter monotonicities. Section 4.2 lifts the analysis to two clients and exposes the cross-client externality term that the GoodSpeed formulation implicitly sets to zero. Section 4.3 discusses global optimality of the integer allocation problem, and §4.4 maps each result to the experiments that test it.

Throughout, $q(k)$ is the cache-miss probability (3.7), $E(k) = (1-\alpha^{k+1})/(1-\alpha)$ the expected accepted-suffix length, $p_{\mathrm{hit}}(k) = 1 - q(k)$, and $u(k) := \tilde\mu^{\mathrm{SSD}}(k) = E(k) - q(k)(E(k)-1)$ the service curve (3.9) on the effective interval $\mathcal{I}$ (3.8).

## 4.1 Single-client analysis

### 4.1.1 Monotonicity of the miss probability

**Lemma 1 (Miss probability is increasing).** *On the effective interval $\mathcal{I}$, $q'(k) > 0$.*

*Proof sketch.* Write $q(k) = G(k)\,h(k)^r$ with $G(k) = N(k)^r D(k)$ and $h(k) = bk/(T_V - ak)$, using $N, D$ from (3.6). The timing factor satisfies $h'(k) = bT_V/(T_V-ak)^2 > 0$. For the shape factor, differentiating $N$ and $D$ and extracting the common factor $\beta^k \log\beta < 0$ reduces both $N'(k)>0$ and $D'(k)>0$ to the single inequality
$$
(1-\alpha)^{1/(1+r)} > 1 - \beta, \qquad \beta = \alpha^{1/(1+r)}. \tag{4.1}
$$
Setting $y = \beta$ so that $\alpha = y^{1+r}$, (4.1) is equivalent to $1 - y^{1+r} > (1-y)^{1+r}$ for $y \in (0,1)$. The function $f(y) = 1 - y^{1+r} - (1-y)^{1+r}$ vanishes at both endpoints and has derivative $f'(y) = (1+r)\big[(1-y)^r - y^r\big]$, which is positive on $(0,\tfrac12)$ and negative on $(\tfrac12,1)$; hence $f$ is strictly positive on $(0,1)$ and (4.1) holds. Therefore $N'(k), D'(k) > 0$, so $G'(k) = rN^{r-1}N'D + N^r D' > 0$, and $q' = G'h^r + Gr h^{r-1}h' > 0$. $\qquad\blacksquare$

Lemma 1 says that lengthening the speculative chain *always* raises the miss probability: the budget squeeze (fewer fan-out per level) outweighs any per-level benefit. Crucially the proof is unconditional — it needs no assumption beyond the model of Chapter 3.

### 4.1.2 First-order condition

Differentiating $u(k) = E(k) - q(k)(E(k)-1)$ and using $E'(k) = \alpha^{k+1}\log(1/\alpha)/(1-\alpha)$ and $E(k)-1 = \alpha(1-\alpha^k)/(1-\alpha)$ gives, after cancelling the common factor $\alpha/(1-\alpha) > 0$,
$$
u'(k) = \frac{\alpha}{1-\alpha}\big[\,\mathrm{MHB}(k) - \mathrm{MMC}(k)\,\big], \tag{4.2}
$$
where the *marginal hit benefit* and *marginal miss cost* are
$$
\mathrm{MHB}(k) = \alpha^{k}\log(1/\alpha)\,p_{\mathrm{hit}}(k), \qquad
\mathrm{MMC}(k) = q'(k)\,(1-\alpha^{k}). \tag{4.3}
$$

**Proposition 1 (FOC).** *Any interior maximizer $k^\ast$ of $u$ on $\mathcal{I}$ satisfies $\mathrm{MHB}(k^\ast) = \mathrm{MMC}(k^\ast)$, i.e.*
$$
\alpha^{k^\ast}\log(1/\alpha)\,p_{\mathrm{hit}}(k^\ast) \;=\; q'(k^\ast)\,(1 - \alpha^{k^\ast}). \tag{4.4}
$$

The reading is economic: the optimum sits where the marginal benefit of one more lookahead level — extra accepted tokens, realized only on a hit — equals its marginal cost — the increase in miss probability scaled by the loss a miss incurs.

### 4.1.3 Single-peakedness

Single-peakedness needs $\mathrm{MHB}$ decreasing and $\mathrm{MMC}$ increasing. The first is unconditional; the second requires control of $q''$.

**Assumption 1 (Convex miss probability).** *On $\mathcal{I}$, $q''(k) \ge 0$.*

This is a genuine assumption, not a theorem: $q(k) = G(k)(bk/(T_V-ak))^r$ contains the $\beta^k$ terms in $G$, whose second-order behaviour is not sign-definite in closed form for finite $T_V$. We therefore carry $q'' \ge 0$ as a finite-$T_V$ regularity condition and validate it numerically (Chapter 5); the large-$T_V$ result below does *not* rely on it.

**Theorem 1 (Conditional single-peakedness).** *Under Assumption 1, $\tilde\mu^{\mathrm{SSD}}(k)$ is single-peaked on $\mathcal{I}$, with a unique interior maximizer $k^\ast$ satisfying (4.4).*

*Proof sketch.* $\mathrm{MHB}(k) = \alpha^k\log(1/\alpha)p_{\mathrm{hit}}(k)$ is a product of the strictly decreasing $\alpha^k$ and the strictly decreasing $p_{\mathrm{hit}} = 1-q$ (Lemma 1), so $\mathrm{MHB}'(k) < 0$. For $\mathrm{MMC}(k) = q'(k)(1-\alpha^k)$,
$$
\mathrm{MMC}'(k) = q''(k)(1-\alpha^k) + q'(k)\,\alpha^k\log(1/\alpha) > 0
$$
under Assumption 1 and Lemma 1. A strictly decreasing curve and a strictly increasing curve cross at most once; boundary behaviour gives $\mathrm{MHB} > \mathrm{MMC}$ as $k \to 0^+$ (since $1-\alpha^k \to 0$ kills $\mathrm{MMC}$ while $\mathrm{MHB} \to \log(1/\alpha)p_{\mathrm{hit}}(0^+) > 0$) and $\mathrm{MHB} < \mathrm{MMC}$ near the right boundary of $\mathcal{I}$, where the budget tightens. Hence a unique crossing $k^\ast$ exists, and by (4.2) $u' > 0$ for $k < k^\ast$ and $u' < 0$ for $k > k^\ast$. $\qquad\blacksquare$

Theorem 1 is the formal counterpart of the "diminishing returns then collapse" picture: the calibrated curve rises to an interior optimum $k^\ast$ and falls thereafter. Its conditionality on $q'' \ge 0$ is stated explicitly and revisited in the limitations (Chapter 7).

### 4.1.4 Large-$T_V$ asymptotic and monotonicities

**Theorem 2 (Large-$T_V$ asymptotic).** *As $T_V \to \infty$ in the unsaturated regime,*
$$
k^\ast \;=\; \frac{r}{\log(1/\alpha)}\,\log T_V \;+\; O(\log\log T_V). \tag{4.5}
$$
*This result does not require Assumption 1.*

*Proof sketch.* For $T_V$ large, $k^\ast = O(\log T_V) \ll T_V/a$, so $T_V - ak^\ast \sim T_V$ and $\beta^{k^\ast} \to 0$, whence $G(k^\ast) \to G_\infty = (1-\alpha)/(1-\beta)^{r+1}$. The miss probability behaves as $q(k) \sim G_\infty (bk/T_V)^r$ with $q'(k) \sim G_\infty r b^r k^{r-1}/T_V^r$, and at the optimum $p_{\mathrm{hit}} \to 1$, $1-\alpha^{k^\ast}\to 1$. The FOC (4.4) then reduces to the balance $\alpha^{k^\ast}\log(1/\alpha) \sim G_\infty r b^r (k^\ast)^{r-1}/T_V^r$. Taking logarithms, the dominant terms are $k^\ast\log(1/\alpha) = r\log T_V + O(\log k^\ast)$, and since $\log k^\ast = O(\log\log T_V)$, (4.5) follows. Self-consistency holds: $k^\ast/T_V = O(\log T_V / T_V) \to 0$. $\qquad\blacksquare$

**Corollary (Parameter monotonicities).** *To leading order $k^\ast \approx r\log T_V / \log(1/\alpha)$, and*
$$
\frac{\partial k^\ast}{\partial \alpha} > 0, \qquad
\frac{\partial k^\ast}{\partial T_V} > 0, \qquad
\frac{\partial k^\ast}{\partial r} > 0, \qquad
\frac{\partial k^\ast}{\partial b} < 0. \tag{4.6}
$$
The first three follow from the leading order; the dependence on $b$ enters only at the second-order correction $-\,r\log b/\log(1/\alpha)$, giving $\partial k^\ast/\partial b \approx -r/(b\log(1/\alpha)) < 0$.

The interpretations are intuitive. Higher acceptance $\alpha$ makes long chains reliable, so the optimum lengthens; more verifier time $T_V$ buys more drafter preparation, so $k^\ast$ rises; a larger cache exponent $r$ means fan-out buys down misses faster, again favouring depth; and a slower drafter (larger $b$) raises the cost of each extra level, lowering $k^\ast$. Two consequences matter for the scheduler. First, (4.6) shows $k^\ast$ is driven primarily by $\alpha$ and only logarithmically by the timing scale $T_V$ — the empirical basis (Chapter 5) for treating cross-client coupling through $T_V$ as a second-order ($\sim 5\%$) effect. Second, with $T_b > 0$ the backup latency only multiplies the right-hand side of the FOC by a constant in the large-$T_V$ limit ($E(k^\ast) \to 1/(1-\alpha)$), so (4.5) is unchanged at leading order: backup latency shifts the subleading constant, not the growth rate.

## 4.2 Multi-client KKT analysis

We now treat two clients sharing the verifier, objective $\sum_{i} \log \mu_i$ with $\mu_i = \mu_i^{\mathrm{SSD}}(k_i, B_i)$ and $B_i = \phi_i(k_1, k_2)$ from (3.11), under $k_1 + k_2 \le C$. Relaxing $k_i$ to the reals for the first-order analysis, the Lagrangian is
$$
\mathcal{L} = \log\mu_1 + \log\mu_2 - \lambda\Big(k_1 + k_2 - C\Big), \tag{4.7}
$$
with stationarity, for $i = 1, 2$,
$$
\frac{\partial \log\mu_i}{\partial k_i} + \frac{\partial \log\mu_j}{\partial k_i} = \lambda, \qquad j \ne i. \tag{4.8}
$$
The first term is client $i$'s own marginal log-utility. The second is the **cross-client externality**, absent from any decoupled formulation. Because $\mu_j$ depends on $k_i$ only through the shared budget,
$$
\frac{\partial \mu_j}{\partial k_i} = \frac{\partial \mu_j}{\partial B_j}\cdot\frac{\partial B_j}{\partial k_i}, \qquad
\frac{\partial B_j}{\partial k_i} = -\,\frac{T_V'\!\left(k_1+k_2\right)}{b_j\,k_j} < 0. \tag{4.9}
$$
The sign of the externality is therefore $-\,\mathrm{sign}(\partial\mu_j/\partial B_j)$. On the increasing branch of the service curve $\partial\mu_j/\partial B_j > 0$ (more fan-out lowers misses, raising service), so $\partial\mu_j/\partial k_i < 0$: client $i$ lengthening its lookahead lengthens the shared verifier window, which *shrinks* client $j$'s induced fan-out budget and lowers its service. From the utility-maximization viewpoint this is a positive externality term that a correct scheduler should internalize.

**Relation to GoodSpeed.** GoodSpeed's stationarity is (4.8) with the cross term deleted: $\partial\log\mu_i^{\mathrm{GS}}/\partial k_i = \lambda$. Two errors follow. First, $\mu^{\mathrm{GS}}$ omits the miss-cost term, so its own marginal never turns negative and the solution pushes each $k_i$ to the capacity boundary rather than to the interior $k_i^\ast$. Second, deleting the cross term ignores the budget that one client's depth steals from another. Both vanish in the decoupled, monotone limit ($T_V' = 0$ and miss term $\to 0$), confirming GoodSpeed as the correct policy in that limit and as a structurally biased one outside it. The magnitude and consequences of these two effects are measured in Chapter 6 (the overcommit experiment E3b and the allocation-disagreement decomposition).

## 4.3 On global optimality of the allocation

The deployed problem is integer: $k_i \in \mathbb{Z}_{\ge 0}$ with $\sum_i k_i \le C$. Even though each per-client curve is single-peaked (Theorem 1), the multi-client objective is not jointly concave in general, because the coupling $\phi_i$ makes $\mu_i$ a function of the whole allocation. Two observations bound what can be claimed. First, when the coupling is treated as a fixed scale (the $\sim 5\%$ second-order effect of §4.1.4), the objective separates into a sum of per-client terms over a single shared budget — the classical *separable resource-allocation* problem. For that problem the incremental marginal-allocation algorithm is exactly optimal *provided each per-client term is discrete-concave* (non-increasing marginal gains). Second, discrete concavity of $\mu_i^{\mathrm{SSD}}$ on its feasible block is not automatic from single-peakedness: a unimodal curve can still have an increasing-marginal segment. Whether the calibrated curve is discrete-concave — and hence whether the greedy scheduler of Chapter 6 is exactly optimal — is therefore an empirical question, settled in §6.x (experiment G3). We make no claim of global optimality for the fully coupled problem; the fixed-point treatment of the coupling and its convergence are left to future work (Chapter 8).

## 4.4 Empirical implications

The theory makes four testable predictions, each routed to an experiment. Lemma 1 and Theorem 1 predict a single interior peak in $\mu^{\mathrm{SSD}}(k)$ — tested on synthetic grids and real LLM runs (Chapter 5, claim C1). The Corollary predicts $k^\ast$ rises steeply with $\alpha$ and only weakly with $T_V$ — tested by the $\alpha \times T_V$ sweep (Chapter 5, claim C2), and underwriting the $\sim 5\%$ coupling approximation. The KKT externality (4.9) predicts a negative cross term of material size in the heterogeneous regime — examined numerically in Chapter 6. Finally, §4.3 predicts that the greedy scheduler is exactly optimal precisely when the calibrated curve is discrete-concave — confirmed by the DP/MILP oracle comparison (Chapter 6, claim C4), which also exhibits a synthetic non-concave curve on which greedy provably fails, delimiting the condition.
