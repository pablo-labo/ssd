# idea.md (v4.1)

## Multi-Client SSD Scheduling under Time-Coupled Verifier–Drafter Dynamics

---

## 0. 相对 v4 的修改

v4.1 修正了一处重要的推理漏洞，并重新组织了 Section 2 和 Section 3 的表述。核心修改如下：

**漏洞修正。** v4 在讨论"scheduler 何时不填满 verifier 预算"时，只关注了 $\partial B_i/\partial k_i$（indirect 负效应），草率地得出"$k_i$ 小时加 $k_i$ 危险"的结论。这忽略了 $E_{\text{hit}}(k_i)$ 随 $k_i$ 单调递增的事实——小 $k_i$ 下 $E_{\text{hit}}$ 本身就小，再高的 $p_{\text{hit}}$ 也救不回来。

**修正后的结构。** $\tilde\mu_i^{\text{SSD}}(k_i)$ 在 $k_i$ 上呈 unimodal 形状，两头（极小 $k_i$ 和极大 $k_i$）都不是 scheduler 想去的地方：

- $k_i$ 小：$E_{\text{hit}}$ 太小，每次 cache hit 推进不了几个 token
- $k_i$ 大：$p_{\text{hit}}$ 崩，cache miss 断崖式惩罚主导

最优 $k_i^*$ 出现在两个效应边际相等的内部点，由 $(\alpha_i, r_i, a_i, b_i, T_V)$ 共同决定。这个修正让 v4 的核心结构更清晰而非更弱——reversal 的代数起源从"$\partial B_i/\partial k_i$ 的大小差异"升级到"$k_i^*(\cdot)$ 作为多参数函数的 ordering 差异"。

---

## 1. 问题

SSD (Speculative Speculative Decoding) 下的 multi-client 调度存在一个被现有工作同时忽略的 gap。

**GoodSpeed** 解决了 multi-client SD 下的 $k_i$ 分配，但它的服务曲线 $\mu_i(k_i) = (1-\alpha_i^{k_i+1})/(1-\alpha_i)$ 来自 SD 模型，在 $k_i$ 上单调递增。这让最优分配几乎总在边界 $\sum_i k_i = C$ 上，且分配只依赖 $\alpha_i$。

**Saguaro** 解决了 single-client SSD 下的 fan-out 形状（Theorem 12：geometric $F_k = F_0 \alpha^{k/(1+r)}$），但把 $k$ 视为固定超参，不作为调度变量，也不考虑 multi-client。

二者的合成并非简单拼接。SSD 改变了 scheduler 面对的资源结构：drafter 必须在 verifier 完成当前轮之前准备好下一轮的候选 cache，这个"准备"受 drafter 自身 compute 能力限制，而 drafter 的时间窗口**就是 verifier 的 wall time**。

这里产生了一个关键耦合：verifier wall time 既是 scheduler 试图压低的成本（决定 $k_i$），也是 drafter 可用的时间预算（决定每个 client 能准备多大的 cache $B_i$）。**进一步地**，在每个 client 内部 $\tilde\mu_i^{\text{SSD}}(k_i)$ 呈 unimodal——小 $k_i$ 和大 $k_i$ 系统都不想要，最优 $k_i^*$ 出现在内部。

GoodSpeed 只看到 $k_i$ 压 verifier 的一面，Saguaro 只处理 single-client 下 fan-out 展开，二者都没有处理**"multi-client 下每个 client 都有自己内部 $k_i^*$，且这些 $k_i^*$ 通过共享 $T_V$ 耦合"**这个结构。这就是本工作的建模和分析目标。

---

## 2. 系统模型

### 2.1 核心量定义

> **$B_i$（drafter 候选 outcome 数）。** $B_i$ 是 drafter 在当前轮为**下一轮**准备的 speculation 链数——每条对应一种可能的当前轮 verification outcome，每条长度为 $k_i$。drafter 实际解码的 token 数为 $k_i \cdot B_i$ 级别。$B_i$ **不是** draft token 总数，**不是** 主链之外的分支 token 量，也 **不是** 当前轮正在被验证的 $s^T$——那是历史决策。
> 
> client 内部按 Saguaro Theorem 12 自动展开 geometric fan-out $\{F_{i,j}\}_{j=0}^{k_i}$ 满足 $\sum_j F_{i,j} = B_i$，scheduler 不干预 fan-out shape。

### 2.2 决策变量

每个调度周期 $t$，scheduler 为每个 client $i \in \{1, \ldots, N\}$ 决定**唯一**变量：

$$k_i(t) \in \mathbb{Z}_+ \quad \text{（verifier 端 lookahead）}$$

$B_i$ 不是独立决策变量。在 Setting 3 下（独立 per-client drafter），让 drafter 闲着没有任何好处——让它满打满做对 client $i$ 有利、对其他 client 无害。因此 $B_i$ 由 drafter 时间预算自动取满：

$$B_i(\{k_j\}_j) = \left\lfloor \frac{T_V\!\left(\sum_j k_j\right) - a_i k_i}{b_i k_i} \right\rfloor_+$$

其中：

- $T_V(\cdot)$：verifier 对总 token load 的 wall time 函数
- $a_i$：drafter 每次 forward pass 的固定开销（与 $B_i$ 无关的部分，memory-bound 主导项）
- $b_i$：drafter 每次 forward pass 中每条候选链的边际时间（compute-bound 主导项）
- $\lfloor \cdot \rfloor_+ = \max(0, \lfloor \cdot \rfloor)$

**公式推导：** drafter 一轮做 $k_i$ 次 forward pass（串行深度），每次同时处理 $B_i$ 条链（并行宽度）。每次 forward pass 时间 $\tau_i^{\text{step}}(B_i) = a_i + b_i B_i$，总时间 $k_i \cdot (a_i + b_i B_i) \le T_V$，解出 $B_i$ 即得上式。分母 $b_i k_i$ 的物理含义是"每增加一条候选链的总时间成本（$k_i$ 步 × 每步每链 $b_i$）"。

### 2.3 约束

**Verifier 约束（全局）：**

$$\sum_i k_i(t) \le C$$

$C$ 是 verifier 在一个调度周期内可承受的最大 token load（沿用 GoodSpeed 定义）。

**关于此约束是否 binding：** 见 Section 3.2。不同于 GoodSpeed，最优解不必然在边界上。

---

### 2.4 服务曲线

Client $i$ 的 SSD 服务曲线（固定 $k_i, B_i$ 时）：

$$\mu_i^{\text{SSD}}(k_i, B_i, \alpha_i, r_i) = \frac{p_{\text{hit},i}(k_i, B_i, \alpha_i, r_i) \cdot E_{\text{hit},i}(k_i, \alpha_i) + (1-p_{\text{hit},i}) \cdot E_{\text{miss},i}(k_i, \alpha_i)}{L_i(k_i, B_i)}$$

代入 $B_i = B_i(\{k_j\})$ 得到耦合形式：

$$\tilde\mu_i^{\text{SSD}}(k_i, \{k_j\}_{j\neq i}) = \mu_i^{\text{SSD}}(k_i, B_i(\{k_j\}), \alpha_i, r_i)$$

> **Remark (Fan-out shape assumption).** 上式中的 $p_{\text{hit},i}(k_i, B_i, \alpha_i, r_i)$ 假设 client $i$ 内部采用 Saguaro Theorem 12 的 geometric-optimal fan-out shape $F_{i,j} = F_{i,0} \cdot \alpha_i^{j/(1+r_i)}$。此 shape 本身依赖 $\alpha_i$——acceptance rate 高的 client 自动将 fan-out 偏向深层（大 $F_K$），acceptance rate 低的 client 偏向浅层（大 $F_0$）。这部分 $\alpha_i$-依赖已被 folding 进 $p_{\text{hit}}(k, B, \alpha, r)$ 的函数形式，在 Section 2.5 的优化问题中不需要额外作为决策变量出现。
>
> **Remark (Drafter timing under geometric shape).** drafter 每步 forward pass 的 batch size 等于 $B_i = \sum_j F_{i,j}$（Saguaro 的 custom attention mask 将所有候选链从第一步开始并行推进），与 shape $\{F_{i,j}\}$ 的分布无关。因此 Section 2.2 的 drafter 时间约束 $k_i(a_i + b_i B_i) \le T_V$ 在 geometric shape 下仍然正确——drafter 时间只依赖 $B_i$ 总量，不依赖其 $\alpha_i$-induced shape。
>
> **Remark ($(\alpha_i, r_i)$ 的联合分布).** 本工作将 $\alpha_i$ 和 $r_i$ 作为独立参数进行解析分析，便于数学表达清爽。真实系统中二者并不独立：Saguaro Figure 3 的实测数据显示 $\alpha$ 高的 draft model 倾向于较陡的 power-law 衰减（$r$ 较大），因为 draft 与 target 分布更接近时，小 $F$ 就能命中。在数值实验中，$(\alpha_i, r_i)$ 从 Saguaro 实测的联合分布采样（见 Section 4 阶段 A 修订），而非独立扫描网格。

**关键性质 1（内部 unimodal）：** 固定 $\{k_j\}_{j\neq i}$，$\tilde\mu_i^{\text{SSD}}$ 作为 $k_i$ 的函数**在 $k_i$ 上 unimodal**，存在内部最优 $k_i^*$。$k_i^*$ 由两个效应的边际平衡决定：

- **$E_{\text{hit}}$ 效应（偏好大 $k_i$）：** cache hit 时每轮推进的 token 数 $E_{\text{hit}}(k_i) \approx (1-\alpha_i^{k_i+1})/(1-\alpha_i)$ 随 $k_i$ 单调递增，边际效益 $\partial E_{\text{hit}}/\partial k_i \propto \alpha_i^{k_i}$ 递减
- **$p_{\text{hit}}$ 效应（偏好小 $k_i$）：** $k_i$ 增大通过两条路径压低 $p_{\text{hit}}$——(a) geometric fan-out 摊薄；(b) drafter 时间限让 $B_i \propto 1/k_i$ 下降。cache miss 的断崖代价（Saguaro Corollary 16）让 $\tilde\mu^{\text{SSD}}$ 快速下降

$k_i^*$ 是 $(\alpha_i, r_i, a_i, b_i, T_V)$ 的函数——**不只依赖 $\alpha_i$**。这是本工作相对 GoodSpeed 最本质的建模差异。

**关键性质 2（非局部耦合 / positive externality）：** $\tilde\mu_i^{\text{SSD}}$ 通过 $B_i(\{k_j\})$ 依赖**所有** $k_j$。其他 client 增大 $k_j$ 拉长 $T_V$，间接让 client $i$ 获得更大 $B_i$。形式上：

$$\frac{\partial \tilde\mu_j^{\text{SSD}}}{\partial k_i} = \frac{\partial \mu_j^{\text{SSD}}}{\partial B_j} \cdot \frac{T_V'}{b_j k_j} > 0 \quad \forall j \neq i$$

这是 GoodSpeed（$\mu_i$ 只依赖 $k_i$）和 Saguaro（single-client）里都不存在的性质。

---

### 2.5 优化问题

$$\max_{\{k_i\}_i} \sum_i U\big(\tilde\mu_i^{\text{SSD}}(k_i, \{k_j\}_{j\neq i}, \alpha_i, r_i, a_i, b_i)\big)\quad \text{s.t.}\quad \sum_i k_i \le C,\ k_i \in \mathbb{Z}_+$$

其中 $U = \log$ 用于 proportional fairness（沿用 GoodSpeed）。

---

## 3. 技术贡献

### 3.1 贡献 A: 单 client 下 $\tilde\mu^{\text{SSD}}(k)$ 的 unimodality 和 $k^*$ 刻画

Saguaro Theorem 12 在**固定 $k$** 下解最优 $\{F_j\}$。本工作反向：**固定 drafter 时间预算** 下解最优 $k$。

Single-client 下 $T_V$ 是 $k$ 的函数，$B$ 被 $k$ 和 drafter 参数完全决定：

$$B(k) = \left\lfloor \frac{T_V(k) - ak}{bk} \right\rfloor_+$$

**目标结果（按强度排列）：**

- **A1（stretch）：** $\tilde\mu^{\text{SSD}}(k)$ 的 unimodality 严格证明 + $k^*$ 的渐近 scaling：
$$k^*(\alpha, r, a, b, T_V) = \Theta\!\left(\frac{\log B(k^*)}{\log(1/\alpha)}\right)$$
这是一个隐式方程（$B$ 与 $k$ 互相依赖），需要 fix-point 分析。

- **A2（target）：** $\tilde\mu^{\text{SSD}}(k)$ 的 unimodality（可能需数值辅助）+ $k^*$ 关于参数的 monotonicity 方向：
$$\frac{\partial k^*}{\partial \alpha} > 0, \quad \frac{\partial k^*}{\partial b} < 0, \quad \frac{\partial k^*}{\partial T_V} > 0$$
直观理解：$\alpha$ 高的 client 值得更长 lookahead；drafter 慢的 client 只能选较小 lookahead；verifier 时间多时可以 afford 更长 lookahead。

- **A3（fallback）：** 数值验证 unimodality，绘制 $k^*$ 关于 $(\alpha, a, b, T_V)$ 的 monotonicity 曲线。

**为什么这个贡献 Saguaro 没做：** Saguaro 中 $k$ 是 speculation lookahead 超参，per-workload 固定；$B$ 是 drafter 能力决定的固定预算。本工作中 $k$ 是 per-client per-round 调度变量，$B$ 由 $k$ 和时间预算隐式决定。**关键观察——$k^*$ 是多参数函数**——是 Saguaro 没提供的。

### 3.2 贡献 B: Multi-client 下 allocation reversal 的刻画

基于贡献 A，写 Lagrangian：

$$\mathcal{L}(\{k_i\}, \lambda) = \sum_i U(\tilde\mu_i^{\text{SSD}}) - \lambda\!\left(\sum_i k_i - C\right)$$

KKT 条件（对 $k_i$ 求导）：

$$\underbrace{U'(\tilde\mu_i) \frac{\partial \tilde\mu_i}{\partial k_i}}_{\text{自身边际（内部 unimodal）}} + \underbrace{\sum_{j\neq i} U'(\tilde\mu_j) \frac{\partial \tilde\mu_j}{\partial k_i}}_{\text{externality（正）}} = \lambda$$

**关键代数观察：** 自身边际项本身在内部最优 $k_i^*$ 处为零（由 unimodal 性质）。所以 FOC 的解平衡的是：

$$\underbrace{U'(\tilde\mu_i) \frac{\partial \tilde\mu_i}{\partial k_i}}_{\text{可正可负}} = \lambda - \underbrace{\sum_{j\neq i} U'(\tilde\mu_j) \frac{\partial \tilde\mu_j}{\partial k_i}}_{\text{正}}$$

这产生两种可能的平衡态：

- **Binding regime（$\lambda > 0$）：** 最优 $k_i$ 处自身边际为正（$k_i < k_i^*$），verifier 约束紧。此时扩大 $k_i$ 仍然对 $i$ 自己有益，只是被 verifier 预算限制。
- **Non-binding regime（$\lambda = 0$）：** 最优 $k_i$ 处自身边际为负（$k_i > k_i^*$），意味着**系统在给 $i$ 分配"超出其自身最优"的 $k_i$，只为了通过 externality 帮助别人**。此时 verifier 约束未满。

**Signature result（目标）：** 存在参数区域 $\mathcal{R} \subset \{(\alpha_i, r_i, a_i, b_i)\}_i$，在该区域内 GoodSpeed 的分配与本工作的联合分配给出**严格相反**的 ordering。

**直观例子。** Client A 有高 $\alpha_A$ 但 drafter 慢（$b_A$ 大），client B 有较低 $\alpha_B$ 但 drafter 快（$b_B$ 小）。GoodSpeed 只看 $\alpha$，倾向把 $k$ 分给 A；但 A 的 $k_A^*$ 受 $b_A$ 压制较小，过多的 $k_A$ 让 $A$ 跌到 $k_A^*$ 右侧（$p_{\text{hit}}$ 崩）；B 的 $k_B^*$ 较大，能 afford 更多 $k$。最优调度可能 reversed。

### 3.3 贡献 C: 时间耦合下的在线调度算法 + 收敛性

设计在线算法 **SSD-Sched**，估计 $(\hat\alpha_i, \hat r_i, \hat a_i, \hat b_i)$ 并在每轮求解 Section 2.5 的约束优化。证明：

- 在 stationary 极限下，SSD-Sched 收敛到问题的最优解
- 证明路径：扩展 GoodSpeed 的 Stolyar fluid sample path 框架到**非单调目标 + 非局部耦合**情形

**相对 GoodSpeed 证明的主要技术挑战：**

1. Stolyar 原框架依赖目标在可行域边界取极值。Setting 3 下最优可能在内部（non-binding regime），需要修改 Lyapunov 构造以处理内部 KKT 点。
2. $\tilde\mu_i^{\text{SSD}}$ 依赖所有 $\{k_j\}$，fluid dynamics 不再 decouple per client。需要证明 coupled ODE system 的全局收敛性。
3. 参数估计 $\hat a_i, \hat b_i$ 引入额外 stochastic noise，需要两时间尺度 stochastic approximation 论证。

**Fallback：** 若 full fluid analysis 推不通，降级到 toy setting 下的数值收敛 + 实证验证。

---

## 4. 实验计划（6 个月）

### 阶段 A（Month 1）：Feasibility check via simulator

纯 simulator，确认：

- $\tilde\mu_i^{\text{SSD}}(k_i)$ 的 unimodality 在 $k_i$ 上确实成立，$k_i^*$ 随 $(\alpha_i, b_i)$ 的 monotonicity 符合 A2 预期
- Allocation reversal region $\mathcal{R}$ 在现实参数范围内**不是测度零集**
- Non-binding regime 的存在性（是否有参数下 $\lambda = 0$）

**参数采样协议：**

- **阶段 A.1（纯合成，1 周）：** 独立扫 $(\alpha_i, r_i, a_i, b_i)$ 的笛卡尔积，用于快速定位 unimodality 曲线形态和 $k_i^*$ 的 monotonicity 方向。此阶段不要求参数组合"物理真实"，只检查建模的数学结构。
- **阶段 A.2（半真实联合分布，2-3 周）：** 从 Saguaro 公开的 Figure 3 实测数据拟合 $(\alpha, r)$ 的联合经验分布，从该分布里采样生成 client profile；$(a, b)$ 则从 Saguaro Appendix B 的 timing 数据拟合。在此 calibrated 分布下重跑 reversal region 实验。
- **阶段 A.2 是 Gate 1 的判据依据**，不能用阶段 A.1 的结果 gate，因为 $(\alpha, r)$ 独立扫描会生成真实系统不会出现的参数组合，可能虚假地放大或缩小 $\mathcal{R}$。

**Gate 1：** 如果阶段 A.2 下 $\mathcal{R}$ 太窄或不存在，pivot 到 "externality 在调度中的显式利用" 为 signature（放弃 reversal claim，保留 externality 作为核心发现）。


### 阶段 B（Month 2–3）：Saguaro-based calibration

在 Saguaro 开源 repo 上扫 $(k, B)$ grid，拟合真实参数：

- $p_{\text{hit},i}(k, B)$ 曲线（验证 power-law 假设在 multi-client batch 下是否仍成立）
- per-client $(\alpha_i, r_i, a_i, b_i)$ 的分布和异质性
- $T_V(\sum_j k_j)$ 的实测 shape

此阶段产出真实参数分布，喂给阶段 A 的 simulator 重跑，检查 reversal 是否在真实参数区域出现。

**Gate 2：** 若真实参数下 reversal 消失，考虑弱化 signature result 到 monotonicity-based 贡献。

### 阶段 C（Month 4–5）：Multi-client SSD 原型

在 Saguaro 基础上实现 multi-client 支持：

- $N$ 个 draft 进程与单 verifier 的 NCCL 协调
- per-client $k_i$ 动态调整
- drafter 时间 budget 的在线监测
- SSD-Sched 实现

### 阶段 D（Month 6）：Predicted-region 实验

- 在阶段 B 确定的 $\mathcal{R}$ 内外各选 workload
- 对比：SSD-Sched vs GoodSpeed-over-Saguaro vs Fixed-$k$ vs Oracle
- 验证：$\mathcal{R}$ 内显著 gap（预期 ≥ 20%），$\mathcal{R}$ 外 gap 接近零
- **关键：reversal region 从理论 $\mathcal{R}$ 预测，不是事后挑的**

**Ablations：**

- 关闭 externality（让 scheduler 忽略第二项 KKT 贡献）
- 强制 $\sum k_i = C$（测试"非 binding"结论的实际 gain）
- 扫 $b_i$ 异质性程度，看 reversal 随异质性的 scaling
- 人工固定 $k_i$ 到各 client 的 $k_i^*$（测试 "ignore externality" 的代价）

---

## 5. 相对工作定位

| 工作 | Multi-client | SSD | $k$ 调度 | $B$ 建模 | Verifier–drafter 耦合 | $k^*$ 多参数 |
|---|---|---|---|---|---|---|
| GoodSpeed | ✓ | ✗ | ✓ | ✗ | ✗ | ✗（只依赖 $\alpha$） |
| Saguaro | ✗ | ✓ | ✗ | 固定 | ✗ | 不适用 |
| SpecBranch / SwiftSpec | ✗ | 部分 | ✗ | ✗ | ✗ | ✗ |
| AdaServe | ✓ | 部分 | 部分 | ✗ | ✗ | ✗ |
| **本工作** | **✓** | **✓** | **✓** | **$k$ 的隐函数** | **✓** | **✓（$(\alpha, r, a, b)$ 多维）** |

**被 scoop 风险：** Saguaro conclusion flag 了 "cluster-level sharing speculation endpoints" 作为 future work，但倾向 Setting 2（共享 drafter pool）。本工作选 Setting 3（独立 drafter + 时间耦合），核心理论不同：前者是 shared-resource scheduling，后者是**非局部 externality + 内部 unimodal $k^*$**。理论贡献独立。

---

## 6. 风险与 fallback

| 风险 | 影响 | Fallback |
|---|---|---|
| 贡献 A 精确 scaling 推不出 | 中 | 降级到 A2（unimodality + monotonicity 方向） |
| 阶段 A 发现 $\mathcal{R}$ 过窄 | 高 | pivot 到 "externality 在调度中的显式利用" 为 signature |
| $\tilde\mu^{\text{SSD}}(k)$ 在某些参数下非 unimodal（如 bimodal） | 中 | 重新审视 $\tilde\mu^{\text{SSD}}$ 的建模，bimodal 本身可能是新的 insight |
| 阶段 B 发现 power-law 假设在 multi-client 下失效 | 中 | 改用经验 $p_{\text{hit}}$ 曲线 + 保留 unimodality |
| 阶段 C multi-client infra 工程量超预算 | 中 | 退到 simulator + Saguaro single-client validation |
| Non-binding regime 在现实下很少发生 | 中 | 改称 "near-binding regime" 并量化 slack，仍保留 reversal claim |
| Saguaro 团队先做 multi-client 扩展 | 低 | 理论独立 |
| 贡献 C fluid analysis 推不通 | 中 | toy 下收敛证明 + 实证 |

---

## 7. 目标场地

**主要目标：SIGMETRICS 或 NeurIPS（理论 + 系统并重）**

Setting 3 的核心吸引力在时间耦合、internal unimodal $k^*$、positive externality 三者共同带来的非平凡调度理论。SIGMETRICS 对这类 scheduling theory + 真实系统 validation 友好；NeurIPS 接受 convergence proof + allocation reversal 的结构性刻画。

**次要目标：MLSys**

若阶段 C 工程干净、端到端 speedup 显著，MLSys 可作为备选。

---

## 8. 一句话定位

> GoodSpeed 在 SSD 下失效，不是因为 $k$ 不适合作为调度变量，也不是因为需要再加一个调度变量 $B$。真正的变化是：SSD 下每个 client 的服务曲线 $\tilde\mu_i^{\text{SSD}}(k_i)$ 呈 unimodal——存在内部最优 $k_i^*$ 使得过小或过大的 $k_i$ 都让系统变差。$k_i^*$ 由 $(\alpha_i, r_i, a_i, b_i, T_V)$ 多参数共同决定，不只看 $\alpha_i$。多个 client 的 $k_i^*$ 通过共享 verifier wall time $T_V$ 耦合，产生 GoodSpeed 没有的 positive externality。本工作刻画这套耦合结构，设计匹配的在线调度算法，并给出非平凡收敛性分析。



---

# idea.md (v4.1, revised)

以下只列出相对 v4.1 的修订部分，其他章节不变。两处修订，都很小。

---



## Section 4 阶段 A 修订

