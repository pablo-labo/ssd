# 面向 SSD / Tree Speculation 的 Freshness-Aware Unified Speculative Budget Scheduling

## 1. 研究背景与问题来源

现有两类相关工作给了我们一个明确起点。

第一类是 GoodSpeed 这一类工作。它把分布式 speculative decoding 抽象成一个多 client、单 verifier 的资源分配问题：每个 client 获得一个 verifier-side token budget (S_i)，系统在总预算约束下动态分配 (S_i)，目标是最大化长期平均 goodput 与公平性。其核心建模仍然是**线性 speculative decoding**：(S_i) 的含义近似是“往前 draft 多少 token”，收益函数是某种 accepted tokens 的期望。

第二类是 G-FAST 这一类工作。它在 GoodSpeed 风格的目标上进一步引入 freshness，把系统目标从单纯 throughput/goodput 推进为 **timely goodput**：accepted tokens 还要乘以 freshness 衰减项 (\Phi(\Delta_i))，长期目标写成 (\sum_i U(\bar y_i))，每时隙通过 gradient scheduling 进行在线分配。它的核心贡献，是把传统“谁能产出更多 accepted tokens”推广为“谁能产出更多**及时且有价值**的 accepted tokens”。但其 client-level service model 仍然是线性 SD 下的 (\mu_i(S_i,\alpha_i))。

这两类工作的共同前提是：

**(S_i) 是一个线性 budget。**

也就是说，系统默认：给 client 更多的 (S_i)，就等价于允许它往前更长地 speculative draft；client 的未来搜索空间是“一条链”，不是“一个结构化 frontier”。

而你提出的问题，正是对这个前提的挑战。

---

## 2. 核心观察

在传统 speculative decoding 调度系统中，真正稀缺的通常不是 drafter 算力，而是 target / verifier 的验证算力。draft 端通常更便宜、更充足，系统真正需要优化的是：

**如何让有限 verifier compute 尽可能换回更多被接受的 token。**

因此，原始 (S_i) 的本质，并不是“给 drafter 派多少活”，而是：

**给某个 client 分配多少 verifier-side speculative budget。**

这个理解在普通线性 SD 中已经成立；只是因为 client 内部只有“线性前瞻”一种使用方式，所以 (S_i) 的含义看起来像“长度控制”。

但如果引入 SSD / speculative tree 机制，情况就变了。

在 SSD/tree setting 中，client 不再只能把预算花在线性草稿链上；它可以把同样的预算内部映射为：

- 更深的前瞻；
- 更宽的分支；
- 更大的 branch frontier；
- 或者某种 depth/width 的混合扩展。

于是，**(S_i) 的形式可以不变，但它的语义已经变了。**

它不再只是“线性 token 数”，而更接近：

**统一的 speculative budget（unified speculative budget）**。

这个预算在 client 内部可被实现为不同形态的未来搜索空间。

这就是目前整个 idea 的真正核心。

---

## 3. 研究问题的本质变化

### 3.1 旧问题

在 GoodSpeed / G-FAST 的旧问题中，系统做的是：

在多个 client 之间分配线性 budget (S_i)，使得长期 average goodput 或 timely goodput 最大。每个 client 的收益由线性 SD 的 accepted length 模型给出。

换句话说，旧问题默认：

**给定 (S_i) 后，client-level service model 已经固定。**

调度器只负责“跨 client 分多少”，不负责“client 内部怎么用”。

### 3.2 新问题

你的 idea 认为：在 SSD/tree regime 下，这个假设可能不再成立。

因为给定同一个 (S_i)，不同 client 可能把它转化为截然不同的未来探索结构，最终带来的 verifier-side accepted utility 也会显著不同。于是调度器再把 (S_i) 当作一个单纯的线性长度变量，可能已经发生了**结构性失配**。

因此，新问题不是简单地“再设计一个更好的 (S_i) 调度器”，而是：

**研究当 (S_i) 从线性 length budget 变为 unified speculative budget 时，原有的多 client 调度结构是否发生变化。**

这比普通调度优化更深，因为它不是在改目标函数，而是在改**资源变量本身的服务语义**。

---

## 4. 当前 idea 的正式研究命题

可以把你的主命题写成如下形式：

> 在多 client、单 verifier 的 distributed speculative decoding 系统中，当 client 能够在 SSD/tree 机制下将 verifier 分配的统一 speculative budget (S_i) 自适应映射为更深、更宽或混合的未来探索结构时，如何在有限 verifier 预算下分配各 client 的 (S_i)，使系统的长期 fresh accepted utility 最大？
> 

如果压缩成一句话，就是：

**Freshness-aware scheduling over unified speculative budgets under adaptive client-side expansion.**

这里最重要的不是词，而是三个研究含义：

第一，(S_i) 继续保留，避免一开始变量爆炸。

第二，(S_i) 的解释从线性长度推广为统一预算。

第三，client 内部 expansion policy 不再是固定黑箱，而成为影响系统最优分配的关键因素。

---

## 5. 与现有工作的关系

### 5.1 与 GoodSpeed 的关系

GoodSpeed 是这个框架的直接基础。它说明：

- verifier 是瓶颈；
- 多 client 之间的预算分配是合理研究对象；
- gradient scheduling / utility maximization 是可行的主线。

但 GoodSpeed 仍然建立在“(S_i) = 线性 draft length”的隐含前提上。因此你的工作不是替代 GoodSpeed，而是把它**推广到 SSD/tree regime**。

更准确地说：

**GoodSpeed 是 unified speculative budget 问题在线性 SD 下的一个特例。**

### 5.2 与 G-FAST 的关系

G-FAST 引入 freshness-aware utility，也就是把 accepted goodput 进一步乘以 freshness 函数，并用 log utility + gradient scheduling 追求长期比例公平。它定义的 timely goodput 目标，为你的工作提供了更符合实时场景的系统目标。

但 G-FAST 的 client-level service abstraction 同样是线性的。你的扩展在 G-FAST 语境下可以表达为：

原文的

[

y_i(t)=\mu_i(S_i(t),\alpha_i(t))\cdot \Phi(\Delta_i(t))

]

被推广为

[

y_i^{\text{SSD}}(t)=\mu_i^{\text{SSD}}(S_i(t),\xi_i(t))\cdot \Phi(\Delta_i(t)),

]

其中 (\xi_i(t)) 表示 client 内部 frontier / tree / branch-quality 状态。

因此，你的工作相对于 G-FAST 的本质，不是再加一个新的 freshness term，而是：

**把 freshness-aware scheduling 的 client-level service model 从 linear SD 推广到 adaptive SSD/tree SD。**

---

## 6. 研究假设与核心科学问题

你的 idea 能否成立，取决于以下中心假设是否为真：

### 假设 H1：统一预算假设

在 SSD/tree setting 下，保留单一变量 (S_i) 是合理的；虽然 client 内部实现复杂，但从 verifier 视角仍可把其理解为一个统一 speculative budget。

### 假设 H2：结构性失配假设

在 SSD/tree regime 下，继续把 (S_i) 当作线性长度预算进行调度，会产生系统性次优甚至错误的资源分配。

### 假设 H3：结构性收益假设

允许 client 自适应地把 (S_i) 用于不同 frontier 扩展形态，可以显著提升 verifier-side accepted utility，尤其在 freshness-sensitive 条件下更明显。

### 假设 H4：调度结构变化假设

在 unified speculative budget 语义下，最优分配结构不再仅由 acceptance rate (\alpha_i) 决定，还受到 frontier quality、expansion efficiency、freshness decay 等因素共同影响。

如果 H2 和 H3 不能成立，这个 idea 会明显缩水，退化成“对 (S_i) 的更优雅解释”。如果 H2/H3/H4 都成立，这个 idea 才真正成为一个新问题定义。

---

## 7. 形式化建模方向

建议建模时不要一开始就把 depth、width、frontier size 全部显式抛出来，而是采用“两层抽象”的方式。

### 7.1 上层：系统调度问题

上层依然是一个多 client 调度问题。给定总 verifier 预算 (C)，每时隙选择各 client 的 (S_i(t))，满足

[

\sum_i S_i(t)\le C.

]

长期目标可以沿用 G-FAST 风格：

[

\max \sum_i U(\bar y_i).

]

如果强调 freshness，就定义

[

y_i(t)=\mu_i^{\text{SSD}}(S_i(t),\xi_i(t))\cdot \Phi(\Delta_i(t)).

]

如果先不引入 freshness，也可以先做 GoodSpeed 风格的

[

y_i(t)=\mu_i^{\text{SSD}}(S_i(t),\xi_i(t)).

]

这里关键是：

**上层调度变量仍然只是 (S_i)**。

### 7.2 下层：client 内部 expansion policy

给定某个 client 获得预算 (S_i)，其内部可以用策略 (\pi_i) 把预算转化为某种 frontier expansion。于是产生：

[

\mu_i^{\text{SSD}}(S_i,\xi_i;\pi_i).

]

这一步有两种研究路径。

第一种，固定 (\pi_i) 为若干可控 heuristic，例如：

- 深度优先 expansion；
- 宽度优先 expansion；
- 混合 expansion；
- frontier-quality-aware expansion。

第二种，把 (\pi_i) 也纳入优化。

从现实性看，第一阶段应该走第一种。先证明结构性差异存在，再考虑联合优化。

---

## 8. 研究贡献的理想形态

如果这个工作做成功，最核心的贡献应该是以下三条，而不是只说“我们做了一个新调度器”。

### 贡献 1：问题定义层面的推广

提出 unified speculative budget 的概念，把 verifier-side (S_i) 从线性 draft length 推广为可在 SSD/tree 下自适应实现的统一未来探索预算。

### 贡献 2：结构性结论

证明或实验性展示：在 SSD/tree regime 下，沿用线性 (S_i) 语义会导致系统性失配；最优调度结构发生变化。

### 贡献 3：新调度框架

在 freshness-aware 或 goodput-aware 的系统目标下，设计一种面向 unified speculative budget 的 scheduling 方法，并证明/验证其优于线性-budget baseline。

注意，这三条中最重要的是第二条。没有第二条，第一条和第三条很容易被看成表述与 heuristic。

---

## 9. 最小可验证研究路径

现在最适合的不是直接写 full theory，而是先做一个**最小验证闭环**。

### 阶段 A：建立简化 simulator

构造一个多 client、单 verifier 的 SSD/tree simulator。每个 client 有：

- acceptance profile；
- frontier expansion policy；
- freshness state（可选）；
- verifier budget (S_i)。

比较两类系统：

1. **Linear-Budget Scheduler**
    
    仍把 (S_i) 当作线性 SD length 的代理变量进行调度。
    
2. **Unified-Budget Scheduler**
    
    允许 client 把 (S_i) 映射到 tree/frontier expansion，并按其真实 SSD 收益反馈进行调度。
    

### 阶段 B：寻找结构性分离

你要找的不是小幅度平均收益提升，而是**regime change**。例如：

- 在相同 target budget 下，Unified-Budget 明显提升 accepted utility；
- 提升主要出现在某些 acceptance heterogeneity / freshness decay / load 区间；
- Linear-Budget 的 allocation 在这些区间表现出系统性误配。

### 阶段 C：建立简化理论

在一个非常简化的 two-client 或 finite-action setting 下，证明至少一个结构性命题，例如：

- 线性 (\mu_i(S_i)) 与树形 (\mu_i^{tree}(S_i)) 诱导出不同的最优 allocation ordering；
- 或者最优分配阈值不再仅由 (\alpha_i) 决定。

只要能证明一个干净的小命题，就足以显著提高论文硬度。

---

## 10. 评估指标

这个项目不能只看 throughput。建议至少测以下指标：

第一，accepted tokens / verifier compute。

这是最基础的 target-side资源效率。

第二，fresh accepted utility。

如果走 G-FAST 方向，这是核心指标。

第三，wasted verification attention。

即 verifier 在低质量 frontier 上花掉的预算。

第四，wasted speculative expansion。

如果 client 预扩展很多最终未被有效消费的 frontier，这部分也应统计。

第五，公平性指标。

如果引入 utility maximization，可看 Jain’s fairness index 或 proportional fairness 相关指标。

真正重要的是：要证明 unified-budget 调度的收益来自**更好的结构理解**，而不是简单做了更多计算。

---

## 11. 风险分析

这项研究最大的风险不是技术实现，而是学术贡献可能塌缩。主要有四类风险。

### 风险 1：只有语义重解释，没有结构性新结果

这是最大风险。若最终只能说“(S_i) 也可以理解成 tree budget”，但调度和结果没有本质变化，则论文价值会明显下降。

### 风险 2：复杂性被隐藏而非解决

如果你继续只优化 (S_i)，但 client 内部 expansion 完全依赖黑箱 heuristic，审稿人可能会质疑你只是把真实难点藏到了下层。

### 风险 3：收益不够大

即便 unified-budget 更合理，如果实验上只比线性调度提高 3%-5%，而且不稳定，那很难支撑高水平投稿。

### 风险 4：理论过重导致无法收敛

如果一开始就试图建立完整 fluid-limit / asymptotic optimality 理论，项目可能陷入证明泥潭。更现实的是先做简化结构结论，再决定是否扩展。

---

## 12. 学术定位评估

客观讲，这个 idea 的性质是：

**高风险，中高上限。**

它比 GoodSpeed 或 G-FAST 风格的“在既有 client-level abstraction 上做调度”更有野心，因为它直接质疑了资源变量的服务语义；但它也更危险，因为很容易最后只剩一个优雅的表述，没有对应的硬结果。

和现有工作相比，可以这样判断：

- 相比 GoodSpeed：你的 idea 更深，但更不稳。
- 相比 G-FAST：你的 idea 在 abstraction 层更强，但 freshness-aware story 不如 G-FAST 那样天然清晰。
- 作为论文题眼：它有潜力。
- 作为已经成熟的 paper idea：目前还不是。

这个方向真正值得做的前提，不是它看上去“新”，而是你能够用实验或理论证明：

**线性 (S_i) 视角在 SSD/tree regime 下确实失效。**

这是整个项目的生死线。

---

## 13. 建议的研究路线图

### 短期（1–2 周）

完成一页 problem statement，明确：

- 系统模型；
- 旧问题 vs 新问题；
- unified (S_i) 的定义；
- 主要假设与目标指标。

### 中期（2–4 周）

实现最小 simulator，先不做复杂理论。验证是否存在明显 regime change。

### 中期第二阶段（4–6 周）

固定几类 expansion policy，做系统性 ablation：

- depth-heavy；
- width-heavy；
- mixed；
- linear baseline。

### 后期（6–8 周）

若实验结果成立，再写简化理论结论；若不成立，尽早收缩为“经验性系统论文”或放弃该方向。

---

## 14. 最终判断

目前我们的 idea 可以总结为：

> 我们并不是简单地为 SSD/tree decoding 设计一个新的调度器，而是在提出一个更基本的问题：在 SSD/tree regime 下，verifier-side 预算变量 (S_i) 是否仍应被视为线性 draft length，还是应被视为统一 speculative budget；如果是后者，那么多 client 调度问题的最优结构是否已经改变。
> 

这是一个真正有研究价值的问题。它的价值不在于“把 (S_i) 换个名字”，而在于：

**它怀疑现有 speculative scheduling 工作共同依赖的线性 service abstraction，是否在更强的 decoding regime 下已经不再成立。**

如果你能证明这个怀疑是对的，这个项目就有可能从一个漂亮的 framing，变成一篇有实质技术贡献的论文。

如果证明不了，它就会退化成概念重述。

这是当前最准确、也最冷静的总结。

如果你需要，我下一步可以把这份研究报告进一步压成适合导师/合作者看的版本，例如“1页摘要版”或“Problem Statement + Research Questions + Contributions”版本。