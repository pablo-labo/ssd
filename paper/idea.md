# 面向 SSD / Tree Speculation 的双层 Speculative Budget Scheduling

## 1. 核心问题

现有 multi-client speculative decoding 调度通常把每个 client 获得的预算
\(S_i\) 当成线性 speculative length：给更多 \(S_i\)，就等价于允许 client
沿一条 draft chain 往前多走几个 token。这个抽象在普通 speculative decoding
里基本合理，因为 client 内部动作几乎只有一个维度：draft 多长。

SSD / tree speculation 改变了这一点。一个 client 不再只准备一条线性草稿链，
而是在 verifier 返回前预先准备多个可能 outcome 的 frontier。于是系统里至少有
两类不同的物理动作：

- verifier 端真正要验证的线性 lookahead 长度 \(k_i\)；
- drafter 端为了支撑当前和后续 round 预铺的 branching / fan-out \(f_i\)。

这意味着原先的单变量预算抽象过粗。真正的问题不再是：

> \(S_i\) 最终应该怎样硬映射成一个 token length？

而是：

> 上层调度器是否可以继续使用一个抽象控制信号 \(S_i\)，同时让下层 client
> policy 将它转化为满足 verifier 和 drafter 双重约束的执行动作
> \((k_i, f_i)\)？

这个分层是当前 idea 的关键升级。

## 2. 三层变量

### 2.1 上层调度信号 \(S_i\)

\(S_i\) 不再被定义为物理 token 长度，也不直接等于 tree size。
它是 scheduler-side control knob，用来表达系统在当前 round 希望给 client
\(i\) 多少 speculative opportunity、priority 或 aggressiveness。

保留 \(S_i\) 的价值是：

- 上层调度仍然可以保持简洁；
- 不需要把 scheduler 暴露给每个 client 的全部 frontier 细节；
- client 可以根据本地状态把同一份调度信号转成不同执行形态。

因此，统一的不是物理约束，而是调度器和 client 之间的控制接口。

### 2.2 Verifier-side action \(k_i\)

\(k_i\) 是 verifier 端真正执行的线性验证长度。它受到全局 verifier
瓶颈约束：

\[
\sum_i k_i(t) \le C.
\]

这里 \(C\) 是每个 scheduling slot 内 verifier 可承受的总验证能力。旧的
GoodSpeed-style 线性模型中，\(S_i\) 实际上承担的就是这个 \(k_i\) 角色。

### 2.3 Drafter-side action \(f_i\)

\(f_i\) 表示 drafter 为当前和未来可能路径准备的 fan-out / branching 强度。
它不主要受全局 verifier 限制，而受 client 本地 draft-side compute 或 latency
window 限制。

对每个 client \(i\)，我们写成：

\[
g_i(k_i(t), f_i(t); \xi_i(t)) \le c_i.
\]

其中：

- \(c_i\)：client \(i\) 的本地 drafter-side 预算；
- \(\xi_i(t)\)：client 状态，例如 draft model speed、prefix length、batch
  size、当前 cache/frontier 状态、机器负载、outcome uncertainty；
- \(g_i\)：实现 lookahead \(k_i\) 和 fan-out \(f_i\) 所需的 drafter cost。

这个约束把 SSD 中的关键事实显式化：fan-out 的上限来自 drafter 在 verifier
完成前最多能准备多少 outcome，而不是来自 verifier token budget 本身。

## 3. 新系统模型

每个 slot 中，上层 scheduler 给出抽象信号 \(S_i(t)\)。client-side policy
将其转成可执行动作：

\[
(k_i(t), f_i(t)) = \pi_i(S_i(t), \xi_i(t)).
\]

执行动作必须满足：

\[
\sum_i k_i(t) \le C,
\]

以及：

\[
g_i(k_i(t), f_i(t); \xi_i(t)) \le c_i,\quad \forall i.
\]

系统随后获得 realized goodput：

\[
y_i(t) = \mu_i^{SSD}(k_i(t), f_i(t), \xi_i(t)).
\]

长期目标可以写成：

\[
\max \sum_i U(\bar y_i),
\]

其中 \(\bar y_i\) 是 client \(i\) 的长期平均 realized goodput。

这个版本比直接写 \(\mu_i^{SSD}(S_i, \xi_i)\) 更扎实，因为它把隐藏在
\(S_i\) 后面的物理执行动作显式拆出来了。

## 4. \(S_i\) 如何进入下层 policy

如果 \(S_i\) 既不等于 \(k_i\)，也不等于 \(f_i\)，就必须明确它怎样影响
\((k_i, f_i)\)。否则 \(S_i\) 会显得太虚。

当前最干净的定义是：\(S_i\) 是 client 可支配的 abstract speculative signal，
client 在本地状态和约束下选择最优执行动作。

一个可执行版本是：

\[
(k_i, f_i)
= \arg\max_{k,f}\ \mu_i^{SSD}(k, f, \xi_i)
\]

\[
\text{s.t.}\quad
g_i(k, f; \xi_i) \le h_i(S_i, c_i),
\]

并且上层调度还必须保证 resulting \(k_i\) 满足全局 verifier 约束
\(\sum_i k_i \le C\)。

这里 \(h_i(S_i, c_i)\) 可以先取一个简单形式，例如
\(\min(S_i, c_i)\)，也可以被解释为 \(S_i\) 对 client 本地 drafter
预算可用比例或 aggressiveness 的调节。关键是：\(S_i\) 控制 policy 的激进程度，
而不是直接指定物理长度。

更简单的 first-pass rule-based policy 也可以作为 baseline：

\[
k_i = \lfloor \lambda_i S_i \rfloor,\quad
f_i = \lfloor (1-\lambda_i) S_i \rfloor,
\]

再通过 \(g_i(k_i,f_i;\xi_i)\le c_i\) 做 clipping 或 projection。

但从论文主线看，cost-aware policy 更适合当核心定义，因为它把
"abstract budget -> executable frontier" 这件事说清楚了。

## 5. Drafter cost model

当前最缺的是 \(g_i\) 的可落地形式。一个最小模型是：

\[
g_i(k_i, f_i) = a_i k_i + b_i k_i f_i.
\]

直觉是：

- \(a_i k_i\)：沿主链准备 \(k_i\) 个 step 的基础成本；
- \(b_i k_i f_i\)：在每个 depth 上额外准备 fan-out outcome 的 branching 成本。

如果后续把 fan-out 写成逐层结构 \(F_{i,d}\)，可以推广为：

\[
g_i(k_i, \{F_{i,d}\}) =
a_i k_i + b_i \sum_{d=0}^{k_i} F_{i,d}.
\]

这个形式更接近 tree/frontier 执行：总 branching cost 由各层展开的候选数决定。
第一阶段可以先使用 \(a_i k_i + b_i k_i f_i\)，因为它足以表达
depth-width tradeoff。

## 6. 为什么不能把 \(S_i\) 硬映射成 \(k_i\)

硬映射 \(S_i \to k_i\) 会丢掉两个关键结构。

第一，它丢掉 drafter-side tradeoff。同样的 verifier lookahead \(k_i\)，不同
\(f_i\) 会产生不同后果：小 fan-out 当前便宜，但未来 cache hit 或 async gain
可能弱；大 fan-out 当前更重，但可能让 verifier 返回后更快衔接下一轮。

第二，它把两种瓶颈混成一种。\(k_i\) 主要受全局 verifier 能力限制，
\(f_i\) 主要受本地 drafter 能力和时延窗口限制。二者来源、粒度和作用位置都不同。
把它们压回单一长度变量会掩盖 SSD 的问题结构。

因此，更合理的定义是：

> \(S_i\) 是上层调度信号；\(k_i\) 和 \(f_i\) 是下层执行动作；
> verifier 约束落在 \(\sum_i k_i\) 上；drafter 约束落在
> \(g_i(k_i,f_i;\xi_i)\) 上。

## 7. 研究问题

这个 framing 产生三个核心科学问题。

### Q1. 双资源约束是否改变最优分配结构？

旧模型只有一个动作变量和一个约束：

\[
\sum_i S_i \le C.
\]

新模型有一个抽象调度信号、两个执行动作和两类瓶颈：

\[
\sum_i k_i \le C,
\quad
g_i(k_i,f_i;\xi_i)\le c_i.
\]

需要证明或实验展示：当 client 的 \(g_i\)、\(\xi_i\)、\(\pi_i\) 不同时，
线性长度调度会产生系统性 misallocation。

### Q2. \(S_i\)-conditioned policy 如何设计？

我们需要比较至少三类 policy：

- depth-heavy：更偏向大 \(k\)、小 \(f\)，优先当前 verifier throughput；
- width-heavy：更偏向小 \(k\)、大 \(f\)，优先未来 frontier/cache benefit；
- cost-aware：在 \(g_i(k,f;\xi_i)\le h_i(S_i,c_i)\) 下最大化
  \(\mu_i^{SSD}(k,f,\xi_i)\)。

这能把 "unified budget" 从概念话变成可执行算法。

### Q3. 如何从真实 SSD 运行校准 \(g_i\) 和 \(\mu_i^{SSD}\)？

需要从真实 async SSD runs 中拟合：

- \(k,f\) 对 accepted suffix length 的影响；
- \(k,f\) 对 cache hit / miss 行为的影响；
- \(k,f\) 对 draft latency 和 target verify time 的影响；
- 不同 workload / prompt distribution 下的参数异质性。

如果实测曲线几乎线性，论文主张会变弱；如果不同 shape 诱导出明显不同的
marginal goodput 和 cost tradeoff，这个方向就成立。

## 8. 最小可验证路径

### 阶段 A：重写 simulator 变量语义

把当前 simulator 从 "budget \(S\) 直接产生 service" 改为：

1. scheduler 输出 \(S_i\)；
2. client policy 输出 \((k_i,f_i)\)；
3. 环境检查 \(\sum_i k_i\le C\) 和 \(g_i(k_i,f_i;\xi_i)\le c_i\)；
4. service model 输出 \(\mu_i^{SSD}(k_i,f_i,\xi_i)\)。

### 阶段 B：结构性分离实验

构造 two-client case：

- client A 线性 acceptance 更高，但 drafter cost 高或 fan-out 效率差；
- client B 线性 acceptance 较低，但在某些 \((k,f)\) shape 下 frontier 效率更高。

目标是展示：linear scheduler 和 two-level SSD-aware scheduler 给出相反的
allocation ordering。

### 阶段 C：真实 shape grid 校准

用真实 SSD runs 扫描 \((k,f)\)：

- accepted suffix mean；
- cache hit rate；
- draft-side timing；
- verifier-side timing；
- accepted tokens per verify second；
- accepted tokens per draft cost proxy。

这些数据用于拟合 \(g_i\) 和 \(\mu_i^{SSD}\)，替代手写 service curve。

## 9. 预期贡献

如果这个方向成立，贡献应该写成三层。

第一，问题定义：指出 SSD / tree speculation 下，单一线性 budget 不足以刻画
multi-client scheduling；提出上层 \(S_i\)、下层 \((k_i,f_i)\) 的双层控制模型。

第二，结构性结果：证明或展示线性长度调度在双资源耦合约束下会 misallocate，
并给出 allocation reversal 的条件。

第三，调度方法：设计 SSD-aware policy，把抽象 \(S_i\) 映射为满足 verifier
和 drafter 约束的 \((k_i,f_i)\)，并用真实 SSD profile 校准。

## 10. 风险

最大风险是 \(S_i\) 变成一个过于抽象的变量。解决办法是必须给出明确的
\(\pi_i(S_i,\xi_i)\)，至少包括一个可运行的 rule-based 版本和一个 cost-aware
版本。

第二个风险是 \(g_i\) 不可校准。如果 draft-side timing 或 fan-out cost 无法可靠
测量，可以先用 proxy，例如 draft tokens generated、frontier node count、
cache write count 或 draft step latency。

第三个风险是收益只来自更强的 local policy，而不是调度结构。实验中必须包含
固定 \((k,f)\)、linear \(S\to k\)、rule-based \(\pi_i\)、cost-aware \(\pi_i\)
等 ablation，说明增益来自双层建模和跨 client 分配，而不是单纯调参。

## 11. 当前最准确的一句话

在 SSD setting 中，问题的关键不在于 verifier-side budget \(S_i\) 是否仍线性，
而在于原先单一线性资源抽象已不足以刻画系统真实瓶颈。实际系统同时存在两类约束：
全局 verifier 预算决定各 client 可提交的线性 lookahead \(k_i\)，本地 drafter
预算限制其可支持的 fan-out \(f_i\) 及其与 \(k_i\) 的组合。因此，更合理的建模不是
将 \(S_i\) 硬映射为 \(k_i\)，而是将 \(S_i\) 作为上层调度抽象变量，通过下层策略
映射为满足双重约束的执行动作 \((k_i,f_i)\)。
