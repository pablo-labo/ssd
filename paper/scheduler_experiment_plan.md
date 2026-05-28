# scheduler_experiment_plan.md (v1)

## Claim → Experiment 对照矩阵

承接 `scheduler_design.md`。目的：在动代码、写正文之前，把"每个实验要证明哪一句
claim"钉死，避免盲跑。故事线沿用 `direction.md`：**现象优先**（单峰服务曲线打破单调
服务调度器）→ F（边际贪心）作 punchline → DP 作稳健性 → 耦合作 ~5% 二阶注脚。

状态图例：✅ 已做可复用 ｜ 🟡 部分（N=2 / 离线 / 需重整）｜ ⬜ 待做（含代码缺口）

---

## 0. 投稿前要锁的全局变量（所有实验共用）

- **目标函数**：主用 sum-throughput $U_i=\mu_i^{\text{SSD}}$；副报 proportional-fair
  $U_i=\log\mu_i^{\text{SSD}}$（两者凹性已验，§ `scheduler_design.md` 10）。
- **容量压力轴**：定义压力比 $\rho=\sum_i k_i^\*/C$。**这是让 overcommit 故事清晰的关键轴**，
  必须显式扫：$\rho<1$（宽松，GoodSpeed 越顶最明显）、$\rho\approx1$（临界）、$\rho>1$（紧约束，退化为上升段 water-filling）。
- **客户端异质性**：$\alpha$ 分布。同质（reversal 不出现）vs 异质（reversal 出现）。
- **标定锚点**：$r=0.6,\ a=2.6285,\ b\in[0.0038,0.077],\ T_V=19.613+0.09437\,S$，$\alpha$ 中心 0.735。
- **统一指标集**：聚合吞吐、各客户端吞吐、被分到峰顶外的客户端比例（overcommit count）、
  对 oracle 的最优性 gap、GS–SSD disagreement 率、wall-time delta。

---

## C1 — 单客户端服务曲线单峰，存在内部 $k^\*$

- **实验 E1**：扫 $k$，看 $\mu^{\text{SSD}}(k)$ 先升后降。合成网格 + 真机。
- **变量 / 指标**：$k$ 扫；`is_unimodal`、`best_k`。
- **预期**：内部峰，真机 $k^\*\approx4\text{–}5$。
- **证伪**：真机 $\mu(k)$ 单调（无内部峰）。
- **状态**：✅ `experiments/results/block1_validate/`（合成）+ `qwen8b_gsm_async`（真机）。
  待办：打包一张真机 $\mu(k)$ 曲线图进正文。

## C2 — $k^\*$ 由 $\alpha$ 主导，耦合（$T_V$）仅 ~5% 二阶

- **实验 E2**：$\alpha\times T_V$ 双扫，$k^\*(\alpha)$ 陡、$k^\*(T_V)$ 平；实测带不变性。
- **变量 / 指标**：$\partial k^\*/\partial\alpha$ vs $\partial k^\*/\partial T_V$；实测带 $T_V\,19.80\!\to\!20.75$
  下 $k^\*$ 不变的格数（18/22）；$T_V$ 拉 8× 仅挪 1–2 步。
- **预期**：$k^\*$ 随 $\alpha$ 单调上行；随 $T_V$ 近乎不动。
- **证伪**：$k^\*$ 在实测 $T_V$ 范围内显著移动。
- **状态**：✅ `kstar_sensitivity.png` + `block1_validate/summary.csv` 全网格。待办：写成正文小节。

## C3 — 单调服务调度器（GoodSpeed）越过 $k^\*$ overcommit，且代价在宽松区($\rho<1$)最大

- **实验 E3a（N=2，离线）**：GoodSpeed-最优 vs SSD-最优分配，扫容量 C8–C20，量 `utility_gap`。
- **实验 E3b（待做）**：(i) 扩到 N>2 客户端；(ii) 在**在线仿真**里跑封顶 vs 不封顶的
  `GreedyMarginalScheduler`，动态复现同一效应。
- **变量 / 指标**：压力比 $\rho$；聚合吞吐 gap；被分到 $>k_i^\*$ 的客户端比例。
- **预期**：SSD 封顶在 $k^\*$，GoodSpeed 推到 6–7（如 C14: $k_{gs}=7,7$ vs $k_{ssd}=4,4$）；
  gap 随 $\rho$ 降低（越宽松）越大。
- **证伪**：GoodSpeed 从不越顶，或越顶不损吞吐。
- **状态**：✅ **E3b 已完成**（`results/e3b_capacity_pressure/`，N∈{2,3,5} × spread × ρ 扫，
  capped_ssd vs ssd_greedy vs goodspeed，全部在真实 μ^SSD 上量 realized 吞吐）。
  N=2 离线亦有（`block3_capacity_sweep/`）。代码缺口 G1、G2 已补（见下）。

## C4 — 边际贪心 F 在标定曲线上取得精确整数最优，且单调时退化回 GoodSpeed

- **实验 E4（待做）**：F vs DP vs MILP oracle，随机标定实例，量最优性 gap（应 ≈0）。
  稳健性：注入非凹曲线，展示 F 出现 gap 而 DP 仍精确。
- **变量 / 指标**：实例随机化（$\alpha,b$ 异质）；optimality gap = $(U_{\text{oracle}}-U_F)/U_{\text{oracle}}$。
- **预期**：凹标定曲线上 gap ≈ 0；非凹注入下 F 出现可见 gap、DP=oracle。
- **证伪**：F 在凹标定曲线上 gap > 0。
- **状态**：✅ **E4/G3 已完成**（`sim/experiments/g3_exact_oracle.py`，`results/g3_exact_oracle/`）。
  真实 `CappedSSDScheduler` vs DP vs MILP(HiGHS)，228 网格点 (N∈{2,3,5,8}×spread×C binding→slack)
  **greedy=DP=MILP 全中、gap=0**（DP-MILP 偏差 3.6e-14）；离散凹性 228/228 成立；
  非凹反例下 greedy 次优 ~16%、DP/MILP 抓到。诚实标注：精确最优条件于 sum-throughput 目标 +
  离散凹性（F 是 sum-μ 优化器，非 PF）。详见 `experiment_log.md` 2026-05-28。

## C5 — GS–SSD 分配 disagreement 可观(~50%)，三类失效模式；但是离散边界翻转，非大 wall-time 摆动

- **实验 E5（N=2，离线）**：reversal/disagreement 扫描 + 三机制分解
  （drafter-cost blindness / near-peak overcommit / strict reversal）。
- **变量 / 指标**：disagreement 率；三机制占比；**utility-gap 分布**（应多数小、仅 strict 尾部大）。
- **预期**：disagreement ≈ 51.6%（已得）；gap 分布印证"边界翻转主导、非大摆动"。
- **证伪**：disagreement 极小，或 wall-time gap 普遍很大（将与 5% 耦合矛盾）。
- **状态**：✅ `block3_reversal_alpaca_calibrated/`（51.6%）+ `native_order` 分解图。
  待办：**按修正叙事重整**——把 51.6% 解释为"5% 扰动把刀尖格子翻过来"的离散效应，
  补一张 gap 分布图（多数小、strict 尾部大）。

## C6 —（稳健性，可选）耦合仅 ≤5%，不动点 1–2 轮收敛

- **实验 E6（待做，小）**：开/关耦合不动点循环，量分配变化与迭代数。
- **指标**：分配 delta（应 ≤ ±1 步 / 客户端）；收敛迭代数。
- **状态**：⬜ 待做（小，代码缺口 G1 之上加一层循环即可）。

---

## 代码缺口（gating，对应 `scheduler_design.md` 的设计）

- **G1** ✅ 已补：`sim/scheduler.py` 加了 `cap_at_peak`/`cap_tolerance` + break，新增
  `CappedGreedyMarginalScheduler` / `CappedSSDScheduler`（F 本体）/ `SSDGreedyScheduler`（去封顶对照）。
- **G2** ✅ 已补：`GoodSpeedScheduler`（不封顶、$\mu^{\text{GS}}$）baseline 类。
- **G3** ✅ 已补：DP 精确解 + MILP oracle，见 `sim/experiments/g3_exact_oracle.py`（gated E4，已跑通）。
- **G4**：把 `block3` 离线优化器从两客户端推广到 N 客户端。**gates E3/E5 的规模化。**
- **Gate（事实核查）**：在 C3/C5/C6 正文断言前，核 GoodSpeed 原文真实分配算法/目标，
  坐实或修正"一行之差"（`scheduler_design.md` §6 标注的唯一纯推断点）。

---

## 优先级（建议执行顺序）

1. ~~**G1 + G2** → 跑 **E3b**~~ ✅ 已完成（punchline 直接证据）。
2. ~~**G3** → **E4**（F vs DP/MILP）~~ ✅ 已完成（精确性 + 稳健性已坐实）。
3. **重整 E5/C5**（已有数据，只需按修正叙事重画 + gap 分布）——低成本、巩固现象侧。
4. **E6**（耦合不动点），把 5% 注脚补全。
5. **Gate**：核 GoodSpeed 原文，放行 §6 断言。
6. 现象侧 **C1/C2** 已基本就绪，打包进正文即可。
7. **写正文**：现象侧 (C1/C2/C3) + 精确性 (C4) 实验资产已齐，可开写 Ch4–6。

**关键判断**：现象侧（C1、C2、C5 的 N=2）已有扎实资产；真正欠的是 F 本体的在线/规模化实现
（G1–G4）与精确性对照（E4）。也就是说，**离能写的距离比"从零"近——主要缺的是把已定稿的
设计落进代码并跑规模化对照。**
