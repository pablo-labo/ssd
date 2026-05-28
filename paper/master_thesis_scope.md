# 硕士毕业论文专用工作文档

**作用域：仅服务当前硕士毕业论文。所有 workshop / 主会 / PhD 方向相关讨论都在 `long_term_roadmap.md`，不在本文件出现。**

---

## 同步更新 (2026-05-28，以 `progress_handoff.md` 为准)

本文件原稿为 5/14。以下三点已向最新进度对齐，下方旧正文若与此冲突，以本节为准：

1. **GPU / 真实 LLM 工作已封板。** 单客户端的两项 GPU 工作（Block 1 真实-LLM shape 验证、timing calibration `a,b,T_V`）已完成并固化进 `sim/types.py` 默认参数（r=0.6, a=2.628523, b=0.0115335, t_v=20.0）。E3b 即在这套标定过的 `mu^SSD` 上跑。**核心路径不再需要上显卡服务器。** 唯一剩余的 GPU 项是 §3.2 的 P1（A2 corollary `k*(B)` 验证，~4h，且主要复用现有 Alpaca/GSM8K 数据），可选；scope 紧的话可降格为 Ch7 limitations 一句话。
2. **调度器命名已演进。** 旧稿的「GoodSpeed++ tie-breaking + Coupling-Greedy」已被当前代码的封顶/SSD-aware 设计取代（见 `sim/scheduler.py`）：当前正典集为 **CappedSSD（主方法，SSD-aware 封顶贪心）** vs **GoodSpeed（baseline，不封顶单调服务）** vs **SSDGreedy（去封顶对照，隔离"封顶"作用）**。⚠️ 旧稿的 GoodSpeed++（按 b 重排打破 tie）已不在当前实验设计中——如仍想保留为对照需明确。
3. **E3b 已完成**，覆盖原 §3.1 P0-4「调度器评估实验」+ claim 矩阵 C3。详见 `progress_handoff.md` §3。

---

## 0. 一句话定位

> 把"耦合预算下多客户端推测式 LLM 推理"作为一个结构性分析问题，**只在 SSD 一个 instance 上**形式化、理论刻画、实测验证、提出两个简单的 coupling-aware 调度器，并诚实记录 limitations。

**不超出这一行的事都暂缓。**

---

## 1. 当前已就绪的资产

| 类型 | 资产 | 位置 |
|---|---|---|
| 形式化 | proposal_en §3 | `paper/proposal_en.md` |
| 单客户端理论 | Lemma 1, Prop 1, Thm 1, Thm 2 | `paper/math/block1a2.md` |
| Block 1 合成验证 | 4032 cases, 100% 单峰 | `paper/experiment_log.md` 4/30 §1 |
| Block 1 真实 LLM | Alpaca + GSM8K, $k^\ast \approx 5$ | `paper/experiment_log.md` 4/30 §2–§3 |
| Timing calibration | $a, b, T_V$ 拟合 | `paper/experiment_log.md` 5/5 |
| Block 3 多客户端 | 4 scenario 反转扫 + scheduler-native 三机制 | `paper/experiment_log.md` 5/5–5/7 |
| Figures | slide + native-order figures | `sim/experiments/results/block3_*_figures/` |
| 详细章节大纲 | 9 章 + 2 附录 | `paper/thesis_outline.md` |
| Supervisor report 文本 | brief + contributions + other info | 见本仓库聊天记录 / 也可拷贝进 thesis 后记 |

---

## 2. 硕士论文 Scope（in / out）

### 2.1 In scope

- 形式化耦合预算 + KKT 分析
- Block 1 A2 单客户端理论（Thm 1 + 作为 corollary 的 Thm 2）
- Real-LLM 单客户端验证（Qwen3-8B / 0.6B + Alpaca / GSM8K）
- Timing calibration（仅来自单一 drafter）
- 多客户端两客户端 KKT 分析 + scheduler-native 三机制分解
- **两个 coupling-aware 启发式调度器（GoodSpeed++ + Coupling-Greedy），仿真器评估**
- 诚实 limitations 章节
- Future work 章节（指向后续工作但不展开）

### 2.2 Out of scope（明确写进 thesis Ch 7 limitations + Ch 8 future work）

- ❌ 真实多客户端 SSD 系统实现
- ❌ Online scheduler 收敛性正式证明
- ❌ PEARL / SwiftSpec / SpecBranch / AdaServe 的 instantiation（thesis 只提到 future work）
- ❌ 第二 drafter / 跨 family / 跨 hardware 校准（thesis 只在 limitations 提到）
- ❌ $N > 2$ 客户端的闭式结构性命题（合成 supporting evidence 可选）
- ❌ "Coupled resource framework universality" 这类跨 variant universal 主张

**这条 scope 严格按 proposal_en §4 的 explicit out-of-scope 划界 + 我们后续对 master's level 的紧缩。**

---

## 3. 必须完成的事项

### 3.1 实验补缺（P0：4–5 天工作）

按优先级：

1. **block3_native_gap.py（scheduler-native utility-gap 分布）** — 半天
   - 读 `sim/experiments/results/block3_reversal_alpaca_calibrated/summary.csv`
   - 按 blindness / overcommit / strict reversal 分桶
   - 输出 CDF + summary table
   - 进 thesis Ch 6.3.4

2. **GoodSpeed++ tie-breaking 调度器** — 半天
   - 在 `sim/policy.py` 或新建 `sim/schedulers/goodspeed_plus.py`
   - 算法：跑标准 monotone-service 分配 → 检测 tie → 按 $b$ 小到大重排
   - 进 thesis Ch 6.4.1

3. **Coupling-Corrected Greedy 调度器** — 1 天
   - 新建 `sim/schedulers/coupling_greedy.py`
   - 算法：初始化 $k_i = 1$ → 贪心选最大 SSD-aware 边际效用 → 累加直到 $\sum k_i = C$
   - 复杂度 $O(NC)$
   - 进 thesis Ch 6.4.2

4. **调度器评估实验** — 半天
   - 在 calibrated 配置下跑 {Equal-split, GoodSpeed, GoodSpeed++, Coupling-Greedy, Oracle}
   - $N \in \{2, 4, 8\}$，$C \in \{8, 12, 16, 20\}$
   - 指标：utility gap vs oracle，decision wall-time
   - 进 thesis Ch 6.5

### 3.2 实验补缺（P1：1 天工作，可选但强烈建议）

5. **Block 1 A2 corollary 真实-LLM 验证** — 4h GPU + 半天分析
   - 复用现有 Alpaca/GSM8K shape_summary，提取 $k^\ast$ vs $\hat\alpha$ 跨数据集
   - 复用 Alpaca calibrated $B \in \{16, ..., 64\}$ 数据，画 $k^\ast(B)$
   - **预期暴露 $k^\ast(B)$ 实测非单调（4-5-5-4-4）**
   - 进 thesis Ch 5.6 作为 honest negative finding

### 3.3 不做的实验（避免 scope creep）

- ❌ Qwen3-1.7B 第二 drafter（留 workshop）
- ❌ PEARL instantiation（留 workshop）
- ❌ $B_i$ 函数形式 sensitivity 详尽扫（thesis 提一句即可）

### 3.4 写作

按 `paper/thesis_outline.md` 9 章 + 2 附录的结构。详细章节内容参考该文件。

---

## 4. 6 周写作时间表

| Week | Days | 任务 |
|---|---|---|
| 1 | D1 | P0-1 跑 `block3_native_gap.py` |
| 1 | D2–3 | P0-2 + P0-3 实现两个调度器 |
| 1 | D4 | P0-4 调度器评估实验 |
| 1 | D5–7 | Ch 4（理论章）写作 |
| 2 | D8 | P1 跑 A2 corollary 验证（可选） |
| 2 | D9–11 | Ch 5（单客户端验证）写作 |
| 2 | D12–14 | Ch 6（多客户端 + 调度器）写作 |
| 3 | D15–17 | Ch 6 完成 |
| 3 | D18–19 | Ch 3（problem formulation）写作 |
| 3 | D20–21 | Ch 7（limitations）写作 |
| 4 | D22–24 | Ch 1 + Ch 9（intro + conclusion） |
| 4 | D25–27 | Ch 2（related work）写作 |
| 4 | D28 | Ch 8（future work）写作 |
| 5 | — | 完整 draft 给导师，等反馈，写 abstract，画 figure |
| 6 | — | Revision + 答辩 PPT + mock defense |

---

## 5. 关键诚实点（必须显式写进 thesis）

1. **原 Gate 3 没过**（plan.md 写过 strict reversal ≥ 20%，实测 10.8%）→ reframe 为三机制分解。Ch 6.3 显式承认。
2. **Block 1 A2 corollary $k^\ast(B)$ 实测非单调**（如果 P1 实验确认）→ Ch 5.6 作为 negative finding 记录，Ch 7 limitations 提到。
3. **单一 drafter calibration**：$b$-heterogeneity 来自合成扫，Ch 7 显式承认。
4. **仿真器 vs 真实系统**：多客户端结果都来自 simulator，Ch 7 显式承认。
5. **Theorem 1 是 conditional**（要求 $q'' \ge 0$）：Ch 4 显式标注。

---

## 6. 与其他文件的关系

- `paper/thesis_outline.md`：本工作文档**只列任务**，详细每章写什么参考它
- `paper/experiment_log.md`：实验日志，作为 Ch 5–6 的素材来源
- `paper/math/block1a2.md`：A2 推导，作为 Ch 4 + Appendix A 的素材来源
- `paper/proposal_en.md`：Ch 1 + Ch 3 改写底稿
- `paper/long_term_roadmap.md`：**所有 workshop / 主会 / PhD 内容都在那里**，写 thesis 期间不要去看，避免分心

---

## 7. 提示：scope creep 警告信号

写作过程中如果你发现自己在想以下任何事，**立刻停下，记到 `long_term_roadmap.md` 的 backlog，回到当前任务**：

- "要不要加 PEARL 来证明 framework universality" → workshop 任务
- "要不要补 Qwen3-1.7B 让 $b$ 异质性更扎实" → workshop 任务
- "要不要给 online scheduler 写 convergence proof" → 主会 / PhD 任务
- "我的 framework 能不能套到 KV cache" → PhD 任务

这些都是真问题，但**不是硕士论文阶段的问题**。

---

## 8. 单一聚焦标准

整个硕士论文阶段，每天醒来问自己一个问题：

> "今天做的事是不是直接服务于 6 周内交完整 thesis draft？"

如果答案是"否"，重新调度。

