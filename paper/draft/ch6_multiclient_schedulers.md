# Chapter 6: Multi-Client Allocation and the Capped Greedy Scheduler

> Draft status: complete first draft. E3b numbers (§6.4) are read directly from `sim/experiments/results/e3b_capacity_pressure/e3b_capacity_pressure.csv`; G3 numbers (§6.5) from `results/g3_exact_oracle/g3_exact_oracle.csv`. Block 3 decomposition numbers (§6.3) are transcribed from `experiment_log.md` 2026-05-05 and 2026-05-07 and from `thesis_outline.md` §6.4 and should be re-verified against the figures at integration. The scheduler set in this chapter (CappedSSD as main method, GoodSpeed as baseline, uncapped SSD-greedy as ablation) reflects the current code in `sim/scheduler.py` (May 2026); the older GoodSpeed++ / Coupling-Greedy names in earlier drafts were folded into this design — see `progress_handoff.md` sync note (2026-05-28).

This chapter is the main contribution of the thesis. We work in the multi-client setting of §3.4, where $N$ clients share the verifier under the capacity constraint $\sum_i k_i \le C$, each client's service is the calibrated single-peaked curve $\mu_i^{\mathrm{SSD}}$ of (3.9), and the budget coupling $\phi_i(\{k_j\})$ of (3.11) introduces the cross-client externality of §4.2. The chapter is organized around five claims.

In §6.1 we restate the setting. In §6.2 we revisit the KKT analysis of §4.2 numerically. In §6.3 we report the *scheduler-native disagreement decomposition*: GoodSpeed and an SSD-aware oracle place identically-parameterized clients into materially different allocations roughly half the time, and the disagreement breaks cleanly into three structurally distinct failure modes. In §6.4 we introduce the proposed scheduler — a capped marginal-greedy on the SSD-aware service curve — and quantify its advantage over GoodSpeed and over an uncapped variant of the same greedy across the slack-to-binding capacity range (claim C3). In §6.5 we close the proof of optimality: across the calibrated grid, the capped greedy is exactly the integer-programming optimum, confirmed by two independent solvers (a DP and a HiGHS MILP), with a synthetic non-concave counterexample showing the result is genuinely conditional on the curve's discrete concavity (claim C4). Section 6.6 discusses design implications.

## 6.1 Setting

We carry forward the formulation of §3.4. Each client $i$ has parameters $(\alpha_i, r_i, a_i, b_i)$; throughout §6.3–6.5 we use the Alpaca / Qwen3-8B+0.6B calibration of Chapter 5 as the anchor, with $r=0.6$, $a \approx 2.63$ ms, $b$ in the documented range, $T_V$ from the linear fit, and heterogeneity introduced by varying $\alpha_i$ symmetrically around the centre $\alpha_0 = 0.735$. The decision variable is the integer allocation $\{k_i\}$, the constraint is $\sum_i k_i \le C$, and the primary objective is the realized sum-throughput on the true SSD service, $\sum_i \mu_i^{\mathrm{SSD}}(k_i)$. Proportional fairness $\sum_i \log \mu_i^{\mathrm{SSD}}(k_i)$ is reported as a secondary metric where relevant. The service curve $\mu_i^{\mathrm{SSD}}$ is a throughput rate, so the experiments below are *static, single-shot* allocations with non-binding backlog — consistent with the rate interpretation and with the convention adopted across the simulator.

## 6.2 KKT externality, numerically

From (4.7)–(4.9), the multi-client stationarity condition carries a cross-client externality term that GoodSpeed implicitly sets to zero. Evaluating $\partial B_j/\partial k_i = -T_V'(k_1+k_2)/(b_j k_j)$ at the calibrated $(T_V', b)$ gives a strictly negative sign on the increasing branch of the service curve: client $i$ widening its lookahead steals verifier wall time, which contracts client $j$'s induced fan-out budget and lowers client $j$'s service. The magnitude is small in absolute terms — the timing slope $T_V' \approx 0.094$ ms/$k$ is two orders of magnitude smaller than $T_V \approx 19.6$ ms, which is why the kstar-sensitivity audit places coupling at roughly five percent (Chapter 5; Figure 5.x). The qualitative role of the externality, however, is structural: it determines which client should yield budget when the constraint binds, and a scheduler that ignores it can place its allocation on the wrong side of the boundary. The magnitude of the resulting *allocation-level* gap is the subject of §6.3 and §6.4.

## 6.3 GoodSpeed–SSD allocation disagreement and its decomposition

We compare GoodSpeed's preferred two-client allocation $k^{\mathrm{GS}}$ against the SSD-aware optimum $k^\ast$ across the Alpaca-calibrated grid, sweeping the heterogeneity drivers $(\alpha_1, \alpha_2)$ and $(b_1, b_2)$ over realistic ranges and the capacity over $C \in \{8, 10, 12, 14, 16, 20\}$. The aggregate disagreement rate — fraction of grid points where the two allocations differ — sits near $51.6\%$ on the calibrated grid. This number is reported in context: it counts a *tie* in either allocation against a *strict order* in the other as a mismatch, so the interpretation depends on the tie convention. Reading the aggregate alone would overstate the structural story.

A more informative view decomposes the disagreement into three distinct failure modes of the monotone-service heuristic. Let "$\sim$" denote the indifference relation in the respective allocation order.

- **Drafter-cost blindness.** GoodSpeed treats two clients with identical $\alpha$ as interchangeable regardless of $b$, returning $k_1 \sim k_2$. The SSD-aware optimum, which sees the timing cost, breaks the tie in favour of the cheaper drafter: $k_1 \ne k_2$. Such "GoodSpeed tie, SSD non-tie" cases account for $22.8\%$ of the grid at $C = 12$.
- **Near-peak overcommit.** GoodSpeed orders the clients strictly, but the SSD-aware optimum places both at their respective interior peaks and reports indifference at the margin, returning a tie. The structural reading is that GoodSpeed has pushed past one client's peak and the SSD-aware optimum refuses to do so. These "GoodSpeed strict, SSD tie" cases are $18.0\%$ at $C = 12$.
- **Strict reversal.** GoodSpeed and the SSD-aware optimum both return strict orders, and the orders are *opposite*. This is the strongest form of disagreement and the cleanest test of the externality. Strict reversal is $10.8\%$ at $C = 12$, rising with capacity (from $6.8\%$ at $C = 8$ to $15.7\%$ at $C = 20$) and with $b$-heterogeneity (reaching roughly $30\%$ at $b_{\max}/b_{\min} \ge 20$).

The utility consequence of each mode differs sharply. Blindness and near-peak overcommit produce small utility gaps on most instances — a boundary flip near the optimum that the realised throughput barely registers — whereas strict-reversal instances carry a mean utility gap of about $37.4\%$ and a maximum near $48.5\%$. The takeaway is that the headline $51.6\%$ disagreement is genuine but mostly composed of boundary flips with limited utility impact; the structurally damaging share is the strict-reversal subset, which is smaller but grows with capacity and with the very $b$-heterogeneity that a real multi-client deployment would exhibit. Figure 6.1 shows the capacity sweep of the three mode shares, and Figure 6.2 the utility-gap CDF separated by mode.

**Reframing note.** An earlier project gate defined "passing" as strict-reversal share $\ge 20\%$ at $C = 12$; on the calibrated grid this threshold is not met ($10.8\%$). Rather than rebadge a borderline number, we report the decomposition itself as the result: the multi-client disagreement is real, large in aggregate, and has interpretable structure, but its severity must be qualified by which of the three modes is being counted. This honest reframing is what the rest of the chapter — the capped greedy scheduler and its evaluation — is designed to address.

## 6.4 The capped marginal-greedy scheduler

### 6.4.1 Algorithm

The scheduler is the textbook incremental marginal-allocation algorithm specialized to the SSD-aware service curve, with one modification: a *peak cap* that refuses to spend a unit whose best marginal gain is non-positive. Concretely:

```
Algorithm 1 (Capped SSD-aware greedy, "F")
  Input: clients {i = 1..N} with calibrated curves mu_i^SSD,
         total budget C, tolerance eps.
  Initialize k_i <- 0 for all i.
  Repeat at most C times:
      For each i, compute the marginal m_i = mu_i^SSD(k_i + 1) - mu_i^SSD(k_i).
      Let i* = argmax_i m_i.
      If m_{i*} <= eps: stop (peak cap).
      k_{i*} <- k_{i*} + 1.
  Return {k_i}.
```

The complexity is $O(NC)$ marginals — one client scan per allocated unit — which is the same order as the GoodSpeed greedy. The two structural differences from the GoodSpeed scheduler are: (i) the per-client marginal is computed on $\mu^{\mathrm{SSD}}$, which is single-peaked, rather than on the monotone $\mu^{\mathrm{GS}}$; and (ii) the loop terminates as soon as no client offers a positive marginal, leaving unspent budget idle. The first change captures the modelling correction; the second prevents overcommit past the per-client peak. We refer to this scheduler as **F** for compactness, following the design document.

We retain two reference policies:

- **GoodSpeed (baseline).** Algorithm 1 with $\mu^{\mathrm{GS}}$ in place of $\mu^{\mathrm{SSD}}$ and no peak cap. The monotone $\mu^{\mathrm{GS}}$ never has a non-positive marginal, so the cap would never bind even if present; the loop spends the full budget.
- **Uncapped SSD-greedy (ablation).** Algorithm 1 with the SSD-aware $\mu^{\mathrm{SSD}}$ but with the cap removed. The loop must spend the full budget and is therefore forced past each client's peak under slack capacity. Pairing F against this ablation isolates the effect of the cap alone, holding the service curve fixed.

The three-way comparison cleanly separates two effects: F vs. GoodSpeed measures the cost of using the wrong service curve, while F vs. uncapped SSD-greedy measures the cost of the missing cap. Both are reported below.

### 6.4.2 Capacity-pressure sweep (E3b)

We sweep the capacity-pressure ratio $\rho := \sum_i k_i^\ast / C$ from the deeply slack regime ($\rho = 0.5$, $C$ much larger than the sum of interior peaks) through the binding regime ($\rho > 1$, $C$ too small to support every client at its peak), varying $N \in \{2, 3, 5\}$ and the $\alpha$ heterogeneity spread in $\{0, 0.1, 0.18\}$. At each operating point all three schedulers are run on the same calibrated $\mu^{\mathrm{SSD}}$, and their *realized* sum-throughput on the true curve is recorded.

Table 6.1 shows the $N = 3$, $\alpha$-spread $= 0.18$ slice (the calibrated heterogeneous regime). The capped greedy attains the same realized throughput of $8.162$ across the entire slack region ($\rho \le 1$): it allocates exactly $k_i^\ast$ for each client and leaves the remaining capacity idle. GoodSpeed and the uncapped SSD-greedy spend the full budget and, depending on which scheduler is responsible, either misallocate by service-curve error (GoodSpeed) or by overcommit (uncapped greedy).

| $\rho$ | $C$ | Idle (F) | F | uncapped SSD | GoodSpeed | F vs GS | F vs SSD-greedy |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 24 | 12 | 8.162 | 3.968 | 4.192 | $+94.7\%$ | $+105.7\%$ |
| 0.67 | 18 | 6 | 8.162 | 7.367 | 4.160 | $+96.2\%$ | $+10.8\%$ |
| 0.80 | 15 | 3 | 8.162 | 8.006 | 3.917 | $+108.4\%$ | $+1.9\%$ |
| 1.00 | 12 | 0 | 8.162 | 8.162 | 3.659 | $+123.1\%$ | $+0.0\%$ |
| 1.20 | 10 | 0 | 7.981 | 7.981 | 6.050 | $+31.9\%$ | $+0.0\%$ |
| 1.50 | 8 | 0 | 7.547 | 7.547 | 6.837 | $+10.4\%$ | $+0.0\%$ |
| 2.00 | 6 | 0 | 6.867 | 6.867 | 6.837 | $+0.4\%$ | $+0.0\%$ |

*Table 6.1.* E3b headline: realized sum-throughput on the true $\mu^{\mathrm{SSD}}$ at $N=3$, $\alpha$-spread $= 0.18$. Values read from `e3b_capacity_pressure.csv`.

Three structural facts emerge.

First, the gap between F and the uncapped SSD-greedy is *purely* a slack-regime effect. They run on the same service curve; only the cap distinguishes them. The gap is largest at $\rho = 0.5$ ($+106\%$), shrinks as $\rho \to 1$, and is exactly zero for $\rho \ge 1$: when the budget is binding the cap never triggers (marginal gains are still positive when the budget runs out). The maximum across the full grid is $+266\%$ (at $N=2$, $\alpha$-spread $= 0$, $\rho = 0.5$).

Second, the gap between F and GoodSpeed is largest *near* $\rho = 1$ and persists across the entire range. GoodSpeed is using the wrong service curve; its allocation is incorrect at every operating point, but the cost is amplified near the binding boundary where it both spends the full budget and spends it on the wrong client. The headline is $+123\%$ at $\rho = 1$ in this slice; the maximum across the full grid is $+281\%$ ($N=3$, $\alpha$-spread $= 0.1$, $\rho = 0.5$).

Third, both gaps grow with $\alpha$-heterogeneity. The homogeneous regime ($\alpha$-spread $= 0$) is the easy case for any allocator; the heterogeneous regime is where the SSD-aware structure pays off.

The realized throughput of F in the slack regime is exactly the sum of interior peaks $\sum_i \mu_i^\ast$ — F achieves it by allocating $k_i^\ast$ to each client and leaving the rest idle. This is the punchline of C3: a scheduler that "leaves resources on the table" can dominate one that fully utilizes them, because the marginal value of an additional lookahead unit is negative past the peak. Figure 6.3 shows the throughput-vs-$\rho$ panel for all $(N, \mathrm{spread})$ pairs; Figure 6.4 shows the corresponding overcommit (units allocated past each client's peak) sliced the same way.

A direct caveat applies. F's advantage is defined against *sum-throughput*. Under a resource-utilization or tail-latency objective, leaving capacity idle is a defect rather than a feature, and the narrative would change. We do not claim that F is the right scheduler for those objectives — only that it is the right scheduler for the objective the problem is posed under.

## 6.5 Exact optimality of the capped greedy (G3)

The capped greedy uses the textbook incremental marginal-allocation rule. A classical result states that this rule is *exactly* optimal for the separable integer resource-allocation problem
$$
\max_{\{k_i\}} \;\sum_i \mu_i(k_i) \quad \text{subject to} \quad \sum_i k_i \le C, \;\; k_i \in \mathbb{Z}_{\ge 0},
$$
provided each $\mu_i$ is *discrete-concave*, i.e. its marginal gains $\mu_i(k+1) - \mu_i(k)$ are non-increasing in $k$. We make this proposition empirical: we compare F's realized objective against the *true* discrete optimum at every operating point on the grid of §6.4, using two independent exact solvers.

The first solver is a dynamic program. Setting $f^{(0)}_c = 0$ for $c = 0, \dots, C$ and iterating
$$
f^{(i)}_c \;=\; \max_{0 \le k \le c} \;\Big( f^{(i-1)}_{c-k} \;+\; \mu_i(k) \Big), \tag{6.1}
$$
yields $f^{(N)}_C$, the exact optimum, regardless of whether the per-client curves are concave; backtracking recovers an optimal allocation. The DP is unconditionally exact for the separable problem.

The second solver is a MILP. Introducing binary variables $x_{i,k}$ for $i \in \{1, \dots, N\}$ and $k \in \{0, 1, \dots, K\}$ with the constraints $\sum_k x_{i,k} = 1$ (each client selects one $k$) and $\sum_{i,k} k\,x_{i,k} \le C$, maximizing $\sum_{i,k} \mu_i(k)\,x_{i,k}$ recovers the same optimum. The MILP is solved by HiGHS via `scipy.optimize.milp`. The two solvers use *different* algorithmic paradigms (DP vs branch-and-bound on a linear relaxation), so agreement between them is a strong cross-check that the reported optimum is not a coding artefact in either.

### 6.5.1 Calibrated grid

We sweep $N \in \{2, 3, 5, 8\}$, $\alpha$-spread $\in \{0, 0.1, 0.18\}$, and $C$ from heavily binding ($C \ge N$) up to $\sum_i k_i^\ast + 4$ in unit steps — 228 operating points in total, of which 168 lie in the binding regime where the allocation is non-trivial. At each point we record F's objective, the DP optimum, and the MILP optimum.

The result is unambiguous. F's objective equals the DP optimum at **228 out of 228** points (worst gap $0.0$); F's allocation vector is *identical* to a DP optimum at every point (no reliance on tie-breaking). The DP and MILP optima agree to $3.6 \times 10^{-14}$, i.e. numerical noise. Discrete concavity of the calibrated $\mu_i^{\mathrm{SSD}}$ holds on its valid prefix at all 228 points — the precondition under which the greedy is provably optimal. Figure 6.5 plots F's objective against the exact optimum for every grid point; every point sits on the diagonal.

### 6.5.2 Non-concave counterexample

The result of §6.5.1 is positive precisely because the calibrated curve happens to be discrete-concave throughout its feasible block. Discrete concavity is not implied by single-peakedness alone — a unimodal curve can still have an increasing-marginal segment — so the "exact optimum" claim is genuinely conditional. To delimit it we construct a small two-client instance with $C = 3$ and curves
$$
\mu_A = (0,\,1.00,\,1.10,\,1.90,\,1.95), \qquad
\mu_B = (0,\,0.50,\,0.60,\,0.65,\,0.68),
$$
where $\mu_A$ has marginals $(1.00,\,0.10,\,0.80,\,0.05)$ — single-peaked but not discrete-concave, because the third marginal ($0.80$) exceeds the second ($0.10$). Algorithm 1 picks $(k_A, k_B) = (2, 1)$ with objective $1.60$, while the exact optimum is $(k_A, k_B) = (3, 0)$ with objective $1.90$: the greedy is trapped in the dip and never reaches $\mu_A$'s buried large marginal. Both the DP and the MILP recover the optimum independently; the greedy's gap is approximately $16\%$. We carry this counterexample into the text not as a defect of F but as a sharp delimitation of the condition under which the optimality claim holds.

### 6.5.3 Safe versus unsafe statements

The safe statement that can be carried into Chapters 1 and 9 is the following. *On the calibrated Alpaca / Qwen3-8B+0.6B regime, the capped marginal-greedy scheduler attains the exact sum-throughput optimum at every tested operating point, confirmed by two independent solvers; this holds because the calibrated $\mu^{\mathrm{SSD}}$ is discrete-concave throughout its feasible range, and a synthetic non-concave curve exhibits a $\sim 16\%$ greedy gap, showing the optimality is genuinely conditional on this precondition.* The unsafe statement to avoid is "the capped greedy is globally optimal": optimality is conditional on (i) the sum-throughput objective — F is a sum-$\mu$ optimizer, not a proportional-fairness optimizer — and (ii) discrete concavity of the per-client curve. Both hold under our calibration; neither is unconditional.

## 6.6 Discussion

The three results of this chapter — the disagreement decomposition (C5), the capacity-pressure sweep (C3), and the exact-optimality check (C4) — fit together as a single argument. The disagreement decomposition shows that the multi-client structure of the problem matters: GoodSpeed and an SSD-aware oracle differ in their allocation roughly half the time, and the differences are not arbitrary — they split into three structurally distinct modes that a scheduler could in principle target. The capacity-pressure sweep shows that closing two of the three modes — the wrong-service-curve error and the missing peak cap — is enough to dominate GoodSpeed across the entire slack-to-binding range, with the largest gaps in the very heterogeneous regime where a real multi-client deployment would operate. The exact-optimality check then closes the chapter on the algorithm: under the discrete concavity that the calibrated curve provides, the capped greedy is not just a heuristic — it is the optimum.

Three design implications follow. First, scheduling under coupled budgets is *not* primarily a wall-time problem; it is a curve-shape problem. Using a monotone surrogate for a single-peaked service costs more than failing to coordinate at all in the slack regime, where the curve-shape error compounds rather than cancels. Second, *leaving budget idle is sometimes the right action.* The cap in Algorithm 1 is not a tie-breaking heuristic — it is the structural source of F's slack-regime dominance, and removing it (the uncapped ablation in §6.4.2) erases the advantage. Schedulers designed for monotone service curves do not have this option in their algorithmic vocabulary. Third, *F is GoodSpeed plus two lines.* The structural change is a service-curve replacement and a non-positive-marginal break in the greedy loop; the data plane is otherwise identical. This makes the result actionable rather than aspirational: the contribution of this thesis is not a complicated new scheduler but a precise diagnosis of where GoodSpeed silently misallocates and the smallest change that restores correctness.

The remaining open questions belong to Chapter 8. The coupling between clients through $T_V(\sum_j k_j)$ is treated here as a fixed scale ($\sim 5\%$ second-order effect, Chapter 5); a fixed-point treatment that iteratively updates $T_V$ given the allocation, and a convergence proof for that fixed point, are left to future work. The proportional-fairness objective is reported as a secondary metric but not as a target; the capped greedy is a sum-throughput optimizer, and a PF-targeted variant — easily expressed by replacing $\mu$ with $\log\mu$ in Algorithm 1 — has not been evaluated. And the $N$-client closed-form structural propositions of §4.2 are stated for $N = 2$; their generalization is conjectural pending the experiments of Chapter 8.
