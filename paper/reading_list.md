# C 方向：现代 ML 系统中的结构化资源分配

本文件由两部分组成：

1. **C 方向的智识纲领与子问题**——为什么这是一个可作 PhD anchor 的方向
2. **分层阅读路线图**——4 周 / 8 周 / 6 个月 / 持续四层，含每篇 paper 的注释和优先级

---

## Part 1：C 方向的智识纲领

### 1.1 一句话刻画

> 现代 ML 系统中，那些经典调度理论假设"正交可分"的资源——compute、memory、bandwidth、token budget、attention capacity、expert capacity、KV cache slot——在 runtime 通过模型的 forward / backward 动力学**紧耦合**。这种耦合让经典服务曲线和分配理论失效，需要一套新的结构性刻画。

### 1.2 三个结构性后果

经典调度理论（max-weight、proportional fair、Stolyar gradient scheduling）建立在两个假设上：(a) 每个 client / tenant 的服务曲线在自己的资源上**单调**；(b) 多 client 之间的资源**可分**。现代 ML 系统违反这两条假设，导致：

1. **服务曲线非单调**：投入更多资源不一定提升服务。speculative decoding 里 $k$ 增大反而降 throughput；KV cache 里多分一点 slot 反而降 batch 效率；MoE 里 capacity factor 增大反而降 router 利用率。
2. **分配问题非可分**：client $i$ 的最优 action 依赖 client $j$ 的 action，不是通过 shared capacity（这是经典的），而是通过**耦合的资源传导**。当前工作的"正外部性"就是这个。
3. **Online 调度收敛性失效**：Stolyar fluid limit 的 Lyapunov function 需要 service curve monotone + separable。耦合 setting 下要重新构造 Lyapunov，可能需要 multi-time-scale separation 或 non-convex relaxation。

### 1.3 PhD thesis 形状

候选 thesis title：

> **Coupled Resource Allocation in Modern ML Systems: Theory, Instances, and Practical Schedulers**

章节结构：

- Ch 2: General framework（abstract coupling, KKT 结构, online scheduling 难点）
- Ch 3: Speculative inference（**当前工作 = first paper**）
- Ch 4: KV cache multi-tenant 耦合（second paper）
- Ch 5: MoE routing 或 multi-LoRA serving（third paper）
- Ch 6: Agent-scale / long-context 应用（fourth paper, more speculative）
- Ch 7: 跨 instance 的统一 lessons + practical scheduler design guidelines

**防御性结构**：framework 章节是 thesis 灵魂，每个 instance 章节既是独立 paper 又是 framework 的 evidence。某个 instance 半途证伪，thesis 整体仍能站住，只需换 instance。

---

## Part 2：C 方向的 6 个具体子问题

每个都遵循同一研究模板：**识别耦合 → 写 closed-form 模型 → 证非单调 / 非可分 → 给 KKT 结构性结论 → 仿真校准 → 真实系统验证**。

### 子问题 1：Coupled Speculative Inference（**当前 first paper**）

- 耦合关系：drafter time ↔ verifier wall time
- 非单调 axis：speculative lookahead $k$
- 多 client 耦合：通过共享 verifier $T_V(\sum k_j)$
- 现成 baseline：GoodSpeed
- **状态**：90% done，2 周可投

### 子问题 2：KV Cache Multi-Tenant 耦合（**最自然 second paper**）

- 耦合关系：cache slot allocation ↔ batch throughput（cache hit 率影响 effective batch size，effective batch size 决定吞吐，吞吐又决定回收 slot 的速度）
- 非单调 axis：per-tenant 预留 cache slot 比例
- 已有相关工作：vLLM 的 cache 管理是静态的；CacheGen / Pensieve / LMCache 做 cache placement 但没有结构性分析
- **可投 venue**：MLSys / OSDI
- 切入点：在多 LoRA / 多 SLO setting 下，固定 capacity，扫 per-tenant cache budget 比例，应能复现非单调曲线
- **新颖度**：高——这个角度目前没有 paper

### 子问题 3：MoE Inference 的 routing × capacity 耦合

- 耦合关系：expert capacity factor ↔ router 决策（capacity 太小溢出降质，太大造成 expert 空闲）
- 非单调 axis：capacity factor 或 routing temperature
- 已有相关工作：MegaBlocks、Tutel、ScatterMoE 工程化但没有 multi-client 调度结构
- **可投 venue**：MLSys / NeurIPS systems track
- 切入点：multi-tenant MoE serving 中 expert capacity 该怎么分

### 子问题 4：Multi-LoRA Serving 的 adapter swap 耦合

- 耦合关系：adapter 加载 latency ↔ batch composition 效率
- 非单调 axis：batch 内 adapter 多样性
- 已有相关工作：S-LoRA、Punica 是 systems 工作，没有理论
- **可投 venue**：MLSys / EuroSys
- 切入点：把 LoRA 选择看作有切换成本的调度问题

### 子问题 5：Agent / Tool-call serving 的 budget 耦合

- 耦合关系：thinking step 数 ↔ tool call 数 ↔ context length
- 非单调 axis：reasoning depth（over-thinking 真的会降准确率）
- 已有相关工作：几乎没有结构性 paper，Parrot (OSDI 2024) 是早期 systems 工作
- **可投 venue**：MLSys / OSDI / NeurIPS workshops
- 风险：问题 formulation 还在 settling，可能 1–2 年后才成熟
- 切入点：作为 PhD 中后期高 ceiling 选项

### 子问题 6：Long-context inference 的缓存层级耦合

- 耦合关系：prefix cache hit ↔ attention compute ↔ KV memory 层级（GPU / CPU / disk）
- 非单调 axis：哪一层放多少 cache
- 已有相关工作：1M context 时代刚开始，工程 paper 多，理论 paper 少
- **可投 venue**：OSDI / FAST

**做 PhD 的实际策略**：选 1 → 选 2 → 在 3/4/5/6 里挑一个。**不要承诺到第 4 个 instance 之前**——保留方向修正的自由度。

---

## Part 3：分层阅读路线图

按"立即读 → 暑期读 → 申请前读 → 持续读"四层组织。每篇标注：**1 句话 why read** + 优先级（必读 / 强烈推荐 / 选读）。

### Tier 0：已读（确认）

来自现 proposal references：

- Leviathan et al. (ICML 2023)
- Kumar et al. (2026) — SSD / Saguaro
- Tran et al. (2025) — GoodSpeed
- Zhang et al. (2025) — SwiftSpec
- Liu et al. (2024 / 2025) — PEARL
- Shen et al. (2025) — SpecBranch
- Li et al. (2025) — AdaServe
- Kwon et al. (SOSP 2023) — vLLM / PagedAttention

如果哪篇只看了 abstract，补一下精读。

---

### Tier 1：写当前 paper 必读（接下来 4 周）

#### A. 经典网络效用最大化与 utility scheduling 理论

这套理论是 GoodSpeed 和 multi-client KKT 分析的直接祖先。不读它写 C3 的 externality 会缺 anchor。

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 1 | **Kelly, Maulloo, Tan (1998)** "Rate control for communication networks: shadow prices, proportional fairness and stability" — *JORS* | 网络效用最大化奠基论文，proportional fairness 出处。重点 §3–§5 | 必读 |
| 2 | **Stolyar (2005)** "Maximizing queueing network utility subject to stability: greedy primal-dual algorithm" — *Queueing Systems* | GoodSpeed 引用的核心理论 paper。重点 fluid limit + Lyapunov | 必读 |
| 3 | **Tassiulas & Ephremides (1992)** "Stability properties of constrained queueing systems..." — *IEEE TAC* | Max-weight scheduling 鼻祖，所有 backpressure / gradient scheduling 的源头 | 强烈推荐 |
| 4 | **Walton (2014)** "Concave switching in single and multi-hop networks" — *Queueing Systems* | 把 max-weight 推广到 concave service curve，和非单调 setting 有连接 | 选读 |

#### B. Speculative decoding 完整图景（补 Tier 0 缺口的 tree speculation 一支）

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 5 | **SpecInfer (Miao et al. ASPLOS 2024)** "Accelerating Generative LLM Serving with Speculative Inference and Token Tree Verification" | Tree-based speculation 代表，framework 应该能 instantiate 它 | 必读 |
| 6 | **Medusa (Cai et al. ICML 2024)** "Simple LLM Inference Acceleration Framework with Multiple Decoding Heads" | Multi-head drafting，drafter 是 verifier 自己的 head，**耦合方式与 SSD 完全不同**——framework universality 的 test case | 必读 |
| 7 | **EAGLE-3 (Li et al. 2025)** | Tree speculation 当前 SOTA，看 service curve 怎么 implicitly 处理 fan-out | 强烈推荐 |
| 8 | **Sequoia (Chen, Beidi et al. NeurIPS 2024)** "Scalable, Robust, and Hardware-aware Speculative Decoding" | 给出 optimal tree shape closed-form。**framework 应该能把它作为 instantiation 推出来**——推不出说明 framework 还缺 axis | 必读 |
| 9 | **Online Speculative Decoding (Liu et al. 2024)** | Drafter 在线学习的 setting，给 framework 加时间维度 | 选读 |

#### C. Framework 的实例化候选 papers

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 10 | **GoodSpeed (Tran et al. 2025)** | 反复读。**关键自问：monotone assumption 在哪条 equation？换成非单调 $\mu^{\text{coupled}}$ 后 convergence proof 哪一步首先失效？** 这是 C3/C6 的攻击点 | 必读 |
| 11 | **Saguaro / SSD (Kumar et al. 2026)** | 反复读 appendix B 的 timing 测量和 §4 的 service curve。所有 calibration 要 cross-check 他们的数字 | 必读 |

---

### Tier 2：暑期读完，为第二个 instance 铺垫（接下来 8 周）

#### D. LLM Serving Systems 主线

认识"什么是耦合的真实 instance"的必经之路。

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 12 | **Orca (Yu et al. OSDI 2022)** "A Distributed Serving System for Transformer-Based Generative Models" | Iteration-level scheduling 鼻祖，理解"不耦合"baseline | 必读 |
| 13 | **vLLM / PagedAttention (Kwon et al. SOSP 2023)** | 反复读，关注 KV cache 分配策略。**KV cache 耦合 paper 的反例就在这里** | 必读 |
| 14 | **DistServe (Zhong et al. OSDI 2024)** "Disaggregating Prefill and Decoding for Goodput-Optimized LLM Serving" | Prefill–decode 解耦是"打破耦合"的尝试，反向看到哪些耦合无法被解耦 | 必读 |
| 15 | **Splitwise (Patel et al. ISCA 2024)** | 同主题，工程视角不同 | 强烈推荐 |
| 16 | **Sarathi-Serve (Agrawal et al. OSDI 2024)** "Taming Throughput-Latency Tradeoff with Chunked Prefill" | Chunked prefill 让 decode/prefill 之间产生新耦合——**KV cache 耦合 paper 的第二切入点** | 必读 |
| 17 | **SGLang (Zheng et al. NeurIPS 2024 / 2025)** | RadixAttention + 结构化生成，理解 prefix cache 在 multi-tenant 下的耦合 | 强烈推荐 |

#### E. KV cache 多租户 / 层级管理（第二篇 paper 的直接背景）

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 18 | **CacheGen (Liu et al. SIGCOMM 2024)** "KV Cache Compression and Streaming for Fast LLM Serving" | Cache 压缩 vs serving latency 的 tradeoff | 强烈推荐 |
| 19 | **CachedAttention (Gao et al. ATC 2024)** | Multi-session KV cache 复用 | 选读 |
| 20 | **Pensieve / LMCache 系列** | 跟最近工作流 | 选读 |

#### F. Multi-LoRA Serving（备选 second paper 背景）

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 21 | **S-LoRA (Sheng et al. MLSys 2024)** | Multi-LoRA serving 现状，**adapter swap latency 就是耦合源** | 必读 |
| 22 | **Punica (Chen et al. MLSys 2024)** | 同主题，工程更深 | 强烈推荐 |

#### G. MoE Inference（备选 second paper）

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 23 | **MegaBlocks (Gale et al. MLSys 2023)** | Block-sparse MoE，capacity factor 怎么影响效率 | 必读 |
| 24 | **Tutel (Hwang et al. MLSys 2023)** | Adaptive MoE，路由耦合的代表 | 强烈推荐 |
| 25 | **Switch Transformer (Fedus et al. JMLR 2022)** | MoE 工程化原型，capacity factor 概念出处 | 强烈推荐 |

---

### Tier 3：申请前 / PhD 第一年读完，理论纵深（6 个月内）

#### H. Queueing Theory 与 Performance Modeling 教材

| # | Paper / Book | Why read | 优先级 |
|---|---|---|---|
| 26 | **Harchol-Balter (2013)** *Performance Modeling and Design of Computer Systems* | 计算机系统 queueing 标准入门。重点 Part V (Server Farms and Networks), §27 (size-based scheduling)。读完它 "服务曲线"和"调度策略" vocabulary 就完整了 | 必读教材 |
| 27 | **Asmussen (2003)** *Applied Probability and Queues* | 更数学，做 fluid limit / heavy traffic 证明需要。重点 Ch X (heavy traffic), Ch XI (fluid models) | 选读教材 |

#### I. Fluid Limits / Network Optimization 进阶

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 28 | **Massoulié & Roberts (2002)** "Bandwidth sharing: objectives and algorithms" | Bandwidth sharing 与 utility max 的连接，KKT 在网络 setting 的应用 | 强烈推荐 |
| 29 | **Maguluri, Srikant et al.** (近 5 年) | Fluid limit for cloud / data center scheduling 系列，对比标杆。选 2–3 篇近作 | 强烈推荐 |
| 30 | **Aalto & Ayesta** size-based scheduling 系列 | Size-based 调度在 heterogeneous service 下的最优性 | 选读 |

#### J. 网络优化的非凸 / 非可分推广（做 C3 证明要用）

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 31 | **Yi & Chiang (2008)** "Stochastic network utility maximization" | NUM 的随机化推广，cross-layer optimization 范本 | 强烈推荐 |
| 32 | **Shakkottai & Srikant (2008)** *Network Optimization and Control* | Survey 形式，把 max-weight、NUM、fluid 串起来 | 强烈推荐 |

#### K. ML Systems 设计哲学

| # | Paper | Why read | 优先级 |
|---|---|---|---|
| 33 | **Crankshaw et al. (NSDI 2017)** "Clipper: A Low-Latency Online Prediction Serving System" | ML serving 祖父 paper，理解演化路径 | 强烈推荐 |
| 34 | **Park et al. (NSDI 2018)** "Accelerating Deep Learning Inference via Freezing" | Early adaptive inference | 选读 |

---

### Tier 4：持续 awareness（订阅，不要 backlog）

- **arxiv-sanity / arxiv daily**：关键词 `speculative`、`KV cache`、`inference serving`、`MoE inference`、`scheduling LLM`、`agent serving`
- **会议 proceedings 优先级**：
  - 系统线：OSDI、SOSP、NSDI、MLSys、ASPLOS
  - ML 线：NeurIPS systems / efficient ML、ICML systems
  - OR 线：Sigmetrics、Performance Evaluation
- **Twitter / X 关注**：Ion Stoica, Beidi Chen, Tianqi Chen, Song Han, Hao Zhang, Tri Dao, Lianmin Zheng——efficient inference community 的引力中心
- **每月 1 次"耦合 watch"**：扫一遍上面 venue 当月新出的 paper，问自己"这个工作里有没有藏着一个耦合？作者是不是把它当独立资源处理了？"——这是 PhD 第二、三篇 paper 的题目来源

---

## Part 4：自我检验

读完 Tier 1 + Tier 2 之后，问自己以下问题。如果都能流利回答，已经具备写完当前 paper 和 PhD 申请的素质：

1. GoodSpeed 的 fluid-limit convergence proof 在哪一步用了 monotone service 假设？换成耦合 service 后，最少需要 reconstruct 哪个 Lyapunov 项？
2. PagedAttention 把 cache slot 当作 batch-independent 资源处理。在 multi-tenant + heterogeneous workload 下，slot 利用率与 batch throughput 的耦合长什么样？
3. Sequoia 给出 single-client optimal tree shape。如果把 Sequoia 放进多 client setting，KKT externality 是不是同样适用？哪一项需要重写？
4. SpecInfer 的 tree verification 和 SSD 的 async drafting，在 $\phi_i$ formalism 下区别是什么？
5. CacheGen 把 KV cache 压缩当作独立优化问题。把它放进耦合 framework，需要补哪些 axis？

第一遍读完答不出来——不是泛读，是带着耦合视角精读再来一遍。

---

## Part 5：一句话路径总结

**未来 4 周读 Tier 1**（理论 anchor 4 篇 + tree speculation 4 篇 + GoodSpeed/Saguaro 精读），**支撑当前 paper 写作**；**暑期读 Tier 2**（serving systems 6 篇 + KV cache/LoRA/MoE 选一支深入 8 篇），**支撑 PhD 申请材料里"second instance"的雏形**；**申请前补 Tier 3**（queueing 教材 + fluid limit + NUM 进阶），**支撑 research statement 里"5 年 thesis 形状"的可信度**；**Tier 4 持续订阅**，**让方向自己长出新 instance**。
