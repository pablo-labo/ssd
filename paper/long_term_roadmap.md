# 长期路线图（硕士答辩通过之后）

**作用域：本文件覆盖 workshop paper、final submission、PhD direction 三个阶段。所有硕士毕业论文相关内容在 `master_thesis_scope.md`，不在本文件出现。**

**触发条件：硕士答辩通过 / thesis 已提交后。提前打开本文件不利于硕士阶段的聚焦。**

---

## 阶段总览

| Stage | 时间窗 | 目标 | 触发条件 |
|---|---|---|---|
| 2 | 答辩后 1–3 月 | Workshop paper | 硕士已交 |
| 3 | Stage 2 后 6–12 月 | 主会 / 期刊 final submission | Workshop 已发或得到 reject feedback |
| 4 | 长期 1–5 年 | PhD anchor | 申请 PhD / 入学 |

---

## Stage 2：Workshop Paper

### 2.1 目标

把硕士 thesis 改写为 8–10 页 workshop 投稿，采用"耦合资源 framework"升级 framing。

### 2.2 Framing 升级（核心 reframing）

**从 master's thesis 的**：
> 多客户端 SSD 调度下耦合预算引发的结构性问题

**升级为 workshop paper 的**：
> 当 drafter 和 verifier 共享硬件资源时，drafter 预算成为 verifier 选择的隐函数，per-client 服务曲线非单调，多客户端分配问题非可分——本文给出框架并在 SSD 上实例化。

### 2.3 Title 候选

1. **Coupled Resources and Non-Monotone Service in Speculative LLM Inference**（推荐）
2. **When the Drafter Borrows Time: Resource Coupling Breaks Monotone Service in Speculative Decoding**

### 2.4 Abstract 骨架（详见后文 §2.7 + 之前 direction.md）

英文 ~220 词：开头观察 → 三条结构性结果 → SSD instantiation → 多客户端 calibrated 分析 → 落脚到 framework subsumes monotone-service formulations as decoupled limit

### 2.5 §1 大纲

- 1.1 Hook：async/parallel SD 家族崛起 → 共享资源
- 1.2 Observation：耦合让 $B_i$ 内生
- 1.3 General coupled-resource model + instantiation 大表（SSD, SwiftSpec, PEARL, AdaServe）
- 1.4 六条 contribution（C1–C6）
- 1.5 Scope + relation to prior work

### 2.6 必须新增的实验（master's 之外）

#### 2.6.1 第二 instance：PEARL（最高优先级）

**为什么必做**：master's 只在 SSD 一个 instance 上，要让 framework 的 "universal" 论点站得住，至少需要 2 个 instance。

**任务**：
- 读 PEARL paper，把它的 adaptive draft length 用 $\phi_i$ formalism 写出来
- 在 simulator 加 PEARL-like instance
- 跑服务曲线，验证是否非单调
- 1–2 天工作量

**风险**：如果 PEARL 不呈现非单调，把 framework 收窄到 "verifier-wall-time-coupled subfamily"，备选用 SwiftSpec 或 SpecBranch。

#### 2.6.2 第二 drafter profile（中优先级）

**任务**：
- Qwen3-1.7B 校准网格（同 master's 的 timing 实验流程）
- 拟合 $(a_{1.7}, b_{1.7}, T_V)$
- 0.6B vs 1.7B 的 $b$ 对比图
- 1.5 天 GPU + 0.5 天分析

**风险**：如果 $b_{1.7} / b_{0.6} < 1.5$，drafter cost 异质性论点变弱，备选换 Llama3-1B 作为 cross-family 锚点。

#### 2.6.3 GoodSpeed++ 防御性扩展（低优先级，已在 master's 做）

如果 master's 阶段没充分展开，workshop 补一节 "If GoodSpeed adopts tie-breaking by drafter cost, does the mismatch close?"，并报告答案。

### 2.7 投递目标

| Venue | 截稿（一般） | 估命中率 |
|---|---|---|
| NeurIPS ENLSP workshop | 9 月初 | 55–65% |
| NeurIPS ML for Systems workshop | 9 月初 | 50–60% |
| MLSys workshop（如果对口） | 滚动 | 40–50% |
| TMLR rolling | 任意 | 40–50% |

**优先策略**：先冲 NeurIPS workshop（截稿近 + signal 高 + 命中率合理）；同时投 TMLR 作为 backup。

### 2.8 估计总工作量

- Framing 升级写作：2 周
- 新增实验（PEARL + 1.7B drafter）：3–5 天
- 投递修改：1 周

合计 **3–4 周**全职。

---

## Stage 3：Final Submission（主会 / 期刊）

### 3.1 目标

把 workshop / TMLR 的工作扩展为 MLSys / NeurIPS / OSDI 级别的投稿。

### 3.2 触发条件

- Workshop 已 accept 或 desk-reject 反馈很 actionable
- 或 6 个月之后即使没 workshop ack 也启动

### 3.3 必须新增的事项（任选两个，全做最好）

#### 3.3.1 真实多客户端 SSD 最小原型（最高收益）

- 2 GPU + 2 drafter 进程 + 1 共享 verifier 进程
- 用真实 throughput 曲线 cross-validate simulator
- 4–6 周 systems 工作
- **收益**：把 reviewer 必问的 "为什么相信 simulator" 一次性回答掉

#### 3.3.2 在线调度算法 + 收敛性 sketch

- 给 Coupling-Greedy 一个 online 版本
- 在耦合 setting 下给 Lyapunov 重构 sketch（即使不完整证明）
- 需要 queueing / OR 背景合作者
- 2–3 个月

#### 3.3.3 多 drafter × 多 hardware calibration 矩阵

- 至少 3–4 个 drafter × 2 hardware × 2 workload
- 给出 $b$ 的真实经验分布
- 2–3 周 GPU

#### 3.3.4 $N > 2$ 客户端的结构性命题

- 把 KKT externality 项的符号在 $N$ 趋大时的渐近行为做出 conditional 命题
- 或给 $N \in \{16, 32\}$ 的仿真 + heuristic vs oracle 性能 gap
- 4–6 周

### 3.4 投递目标

| Venue | 截稿 | 估命中率 |
|---|---|---|
| MLSys 春季 | 10 月 | 25–35%（如做 3.3.1） |
| NeurIPS main systems track | 5 月 | 12–20% |
| OSDI | 12 月 / 4 月 | 5–10% |
| TMLR full accept | 任意 | 50–60% |

### 3.5 估计总工作量

6–12 个月全职。

---

## Stage 4：PhD Direction

### 4.1 核心方向（方向 C）

**Coupled Resource Allocation in Modern ML Systems: Theory, Instances, and Practical Schedulers**

> 现代 ML 系统中，那些经典调度理论假设"正交可分"的资源——compute、memory、bandwidth、token budget、attention capacity、expert capacity、KV cache slot——在 runtime 通过模型动力学紧耦合。这种耦合让经典服务曲线和分配理论失效，需要一套新的结构性刻画。

### 4.2 6 个候选子问题（每个都可出一篇 paper）

1. **Coupled Speculative Inference**（当前工作 = first instance）
2. **KV Cache Multi-Tenant 耦合**（最自然 second instance）
3. **MoE Inference 的 routing × capacity 耦合**
4. **Multi-LoRA Serving 的 adapter swap 耦合**
5. **Agent / Tool-call serving 的 budget 耦合**
6. **Long-context inference 的缓存层级耦合**

### 4.3 PhD thesis 形状

- Ch 2: General framework
- Ch 3: Speculative inference（first instance）
- Ch 4: KV cache multi-tenant 耦合（second instance）
- Ch 5: MoE 或 multi-LoRA（third instance）
- Ch 6: Agent-scale 或 long-context（fourth instance, speculative）
- Ch 7: 跨 instance 的统一 lessons + practical scheduler design

### 4.4 阅读路线图

Tier 1（4 周必读，写当前 paper 用）：
- Kelly Maulloo Tan 1998；Stolyar 2005；Tassiulas-Ephremides 1992
- SpecInfer；Medusa；EAGLE-3；Sequoia
- GoodSpeed 精读；Saguaro 精读

Tier 2（暑期 8 周读，second instance 铺垫）：
- Orca；vLLM；DistServe；Splitwise；Sarathi-Serve；SGLang
- CacheGen；CachedAttention
- S-LoRA；Punica
- MegaBlocks；Tutel；Switch Transformer

Tier 3（PhD 第一年读，理论纵深）：
- Harchol-Balter《Performance Modeling and Design of Computer Systems》
- Massoulié-Roberts；Maguluri-Srikant；Yi-Chiang
- Shakkottai-Srikant《Network Optimization and Control》

Tier 4（持续 awareness）：arxiv 关键词、OSDI/SOSP/NSDI/MLSys/ASPLOS proceedings、关键学者动态

### 4.5 PhD 申请准备路径

**月份 1–3**：投出 workshop paper（first instance），仓库 public artifact 化

**月份 4–6**：second instance（KV cache）proof-of-concept，6–8 页文档作为 research statement 附件

**月份 7–9**：申请

- Research statement 1.5–2 页：
  - 0.5 页 first instance
  - 0.5 页 framework 抽象层
  - 1 页 second instance + 5 年 thesis vision
- 推荐信：硕士导师 + 一个真实读懂工作的人
- Writing sample：first paper preprint
- Code artifact：GitHub repo

**月份 10–12**：second instance 写成完整 paper（MLSys 春季截稿）

### 4.6 候选 lab pool（不是详尽列表）

- CMU Beidi Chen（efficient inference）
- MIT Song Han（systems for AI）
- Berkeley Sky Computing（Ion Stoica）
- Stanford CRFM
- UW SAMPL（Luis Ceze）
- SJTU IPADS
- THU Yu Wang 组

---

## Backlog（scope creep 时把想法记在这里）

当硕士论文阶段冒出"想做但不能现在做"的想法时，把它放进下面这个 list，将来到对应 stage 再处理。

### Workshop 阶段 backlog

- [ ] 列在此处的工作要在硕士提交后才能动
- [ ]

### Final submission 阶段 backlog

- [ ]

### PhD 阶段 backlog

- [ ]

---

## 与其他文件的关系

- `master_thesis_scope.md`：硕士阶段唯一工作文档，本文件期间不要去看
- `thesis_outline.md`：硕士论文详细章节大纲（master's 阶段用）
- 本文件取代了之前的 `direction.md` 和 `reading_list.md`——这两个文件的内容已合并进本文件，原文件可以删除或保留作为详细备份

