# Scheduler 工作进度与交接 (handoff)

> 用途：下个对话里直接说"读 paper/progress_handoff.md 继续"，即可无缝接上。
> 最后更新：2026-05-28（含当日自主推进的 G3 实验 + Ch3–7 草稿）。

## 0. 一句话现状

核心代码 + 设计文档 + **E3b (C3) + G3 (C4)** 两个 punchline 实验都已跑通验证。
**正文 Ch3–Ch9 + Appendix A/B 一稿都已落进 `specspeed/` LaTeX**（最初先在 `paper/draft/` 写 markdown，后整合进 LaTeX；详见 §9 LaTeX 状态）。
代码 b 值 ✅ 已统一到 0.0038445（`sim/types.py` 默认 + `e3b` SSD_B 常量同步，canonical 结果目录已重跑覆盖）。
剩下：投稿前核实新引入的 bib 占位条目（fox1966 / katoh1979 / huangfu2018parallelizing / zhang2025swiftspec / shen2025specbranch / fedus2022switch）。

## 9. specspeed LaTeX 状态（2026-05-28 整合后）

- `abstract.tex`：✅ 同步,已把 GoodSpeed++ / Coupling-Corrected Greedy 改写为新的 capped SSD-aware greedy 结果。
- `introduction.tex`：✅ 同步,RQ3 + 贡献清单 + 章节导览全部更新。
- `theory/probformulation.tex`：✅ 已做命名/oracle 同步。
- `theory/evaluation.tex`（Ch4 理论）：✅ 已做 oracle 描述同步。
- `experiments/Single-Client_Validation.tex`：原本已完整 + 已含 k\*(B)=4,5,5,4,4 诚实记录,无需改。
- `experiments/multi_client_schedulers.tex`：✅ §6.1–6.3 保留 + **新增 §6.4 = scheduler + E3b table + G3 oracle + 非凹反例 + 总结**(`in preparation` stub 已替换)。
- `limitations.tex`：✅ 已添加 §5.6（capped greedy 条件性）+ §5.7（sum-throughput objective 范围）。
- `future_work/future_work.tex`：✅ 全文新写,4 节(real system / multi-drafter / online + fixed point / broader)。
- `conclusion/conclusion.tex`：✅ 全文新写,含 3 条 implications。
- `appendices/a2_derivation.tex`：✅ 从 block1a2.md 完整转写为 LaTeX,含所有 lemma/prop/thm 证明。
- `appendices/implementation.tex`：✅ 全文新写,含目录布局/scheduler 命名/标定参数/复现命令。
- `results/results.tex`：thesis.tex 里 `\input` 行已注释,stub 文件保留以备复用。
- `images/`：✅ `g3_greedy_vs_optimum.png` / `e3b_throughput_vs_rho.png` / `e3b_overcommit_vs_rho.png` 已拷入。
- `references.bib`：✅ 加了 6 个新 bib key(fox1966 / katoh1979 / huangfu2018parallelizing / chen2025swiftspec / sun2025specbranch / fedus2022switch);为占位条目,投稿前需核实。

E3b/G3 实验在 `b=0.0038445` 下重跑过,结果存于 `sim/experiments/results/{e3b_capacity_pressure,g3_exact_oracle}_blat/`,作为论文 Ch6 §6.4/§6.5 引用的数据源(G3 仍 270/270 全中,greedy=DP=MILP)。

---

## 1. 项目主线（别忘了的大框架）

- 论文主题：多客户端 **SSD (Speculative Speculative Decoding) 验证器预算调度**。
- 决策变量：每个 client 的前瞻步数 `k_i`（drafter fan-out 预算 `B_i` 是耦合派生量）。
- 核心现象：服务曲线 `mu^SSD(k)` 是**单峰**的（先升后降），存在内部最优 `k_i* = argmax_k mu(k)`。
- 核心主张：好的调度器要在 `k_i*` **见好就收**，而不是像 GoodSpeed 那样假设"越多越好"花光预算、过峰自残。
- 方法论：混合式。真实标定 (`bench/`, 单客户端) + 模拟 (`sim/`, 多客户端)。**不**搭真实多客户端系统（见 plan.md），作为论文的 stated limitation。
- **GPU 工作已封板 (2026-05-28)。** 单客户端的两项 GPU 工作（Block 1 真实-LLM shape 验证、timing calibration `a,b,T_V`）已完成并固化进 `sim/types.py` 默认参数。核心路径不再上显卡服务器。唯一剩余 GPU 项是可选的 A2 corollary `k*(B)` 验证（~4h，复用现有 Alpaca/GSM8K 数据，见 master_thesis_scope.md §3.2 P1）。剩下的工作是模拟实验 + 写作。
- `k*` 由 α（接受率）驱动，耦合 `T_V` 只是 ~5% 的二阶效应（已用 `kstar_sensitivity.png` 证明）。

---

## 2. 已完成的代码（都已验证、可在远端跑）

运行约定：`uv`/`.venv`，CPU-only，`python -m sim.experiments.<name>`，参考 `scripts/start.sh`。

### 调度器 `sim/scheduler.py`
给 `GreedyMarginalScheduler` 加了 `cap_at_peak` / `cap_tolerance` 开关 + break 逻辑。新增类：
- `CappedGreedyMarginalScheduler` (cap_at_peak=True) —— 通用封顶贪心 ("F")
- `GoodSpeedScheduler` (estimate_mode="goodspeed", 不封顶) —— baseline ("E")
- `CappedSSDScheduler` (estimate_mode="ssd", 封顶) —— **主方法 G5/F**
- `SSDGreedyScheduler` (estimate_mode="ssd", 不封顶) —— 隔离"封顶"作用的对照
- `CappedEmpiricalScheduler` (estimate_mode="empirical")
- 旧的 Linear/Unified/Empirical 行为不变（默认 cap_at_peak=False）。

### 服务曲线 `sim/policy.py`
- `goodspeed_service` = `min(backlog, (1-α^(k+1))/(1-α))`，单调饱和。
- `ssd_service` + `_ssd_mu`（lru_cache）—— 接入标定过的单峰 `mu^SSD`（来自 `sim/ssd_math.py`）。
  **注意：`mu^SSD` 是吞吐率不是 token 计数**，因此 ssd 模式用于静态分配实验（backlog 取非约束大值），不用于 backlog 排队动态。

### 其余
- `sim/client.py`：加了 `ssd_r/ssd_a/ssd_b/ssd_t_v` 字段 + `_service` 的 goodspeed / ssd 分支。
- `sim/types.py`：`ClientConfig` 加了 ssd 标定参数字段（默认 Alpaca / Qwen3-8B+0.6B：r=0.6, a=2.628523, b=0.0115335, t_v=20.0）。
- `sim/ssd_math.py`（**未改**）：`curve_point(k, Block1Params)` → `.mu/.valid`；`curve_summary(points)` → `best_k`(=k*)。

---

## 3. 实验脚本

### E3b（刚完成，论文 punchline）`sim/experiments/e3b_capacity_pressure.py`
静态单次分配。扫容量压力 `rho = Σk* / C`（从 slack 到 binding），扫 N∈{2,3,5} 与 α 异质性 spread∈{0,0.1,0.18}。
对比 capped_ssd(F) vs ssd_greedy(去封顶) vs goodspeed，**全部在真实 mu^SSD 上量 realized 吞吐**。主目标 sum-throughput，PF (Σlog μ) 作 robustness 列。
输出在 `sim/experiments/results/e3b_capacity_pressure/`：
- `e3b_capacity_pressure.csv`（63 行）
- `e3b_throughput_vs_rho.png`（吞吐 vs ρ，9 宫格 facet）
- `e3b_overcommit_vs_rho.png`（过峰单位数 vs ρ）

**关键结果**（N=3, spread=0.18）：
- capped_ssd 在整个 slack 区平且最优（恒 8.162），即使留一堆 idle。
- ssd_greedy 在 slack 区被迫花光、过峰，ρ=0.5 时低 ~106%；ρ→1 收敛；ρ>1 两者相同。→ 隔离"封顶"作用。
- goodspeed 在宽区间明显次优，最差在 ρ≈1（+123%）。→ 隔离"用错服务曲线"的建模误差。
- α 异质性越大，两个 gap 越宽（天然 ablation 轴）。

**诚实标注**：capped_ssd 的"赢"是按 sum-throughput 定义的（靠不做负边际亏本买卖，不是用满资源）。换成"资源利用率/尾延迟"目标，叙事要重述。

---

### G3（刚完成，C4 精确最优）`sim/experiments/g3_exact_oracle.py`
静态分配的精确最优性检验。对每个 (N∈{2,3,5,8}, spread∈{0,0.1,0.18}, C 从 binding 扫到 slack) 共 228 个网格点，把**真实的** `CappedSSDScheduler`(F) 的目标值同时对照两个独立精确解：
- **DP**（可分离整数分配的精确解，与凹性无关）
- **MILP oracle**（`scipy.optimize.milp` / HiGHS，独立交叉验证 DP）

输出在 `sim/experiments/results/g3_exact_oracle/`：
- `g3_exact_oracle.csv`（228 行，每行 greedy/dp/milp 目标 + 分配向量 + 凹性标志）
- `g3_greedy_vs_optimum.png`（greedy 目标 vs 精确最优散点，全部落在对角线）

**关键结果**：
- greedy=DP **228/228 全中**，worst gap = 0.0（其中 168 个是 binding 区、分配非平凡）；连分配向量都与 DP 逐位相同，不靠 tie-breaking。
- DP vs MILP 最大偏差 3.6e-14（纯数值噪声）→ 两个独立 solver 互证，排除"DP 写错"。
- 离散凹性前提在 228/228 点全部成立 → 这正是 greedy 可证最优的条件。
- **非凹反例**（2 client，C=3，A 曲线 marginal 1.00/0.10/0.80/0.05 非凹）：greedy=1.60[2,1] vs 最优=1.90[3,0]，差 ~16%，DP/MILP 抓到。→ 证明 solver 不是橡皮图章，且"精确最优"是**有条件的**（凹性破坏即失效）。

**诚实标注**：C4 的"精确最优"是对 **sum-throughput** 目标、且在**离散凹性成立**时的结论。F 按 marginal-of-μ 贪心，是 sum-μ 优化器，不是 PF(Σlog μ) 优化器。标定曲线在整个可行 k 区恒凹，故命题在标定 regime 内无条件成立；离开该 regime（合成非凹曲线）greedy 可证次优。

## 4. 设计文档（已写）

- `paper/scheduler_design.md`：完整数学设计。notation、mu^SSD 链、分配问题、边际增益=峰=符号翻转、贪心算法 + 精确性命题、KKT/water-filling、与 GoodSpeed 的关系、耦合 fixed-point、复杂度、在线行为、**§10 overclaim 审计**、§11 替代方法表、§12 推荐（F 主 / B 稳健兜底 / C oracle / E baseline / D 理论）。
- `paper/scheduler_experiment_plan.md`：claim→experiment 矩阵（C1–C6，code gap G1–G5）。
- `kstar_sensitivity.png`（repo 根）：证明 k* 由 α 驱动、耦合仅 ~5%。

---

## 5. claim→experiment 矩阵状态

| Claim | 内容 | 状态 |
|---|---|---|
| C1 | mu^SSD 单峰 | ✅ block1_validate |
| C2 | k* 由 α 驱动 | ✅ kstar_sensitivity.png |
| C3 | GoodSpeed 过度承诺 / 封顶有用 | ✅ **E3b 刚完成**（静态、N 客户端、扫 ρ）|
| C4 | F 在离散凹性下精确最优 | ✅ **G3 刚完成**（228/228 网格点 greedy=DP=MILP，gap=0；含非凹反例）|
| C5 | ~50% 分配分歧分解 | 🟡 已有 block3 N=2，需重述为离散边界翻转 + 加 utility-gap 分布图 |
| C6 | 耦合 5% / fixed-point 收敛 | ⬜ 目前用固定 T_V（解耦）|

---

## 6. 下一步（待你拍板，建议顺序）

- ~~G3：DP 精确解 + MILP oracle~~ ✅ **已完成**（见 §3 G3 节，C4 已 ✅）。
- ~~写 Ch3/4/5/6/7 正文一稿~~ ✅ **已完成**（`paper/draft/`，含 `README.md` 状态表）。

**回来后建议优先做的 3 件事（按优先级）**：
1. **过一遍 `paper/draft/README.md` 列出的 4 个 verify 项**：(a) `ssd_b` 标定值 sim 默认 0.0115335 vs 文档拟合 0.0077 的对齐；(b) block3 三机制百分比 (22.8/18/10.8 etc.) 对图复核；(c) 「F = GoodSpeed 少两行」这句去 GoodSpeed 原文坐实或改写；(d) 把 figure 占位符接到真实路径。
2. **整合 + 写 Ch1（Intro）+ Ch2（Related Work）**：outline 排到 Week 4，因为它们 distill body；body 一稿落地后这两章好写得多。
3. **动态 sanity-check / G4 / C6 耦合 fixed-point**：余下的实验侧补完，但都属于 stretch 项，按硕士 scope 可以推到 limitations。

## 7. 待验证的诚实门槛（写进论文正文前必须做）

- 去 GoodSpeed **原始论文**确认它的真实算法/目标，再断言"F = GoodSpeed 少一行"。目前这句是 model-level 的，未经原文核实。
- "精确最优"是有条件的：依赖（模型≠现实、可分离性、有限网格上验证的离散凹性）。fixed-point 收敛未证明。
  → G3 已把"离散凹性→greedy 最优"实测落地，并用非凹反例界定了边界；但"模型≠现实"和 fixed-point 收敛仍是 limitation。

## 8. 路径速查（远端/本地）

- 项目根：`/Users/ruben/Documents/Git_docs/specdiff/ssd`
- 实验结果：`sim/experiments/results/`
- 跑 E3b：`python -m sim.experiments.e3b_capacity_pressure`（加 `--no-plots` 跳过画图）
- 跑 G3：`python -m sim.experiments.g3_exact_oracle`（加 `--no-plots` 跳过画图）。
  仅需 numpy / scipy(>=1.15，用 `scipy.optimize.milp`) / matplotlib，**不**需要 pyproject 里的 GPU 重依赖（torch/flashinfer/sgl-kernel）。CPU-only 轻量 venv 即可。MILP 缺失时自动降级为 DP-only，不影响 C4 结论。
