# Framing 升级稿

把论文的中心从"SSD 多客户端调度 vs GoodSpeed"抬到**"共享资源耦合 → 非单调服务曲线 → 多客户端分配结构改变"** 三段式。所有现有资产（Block 1、A2、Block 3、calibration）保留位置不变，只是被重新组织。

---

## Title 候选

1. **Coupled Resources and Non-Monotone Service in Speculative LLM Inference**
2. **When the Drafter Borrows Time: Resource Coupling Breaks Monotone Service in Speculative Decoding**
3. **A Structural Account of Speculative Inference: Coupled Budgets, Non-Monotone Service, and Multi-Client Allocation**

推荐 **Title 1**：技术中性、关键词齐、不卖弄。

---

## Abstract（英文版，~220 词）

> Modern speculative LLM inference variants—asynchronous and tree-based speculative decoding, parallel drafting (SSD), adaptive draft length—accelerate generation by overlapping a fast drafter with a slower verifier. We observe that **whenever drafter and verifier share a hardware resource (compute time, memory bandwidth, or attention budget), the drafter's effective budget becomes an implicit function of the verifier's lookahead choice**. This coupling has a structural consequence: the per-client service curve $\mu(k)$ as a function of speculative lookahead $k$ is **non-monotone**, with an interior optimum $k^\ast$.
>
> We formalize this coupled-resource regime and prove three structural results under closed-form assumptions inherited from Saguaro (power-law cache hit, geometric fan-out). (i) The single-client service curve is **single-peaked** under finite verifier-time regularity. (ii) The optimum satisfies $k^\ast \sim r \log T_V / \log(1/\alpha)$ asymptotically. (iii) In the multi-client allocation problem, KKT conditions expose a **positive externality** term that is structurally absent from monotone-service schedulers such as GoodSpeed. We instantiate the framework in SSD, calibrate timing from real Qwen3-8B / 0.6B execution on Alpaca, and verify $k^\ast \approx 5$ in real LLM runs. A two-client allocation analysis under calibrated parameters shows that scheduler-native allocation disagreement between GoodSpeed and our coupling-aware optimum reaches approximately 50% of cases, decomposing into three distinct failure modes: drafter-cost blindness, near-peak overcommit, and strict reversal.
>
> The framework subsumes single-client SSD as a special case and clarifies which existing speculative-inference schedulers inherit monotone service from a hidden decoupling assumption.

**中文要点**：

- 立论：所有 drafter 与 verifier 共享硬件资源的 SD 变种都受同一个结构性规律支配
- 三条理论 claim：单客户端单峰、$k^\ast$ 渐近 scaling、多客户端正外部性
- 一条实证：SSD instantiation 在真实 LLM 上验证 + Alpaca calibrated 多客户端反转
- 落点：framework 把 GoodSpeed 解释为 decoupled 极限的退化特例

---

## Intro 章节大纲（5 节，目标 3 页）

### §1.1 Hook：speculative inference 的资源结构正在改变

- 起点：LLM 推理 latency-bound；speculative decoding（SD, Leviathan 2023）通过 drafter + verifier 并行化解决
- 近 1.5 年趋势：async / parallel SD 家族崛起——SSD/Saguaro (Kumar 2026)、SwiftSpec (Zhang 2026)、PEARL (Liu 2025)、SpecBranch (Shen 2025)、AdaServe (Li 2025)
- 这些 variant 的共同点：drafter 和 verifier 不再串行，而是**重叠或并行**在共享硬件上运行
- 立论一句话：**这种重叠让 drafter 的预算不再是独立参数，而是 verifier 选择的隐函数**——这件事在过去的调度建模里被忽略

### §1.2 Observation：共享资源导致 drafter budget 内生

- 给一张概念图：drafter 时间 $B_i$ 怎么由 verifier 的 wall time $T_V(k_i)$ 反推
- 关键观察：把 $B_i$ 写成 $\{k_j\}$ 的函数后，原本"$\mu_i(k_i)$ 单调递增"的标准 SD 服务曲线不再成立
- 给一个 minimal counter-example（1 张图）：固定其他参数，单独扫 $k$，throughput 出现内部峰
- **资产复用**：Block 1 GSM8K 真实-LLM 曲线（$k = 2 \to 5$ 上升，$k = 5 \to 12$ 下降）直接做这张头图
- 视觉上加一条 monotone SD service curve 作对照线，一秒讲清楚 non-monotone 在哪里

### §1.3 General Coupled-Resource Model

形式化定义（**这是论文最关键的一页**）：

> **Definition (Coupled Speculative Inference).** A speculative-inference scheme is *coupled* if there exist resource constraints $g(\{k_j\}, \{B_j\}) \le 0$ such that for any feasible $(k_i, B_i)$, $B_i$ is determined as a function $B_i = \phi_i(\{k_j\})$. The service curve is $\mu_i(k_i; \{k_j\}) = f_i(k_i, \phi_i(\{k_j\}))$.

然后给出一张"已有方案在此 framework 下的 instantiation 表"：

| Scheme | 共享资源 | $\phi_i$ 形式 | $\mu$ 在 $k_i$ 上 monotone? |
|---|---|---|---|
| Classical SD | 无 | $B_i$ 独立 | yes |
| GoodSpeed | 无（drafter 独立） | $B_i$ 独立 | yes |
| **SSD (Saguaro)** | verifier wall time | $\lfloor (T_V(\sum k_j) - a_i k_i)/(b_i k_i)\rfloor_+$ | **no** |
| SwiftSpec | pipeline depth | 类似 SSD | **no** |
| PEARL | adaptive draft length | $\phi_i$ 依赖 acceptance | **conditional** |
| AdaServe | SLO-shared | partial coupling | partial |

**这张表是 paper 的灵魂卖点**：它告诉 reviewer 你研究的不是 SSD 的子问题，而是 async SD 家族的共有结构问题。

### §1.4 主要 contribution（论文的"承诺清单"）

六条 claim，每条对应一块已有资产：

**C1（结构性命题）.** Under coupled drafter–verifier budgets with Saguaro's closed-form assumptions, the single-client service curve $\tilde\mu^{\text{coupled}}(k)$ is single-peaked. The FOC takes the form

$$\alpha^{k^\ast}\log(1/\alpha)\,p_{\text{hit}}(k^\ast) = q'(k^\ast)(1-\alpha^{k^\ast})$$

**资产复用**：Block 1 A2 derivation（`paper/math/block1a2.md`）整段移过来。

**C2（渐近 scaling）.** In the large-$T_V$ unsaturated regime,

$$k^\ast = \frac{r \log T_V}{\log(1/\alpha)} + O(\log\log T_V)$$

**资产复用**：A2 Theorem 2。

**C3（多客户端 KKT 与正外部性）.** In two-client allocation under shared verifier capacity $C$, KKT conditions for the coupled service curve include a non-zero cross-client term $\partial \mu_j / \partial k_i$ that monotone-service formulations (GoodSpeed) assume zero.

**资产复用**：proposal_en §3.2 的 KKT formulation。

**C4（实证 instantiation: SSD）.** Real LLM execution on Qwen3-8B target + Qwen3-0.6B drafter confirms a single-peaked decode throughput curve at $k^\ast \approx 5$ for fixed fan-out budget, with cache hit, accepted suffix, and verify time all moving consistently with the coupling mechanism.

**资产复用**：GSM8K 细扫 + Alpaca 校准（experiment_log 4/30 和 5/5 章节）。

**C5（分配结构 disagreement）.** Under Alpaca-calibrated timing, scheduler-native allocation between GoodSpeed and coupling-aware optimal disagrees on $\sim$50% of cases, decomposing into three structurally distinct mechanisms: (a) **blindness** to drafter-cost heterogeneity (22.8% at $C=12$); (b) **overcommit** near the unimodal peak (18.0%); (c) **strict reversal** (10.8%, growing to 15.7% at $C=20$).

**资产复用**：Block 3 全套 + 5/7 reframing。

**C6（应用 implication）.** Designing multi-client schedulers for any coupled speculative-inference variant requires explicit modeling of drafter-budget coupling; monotone-service formulations are exact only in the decoupled (classical SD) limit.

### §1.5 Scope, Non-Scope, and Relation to Prior Work

- **In scope**: framework definition, structural theorems, SSD instantiation, simulator-based multi-client analysis, calibration from real timing fits
- **Explicitly out of scope**（继承 proposal 的诚实划界）: full production-grade multi-client SSD system; convergence proof for online schedulers; shared-drafter (Setting 2) architectures
- **Relation to prior work**:
  - Saguaro 提供 closed-form 假设，但只研究 single-client
  - GoodSpeed 提供 multi-client 调度，但假设 monotone service
  - SwiftSpec / PEARL / AdaServe 有耦合现象但无 structural analysis
  - **本文是 first unification across these variants**

---

## 与现有 proposal 的关键差异

| 维度 | 现 proposal | 升级版 framing |
|---|---|---|
| Unit of analysis | "SSD 多客户端 vs GoodSpeed" | "耦合资源 → 非单调服务 → 多客户端结构" |
| Block 1 | 单峰性验证 | **核心定理 C1**（结构性命题） |
| Block 3 | 反转区域 / Gate 3 | **C5 三机制分解**（不再是 pass/fail gate） |
| SSD 的地位 | 研究对象 | **一个 instantiation 实例** |
| GoodSpeed 的地位 | attack target | **decoupled 特例** |
| Reviewer 攻击面 | "为什么不做真实系统" | 同样存在，但被 "general framework" 缓冲 |
| 半衰期 | 取决于 SSD 是否流行 | 取决于 async SD 家族整体是否流行（更长） |
| Scoop 风险 | 高（SSD 多客户端是显式 follow-up） | 中（"耦合 framework" 这个抽象层目前无人占） |

---

## 立刻可做的三件事

1. **写 §1.3 那张 instantiation 大表**（30 分钟）。这张表本身就是 paper 灵魂。把 SwiftSpec / PEARL / SpecBranch / AdaServe 的论文摘要拉出来，验证它们的 drafter budget 是否真的能写成某种 $\phi_i$ 形式。如果其中 2–3 个不是耦合，framework 收窄到剩下的 variant 上；如果都是耦合，那 framework 就是 universal。

2. **改 §1.2 的反例图**（1 小时）。Block 1 GSM8K 曲线已经是论文头图候选。给它加一条 "monotone SD service curve" 作对照线，视觉上一秒讲清楚 non-monotone 在哪里。

3. **在 simulator 里加一个 PEARL-like instance**（半天到 1 天）。把 PEARL 的 adaptive draft length 用同一个 $\phi$ formalism 表达一遍，跑一张服务曲线。如果它也呈现 non-monotone，C1 在 SSD 之外有第二个真实 instantiation——**这件事对 framework 的 universality 论点价值最高，单独就能把 workshop 命中率再加 5–10%**。
