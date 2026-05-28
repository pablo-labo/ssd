# scheduler_design.md (v1)

## Coupling-Aware Multi-Client SSD Scheduler: Marginal-Gain Allocation

本文件把调度器设计固化下来，承接 `idea.md` (v4.1) 的 unimodal 结论与
`thesis_outline.md` 的符号约定。核心立场一句话：

> **承重墙是单峰服务曲线，不是耦合。** 调度器 = "GoodSpeed 那个边际贪心，
> 外加一条 `边际变成非正就停`"。分情形、峰顶封顶、water-filling 在数学上是
> 同一条规则的三个侧影。耦合只是 $T_V$ 上一个 ~5% 的二阶修正。

---

## 0. 符号与范围

沿用 `thesis_outline.md`：

- $k_i \in \mathbb{Z}_{\ge 0}$：客户端 $i$ 的 verifier 端 speculative lookahead（**决策变量**）
- $B_i(\{k_j\})$：客户端 $i$ 的 drafter fan-out 预算（**导出变量**，耦合通过它进入）
- $T_V(S)$：verifier wall-time，$S=\sum_j k_j$ 为聚合负载
- $a_i, b_i$：drafter 时间成本系数（per-depth, per-fanout）
- $\alpha_i$：token acceptance rate（**唯一的实时信号**，见 §9）
- $r_i$：cache-hit power-law 指数
- $C$：verifier 总容量约束，$\sum_i k_i \le C$
- $\mu_i^{\text{SSD}}(k)$：SSD-aware 服务曲线（**unimodal**）
- $\mu_i^{\text{GS}}(k) = (1-\alpha_i^{k+1})/(1-\alpha_i)$：GoodSpeed monotone 服务曲线（= $e_{\text{hit}}$）

标定锚点（Alpaca / Qwen3-8B+0.6B，见 `scripts/run_block3_alpaca_calibrated_scan.sh`）：
$r=0.6,\ a=2.6285,\ b\in[0.0038,0.077],\ T_V=19.613+0.09437\,S$，中心 $\alpha\approx0.735$。

---

## 1. 底层：服务曲线 $\mu_i^{\text{SSD}}(k)$ 从哪里算

给定 $(\alpha_i, r_i, a_i, b_i, T_V)$，吞吐由下面这条闭式链算出，每步对应
`sim/ssd_math.py` 的一个函数（**这就是"从哪里计算"的入口**）：

$$\beta = \alpha^{1/(1+r)} \qquad\texttt{beta()}$$

$$B(k) = \frac{T_V - a\,k}{b\,k} \qquad\texttt{budget\_b()}$$

$$D(k) = \beta^{k}(1-\alpha)^{-1/(1+r)} + \frac{1-\beta^{k}}{1-\beta} \qquad\texttt{fanout\_denominator()}$$

$$f_0(k) = B(k)/D(k) \qquad\texttt{fanout\_f0()}$$

$$p_{\text{hit}}(k) = 1 - f_0(k)^{-r}\Big[(1-\alpha)^{r/(1+r)}\beta^{k} + (1-\alpha)\tfrac{1-\beta^{k}}{1-\beta}\Big] \qquad\texttt{phit\_primary()}$$

$$e_{\text{hit}}(k) = \frac{1-\alpha^{\,k+1}}{1-\alpha} \qquad\texttt{e\_hit()}$$

$$\boxed{\ \mu_i^{\text{SSD}}(k) = \frac{p_{\text{hit}}\,e_{\text{hit}} + (1-p_{\text{hit}})\,e_{\text{miss}}}{p_{\text{hit}}\,l_{\text{hit}} + (1-p_{\text{hit}})\,l_{\text{miss}}}\ },\quad l_{\text{miss}}=l_{\text{hit}}+t_b \qquad\texttt{mu\_ssd\_from\_parts()}$$

可行域 $K_i=\{1,\dots,k_i^{\max}\}$ 由三个有效性条件界定（见 `curve_point()`）：
$B(k)>0$（即 $k<T_V/a$）、最小 fanout $\ge 1$、$p_{\text{hit}}\in[0,1]$。
运行时 `curve()` 输出 $\{\mu_i(k)\}$ 数组，`curve_summary()` 取 argmax 给 `best_k`。

**对比锚点。** GoodSpeed 的服务曲线在本约定下就是 $\mu^{\text{GS}}=e_{\text{hit}}$，
单调递增且离散凹（差分 $\alpha^{k+1}>0$ 恒正）。我们的 $\mu^{\text{SSD}}$ 因为
$p_{\text{hit}}$ 随 $k$ 崩塌而**单峰**。两条曲线的差别就是 unimodal 修正的全部来源。

---

## 2. 分配问题

$$\max_{\{k_i\}}\ \sum_{i=1}^{N} U_i(k_i)\quad\text{s.t.}\quad \sum_i k_i \le C,\ \ k_i\in\mathbb{Z}_{\ge0}$$

效用 $U_i$ 是插件：总吞吐取 $U_i=\mu_i^{\text{SSD}}$；比例公平取 $U_i=w_i\log\mu_i^{\text{SSD}}$。
两者下文要用的凹性在标定曲线上都验证过（§10）。

---

## 3. 边际增益，与"峰顶"的代数起源

$$\Delta_i(k) = U_i(k) - U_i(k-1),\quad k=1,2,\dots$$

**经验事实（§10 验证）：** 上升段 $\Delta_i(k)$ 单调不增（离散凹），过峰顶后 $\le 0$。
于是峰顶不是单独求的，它是边际的变号点：

$$k_i^\* = \max\{k:\Delta_i(k)>0\} = \arg\max_k \mu_i^{\text{SSD}}(k)$$

渐近（`idea.md`）：$k_i^\* \sim r\,\log T_V / \log(1/\alpha)$。**$k^\*$ 由 $\alpha$ 主导，
对 $T_V$ 几乎不敏感**——实测耦合带 $T_V:19.80\!\to\!20.75$ 下，$k^\*$ 在 22 个
$\alpha$-格中 18 个完全不变、其余仅 $\pm1$；$T_V$ 拉 8 倍才挪 1–2 步
（见 `kstar_sensitivity.png`）。

---

## 4. 主方案：边际贪心（带箱 water-filling 的精确整数解）

```
k_i ← 0  for all i
heap ← 大根堆，键 = 每个 client 的下一份边际 Δ_i(k_i + 1)
repeat at most C times:
    i* ← argmax_i Δ_i(k_i + 1)            # pop 堆顶
    if Δ_{i*}(k_{i*}+1) ≤ 0: break        # 没人再赚 → 余下容量故意空着
    k_{i*} ← k_{i*} + 1
    push Δ_{i*}(k_{i*}+1)
return {k_i}
```

**精确性（命题）。** 当各 $U_i$ 在 $[0,k_i^\*]$ 上离散凹（$\Delta_i$ 不增）且目标可分离时，
上述贪心给出问题 §2 的**全局整数最优解**。证明用交换论证：边际不增时，任何把一份
从高边际处移到低边际处的重排都不增加目标。

**为什么它吃掉了分情形。** "装得下 / 装不下"是同一个贪心的两种结局：
- $C$ 大 → 先取光所有正边际，每人停在 $k_i^\*$，余量自动空置（剩余边际 $\le0$ 不被弹出）；
- $C$ 小 → 容量先耗尽，停在上升段 = water-filling。

**峰顶封顶不是写进去的规则**，而是 $\Delta_i\le0$ 的份永不被选。

---

## 5. 对偶视角：单一影子价 = water-filling

连续松弛，给容量约束配 $\lambda\ge0$，带箱 $0\le k_i\le k_i^\*$，KKT：

$$U_i'(k_i)=\lambda\ (\text{内点}),\qquad k_i=k_i^\*\ \text{若}\ U_i'(k_i^\*)>\lambda$$

抬高水位 $\lambda$ 直到 $\sum_i k_i=C$。$\lambda=0$ → 人人到峰顶；$\lambda>0$ → 上升段注水。
§4 的离散贪心就是它的精确整数实现：**最后发出去那一份的边际值 $=\lambda$。**

---

## 6. 与 GoodSpeed 的关系：一行之差

GoodSpeed（本文建模为 $\mu^{\text{GS}}=e_{\text{hit}}$，单调）喂进**同一个** §4 贪心时，
其边际 $\Delta^{\text{GS}}(k)=\alpha^{k+1}>0$ **恒正**，于是 `break` 永不触发——它会一直
把容量塞到 $k$ 超过真实峰顶，这正是 overcommit / 不可行 / 吞吐悬崖的代数起源。

> **我们与 GoodSpeed 的唯一差别：边际会转负，于是会停。** 那个负号就是单峰修正。
> 当某 client 的 $\mu^{\text{SSD}}$ 在可行域内恰好单调（无内部峰）时，本方案逐字退化为
> GoodSpeed。故本方案是 GoodSpeed 的严格泛化。

*待核（见 §10 audit）：* 此处"一行之差"是在**本文 service model** 层面成立的；
GoodSpeed 原文的实际分配算法/目标需引文核对后再在正文断言。

---

## 7. 耦合：外层不动点（二阶修正）

$T_V$ 依赖 $S=\sum_j k_j$，故严格说 $\mu_i$ 不可分。处理为外层不动点：

$$T_V^{(0)}=\text{base}\to \text{贪心}\to S^{(0)}\to T_V^{(1)}=\text{base}+\text{slope}\cdot S^{(0)}\to\text{重算曲线}\to\dots$$

**诚实标注：** 这一层让解自洽，但 (i) 不提供全局最优证明（耦合下目标不可分，贪心精确性
失效）；(ii) 收敛性未证。靠的是耦合仅 ~5%、峰顶最多挪 $\pm1$ 的经验事实，通常 1–2 轮稳。
在实测范围可整步跳过，误差 $<$ 一个 $k$ 台阶。

---

## 8. 复杂度与计算入口

- 曲线：$O(N\,k_{\max})$，$k_{\max}\le 7$（标定下），极小。
- 贪心：$O\big((\sum_i k_i)\log N\big)$。
- 计算起点：`ssd_math.curve()` 给出每 client 的 $\mu_i(k)$ 数组；调度器是其上的
  **一阶差分 + 大根堆**，不重算闭式链。给定 $\alpha_i$，边际序列可查表。

---

## 9. 在线行为：由 $\alpha_i$ 驱动，事件触发

运行时输入分三档：
- $r,a,b$：标定常数，不变。
- $\alpha_i$：**唯一实时信号**。每个 verify step 观察"提议被接受几个"，EMA 平滑。
  $\alpha_i$ 变 → $\mu_i$ 曲线变 → 边际变 → $k_i^\*$ 挪。
- $S$：聚合负载，仅经 $T_V$ 以 ~5% 进入（§7），配角。

**重算是事件驱动，不是每 token：** 仅当 (a) 活跃 client 集合 / $C$ 份额变化，或
(b) 某 $\alpha_i$ 漂到跨越一个整数边界时，才重跑分配。$k$ 是小整数且对扰动稳，
多数时刻分配不动。

---

## 10. 精确性条件与 overclaim 自查

主方案的"精确最优"是**带条件**的，正文必须带上三个限定词：

1. **对模型精确，非对真机精确。** 凹性是 `ssd_math` 解析模型的性质；真实 $\mu(k)$ 可能更毛糙。
2. **要求可分离（无耦合）。** 耦合下贪心退化为近似，靠 5% 小量兜底（§7），非证明。
3. **凹性是有限网格上验证的经验规律，非普适定理。**

**已验证（`sim/ssd_math.py` 模型，标定网格）：** 上升段 $\Delta_i$ 单调不增（离散凹）
在 33/36 配置成立，其余 3 例是峰顶在 $k=2$ 点数不足、非违反；$\mu$ 与 $\log\mu$ 两个
目标都凹。

**护栏：** 上线前对每条标定曲线查"上升段边际是否递减"。单峰 $\ne$ 上升段凹，须分开查
（代码已有 `is_discrete_unimodal`，需另加凹性检查）。若某曲线不凹 → 主贪心退化为启发式，
改用 §11-B 的 DP 兜底。

**守得住的硬结论：** *在标定域内、忽略 ~5% 耦合的前提下，边际贪心对解析模型给出精确整数
最优解，且严格退化回 GoodSpeed。*

---

## 11. 其他方法（候选与权衡）

| 方法 | 假设 | 复杂度 | 最优性 | 角色 |
|---|---|---|---|---|
| **A. 连续 water-filling（对 $\lambda$ 二分）** | 凹 + 可分离 | $O(N\log\frac1\varepsilon)$ | 连续最优，取整后有边界误差 | 理论陈述（§5 的连续形） |
| **B. DP / 有界背包** | 仅需有限 $C,k_{\max}$ | $O(N\,C\,k_{\max})$ | **任意 $U_i$ 精确**（不需凹） | 凹性失效时的稳健兜底 |
| **C. MILP / 精确求解器** | 无 | 指数最坏 | 精确 | 实验中的 ground-truth oracle |
| **D. 指数 / Whittle 策略** | 可分离 | $O((\sum k_i)\log N)$ | 等价于 §4 | 理论框架（边际 $\Delta_i$ 即 index） |
| **E. GoodSpeed** | 单调服务 | water-filling | 仅单调下最优，会越顶 | 主 baseline，被本方案泛化 |
| **F. 主方案：边际贪心** | 凹 + 可分离 | $O((\sum k_i)\log N)$ | 条件精确（§10），退化回 E | **承重墙** |

要点：

- **A 与 F 同解**，A 是 F 的连续影子；因 $k$ 是小整数，F 的离散形更干净、无取整修复。
- **B 是最诚实的精确法**：它不依赖我只在有限网格上验证过的凹性假设，即使真机 $\mu(k)$
  非凹/多峰也精确。代价是 $O(N\,C)$ 与失去闭式结构。**建议作为论文的稳健性对照 + F 的退路。**
- **C** 只用于离线验证 F/B 的最优性，不进运行时。
- **D** 给 F 一个理论家园：边际 $\Delta_i(k)$ 就是一个 Gittins/Whittle 式 index，
  "每次服务最高 index"即 F。可在相关工作里挂靠 restless-bandit 文献。
- **F vs E** 是核心对照实验（disagreement / reversal 分析，见 `idea.md`）。

---

## 12. 建议

主线用 **F（边际贪心）** 做承重墙：闭式、$O((\sum k_i)\log N)$、能退化回 GoodSpeed、
踩在被验证的 unimodal 凹性上。用 **B（DP）** 作稳健精确退路与 robustness 对照（摆脱凹性
假设），**C（MILP）** 作离线 oracle，**E（GoodSpeed）** 作 baseline，**D** 作理论框架。
耦合作为 §7 的二阶不动点写，并明确标注其量级标定依赖、实测仅 ~5%。

诚实代价（不回避）：靠 unimodal 立论扎实但新意偏小（本质 = GoodSpeed + 峰顶封顶）；
真正让问题不可分、有新意的是耦合，而那恰是数据最薄处。取舍倾向：**扎实优先**，
把耦合作为"同一个调度器顺带处理的二阶结构效应"呈现。
