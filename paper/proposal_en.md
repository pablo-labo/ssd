
# Multi-Client Scheduling for Speculative Speculative Decoding: Problem Formulation and Structural Analysis

**Research Proposal · Master's Thesis**

---

## 1. Motivation

Autoregressive decoding in large language models is latency-bound by its sequential structure. Speculative decoding (SD) [Leviathan et al., 2023] mitigates this by using a fast draft model to propose candidate tokens verified in parallel by a larger target model. Recent work on Speculative Speculative Decoding (SSD) [Kumar et al., 2026] parallelizes drafting and verification themselves: while verification is in progress, the drafter pre-speculates for multiple likely verification outcomes, achieving up to 2× speedup over optimized SD on single-client workloads.

In multi-user edge inference systems, multiple draft servers share a single verifier. GoodSpeed [Tran et al., 2025] formulates this as a utility-maximization problem constrained by verifier token budget $C$, allocating speculation lengths $k_i$ across clients via a gradient scheduling algorithm that converges to the optimal allocation in the fluid limit. GoodSpeed's service curve inherits SD's form: $\mu_i(k_i) = (1-\alpha_i^{k_i+1})/(1-\alpha_i)$, strictly monotone in $k_i$.

A structural gap exists between GoodSpeed's scheduling model and SSD's system mechanics. This gap is the focus of this thesis. Specifically, in an SSD system, the drafter-side cache capacity $B_i$ is not an independent parameter but a function of all clients' lookahead choices $\{k_j\}$, because the drafter's time budget is the verifier's wall time:

$$B_i(\{k_j\}) = \left\lfloor \frac{T_V\!\left(\textstyle\sum_j k_j\right) - a_i k_i}{b_i k_i} \right\rfloor_+$$

where $a_i, b_i$ are drafter-side cost coefficients and $T_V$ is the verifier wall-time function.

This coupling induces two properties absent from GoodSpeed's model:

**Non-monotonicity.** The effective service curve $\mu_i^{\text{SSD}}(k_i, B_i(\{k_j\}))$ is non-monotone in $k_i$. Increasing $k_i$ raises the expected tokens per hit $E_{\text{hit}}(k_i)$ but simultaneously shrinks $B_i$, reducing cache hit rate $p_{\text{hit}}$. The cliff-like latency penalty on cache miss (Saguaro's Corollary 16) makes the total utility potentially concave-down in $k_i$.

**Non-local coupling.** Client $i$'s service depends on all $\{k_j\}$ through $B_i$. Increasing $k_j$ for $j \neq i$ slows the verifier but extends client $i$'s drafter time budget, yielding a **positive externality** entirely absent from GoodSpeed.

These properties suggest that GoodSpeed's linear allocation may be systematically suboptimal in SSD regimes, with two concrete consequences: (a) optimal allocations may strictly reverse GoodSpeed's ordering in certain parameter regions, and (b) the verifier capacity constraint $\sum_i k_i \le C$ may not be binding at optimum—the Stolyar-style fluid analysis underlying GoodSpeed's convergence proof assumes boundary optima and thus does not directly extend.

## 2. Research Questions

This thesis addresses the following questions:

**RQ1.** What is the correct formalization of multi-client scheduling under SSD, and what structural properties distinguish it from existing multi-client SD scheduling?

**RQ2.** Under analytically tractable assumptions (specifically, Saguaro's power-law cache hit rate and geometric fan-out), what can be said in closed or semi-closed form about: (a) the unimodality of $\mu^{\text{SSD}}(k)$; (b) the monotonicity of the optimal $k^*$ in workload parameters; (c) the existence and characterization of allocation-reversal regions $\mathcal{R}$?

**RQ3.** Do the structural predictions of RQ2 hold under realistic parameter distributions calibrated from published SSD measurements?

## 3. Approach

### 3.1 Formulation

Decision variable: per-client lookahead $k_i \in \mathbb{Z}_+$.

Derived quantity: drafter cache capacity $B_i(\{k_j\})$, automatically saturated to the time budget because drafters are independent per-client—no reason to leave drafter time idle.

Constraint: $\sum_i k_i \le C$ (verifier capacity).

Objective: $\max \sum_i \log \mu_i^{\text{SSD}}(k_i, B_i(\{k_j\}), \alpha_i, r_i)$, proportional-fairness utility following GoodSpeed.

Within each client, fan-out shape $\{F_{i,k}\}$ follows Saguaro's geometric-optimal form (Theorem 12) given $(k_i, B_i)$; this remains optimal at the per-client level because fan-out shape affects only $p_{\text{hit},i}$ and does not enter $T_V$.

### 3.2 Theoretical Analysis

Starting from Saguaro's closed-form assumptions (power-law $1 - p_{\text{hit}}(F) = F^{-r}$; geometric $F_k = F_0 \alpha^{k/(1+r)}$), I plan to:

1. Derive $\mu^{\text{SSD}}(k, B)$ in closed form under the implicit relation $B = B(k, T_V, a, b)$.
2. For the 2-client case, write KKT conditions of the Lagrangian and identify the externality term $\sum_{j \neq i} U'(\mu_j) \partial \mu_j / \partial k_i$ that GoodSpeed's formulation lacks.
3. Characterize the reversal region $\mathcal{R} \subset \{(\alpha_i, r_i, a_i, b_i)\}$ where GoodSpeed's allocation differs from the KKT-optimal one in ordering.
4. Identify conditions under which the verifier constraint is slack at optimum.

Where closed form is intractable (likely for general $N$), I aim for qualitative structural results (unimodality, monotonicity direction) and numerical confirmation.

### 3.3 Simulator-Based Validation

I will implement a discrete-time SSD simulator in Python, parameterized by $(\alpha_i, r_i, a_i, b_i, T_V)$, to:

- verify the predicted structural properties numerically,
- quantify the utility gap between GoodSpeed and KKT-optimal allocations,
- locate $\mathcal{R}$ under (a) synthetic parameter sweeps and (b) realistic parameters calibrated from Saguaro's published measurements (their Figure 3, Figure 4, Appendix B).

Baselines include GoodSpeed's linear allocation, fixed equal-split $k_i = C/N$, and oracle brute-force search.

## 4. Scope and Non-Scope

**In scope:**
- Problem formulation under time-coupled drafter–verifier dynamics
- Structural theoretical analysis under Saguaro's assumptions (2-client closed form; N-client qualitative)
- Simulator-based empirical validation
- Calibration against published SSD measurements

**Explicitly out of scope** (and reserved for follow-up work):
- **Real multi-client SSD system implementation.** The systems engineering required to extend Saguaro's single-client codebase to multi-client with per-client drafter coordination (NCCL synchronization, page-table bookkeeping for multiple draft processes, custom attention mask scheduling) exceeds the thesis time budget. A real-system prototype is planned as the immediate follow-up.
- **Rigorous convergence proof for the online scheduler.** Extending GoodSpeed's Stolyar-style fluid analysis to non-monotone objectives with non-local coupling requires non-trivial Lyapunov reconstruction. The thesis presents a proof sketch and numerical convergence evidence; a full proof is reserved.
- **Shared-drafter settings.** When drafters share compute (Setting 2 in our taxonomy), the resource structure differs substantially. The thesis focuses on independent per-client drafters (Setting 3); Setting 2 is a separate direction.

These scope boundaries are intentional and form a concrete roadmap for subsequent work.

## 5. Timeline

| Week | Milestone | Deliverable |
|---|---|---|
| 0 | Literature mapping, proposal finalized | This document |
| 1–2 | 2-client closed-form derivation, baseline simulator | Technical note; initial $\mathcal{R}$ visualization |
| 3–4 | N-client simulator extension, parameter calibration from Saguaro data, sensitivity analysis | Full simulator; realistic-parameter reversal region maps |
| 5–6 | Thesis writing | Draft thesis |

**Decision gate at Week 2.** If $\mathcal{R}$ is numerically near-empty under synthetic parameters, the thesis pivots to a negative-result framing: *"Structural analysis of multi-client SSD scheduling shows that Saguaro's geometric fan-out is near-optimal in multi-client regimes, bounding the gains achievable through lookahead reallocation."* This outcome is itself a publishable structural result and does not endanger the thesis.

## 6. Relation to Prior Work

| Work | Multi-client | SSD | $k$ as decision var | $B$ modeling | Drafter–verifier coupling |
|---|---|---|---|---|---|
| GoodSpeed [Tran et al. 2025] | ✓ | ✗ | ✓ | — | ✗ |
| Saguaro [Kumar et al. 2026] | ✗ | ✓ | ✗ | fixed budget | ✗ |
| AdaServe [Li et al. 2025] | ✓ | partial | partial | — | ✗ |
| SpecBranch, SwiftSpec | ✗ | partial | ✗ | — | ✗ |
| **This thesis** | **✓** | **✓** | **✓** | **implicit function of $\{k_j\}$** | **✓** |

Concurrent-work risk: Saguaro's conclusion flags "sharing speculation endpoints at cluster level" as future work but targets a shared-drafter (Setting 2) architecture. The theoretical contribution of this thesis (non-local coupling, positive externality, non-binding verifier constraint) is orthogonal to shared-drafter analysis and stands independently.

## 7. Expected Outcomes

Beyond the thesis itself, this work is designed to produce:

- A clean problem formulation useful to subsequent work on SSD at the cluster level
- A reusable simulator (planned open-source release) supporting parameter exploration without real-LLM runs
- Identified follow-up directions, each with a concrete methodological entry point

---

## References

[1] Tran, P., Liu, T.-H., Le, L. T., Nguyen, T.-A., et al. *GoodSpeed: Optimizing Fair Goodput with Adaptive Speculative Decoding in Distributed Edge Inference.* arXiv:2512.09963, 2025.

[2] Kumar, T., Dao, T., May, A. *Speculative Speculative Decoding.* arXiv:2603.03251, 2026.

[3] Leviathan, Y., Kalman, M., Matias, Y. *Fast inference from transformers via speculative decoding.* ICML 2023.

[4] Chen, C., Borgeaud, S., Irving, G., et al. *Accelerating large language model decoding with speculative sampling.* arXiv:2302.01318, 2023.

[5] Stolyar, A. L. *On the asymptotic optimality of the gradient scheduling algorithm for multiuser throughput allocation.* Operations Research, 53(1), 2005.

[6] Li, Z., Chen, Z., Delacourt, R., et al. *AdaServe: Accelerating Multi-SLO LLM Serving with SLO-Customized Speculative Decoding.* arXiv:2501.12162, 2025.

[7] Liu, T., Li, Y., Lv, Q., et al. *PEARL: Parallel Speculative Decoding with Adaptive Draft Length.* arXiv:2408.11850, 2025.

[8] Shen, Y., Shen, J., Kong, Q., et al. *Speculative decoding via hybrid drafting and rollback-aware branch parallelism.* arXiv:2506.01979, 2025.

[9] Zhang, Z., Jiang, Y., Jiang, C., et al. *SwiftSpec: Ultra-Low Latency LLM Decoding by Scaling Asynchronous Speculative Decoding.* arXiv:2506.11309, 2025.

[10] Miao, X., Oliaro, G., Zhang, Z., et al. *SpecInfer: Accelerating Generative LLM Serving with Speculative Inference and Token Tree Verification.* ASPLOS 2024.

[11] Cai, T., Li, Y., Geng, Z., et al. *Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads.* ICML 2024.

[12] Li, Y., Wei, F., Zhang, C., Zhang, H. *EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test.* arXiv:2503.01840, 2025.

[13] Zhong, Y., Liu, S., Chen, J., et al. *DistServe: Disaggregating Prefill and Decoding for Goodput-Optimized LLM Serving.* OSDI 2024.

[14] Agrawal, A., Kedia, N., Panwar, A., et al. *Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve.* OSDI 2024.

[15] Kwon, W., Li, Z., Zhuang, S., et al. *Efficient Memory Management for Large Language Model Serving with PagedAttention.* SOSP 2023.

