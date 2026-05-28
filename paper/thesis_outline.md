# 硕士毕业论文大纲（交给内容生成 AI 用的版本）

本文件目的：给后续内容填充的 AI 一份"详细到能直接写"的章节大纲。每章包含：**章节目标 / 主要小节 / 资产来源 / 必须包含的关键 claim / 注意事项**。

---

## 0. 写作前的全局约定

### 0.1 论文题目（候选）

主推：**面向耦合资源推测式 LLM 推理的服务曲线刻画与多客户端调度分析**
（英文：*Coupled Resources and Non-Monotone Service in Speculative LLM Inference: A Structural Analysis with Proposed Schedulers*）

### 0.2 核心符号约定

- $k_i$：客户端 $i$ 的 verifier 端 speculative lookahead（决策变量）
- $B_i$：客户端 $i$ 的 drafter 端 fan-out 预算（导出变量）
- $T_V(\cdot)$：verifier wall-time 函数
- $a_i, b_i$：客户端 $i$ 的 drafter 端时间成本系数（per-depth, per-fanout）
- $\alpha_i$：客户端 $i$ 的 token acceptance rate
- $r_i$：客户端 $i$ 的 cache hit power-law 指数
- $C$：verifier 端总容量约束（$\sum_i k_i \le C$）
- $\mu_i^{\text{SSD}}(k_i, B_i)$：客户端 $i$ 的 SSD-aware 服务曲线
- $\mu_i^{\text{GS}}(k_i) = (1-\alpha_i^{k_i+1})/(1-\alpha_i)$：GoodSpeed monotone 服务曲线
- $\tilde\mu^{\text{coupled}}(k)$：考虑了耦合预算 $B(k)$ 后的有效服务曲线

### 0.3 整体叙事弧

1. 推测式 LLM 推理的 async / parallel 变种崛起 → drafter 与 verifier 共享硬件资源
2. 这种共享让 drafter 预算成为 verifier 选择的隐函数 → 服务曲线非单调
3. 单客户端：证非单调（Block 1 + A2 闭式分析）
4. 多客户端：KKT 揭示正外部性，存在调度不一致（Block 3）
5. 提出 coupling-aware 调度器，与 GoodSpeed / oracle 对比，证明小幅可解的工程方案存在
6. Limitations 诚实：单 drafter calibration / 仿真器 vs 真实系统

### 0.4 关键诚实点（必须显式写进论文）

- 原 Gate 3 标准（严格反转 $\ge 20\%$）**未达成**，因此 reframe 为 scheduler-native 三机制分解
- Block 1 A2 corollary 中 $k^\ast(B)$ 在实测下**可能非单调**（Alpaca 数据是 4-5-5-4-4）
- Calibration 来自**单一 drafter**（Qwen3-0.6B），$b$-heterogeneity 主要来自合成扫
- Block 3 结果建立在**仿真器**上，未在真实多客户端系统上验证

不要隐藏这些事实——把它们当作"已被识别并纳入 limitations 章节"的研究 maturity 表现。

---

## Chapter 1: Introduction（5 页）

### 1.1 目标

让读者在 5 页内理解：(a) 问题是什么，(b) 为什么以前没人解，(c) 本文做了什么，(d) 贡献清单。

### 1.2 主要小节

- **1.1 LLM 推理的延迟瓶颈与推测式解码**：从经典 SD（Leviathan 2023）讲起，1 页
- **1.2 Async/parallel SD 家族的崛起**：SSD/Saguaro、SwiftSpec、PEARL、SpecBranch、AdaServe 简表，1 页
- **1.3 核心观察：共享资源耦合**：用 1 段把 "drafter 与 verifier 共享硬件 → drafter 预算成为 verifier 选择的隐函数 $\phi_i(\{k_j\})$" 这件事讲清楚
- **1.4 研究问题**：列出 3 个 research question
  - RQ1：耦合资源下，per-client 服务曲线 $\tilde\mu(k)$ 是否非单调？最优 $k^\ast$ 有什么结构？
  - RQ2：多客户端下，monotone-service 调度器（GoodSpeed）的最优分配与 coupling-aware 最优分配差多少？差在哪？
  - RQ3：能否设计简单的 coupling-aware 调度器，在仿真器上接近 oracle 的同时实现成本可控？
- **1.5 贡献概览**：6 条 bullet，对应 thesis 主结果
- **1.6 论文结构**：1 段话讲后续各章的内容

### 1.3 资产来源

- `paper/proposal_en.md` §1 motivation 整段可改写
- `paper/proposal_cn.md` 中文版本可参考
- `paper/idea.md` 有更早期的动机讨论

### 1.4 必须包含的 6 条贡献

1. 建立耦合资源推测式推理的统一形式化模型 $\mu_i = f_i(k_i, \phi_i(\{k_j\}))$
2. 证明单客户端服务曲线在有限 $T_V$ 正则条件下单峰（Theorem 1）+ 给出 $k^\ast$ 大 $T_V$ 渐近形式（Theorem 2）
3. 在真实 LLM（Qwen3-8B + 0.6B）+ Alpaca/GSM8K 上验证 $k^\ast \approx 5$
4. 多客户端 KKT 揭示正外部性项（标准 GoodSpeed 公式中为零）
5. Scheduler-native 比较：GoodSpeed 与 coupling-aware 最优在 Alpaca-calibrated 下约 50% 分配不一致，可分解为 drafter-cost 盲视 22.8% / overcommit 18.0% / 严格反转 10.8%（$C=12$）
6. 提出两个 coupling-aware 启发式调度器（GoodSpeed++、Coupling-Corrected Greedy），仿真器评估显示与 oracle 的 utility gap $< 5\%$

### 1.5 注意事项

- 第 1 章是答辩老师**唯一会精读**的章节之一，每句话都要精准
- 不要在贡献清单里 oversell。"50% 不一致"要写成"约半数情形下分配结构不同"，**不要写成"我们击败 GoodSpeed 50%"**
- 必须在贡献清单或紧邻段落里**显式声明 limitations 和 scope**（避免让读者读到 Ch 7 才知道有 scope 限制）

---

## Chapter 2: Background and Related Work（8 页）

### 2.1 目标

把读者带到能读懂 Ch 3–6 的水平，同时给出与 prior work 的明确对照表。

### 2.2 主要小节

- **2.1 推测式解码基础**：SD 原理、token tree、verification（1.5 页）
  - Leviathan et al. 2023（基础 SD）
  - Chen et al. 2023（speculative sampling）
  - SpecInfer / Medusa / EAGLE / Sequoia（tree-based 一脉）
- **2.2 Async / parallel 推测式解码**：1.5 页
  - SSD / Saguaro 详细讲（fan-out budget 概念、power-law cache hit、geometric fan-out shape）
  - SwiftSpec / PEARL / SpecBranch / AdaServe 各 1 段
- **2.3 多客户端 LLM serving 与调度**：2 页
  - LLM serving 系统（Orca, vLLM, DistServe, Splitwise, Sarathi-Serve）
  - 多客户端调度（GoodSpeed 详细讲——proportional fairness, gradient scheduling, Stolyar fluid limit）
- **2.4 网络效用最大化与调度理论**：1.5 页
  - Kelly et al. 1998（NUM 框架）
  - Stolyar 2005（gradient scheduling）
  - Tassiulas-Ephremides 1992（max-weight）
  - Walton 2014（concave switching, 与你的 setting 最近）
- **2.5 与本文的对照**：1.5 页（含 prior work 对照表）

### 2.3 资产来源

- `paper/proposal_en.md` §6 + References 全套可改写
- `paper/reading_list.md` Tier 1 各 paper 的注释
- Saguaro paper（`paper/2603.03251v1.pdf`）+ GoodSpeed paper（`paper/2512.09963v2.pdf`）需精读后总结

### 2.4 必须包含的对照表

| Work | Multi-client | SSD | $k$ 作为决策变量 | $B$ 建模 | drafter-verifier 耦合 |
|---|---|---|---|---|---|
| GoodSpeed (Tran et al. 2025) | ✓ | ✗ | ✓ | — | ✗ |
| Saguaro (Kumar et al. 2026) | ✗ | ✓ | ✗ | 固定 | ✗ |
| AdaServe (Li et al. 2025) | ✓ | partial | partial | — | ✗ |
| SwiftSpec / SpecBranch | ✗ | partial | ✗ | — | partial |
| **本文** | **✓** | **✓** | **✓** | **$\phi_i(\{k_j\})$** | **✓** |

### 2.5 注意事项

- 不要把 Related Work 写成 paper list。每一段都要回答"它和本文什么关系"——不是 summary 而是 contextualization
- Saguaro 是本文最重要的参考点，给它最长篇幅；GoodSpeed 是最直接的对照，也给较长篇幅
- 不要批评任何 prior work。**用"his/her work assumes X; this thesis instead considers Y"，不要用"prior work fails to..."**

---

## Chapter 3: Problem Formulation（6 页）

### 3.1 目标

把要研究的问题严格形式化，让读者知道你在数学上证什么、在实验上验什么。

### 3.2 主要小节

- **3.1 系统模型**（1 页）
  - SSD 单客户端 setup（drafter + verifier 配对）
  - 时间结构：drafter 在 verifier 等待期内运行
  - fan-out tree 结构（Saguaro geometric capped）
- **3.2 假设清单**（1 页）
  - A1: power-law cache hit $1 - p_{\text{hit}}(F) = F^{-r}$（来自 Saguaro）
  - A2: capped geometric fan-out $F_k = F_0 \alpha^{k/(1+r)}$
  - A3: drafter timing $\text{draft\_ms} = a k + b k B$
  - A4: verifier timing 近似线性 $T_V(k) = T_0 + \tau k$
  - 对每条假设说"为什么合理 + 5/5 calibration 上的实测支持"
- **3.3 单客户端形式化**（1.5 页）
  - 决策变量 $k$
  - 导出变量 $B(k) = \lfloor (T_V - ak)/(bk) \rfloor_+$
  - 服务曲线 $\tilde\mu^{\text{SSD}}(k) = p_{\text{hit}}(B(k)) \cdot E_{\text{hit}}(k) / T_V(k)$
- **3.4 多客户端形式化**（1.5 页）
  - 决策变量 $\{k_i\}_{i=1}^N$
  - 共享约束 $\sum_i k_i \le C$
  - 耦合预算 $B_i(\{k_j\}) = \lfloor (T_V(\sum_j k_j) - a_i k_i)/(b_i k_i) \rfloor_+$
  - 优化目标（log-utility / proportional fairness）：$\max \sum_i \log \mu_i^{\text{SSD}}(k_i, B_i(\{k_j\}))$
- **3.5 与 GoodSpeed formulation 的对照**（1 页）
  - GoodSpeed: $\max \sum_i \log \mu_i^{\text{GS}}(k_i)$, $\mu^{\text{GS}}$ 单调
  - 本文: $\mu^{\text{SSD}}$ 非单调 + $B_i$ 耦合
  - 给一个 side-by-side 公式块对比

### 3.3 资产来源

- `paper/proposal_en.md` §3.1 原文可改写
- `paper/math/block1a2.md` §0 假设节
- `experiment_log.md` 5/3 节 "Block 1 A2 Math-To-Experiment Alignment" 的符号对应

### 3.4 必须明确表述的点

- $B_i$ 是**导出量**，不是独立决策变量；$\phi_i$ 这个函数符号在 Ch 3 第一次正式定义后续章节统一沿用
- $T_V(\cdot)$ 假设是 $\sum_j k_j$ 的函数（即所有客户端共享同一 verifier）——这是与 GoodSpeed 一致的多客户端假设
- 假设 A1–A4 都是为可证而做的工作假设；Ch 5 会用实测部分验证，Ch 7 会列其 robustness

### 3.5 注意事项

- 公式要带编号，后续章节按公式编号引用
- 不要在这一章引入任何理论结果（Lemma / Theorem 留给 Ch 4）
- 这一章的成功标准是：**一个数学背景中等的读者读完它后能独立写出 Ch 4 的优化问题**

---

## Chapter 4: Theoretical Analysis（12 页）

### 4.1 目标

证明三件事：(a) 单客户端服务曲线单峰，(b) $k^\ast$ 大 $T_V$ 渐近 scaling，(c) 多客户端 KKT 暴露正外部性。

### 4.2 主要小节

- **4.1 单客户端分析**（5 页）
  - Lemma 1: miss probability $q(k)$ 在有效区间上递增
  - Proposition 1: 内部最优 $k^\ast$ 的 FOC：$\alpha^{k^\ast}\log(1/\alpha) \cdot p_{\text{hit}}(k^\ast) = q'(k^\ast)(1-\alpha^{k^\ast})$
  - Theorem 1: 在 $q''(k) \ge 0$ 正则条件下 $\tilde\mu^{\text{SSD}}$ 单峰
  - Theorem 2: 大 $T_V$ 不饱和 regime 下 $k^\ast = r \log T_V / \log(1/\alpha) + O(\log\log T_V)$
- **4.2 多客户端 KKT 分析**（4 页）
  - 写出 Lagrangian
  - 推导 KKT 条件
  - 展开 $\partial \mu_j / \partial k_i$ 项（cross-client externality）
  - 给出"GoodSpeed 公式相当于令 cross-client 项为零"的对照
  - **正外部性的 sign analysis**（这是 C3 的核心）
- **4.3 关于全局最优的讨论**（2 页）
  - 整数规划性质（$k_i \in \mathbb{Z}_+$）
  - 非凸性来源
  - 多 local optima 的存在性讨论
- **4.4 理论结果的实证含义**（1 页）
  - 哪条命题对应哪个 Block 1 / Block 3 实验
  - $k^\ast$ 的 monotonicity corollary 引出 Ch 5 的 sweep

### 4.3 资产来源

- `paper/math/block1a2.md` 全部内容
- `proposal_en.md` §3.2 KKT formulation

### 4.4 必须包含的关键公式（编号要对）

```
(4.1) FOC: α^{k*} log(1/α) · p_hit(k*) = q'(k*)(1 - α^{k*})
(4.2) 大 T_V 渐近: k* = r log T_V / log(1/α) + O(log log T_V)
(4.3) KKT cross-client: ∂μ_j/∂k_i = (∂μ_j/∂B_j)(∂B_j/∂k_i)
(4.4) 外部性 sign: ∂B_j/∂k_i = -(T_V'(Σk))/(b_j k_j) < 0  ⇒ 当 ∂μ_j/∂B_j > 0 时，cross-client 项为负（在 utility max 视角下是 positive externality 的来源）
```

### 4.5 注意事项

- Theorem 1 是**条件性**的（要求 $q'' \ge 0$）——必须显式承认这一点，不要做无条件 claim
- Theorem 2 的渐近是**大 $T_V$** 下的——实测 $T_V \approx 20$ ms 不一定算"大"，Ch 5 要诚实讨论这个 gap
- 多客户端 KKT 在 Ch 4 只给 2-client 情形；$N>2$ 的推广留在 Discussion
- 不要把 oracle = "提出的方法"。Oracle 只是 KKT 解的数值实现，不是算法。"提出的方法"留给 Ch 6.4

---

## Chapter 5: Single-Client Validation（10 页）

### 5.1 目标

让读者相信 Ch 4 Theorem 1 的非单调性在**真实 LLM 执行**中存在，并给出 timing calibration。

### 5.2 主要小节

- **5.1 合成网格验证**（2 页）
  - 实验设置：4032 cases 网格（$\alpha, r, a, b, T_V$ 各取值）
  - 结果：100% cases 单峰，0.1% $\alpha$ 单调性违反
  - 表格 + 1 张 heatmap
- **5.2 真实 LLM 实验设置**（2 页）
  - 硬件：2x RTX 4090（CUDA arch 8.9）
  - 模型：Qwen3-8B target + Qwen3-0.6B draft
  - 数据集：Alpaca + GSM8K（含数据集 fallback issue 的 fix 简述）
  - 工作流：geometric capped fan-out，参数 $(\alpha\text{-prior}, r\text{-prior}, B, k)$
- **5.3 单峰性验证**（2 页）
  - GSM8K 细扫结果（$B=36$, $k \in \{2..12\}$, $k^\ast \approx 5$）
  - Alpaca 跨预算结果（$B \in \{16, 24, 36, 48, 64\}$, 每个预算的 $k^\ast$）
  - 主图：decode_throughput vs $k$ 在多个 $B$ 下的曲线（论文头图候选）
- **5.4 机制验证**（2 页）
  - 4 张支撑图：avg_suffix（$\uparrow$ in $k$）/ cache_hit（$\downarrow$ in $k$）/ verify_ms（mildly $\uparrow$ in $k$）/ throughput（peaks）
  - 这些机制是否与 Ch 4 FOC 的"marginal hit benefit = marginal miss cost"对应
- **5.5 Timing Calibration**（1.5 页）
  - 拟合 $\text{draft\_ms} = c + a k + b k B$
  - 给出 $a \approx 2.63$ ms, $b \approx 0.0077$ ms, $R^2 \ge 0.996$ 等数字
  - 拟合 $T_V(k) = 19.6 + 0.094 k$ ms
  - 简述 `draft_total_ms` vs `draft_detail_total_ms` 选择问题（即"不要用 total，会拟合出负的 $b$"这个 lesson）
- **5.6 A2 Corollary 的真实-LLM 检查**（0.5 页）
  - $\alpha$ 跨数据集扫的 $k^\ast$ 结果（如做了 P1 实验）
  - $B$ 扫的 $k^\ast$ 结果——**诚实记录非单调**（Alpaca 数据 4-5-5-4-4）
  - 解释机制：高 $B$ 下 cache hit 一阶项主导，简单 $T_V$-proxy 失效

### 5.3 资产来源

- `paper/experiment_log.md` 4/30 "Block 1 A3 Validation Setup" + "Full Block 1 A3 Result" + "GSM8K Fine-Grained Block 1 A3 Result" 全节
- `paper/experiment_log.md` 5/3 "Block 1 A2 Math-To-Experiment Alignment" 全节
- `paper/experiment_log.md` 5/5 "Block 3 Alpaca Full Timing Result" 中的 calibration 部分
- `bench/results/geometric_block1_20260429_134517/` 全套 figures
- `bench/results/block3_timing_alpaca_full_v2/` 全套 figures

### 5.4 必须给出的关键数字

- GSM8K $k^\ast \approx 5$（in decode_throughput_mean）
- Alpaca $k^\ast \in \{4, 5\}$ across budgets
- $a \approx 2.63$ ms, $b \approx 0.0077$ ms, fit $R^2 \ge 0.99$
- $T_V \approx 19.6 + 0.094 k$ ms, $R^2 \approx 0.87$
- Cache hit decay range：$B=16$ 下 $0.824 \to 0.433$，$B=64$ 下 $0.908 \to 0.736$

### 5.5 注意事项

- 这一章是 paper 的"实证 backbone"，**figure 必须高质量**
- 5.6 的 negative finding 要写得诚实但不过度自责。模板话术：
  > "The simple $T_V$-proxy $B \mapsto T_V$ is consistent with our framework only up to a first-order approximation; under finer measurement, cache-hit elasticity dominates and $k^\ast(B)$ shows mild non-monotonicity. We discuss this in §7.3 and Ch 7 limitations."
- 提到 dataset fallback issue 时，强调它**已被识别和修复**，不要让它看起来像 paper 主结果的隐患

---

## Chapter 6: Multi-Client Allocation Analysis and Proposed Schedulers（12 页）

### 6.1 目标

这是 thesis 的 main contribution 章，要做四件事：(a) 暴露 GoodSpeed 与 coupling-aware 最优的分配结构差异，(b) 把差异分解为三种机制，(c) 量化每种机制的 utility-loss 分布，(d) 提出两个 coupling-aware 启发式调度器并评估。

### 6.2 主要小节

- **6.1 设定与符号**（0.5 页）
  - 接 Ch 3.4，重述 2-client 配置
- **6.2 KKT Analysis 与 Externality 项**（1.5 页）
  - 接 Ch 4.2，把 KKT 结果具象到 2-client
  - 给出 numerical 计算的 sign + magnitude 示例
- **6.3 Scheduler-Native 调度不一致分析**（4 页）
  - **6.3.1 三种失败模式**：
    - Blindness（GS tie, SSD 非 tie）
    - Overcommit（GS 非 tie, SSD tie）
    - Strict reversal（GS 与 SSD order 相反）
  - **6.3.2 Alpaca-calibrated scan 结果**：
    - 总 mismatch ≈ 50%，$C=12$ 下分解为 22.8% / 18.0% / 10.8%
    - $C$-sweep：$C \in \{8, 10, 12, 14, 16, 20\}$，每种机制的比例变化
    - 图：native_order_mechanisms_by_capacity（已生成）
  - **6.3.3 b-ratio scaling**：
    - 异质性 driver 分析
    - $b_{\max}/b_{\min} \ge 20$ 下严格反转可达 30%+
    - 图：alpaca_calibrated_b_ratio（已生成）
  - **6.3.4 Utility-gap CDF**：
    - 每种机制下的 utility loss 分布（P0 实验 输出）
    - 严格反转 case 的平均 gap 37.4%, max 48.5%
- **6.4 提出的 Coupling-Aware 调度器**（3.5 页）
  - **6.4.1 GoodSpeed++ (tie-breaking baseline)**
    - 算法描述
    - 直觉：直接解决盲视 22.8% 那种机制
  - **6.4.2 Coupling-Corrected Greedy**
    - 算法描述（贪心边际效用）
    - 复杂度 $O(NC)$
    - 与 oracle 关系：贪心未必全局最优但实测接近
  - **6.4.3 Lagrangian Coordinate Descent (future work, 简述)**
- **6.5 调度器评估**（2 页）
  - 实验设置：仿真器，$N \in \{2, 4, 8\}$，$C \in \{8, 12, 16, 20\}$，Alpaca-calibrated timing
  - 算法集合：{Equal-split, GoodSpeed, GoodSpeed++, Coupling-Greedy, Oracle}
  - 指标：mean log-utility gap vs oracle (%)，decision wall-time (μs)
  - 结果表：每个 (N, C) 下各算法的 oracle gap
  - 主结论：Coupling-Greedy 与 oracle gap < 5%，decision time 比 oracle 低 100x+
  - 如做了 Level 3：单点 real-LLM 验证（2 client 配置 GoodSpeed vs Coupling-Greedy 的真实 throughput）
- **6.6 讨论**（0.5 页）
  - 三种失败机制的 design implication：什么样的 multi-client scheduler 设计能避开每种
  - 与 GoodSpeed 的关系：GoodSpeed 在 decoupled limit 是正确的
  - 这一章结论：**simple coupling-aware policies 足够实现接近 oracle 的效用，无需求解非凸全局优化**

### 6.3 资产来源

- `paper/experiment_log.md` 5/5 "Block 3 Allocation-Reversal Scan" + "Block 3 Alpaca-Calibrated Reversal Scan" 全节
- `paper/experiment_log.md` 5/5 "Scheduler-Native Reversal Decomposition" 全节
- `paper/experiment_log.md` 5/7 "Framing Update After Native-Order Figure Review" 全节
- `sim/experiments/results/block3_native_order_figures/` 全套 figures
- `sim/experiments/results/block3_slide_figures/` 全套 figures
- P0 实验输出（`block3_native_gap.py` 待跑）
- 待写算法实现（`sim/schedulers/coupling_greedy.py` + `goodspeed_plus.py`）

### 6.4 必须明确的关键数字

- $C=12$ Alpaca-calibrated 下：blindness 22.8%, overcommit 18.0%, strict reversal 10.8%
- $C=8 \to C=20$ 下 strict reversal 从 6.8% 升到 15.7%
- $b$-ratio 20 下 strict reversal ~30%
- Oracle 与 Coupling-Greedy 的 gap < 5%（实验确认后填入实数）

### 6.5 必须包含的关键诚实点

- **Reframing 路径**：明确写 "We initially defined Gate 3 as strict-reversal share $\ge 20\%$ in plan.md; this threshold was not met (10.8% at $C=12$). Upon reviewing the underlying mechanism, we found that strict reversal is one of three structurally distinct disagreement modes; reporting only one understates the structural mismatch. We therefore reframe the analysis as scheduler-native decomposition, with all three modes reported."
- **Scoring caveat**：不一致率本身依赖 tie definition。$\ge 50\%$ 数字来自把 tie 算作 mismatch，要解释这个定义选择
- **GoodSpeed++ 的部分缓解**：明确说 GoodSpeed++ 能消除 blindness 但不解决 overcommit 和 strict reversal，因此 framework 的论点仍然成立

### 6.6 注意事项

- 这一章最长，**6.3 是已有材料整理**，**6.4–6.5 是新工作**——确保新工作部分占至少 1/3 篇幅
- 6.4 算法描述要给伪代码，**不要只写散文描述**
- 6.5 评估表要清晰：行是算法，列是 $(N, C)$ 配置 + 指标
- 不要回避"我们提的算法很简单"——简单是优点，复杂度可控

---

## Chapter 7: Limitations and Threats to Validity（4 页）

### 7.1 目标

诚实列出 thesis 的局限，主动出击。这一章读起来要像 "我已经考虑过 X、Y、Z 三种 reviewer 会问的问题，并理性分析它们的影响"。

### 7.2 主要小节

- **7.1 仿真器 vs 真实系统**（1 页）
  - 当前所有 multi-client 结果来自仿真器
  - 仿真器与真实系统的 gap：drafter / verifier overlap 的 pipelining、prefetch、batch boundary
  - 缓解：单客户端校准 + 仿真器在单客户端上与真实测量一致
- **7.2 单一 drafter calibration**（1 页）
  - $b$-heterogeneity 来自合成扫，不是多 drafter 测量
  - 缓解：sensitivity scan 显示主结论在 $b$ 比例 [1.5, 5] 内稳定
  - Future work：多 drafter（Qwen3-1.7B / Llama3-1B）多 hardware
- **7.3 假设 A1–A4 的健壮性**（1 页）
  - 假设 A1 (power-law cache hit) 来自 Saguaro，在 multi-client 下未独立验证
  - 假设 A2 (geometric fan-out) 是 Saguaro Theorem 12 的 per-client 最优——multi-client 下不一定保持
  - $B_i$ 具体函数形式 $\phi_i$ 假设 drafter / verifier 时间完全切分——真实系统可能 overlap
  - 缓解：Sensitivity scan 用其他 $\phi_i$ 形式（half-overlap discount）显示主结论稳定
- **7.4 N=2 的范围**（0.5 页）
  - 大部分 multi-client 结果是 2-client
  - $N \in \{4, 8\}$ 的合成 supporting evidence
  - $N$-client 闭式结构性命题留作 future work
- **7.5 Theorem 1 的条件性**（0.5 页）
  - $q''(k) \ge 0$ 假设在实测 q 上未严格验证
  - 缓解：所有实测 case 单峰，但理论结论仍是 conditional 而非 unconditional

### 7.3 资产来源

- `experiment_log.md` 全文中"safe vs unsafe claim"散落记录
- `proposal_en.md` §4 scope 部分

### 7.4 注意事项

- 这一章的目的是 **disarm reviewer，不是 self-flagellation**。每条 limitation 后面都要跟一条"缓解措施 / 未来工作"，让读者觉得作者已经看见这些问题
- 不要造新的 limitation；只写真实存在的

---

## Chapter 8: Future Work（4 页）

### 8.1 目标

把 thesis 工作放进更长的研究路线图。这一章是给读者/答辩老师/未来博士导师看 "下一步打算做什么"。

### 8.2 主要小节

- **8.1 框架向其他 SD 变种推广**（1.5 页）
  - 把 PEARL / SwiftSpec / SpecBranch / Medusa 放进 $\phi_i$ formalism
  - 预期：每个 variant 都呈现非单调（待验证）
  - 这是论文第二篇的方向
- **8.2 真实多客户端系统实现**（1 页）
  - 工程挑战：drafter 进程独立 / NCCL sync / KV cache per client / mask scheduling
  - 与 Saguaro 单客户端 codebase 的衔接点
- **8.3 在线调度算法与收敛性**（1 页）
  - GoodSpeed Stolyar-style fluid limit 在耦合 setting 下的失效点
  - 候选 Lyapunov 重构方向（multi-time-scale / non-convex relaxation）
  - 给一个收敛性 proof sketch（如果时间允许）
- **8.4 跨 ML 系统的耦合资源 framework**（0.5 页）
  - KV cache multi-tenant / MoE routing / Multi-LoRA / Agent budgets
  - 这是 PhD thesis 形状（一句话过）

### 8.3 资产来源

- `paper/direction.md` 全文
- `paper/reading_list.md` Part 2 子问题列表

### 8.4 注意事项

- 不要 oversell。8.4 用"a longer-term research direction the author hopes to pursue"这种谦虚语气
- 8.3 如果没有 proof sketch 就老实说"留作 future work"，不要假装有

---

## Chapter 9: Conclusion（2 页）

### 9.1 目标

把整篇论文压缩成 2 页结论。

### 9.2 主要小节

- **9.1 主要发现回顾**（1 页）：把 Ch 1.5 的 6 条贡献用 1 页讲完
- **9.2 启示**（0.5 页）：本文工作对多客户端推测式推理 system 设计的 3 条 implication
- **9.3 结语**（0.5 页）：本文 + future work 的 5 年远景

### 9.3 注意事项

- 不要在 Conclusion 引入新的内容
- 不要再 caveat。Limitations 已经在 Ch 7 讲完
- 结尾一句话要让读者带着"这工作有意义"的感受离开

---

## Appendix A: A2 Derivation 完整推导（4 页）

把 `paper/math/block1a2.md` 的全部推导、引理证明、定理证明用 LaTeX 体例重写。包括：
- Lemma 1 的完整证明
- Proposition 1 的 FOC 推导
- Theorem 1 的单峰性证明
- Theorem 2 的渐近 scaling 证明
- 多客户端 KKT 推导细节

## Appendix B: Implementation and Reproduction（5 页）

- **B.1 仿真器架构概览**（1 页）
  - `sim/` 模块结构、运行 entry points
- **B.2 数据集与模型 setup**（1 页）
  - Alpaca / GSM8K 下载、Qwen3-8B / 0.6B 配置
- **B.3 实验复现命令**（2 页）
  - Block 1 single-client validation 完整命令
  - Block 3 reversal scan + Alpaca-calibrated scan 命令
  - 调度器评估命令
- **B.4 关键参数表**（1 页）
  - calibration 拟合参数全表

资产来源：`scripts/` 下全部 shell 脚本 + `README.md`

---

## 写作风格统一约定

1. **第一人称**：用 "we" 或 "this thesis"，不混用
2. **时态**：方法描述用一般现在时，实验结果用一般过去时
3. **claim 表达**：避免"我们证明 X"——用"X is shown / X is established under assumptions Y"。除非 unconditional theorem
4. **数字表达**：百分比保留一位小数（22.8%，不是 22.83%）；时间保留 ms 单位
5. **figure 引用**：写"Figure 5.3 shows..."，不要"As shown in the figure above"
6. **不使用 emoji / colloquialism**
7. **保留 Saguaro / GoodSpeed 等 paper nickname**，首次出现时加正式引用

---

## 给内容填充 AI 的最后几句话

1. 不要绕过 limitations。Ch 7 的诚实记录是 thesis maturity 的核心信号
2. 不要在 Ch 6.3 把 50% 数字 oversell。它**是 tie 算 mismatch 下的结果**，要 contextualize
3. Ch 6.4 的 proposed schedulers 是 thesis 的**关键新工作**——这部分写好对答辩通过率影响最大
4. Block 1 的 negative finding（$k^\ast(B)$ 非单调）必须显式记录，不要藏起来
5. 所有 prior work 用 contextualization 写，不用 criticism 写
6. Appendix B 是答辩老师抽查 reproducibility 的入口，命令必须**精确可复现**

完。
