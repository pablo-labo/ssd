# 面向 Speculative Speculative Decoding 的多客户端调度：问题建模与结构性分析

## 硕士学位论文开题报告

---

## 1. 研究背景与问题

大语言模型 (LLM) 的推理延迟长期受自回归解码的串行性制约。Speculative Decoding (SD)[Leviathan et al., 2023] 通过轻量 draft 模型生成候选 token、由大模型并行验证的方式缓解这一瓶颈。近期提出的 Speculative Speculative Decoding (SSD)[Kumar et al., 2026] 进一步将 drafting 与 verification 解耦到异步执行，在 verifier 工作期间 drafter 预先为多种可能的验证结果准备 speculation cache，命中时无需再次 drafting 即可进入下一轮验证。SSD 在 single-client 设定下相对 SD 取得最高 2× 的端到端加速。

在服务多用户的边缘推理系统中，多个 draft 服务器共享一个 verifier 的场景已被研究。GoodSpeed[Tran et al., 2025] 将此场景建模为效用最大化问题，以 verifier token budget $C$ 为约束，通过梯度调度算法为每个 client 分配 speculation 长度 $k_i$，并证明了在 fluid limit 下的收敛性。GoodSpeed 的服务曲线基于 SD 模型：$\mu_i(k_i) = (1-\alpha_i^{k_i+1})/(1-\alpha_i)$，在 $k_i$ 上严格递增。

然而，GoodSpeed 的调度模型和 SSD 的系统机制之间存在未被研究的结构性缺口。本工作的核心观察是：**在 SSD 系统下直接应用 GoodSpeed 式线性调度无法充分刻画系统真实瓶颈，因为 drafter 侧的候选 outcome 容量 $B$ 与 verifier 侧的 lookahead $k$ 不再独立，而是通过 verifier wall time 形成非局部耦合**。

具体而言：

- drafter 必须在 verifier 完成当前轮之前准备好下一轮的候选 cache
- drafter 的时间预算等于 verifier wall time $T_V(\sum_j k_j)$
- 因此每个 client $i$ 的 cache 容量 $B_i$ 不是独立参数，而是所有 client lookahead $\{k_j\}$ 的隐函数

这个耦合让 client $i$ 的有效服务曲线 $\mu_i^{\text{SSD}}$ 呈现两个 GoodSpeed 模型不具备的性质：

1. **非单调性**：$\mu_i^{\text{SSD}}$ 在 $k_i$ 方向不再单调递增——$k_i$ 增大虽然提升 cache hit 下的 token 产出 $E_{\text{hit}}$，但同时压低 drafter 能准备的 $B_i$，降低 cache hit 率 $p_{\text{hit}}$，miss 时的断崖式延迟惩罚使总体效用可能下降
2. **非局部耦合**：$\mu_i^{\text{SSD}}$ 通过 $B_i(\{k_j\})$ 依赖所有其他 client 的决策——其他 client 增大 $k_j$ 让 verifier 变慢，反而给 client $i$ 的 drafter 更多时间

这两个性质使得 GoodSpeed 的调度策略在 SSD 场景下可能系统性次优：最优调度可能出现与 GoodSpeed 严格相反的 allocation 排序 (allocation reversal)，且最优解可能不在 verifier 约束的边界上取得。

## 2. 研究内容与目标

本论文聚焦多客户端 SSD 调度问题的**问题建模与结构性分析**。具体工作内容分为三部分。

### 2.1 问题建模

建立 multi-client SSD 下的调度问题的形式化描述。决策变量为每个 client 的 lookahead $k_i$，约束包括：

- 全局 verifier 容量约束：$\sum_i k_i \le C$
- drafter 时间耦合：每个 client 的 cache 容量 $B_i = B_i(\{k_j\})$ 由 verifier wall time 决定

服务曲线 $\mu_i^{\text{SSD}}(k_i, B_i(\{k_j\}), \alpha_i, r_i)$ 综合 cache hit/miss 情形，在 Saguaro 提出的 power-law cache hit rate 和 geometric fan-out 假设下具有可分析形式。优化目标沿用 GoodSpeed 的 proportional fairness 形式 $\sum_i \log \mu_i^{\text{SSD}}$。

### 2.2 结构性分析

在该建模下推导以下结构性结论：

**(a) 单 client 性质**：$\mu^{\text{SSD}}(k)$ 在 $k$ 方向的 unimodality 和最优 $k^*$ 关于参数 $(\alpha, b)$ 的单调方向；

**(b) 多 client KKT 分析**：写出 Lagrangian KKT 条件，识别 GoodSpeed 中不存在的 positive externality 项（$k_i$ 增大通过拉长 $T_V$ 补偿其他 client 的 $B_j$）；

**(c) Allocation reversal 条件**：刻画参数区域 $\mathcal{R}$，在该区域内 GoodSpeed 的 $k_i$ 分配与本建模下的最优分配给出相反的排序；

**(d) Verifier 约束非 binding 条件**：识别最优解严格小于 verifier 容量的参数区域。

### 2.3 Simulator 实证

设计离散时间 SSD simulator，在合成参数和基于 Saguaro 实测的真实参数下：

- 数值验证 2.2 中的结构性结论
- 测量 GoodSpeed 与本建模下最优策略的效用差距
- 扫描参数空间，定位 reversal region $\mathcal{R}$ 在现实参数下的大小

## 3. 研究方法

### 3.1 理论方法

以 GoodSpeed 的 Stolyar fluid sample path 框架为起点，以 Saguaro 的 power-law cache hit 和 geometric fan-out 假设为 closed-form 基础，对 $\mu_i^{\text{SSD}}$ 的耦合结构进行 Lagrangian KKT 分析。考虑到耦合约束带来的解析复杂度，计划在 2-client toy case 下给出闭式或半闭式结果，在 N-client 情形下给出结构性（unimodality、monotonicity）结论。

### 3.2 实验方法

**Simulator 实现**：基于 Python 实现离散时间 simulator，包含 verifier 容量、drafter 时间约束、fan-out 展开、cache hit/miss 动力学。Simulator 不依赖真实 LLM，运行代价低，支持参数网格扫描。

**参数校准**：从 Saguaro 论文公开实验数据（Figure 3、4、Appendix B）提取 $(\alpha, r)$ 和 verifier wall time 的实测分布，用于 simulator 的 realistic 参数设置。

**对比方法**：GoodSpeed（线性 $k$ 分配）、Fixed-$k$ 均分、Oracle（暴力搜索最优）、本工作的 KKT-driven 调度。

## 4. 研究计划

| 周次 | 工作内容 | 交付物 |
|---|---|---|
| 0 | Literature mapping, 开题报告完稿 | 本报告 |
| 1-2 | 2-client toy case 数学推导 + 基础 simulator | Technical note, reversal region 初步图 |
| 3-4 | N-client simulator + 真实参数校准 | 扩展 simulator, 参数敏感性分析 |
| 5-6 | 论文写作 | 硕士论文初稿 |

每阶段结束设 gate 检查点：若 Week 2 发现 reversal region 近乎空，立即将论文重新定位为"多客户端 SSD 调度的结构性限制"的 negative result 论文，此时工作产出（formulation + simulator + 不存在性的实证）仍完整。

## 5. 预期贡献与局限

### 预期贡献

1. 识别并形式化 multi-client SSD 调度中的时间耦合和 positive externality 结构，填补 GoodSpeed（multi-client + SD）和 Saguaro（single-client + SSD）之间的建模空缺
2. 给出 2-client toy case 下的闭式或半闭式结构性结论
3. 提供 simulator-based 实证，定位 allocation reversal 出现的参数区域

### 已知局限

本论文**不包含**以下内容，作为后续工作的起点：

- **多客户端 SSD 真实系统实现**：受时间所限，本论文以 simulator 验证为主。基于 Saguaro 开源代码的真实多客户端系统原型将作为直接后续工作进行
- **收敛性严格证明**：在非单调目标函数和耦合约束下，GoodSpeed 的 Stolyar-style fluid 证明需非平凡扩展。本论文给出收敛性的数值证据和证明路径 sketch，完整证明留作后续
- **Drafter 共享设定 (Setting 2)**：本论文聚焦 per-client 独立 drafter（Setting 3），共享 drafter pool 场景下资源结构不同，留作独立方向

这些局限已形成明确的 follow-up plan，作者已开始相关初步工作。

## 6. 参考文献

[1] Tran, P., Liu, T.-H., Le, L. T., et al. GoodSpeed: Optimizing Fair Goodput with Adaptive Speculative Decoding in Distributed Edge Inference. arXiv:2512.09963, 2025.

[2] Kumar, T., Dao, T., May, A. Speculative Speculative Decoding. arXiv:2603.03251, 2026.

[3] Leviathan, Y., Kalman, M., Matias, Y. Fast inference from transformers via speculative decoding. ICML 2023.

[4] Stolyar, A. L. On the asymptotic optimality of the gradient scheduling algorithm for multiuser throughput allocation. Operations Research, 2005.

[5] Li, Z., Chen, Z., et al. AdaServe: Accelerating Multi-SLO LLM Serving with SLO-Customized Speculative Decoding. arXiv:2501.12162, 2025.
