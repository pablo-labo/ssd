# Block 1 / A2 最终详细版：单 client 下 (\tilde\mu^{\mathrm{SSD}}(k)) 的结构

## 0. 我们到底要证明什么？

我们关心一个问题：

> 在单个 client 的 SSD 中，lookahead 长度 (k) 是不是越大越好？

直觉上不是。

因为 (k) 变大有两个相反效果：

第一，**hit 的时候收益更大**。如果 cache hit，并且 drafted tokens 被接受，那么更长的 (k) 可以一次推进更多 token。

第二，**miss 的概率变大**。因为总 drafter 时间有限，(k) 越大，每一层能分到的 fan-out 越少；同时 drafter 要生成更长链条，能准备的 cache budget 反而下降。你的 roadmap 里也正是把 Block 1 定义为地基：目标是揭示 (\tilde\mu^{\mathrm{SSD}}(k)) 的 unimodal 结构，并刻画 (k^*) 对 ((\alpha,r,a,b,T_V)) 的依赖。

所以 A2 最终要得到三件事：

$$
\begin{aligned}
\boxed{ \\
\text{FOC: marginal hit benefit = marginal miss cost} \\
}
\end{aligned}
$$

$$
\begin{aligned}
\boxed{ \\
\text{在一个可检查条件下，}\tilde\mu^{\mathrm{SSD}}(k)\text{ 是 single-peaked} \\
}
\end{aligned}
$$

$$
\begin{aligned}
\boxed{ \\
k^* \\
&= \frac{r}{\log(1/\alpha)}\log T_V \\
+ \\
O(\log\log T_V) \\
}
\end{aligned}
$$

注意：这里我们不硬说“无条件严格证明 unimodality”。更稳的版本是：

> (q'(k)>0) 可以证明；(q''(k)\ge 0) 作为 finite-(T_V) 的 regularity assumption；大 (T_V) 渐近结论单独证明，不依赖 (q''\ge0)。

---

# 1. 基础设定

考虑单个 client。固定参数：

$$
0<\alpha<1,\qquad r>0,\qquad a>0,\qquad b>0,\qquad T_V>0.
$$

含义如下：

$$
\alpha=\text{draft token 被 target 接受的概率},
$$

$$
r=\text{cache hit power-law exponent},
$$

$$
a,b=\text{drafter timing cost parameters},
$$

$$
T_V=\text{verifier wall time}.
$$

这里 (k) 是 verifier lookahead，也就是 speculative chain 的长度。

---

# 2. 为什么要定义有效区间？

你的公式里会出现：

$$
B(k)=\frac{T_V-ak}{bk}.
$$

它表示：在 verifier 工作的时间里，drafter 最多能准备多少个 verification outcomes。

但是这个式子要求：

$$
T_V-ak>0.
$$

所以至少需要：

$$
0<k<\frac{T_V}{a}.
$$

可是这还不够。因为 Saguaro 的 cache miss power-law 假设是：

$$
1-p_{\mathrm{hit}}(F)=F^{-r}.
$$

这个模型只有在 fan-out (F\ge1) 时才有意义。Saguaro 里 geometric fan-out 的 base fan-out 是 (F_0)，因此我们还需要：

$$
F_0(k)\ge1.
$$

后面会看到：

$$
F_0(k)=\frac{B(k)}{N(k)}.
$$

所以有效区间定义为：

$$
\begin{aligned}
\boxed{ \\
\mathcal I \\
&= \left{ \\
k\in(0,T_V/a): \\
F_0(k)\ge1 \\
\right} \\
}
\end{aligned}
$$

也就是：

$$
\begin{aligned}
\boxed{ \\
\mathcal I \\
&= \left{ \\
k\in(0,T_V/a): \\
B(k)\ge N(k) \\
\right}. \\
}
\end{aligned}
$$

这句话很重要。它的意思是：我们只在 power-law cache model 有效的区域里做数学分析。否则 (q(k)) 可能被公式算成大于 1，而概率不可能大于 1。

---

# 3. 从 Saguaro geometric fan-out 写出 (p_{\mathrm{hit}})

Saguaro Theorem 12 说：在 power-law cache hit 假设下，最优 fan-out shape 是 capped geometric series。也就是对于 (j<k)：

$$
F_j=F_0\alpha^{j/(1+r)},
$$

而最后一层是：

$$
F_k=F_0\alpha^{k/(1+r)}(1-\alpha)^{-1/(1+r)}.
$$

这是从 Saguaro 原文来的核心工具：它说明在 budget 约束下，fan-out 不应该平均分配，而应该按 capped geometric 形状分配。

为了简化，定义：

$$
\begin{aligned}
\boxed{ \\
\beta:=\alpha^{1/(1+r)}. \\
}
\end{aligned}
$$

于是：

$$
F_j=F_0\beta^j,\qquad j<k.
$$

最后一层：

$$
F_k=F_0\beta^k(1-\alpha)^{-1/(1+r)}.
$$

---

## 3.1 cache miss probability 怎么写？

cache hit 的反面是 cache miss。

对于 (j<k)，接受恰好 (j) 个 tokens 的概率是：

$$
\alpha^j(1-\alpha).
$$

这一层的 cache miss 概率是：

$$
F_j^{-r}.
$$

所以中间层贡献为：

$$
(1-\alpha)\sum_{j=0}^{k-1}\alpha^j F_j^{-r}.
$$

最后一种情况是：全部 (k) 个 tokens 都被接受。概率是：

$$
\alpha^k.
$$

最后层的 miss 概率是：

$$
F_k^{-r}.
$$

所以总 miss probability 是：

$$
\begin{aligned}
q(k,B) \\
&= 1-p_{\mathrm{hit}}(k,B) \\
&= \alpha^kF_k^{-r} \\
+ \\
(1-\alpha)\sum_{j=0}^{k-1}\alpha^jF_j^{-r}.
\end{aligned}
$$

---

## 3.2 代入 (F_j)

先看 (j<k) 的项。

$$
F_j=F_0\beta^j.
$$

所以：

$$
F_j^{-r}=F_0^{-r}\beta^{-jr}.
$$

又因为：

$$
\beta=\alpha^{1/(1+r)},
$$

所以：

$$
\begin{aligned}
\beta^{-jr} \\
&= \alpha^{-jr/(1+r)}. \\
\end{aligned}
$$

因此：

$$
\begin{aligned}
\alpha^jF_j^{-r} \\
&= F_0^{-r}\alpha^{j-jr/(1+r)} \\
&= F_0^{-r}\alpha^{j/(1+r)} \\
&= F_0^{-r}\beta^j. \\
\end{aligned}
$$

于是中间层贡献变成：

$$
(1-\alpha)F_0^{-r}\sum_{j=0}^{k-1}\beta^j.
$$

几何级数：

$$
\begin{aligned}
\sum_{j=0}^{k-1}\beta^j \\
&= \frac{1-\beta^k}{1-\beta}. \\
\end{aligned}
$$

所以中间层贡献是：

$$
(1-\alpha)F_0^{-r}\frac{1-\beta^k}{1-\beta}.
$$

---

## 3.3 最后一层项

最后一层：

$$
F_k=F_0\beta^k(1-\alpha)^{-1/(1+r)}.
$$

所以：

$$
\begin{aligned}
F_k^{-r} \\
&= F_0^{-r}\beta^{-kr}(1-\alpha)^{r/(1+r)}. \\
\end{aligned}
$$

乘上 (\alpha^k)：

$$
\begin{aligned}
\alpha^kF_k^{-r} \\
&= F_0^{-r}\alpha^k\beta^{-kr}(1-\alpha)^{r/(1+r)}. \\
\end{aligned}
$$

因为：

$$
\begin{aligned}
\alpha^k\beta^{-kr} \\
&= \alpha^k\alpha^{-kr/(1+r)} \\
&= \alpha^{k/(1+r)} \\
&= \beta^k. \\
\end{aligned}
$$

所以最后一层贡献是：

$$
F_0^{-r}(1-\alpha)^{r/(1+r)}\beta^k.
$$

---

## 3.4 合并得到 (D(k))

因此：

$$
\begin{aligned}
q(k,B) \\
&= F_0^{-r} \\
\left[ \\
(1-\alpha)^{r/(1+r)}\beta^k \\
+ \\
(1-\alpha)\frac{1-\beta^k}{1-\beta} \\
\right].
\end{aligned}
$$

定义：

$$
\begin{aligned}
\boxed{ \\
D(k) \\
:= \\
(1-\alpha)^{r/(1+r)}\beta^k \\
+ \\
(1-\alpha)\frac{1-\beta^k}{1-\beta}. \\
}
\end{aligned}
$$

于是：

$$
\begin{aligned}
\boxed{ \\
q(k,B)=F_0^{-r}D(k). \\
}
\end{aligned}
$$

这一步的意义是：我们把复杂的 cache miss probability 写成了一个很干净的形式。

---

# 4. 用 (B(k)) 消去 (F_0)

Saguaro 的 budget equation 是：

$$
\sum_{j=0}^{k}F_j=B.
$$

代入 geometric fan-out：

$$
\begin{aligned}
B \\
= \\
F_0\beta^k(1-\alpha)^{-1/(1+r)} \\
+ \\
\sum_{j=0}^{k-1}F_0\beta^j.
\end{aligned}
$$

所以：

$$
\begin{aligned}
B \\
= \\
F_0 \\
\left[ \\
(1-\alpha)^{-1/(1+r)}\beta^k \\
+ \\
\frac{1-\beta^k}{1-\beta} \\
\right].
\end{aligned}
$$

定义：

$$
\begin{aligned}
\boxed{ \\
N(k) \\
:= \\
(1-\alpha)^{-1/(1+r)}\beta^k \\
+ \\
\frac{1-\beta^k}{1-\beta}. \\
}
\end{aligned}
$$

于是：

$$
\begin{aligned}
\boxed{ \\
F_0=\frac{B}{N(k)}. \\
}
\end{aligned}
$$

因此：

$$
\begin{aligned}
F_0^{-r} \\
&= \left(\frac{N(k)}{B}\right)^r. \\
\end{aligned}
$$

所以：

$$
\begin{aligned}
q(k,B) \\
&= N(k)^rD(k)B^{-r}. \\
\end{aligned}
$$

定义：

$$
\begin{aligned}
\boxed{ \\
G(k):=N(k)^rD(k). \\
}
\end{aligned}
$$

于是：

$$
\begin{aligned}
\boxed{ \\
q(k,B)=G(k)B^{-r}. \\
}
\end{aligned}
$$

现在代入你的 drafter budget：

$$
B(k)=\frac{T_V-ak}{bk}.
$$

所以：

$$
\begin{aligned}
B(k)^{-r} \\
&= \left( \\
\frac{bk}{T_V-ak} \\
\right)^r.
\end{aligned}
$$

最终得到：

$$
\begin{aligned}
\boxed{ \\
q(k) \\
&= G(k) \\
\left( \\
\frac{bk}{T_V-ak} \\
\right)^r. \\
}
\end{aligned}
$$

这就是整个 A2 的核心表达式。

它的意思是：

$$
\begin{aligned}
\text{miss probability} \\
&= \text{Saguaro cache shape factor} \\
\times \\
\text{drafter timing penalty}.
\end{aligned}
$$

---

# 5. 证明 (q'(k)>0)

这是最终版相对之前的关键改进。

我们想证明：

$$
\begin{aligned}
q(k) \\
&= G(k)h(k)^r \\
\end{aligned}
$$

严格递增，其中：

$$
h(k)=\frac{bk}{T_V-ak}.
$$

因为：

$$
\begin{aligned}
h'(k) \\
&= \frac{bT_V}{(T_V-ak)^2}>0. \\
\end{aligned}
$$

所以 (h(k)) 严格递增。

但还要证明 (G(k)) 也递增。

---

## 5.1 证明 (N'(k)>0)

回忆：

$$
\begin{aligned}
N(k) \\
&= (1-\alpha)^{-1/(1+r)}\beta^k \\
+ \\
\frac{1-\beta^k}{1-\beta}.
\end{aligned}
$$

求导：

$$
\begin{aligned}
N'(k) \\
&= ## (1-\alpha)^{-1/(1+r)}\beta^k\log\beta \\
\frac{\beta^k\log\beta}{1-\beta}.
\end{aligned}
$$

提取公因子：

$$
\begin{aligned}
N'(k) \\
&= \beta^k\log\beta \\
\left[ \\
(1-\alpha)^{-1/(1+r)} \\
&- \frac{1}{1-\beta} \\
\right].
\end{aligned}
$$

因为：

$$
0<\beta<1,
$$

所以：

$$
\log\beta<0.
$$

因此，要证明 (N'(k)>0)，只要证明括号里是负的：

$$
\begin{aligned}
(1-\alpha)^{-1/(1+r)} \\
< \\
\frac{1}{1-\beta}.
\end{aligned}
$$

两边取倒数，等价于：

$$
\begin{aligned}
(1-\alpha)^{1/(1+r)} \\
> \\
1-\beta.
\end{aligned}
$$

又因为：

$$
\beta=\alpha^{1/(1+r)}.
$$

令：

$$
y=\beta.
$$

那么：

$$
\alpha=y^{1+r}.
$$

所以要证：

$$
(1-y^{1+r})^{1/(1+r)}>1-y.
$$

两边都为正，可以同时取 (1+r) 次方：

$$
1-y^{1+r}>(1-y)^{1+r}.
$$

定义：

$$
f(y)=1-y^{1+r}-(1-y)^{1+r}.
$$

当 (y=0)：

$$
f(0)=1-0-1=0.
$$

当 (y=1)：

$$
f(1)=1-1-0=0.
$$

求导：

$$
\begin{aligned}
f'(y) \\
&= -(1+r)y^r \\
+ \\
(1+r)(1-y)^r.
\end{aligned}
$$

所以：

$$
\begin{aligned}
f'(y) \\
&= (1+r)\left[(1-y)^r-y^r\right]. \\
\end{aligned}
$$

当：

$$
0<y<\frac12,
$$

有：

$$
(1-y)^r>y^r,
$$

所以：

$$
f'(y)>0.
$$

当：

$$
\frac12<y<1,
$$

有：

$$
(1-y)^r<y^r,
$$

所以：

$$
f'(y)<0.
$$

因此 (f(y)) 先升后降，并且两端都是 0，所以中间严格大于 0：

$$
f(y)>0,\qquad y\in(0,1).
$$

也就是：

$$
1-y^{1+r}>(1-y)^{1+r}.
$$

因此：

$$
(1-\alpha)^{1/(1+r)}>1-\beta.
$$

所以：

$$
\begin{aligned}
(1-\alpha)^{-1/(1+r)} \\
< \\
\frac{1}{1-\beta}.
\end{aligned}
$$

括号为负，而 (\beta^k\log\beta<0)，所以：

$$
\begin{aligned}
\boxed{ \\
N'(k)>0. \\
}
\end{aligned}
$$

---

## 5.2 证明 (D'(k)>0)

回忆：

$$
\begin{aligned}
D(k) \\
&= (1-\alpha)^{r/(1+r)}\beta^k \\
+ \\
(1-\alpha)\frac{1-\beta^k}{1-\beta}.
\end{aligned}
$$

求导：

$$
\begin{aligned}
D'(k) \\
&= ## (1-\alpha)^{r/(1+r)}\beta^k\log\beta \\
(1-\alpha)\frac{\beta^k\log\beta}{1-\beta}.
\end{aligned}
$$

提取公因子：

$$
\begin{aligned}
D'(k) \\
&= \beta^k\log\beta \\
\left[ \\
(1-\alpha)^{r/(1+r)} \\
&- \frac{1-\alpha}{1-\beta} \\
\right].
\end{aligned}
$$

因为 (\beta^k\log\beta<0)，所以要证明 (D'(k)>0)，只要证明：

$$
\begin{aligned}
(1-\alpha)^{r/(1+r)} \\
&- \frac{1-\alpha}{1-\beta} \\
<0.
\end{aligned}
$$

即：

$$
\begin{aligned}
(1-\alpha)^{r/(1+r)} \\
< \\
\frac{1-\alpha}{1-\beta}.
\end{aligned}
$$

两边除以 ((1-\alpha)^{r/(1+r)})，得到：

$$
\begin{aligned}
1< \\
\frac{(1-\alpha)^{1/(1+r)}}{1-\beta}.
\end{aligned}
$$

也就是：

$$
(1-\alpha)^{1/(1+r)}>1-\beta.
$$

这正是前面已经证明过的不等式。

所以：

$$
\begin{aligned}
\boxed{ \\
D'(k)>0. \\
}
\end{aligned}
$$

---

## 5.3 证明 (G'(k)>0)

因为：

$$
G(k)=N(k)^rD(k).
$$

且：

$$
N(k)>0,\quad D(k)>0,\quad r>0,
$$

并且已经证明：

$$
N'(k)>0,\qquad D'(k)>0.
$$

所以：

$$
\begin{aligned}
G'(k) \\
&= rN(k)^{r-1}N'(k)D(k)+N(k)^rD'(k)>0. \\
\end{aligned}
$$

因此：

$$
\begin{aligned}
\boxed{ \\
G'(k)>0. \\
}
\end{aligned}
$$

---

## 5.4 证明 (q'(k)>0)

现在：

$$
q(k)=G(k)h(k)^r,
$$

其中：

$$
\begin{aligned}
G'(k)>0, \\
\qquad \\
h'(k)>0.
\end{aligned}
$$

求导：

$$
\begin{aligned}
q'(k) \\
&= G'(k)h(k)^r \\
+ \\
G(k)rh(k)^{r-1}h'(k).
\end{aligned}
$$

每一项都严格为正，所以：

$$
\begin{aligned}
\boxed{ \\
q'(k)>0. \\
}
\end{aligned}
$$

这一步非常重要。它说明：**随着 (k) 变大，cache miss probability 一定上升。**

但注意：这里只证明了一阶导大于 0。我们还没有证明：

$$
q''(k)\ge0.
$$

这就是后面要保留为 assumption 的部分。

---

# 6. 写出 SSD service curve

根据 SSD speedup 形式，Saguaro Theorem 7 的结构是：

$$
\begin{aligned}
\text{speedup}^{SSD} \\
&= \frac{ \\
p_{\mathrm{hit}}E_{\mathrm{hit}}+(1-p_{\mathrm{hit}})E_{\mathrm{miss}} \\
}{ \\
p_{\mathrm{hit}}\max(1,T_p)+(1-p_{\mathrm{hit}})(1+T_b) \\
}.
\end{aligned}
$$

Saguaro 论文里也强调了 cache hit rate 和 expected generated tokens 一起决定 SSD speedup。

现在我们先分析最简单的一阶版本：

$$
T_p<1,\qquad T_b=0,\qquad E_{\mathrm{miss}}=1.
$$

于是分母变成 1。

定义：

$$
\begin{aligned}
E(k):=E_{\mathrm{hit}}(k) \\
&= \frac{1-\alpha^{k+1}}{1-\alpha}. \\
\end{aligned}
$$

这个就是 capped geometric expectation。

又定义：

$$
q(k):=1-p_{\mathrm{hit}}(k).
$$

那么：

$$
p_{\mathrm{hit}}(k)=1-q(k).
$$

所以：

$$
\begin{aligned}
\tilde\mu^{\mathrm{SSD}}(k) \\
&= p_{\mathrm{hit}}(k)E(k) \\
+ \\
(1-p_{\mathrm{hit}}(k))\cdot1.
\end{aligned}
$$

代入 (q(k))：

$$
\begin{aligned}
\tilde\mu^{\mathrm{SSD}}(k) \\
&= (1-q(k))E(k)+q(k). \\
\end{aligned}
$$

整理：

$$
\begin{aligned}
\boxed{ \\
\tilde\mu^{\mathrm{SSD}}(k) \\
&= E(k)-q(k)(E(k)-1). \\
}
\end{aligned}
$$

为了简洁，下面记：

$$
u(k):=\tilde\mu^{\mathrm{SSD}}(k).
$$

所以：

$$
\begin{aligned}
\boxed{ \\
u(k)=E(k)-q(k)(E(k)-1). \\
}
\end{aligned}
$$

这句话非常重要。

它的直觉是：

$$
\begin{aligned}
\text{理想 hit 收益} \\
&- \text{miss 概率}\times\text{miss 造成的收益损失}. \\
\end{aligned}
$$

---

# 7. 求一阶导数，得到 FOC

先准备两个式子。

$$
E(k)=\frac{1-\alpha^{k+1}}{1-\alpha}.
$$

所以：

$$
\begin{aligned}
E'(k) \\
&= \frac{-\alpha^{k+1}\log\alpha}{1-\alpha} \\
&= \frac{\alpha^{k+1}\log(1/\alpha)}{1-\alpha}. \\
\end{aligned}
$$

另外：

$$
\begin{aligned}
E(k)-1 \\
&= \frac{1-\alpha^{k+1}}{1-\alpha}-1. \\
\end{aligned}
$$

通分：

$$
\begin{aligned}
E(k)-1 \\
&= \frac{1-\alpha^{k+1}-(1-\alpha)}{1-\alpha}. \\
\end{aligned}
$$

所以：

$$
\begin{aligned}
E(k)-1 \\
&= \frac{\alpha-\alpha^{k+1}}{1-\alpha} \\
&= \frac{\alpha(1-\alpha^k)}{1-\alpha}. \\
\end{aligned}
$$

现在对：

$$
u(k)=E(k)-q(k)(E(k)-1)
$$

求导。

第一项：

$$
E'(k).
$$

第二项用乘积法则：

$$
\begin{aligned}
\frac{d}{dk}\left[q(k)(E(k)-1)\right] \\
&= q'(k)(E(k)-1)+q(k)E'(k). \\
\end{aligned}
$$

所以：

$$
\begin{aligned}
u'(k) \\
&= E'(k)-q'(k)(E(k)-1)-q(k)E'(k). \\
\end{aligned}
$$

整理：

$$
\begin{aligned}
u'(k) \\
&= E'(k)(1-q(k))-q'(k)(E(k)-1). \\
\end{aligned}
$$

因为：

$$
1-q(k)=p_{\mathrm{hit}}(k),
$$

所以：

$$
\begin{aligned}
\boxed{ \\
u'(k) \\
&= ## E'(k)p_{\mathrm{hit}}(k) \\
q'(k)(E(k)-1). \\
}
\end{aligned}
$$

内部最优点 (k^*) 满足：

$$
u'(k^*)=0.
$$

因此：

$$
\begin{aligned}
E'(k^*)p_{\mathrm{hit}}(k^*) \\
&= q'(k^*)(E(k^*)-1). \\
\end{aligned}
$$

代入 (E'(k)) 和 (E(k)-1)：

$$
\begin{aligned}
\frac{\alpha^{k^*+1}\log(1/\alpha)}{1-\alpha} \\
p_{\mathrm{hit}}(k^*) \\
&= q'(k^*) \\
\frac{\alpha(1-\alpha^{k^*})}{1-\alpha}.
\end{aligned}
$$

两边约掉：

$$
\frac{\alpha}{1-\alpha}.
$$

得到：

$$
\begin{aligned}
\boxed{ \\
\alpha^{k^*}\log(1/\alpha)p_{\mathrm{hit}}(k^*) \\
&= q'(k^*)(1-\alpha^{k^*}). \\
}
\end{aligned}
$$

这就是最终 FOC。

---

# 8. FOC 的物理解释

把左边叫做：

$$
\begin{aligned}
\mathrm{MHB}(k) \\
&= \alpha^k\log(1/\alpha)p_{\mathrm{hit}}(k). \\
\end{aligned}
$$

MHB = marginal hit benefit。

它表示：多加一层 (k)，如果 cache hit，可以多吃一点 token。但这个收益要乘以 (p_{\mathrm{hit}})，因为只有 hit 了才兑现。

把右边叫做：

$$
\begin{aligned}
\mathrm{MMC}(k) \\
&= q'(k)(1-\alpha^k). \\
\end{aligned}
$$

MMC = marginal miss cost。

它表示：多加一层 (k)，miss probability 上升了 (q'(k))，而 miss 损失的规模大概是 (1-\alpha^k)。

所以 FOC 是：

$$
\begin{aligned}
\boxed{ \\
\mathrm{MHB}(k^*)=\mathrm{MMC}(k^*). \\
}
\end{aligned}
$$

中文就是：

> 最优 (k^*) 出现在“继续加深 lookahead 的边际收益”等于“继续加深 lookahead 带来的 miss 风险边际成本”的地方。

---

# 9. 为什么不无条件证明 unimodality？

我们已经证明：

$$
q'(k)>0.
$$

也就是 (k) 越大，miss probability 越高。

但要证明 (u(k)) 是 single-peaked，我们还想要：

$$
\mathrm{MHB}(k)\text{ 递减},
$$

$$
\mathrm{MMC}(k)\text{ 递增}.
$$

MHB 递减可以证明。

MMC 递增需要：

$$
q''(k)\ge0.
$$

而 (q''(k)\ge0) 对完整的：

$$
q(k)=G(k)\left(\frac{bk}{T_V-ak}\right)^r
$$

并不显然。因为 (G(k)) 里有复杂的 (\beta^k) 项。

所以最终版采取诚实写法：

$$
\begin{aligned}
\boxed{ \\
q'(k)>0\text{ 作为 lemma 证明；} \\
}
\end{aligned}
$$

$$
\begin{aligned}
\boxed{ \\
q''(k)\ge0\text{ 作为 finite-}T_V\text{ assumption。} \\
}
\end{aligned}
$$

---

# 10. Assumption：(q''(k)\ge0)

正式写：

**Assumption A2.1.** On the effective interval (\mathcal I), the cache miss probability has nondecreasing marginal slope:

$$
\begin{aligned}
\boxed{ \\
q''(k)\ge0,\qquad k\in\mathcal I. \\
}
\end{aligned}
$$

中文解释：

> 在我们分析的有效参数区间内，随着 (k) 增大，miss probability 不仅上升，而且上升速度不下降。

这可以用数值实验支撑。

---

# 11. 证明 single-peakedness

现在证明：

$$
u(k)
$$

是先升后降的。

---

## 11.1 证明 MHB 递减

定义：

$$
\begin{aligned}
M(k) \\
&= \alpha^k\log(1/\alpha)p_{\mathrm{hit}}(k). \\
\end{aligned}
$$

因为：

$$
0<\alpha<1,
$$

所以：

$$
\alpha^k
$$

严格递减。

又因为刚才证明了：

$$
q'(k)>0,
$$

所以：

$$
p_{\mathrm{hit}}(k)=1-q(k)
$$

严格递减。

两个正的递减因子相乘仍然递减。更严格地，求导：

$$
\begin{aligned}
M'(k) \\
&= \log(1/\alpha) \\
\left[ \\
\alpha^k\log\alpha\cdot p_{\mathrm{hit}}(k) \\
+ \\
\alpha^k p_{\mathrm{hit}}'(k) \\
\right].
\end{aligned}
$$

其中：

$$
\log(1/\alpha)>0,
$$

$$
\log\alpha<0,
$$

$$
p_{\mathrm{hit}}(k)>0,
$$

$$
p_{\mathrm{hit}}'(k)=-q'(k)<0.
$$

所以括号里两项都小于 0，因此：

$$
\begin{aligned}
\boxed{ \\
M'(k)<0. \\
}
\end{aligned}
$$

也就是：

$$
\begin{aligned}
\boxed{ \\
\mathrm{MHB}(k)\text{ 严格递减。} \\
}
\end{aligned}
$$

---

## 11.2 证明 MMC 递增

定义：

$$
C(k)=q'(k)(1-\alpha^k).
$$

求导：

$$
\begin{aligned}
C'(k) \\
&= q''(k)(1-\alpha^k) \\
+ \\
q'(k)\frac{d}{dk}(1-\alpha^k).
\end{aligned}
$$

而：

$$
\begin{aligned}
\frac{d}{dk}(1-\alpha^k) \\
&= -\alpha^k\log\alpha \\
&= \alpha^k\log(1/\alpha)>0. \\
\end{aligned}
$$

所以：

$$
\begin{aligned}
C'(k) \\
&= q''(k)(1-\alpha^k) \\
+ \\
q'(k)\alpha^k\log(1/\alpha).
\end{aligned}
$$

在 Assumption A2.1 下：

$$
q''(k)\ge0.
$$

并且已经证明：

$$
q'(k)>0.
$$

所以：

$$
C'(k)>0.
$$

因此：

$$
\begin{aligned}
\boxed{ \\
\mathrm{MMC}(k)\text{ 严格递增。} \\
}
\end{aligned}
$$

---

## 11.3 唯一交点

FOC 是：

$$
M(k)=C(k).
$$

我们已经知道：

$$
\begin{aligned}
M(k)\downarrow, \\
\qquad \\
C(k)\uparrow.
\end{aligned}
$$

所以它们最多交一次。

再看边界。

当 (k\to0^+)：

$$
1-\alpha^k\to0.
$$

所以：

$$
C(k)=q'(k)(1-\alpha^k)\to0.
$$

而：

$$
M(k)\to \log(1/\alpha)p_{\mathrm{hit}}(0^+)>0.
$$

所以左端：

$$
M(k)>C(k).
$$

当 (k) 接近有效区间右边界时，cache budget 已经很紧，miss cost 会主导；形式上我们要求右端存在：

$$
M(k)<C(k).
$$

这通常由有效区间右端的 (F_0(k)\to1) 或 numerical verification 支撑。

因此由连续性，存在唯一交点：

$$
k^*.
$$

---

## 11.4 推出 single-peaked

前面有：

$$
\begin{aligned}
u'(k) \\
&= E'(k)p_{\mathrm{hit}}(k)-q'(k)(E(k)-1). \\
\end{aligned}
$$

而我们已经把它化成：

$$
\begin{aligned}
u'(k) \\
&= \frac{\alpha}{1-\alpha} \\
\left[ \\
M(k)-C(k) \\
\right].
\end{aligned}
$$

因为：

$$
\frac{\alpha}{1-\alpha}>0,
$$

所以 (u'(k)) 的符号完全由 (M(k)-C(k)) 决定。

当：

$$
k<k^*,
$$

有：

$$
M(k)>C(k),
$$

所以：

$$
u'(k)>0.
$$

当：

$$
k>k^*,
$$

有：

$$
M(k)<C(k),
$$

所以：

$$
u'(k)<0.
$$

因此：

$$
\begin{aligned}
\boxed{ \\
u(k)\text{ 先升后降，在 }k^*\text{ 处取得唯一最大值。} \\
}
\end{aligned}
$$

也就是：

$$
\begin{aligned}
\boxed{ \\
\tilde\mu^{\mathrm{SSD}}(k)\text{ is single-peaked on }\mathcal I. \\
}
\end{aligned}
$$

这就是 finite-(T_V) 的条件性 unimodality 证明。

---

# 12. 大 (T_V) 渐近：求 (k^*) 的增长速度

现在进入第二个结果。

注意：这一部分不依赖 (q''(k)\ge0)。它直接从 FOC 做渐近平衡。

我们从 FOC 出发：

$$
\begin{aligned}
\alpha^{k^*}\log(1/\alpha)p_{\mathrm{hit}}(k^*) \\
&= q'(k^*)(1-\alpha^{k^*}). \\
\end{aligned}
$$

当 (T_V\to\infty) 时，直觉上 verifier 时间很多，所以最优 (k^*) 会变大，但不会像 (T_V) 一样线性变大，而是只会 logarithmic 增长。

我们后面会得到：

$$
k^*=O(\log T_V).
$$

因此：

$$
\frac{k^*}{T_V}\to0.
$$

---

## 12.1 近似 (B(k))

因为：

$$
k^*\ll T_V/a,
$$

所以：

$$
T_V-ak^*\sim T_V.
$$

因此：

$$
\begin{aligned}
\frac{bk^*}{T_V-ak^*} \\
\sim \\
\frac{bk^*}{T_V}.
\end{aligned}
$$

---

## 12.2 近似 (G(k))

因为 (k^*\to\infty)，而：

$$
0<\beta<1,
$$

所以：

$$
\beta^{k^*}\to0.
$$

回忆：

$$
\begin{aligned}
N(k) \\
&= (1-\alpha)^{-1/(1+r)}\beta^k \\
+ \\
\frac{1-\beta^k}{1-\beta}.
\end{aligned}
$$

所以：

$$
N(k^*)\to \frac{1}{1-\beta}.
$$

又：

$$
\begin{aligned}
D(k) \\
&= (1-\alpha)^{r/(1+r)}\beta^k \\
+ \\
(1-\alpha)\frac{1-\beta^k}{1-\beta}.
\end{aligned}
$$

所以：

$$
D(k^*)\to \frac{1-\alpha}{1-\beta}.
$$

因此：

$$
\begin{aligned}
G(k^*)=N(k^*)^rD(k^*) \\
\to \\
\left(\frac{1}{1-\beta}\right)^r \\
\frac{1-\alpha}{1-\beta}.
\end{aligned}
$$

所以：

$$
\begin{aligned}
\boxed{ \\
G_\infty \\
&= \frac{1-\alpha}{(1-\beta)^{r+1}}. \\
}
\end{aligned}
$$

---

## 12.3 近似 (q(k)) 和 (q'(k))

原来：

$$
\begin{aligned}
q(k) \\
&= G(k) \\
\left( \\
\frac{bk}{T_V-ak} \\
\right)^r.
\end{aligned}
$$

在大 (T_V) 下：

$$
\begin{aligned}
q(k) \\
\sim \\
G_\infty \\
\left( \\
\frac{bk}{T_V} \\
\right)^r.
\end{aligned}
$$

也就是：

$$
\begin{aligned}
q(k) \\
\sim \\
G_\infty b^r \frac{k^r}{T_V^r}.
\end{aligned}
$$

求导：

$$
\begin{aligned}
q'(k) \\
\sim \\
G_\infty r b^r\frac{k^{r-1}}{T_V^r}.
\end{aligned}
$$

所以：

$$
\begin{aligned}
\boxed{ \\
q'(k^*) \\
\sim \\
G_\infty r b^r \\
\frac{(k^*)^{r-1}}{T_V^r}. \\
}
\end{aligned}
$$

---

## 12.4 近似 FOC

在最优点，如果 (T_V\to\infty)，那么：

$$
q(k^*)\to0.
$$

所以：

$$
p_{\mathrm{hit}}(k^*)=1-q(k^*)\to1.
$$

同时 (k^*\to\infty)，所以：

$$
\alpha^{k^*}\to0.
$$

因此：

$$
1-\alpha^{k^*}\to1.
$$

FOC：

$$
\begin{aligned}
\alpha^{k^*}\log(1/\alpha)p_{\mathrm{hit}}(k^*) \\
&= q'(k^*)(1-\alpha^{k^*}) \\
\end{aligned}
$$

变成：

$$
\begin{aligned}
\alpha^{k^*}\log(1/\alpha) \\
\sim \\
G_\infty r b^r \\
\frac{(k^*)^{r-1}}{T_V^r}.
\end{aligned}
$$

这是 asymptotic 的核心平衡式。

---

# 13. 对核心平衡式取 log

我们有：

$$
\begin{aligned}
\alpha^{k^*}\log(1/\alpha) \\
\sim \\
G_\infty r b^r \\
\frac{(k^*)^{r-1}}{T_V^r}.
\end{aligned}
$$

两边取 log：

左边：

$$
\begin{aligned}
\log\left(\alpha^{k^*}\log(1/\alpha)\right) \\
&= k^*\log\alpha+\log\log(1/\alpha). \\
\end{aligned}
$$

右边：

$$
\begin{aligned}
\log\left( \\
G_\infty r b^r \\
\frac{(k^*)^{r-1}}{T_V^r} \\
\right) \\
&= \log(G_\infty r b^r) \\
+ \\
(r-1)\log k^* \\
&- r\log T_V. \\
\end{aligned}
$$

所以：

$$
\begin{aligned}
k^*\log\alpha+\log\log(1/\alpha) \\
&= \log(G_\infty r b^r) \\
+ \\
(r-1)\log k^* \\
&- r\log T_V \\
+ \\
o(1).
\end{aligned}
$$

因为：

$$
\log\alpha=-\log(1/\alpha),
$$

整理为：

$$
\begin{aligned}
k^*\log(1/\alpha) \\
&= ## r\log T_V \\
(r-1)\log k^* \\
+ \\
\log\log(1/\alpha) \\
&- \log(G_\infty r b^r) \\
+ \\
o(1).
\end{aligned}
$$

主导项是：

$$
r\log T_V.
$$

因为 (\log k^*) 最多是 (\log\log T_V) 级别，是次阶项。

所以：

$$
\begin{aligned}
\boxed{ \\
k^* \\
&= \frac{r}{\log(1/\alpha)}\log T_V \\
+ \\
O(\log\log T_V). \\
}
\end{aligned}
$$

这就是 A2 的核心 takeaway。

---

# 14. 自洽性检查

我们刚才假设：

$$
k^*\ll T_V.
$$

现在结果是：

$$
k^*=O(\log T_V).
$$

所以：

$$
\begin{aligned}
\frac{k^*}{T_V} \\
&= O\left(\frac{\log T_V}{T_V}\right) \\
\to0.
\end{aligned}
$$

自洽。

我们也假设：

$$
k^*\to\infty.
$$

因为：

$$
\log T_V\to\infty,
$$

所以：

$$
k^*\to\infty.
$$

也自洽。

---

# 15. 参数单调性

从 leading order：

$$
\begin{aligned}
k^* \\
\approx \\
\frac{r\log T_V}{\log(1/\alpha)}.
\end{aligned}
$$

---

## 15.1 对 (T_V)

$$
\begin{aligned}
\frac{\partial k^*}{\partial T_V} \\
\approx \\
\frac{r}{T_V\log(1/\alpha)}.
\end{aligned}
$$

因为：

$$
r>0,\qquad T_V>0,\qquad \log(1/\alpha)>0,
$$

所以：

$$
\begin{aligned}
\boxed{ \\
\frac{\partial k^*}{\partial T_V}>0. \\
}
\end{aligned}
$$

直觉：verifier 时间越长，drafter 有更多时间准备 cache，所以可以选更长 (k)。

---

## 15.2 对 (\alpha)

$$
\begin{aligned}
k^* \\
\approx \\
r\log T_V\cdot \frac{1}{\log(1/\alpha)}.
\end{aligned}
$$

求导：

$$
\begin{aligned}
\frac{d}{d\alpha}\log(1/\alpha) \\
&= -\frac{1}{\alpha}. \\
\end{aligned}
$$

所以：

$$
\begin{aligned}
\frac{d}{d\alpha} \\
\frac{1}{\log(1/\alpha)} \\
&= \frac{1}{\alpha[\log(1/\alpha)]^2}. \\
\end{aligned}
$$

因此：

$$
\begin{aligned}
\boxed{ \\
\frac{\partial k^*}{\partial \alpha} \\
\approx \\
\frac{r\log T_V}{\alpha[\log(1/\alpha)]^2}>0. \\
}
\end{aligned}
$$

直觉：acceptance rate 越高，长链条越可靠，所以值得更长 lookahead。

---

## 15.3 对 (r)

$$
\begin{aligned}
\boxed{ \\
\frac{\partial k^*}{\partial r} \\
\approx \\
\frac{\log T_V}{\log(1/\alpha)}>0. \\
}
\end{aligned}
$$

直觉：(r) 越大，fan-out 增加对 miss probability 的改善越明显，所以更值得扩大 (k)。

---

## 15.4 对 (b)

leading order 里没有 (b)。

但是次阶项里有：

$$
\begin{aligned}
-\log(G_\infty r b^r) \\
&= -\log(G_\infty r)-r\log b. \\
\end{aligned}
$$

所以：

$$
\begin{aligned}
k^* \\
&= \frac{ \\
r\log T_V \\
&- (r-1)\log k^* \\
+ \\
\log\log(1/\alpha) \\
&- \log(G_\infty r b^r) \\
}{ \\
\log(1/\alpha) \\
} \\
+ \\
o(1).
\end{aligned}
$$

看 (b) 相关项：

$$
-\frac{r\log b}{\log(1/\alpha)}.
$$

因此：

$$
\begin{aligned}
\boxed{ \\
\frac{\partial k^*}{\partial b} \\
\approx \\
-\frac{r}{b\log(1/\alpha)}<0. \\
}
\end{aligned}
$$

直觉：drafter 越慢，每增加 (k) 的代价越高，所以最优 (k^*) 下降。

---

# 16. 加上 (T_b>0) 时怎么办？

前面取了 (T_b=0)。如果保留 backup latency：

$$
\begin{aligned}
\tilde\mu^{\mathrm{SSD}}(k) \\
&= \frac{ \\
E(k)-q(k)(E(k)-1) \\
}{ \\
1+q(k)T_b \\
}.
\end{aligned}
$$

在大 (T_V) 下：

$$
q(k^*)\to0.
$$

所以可以展开：

$$
\begin{aligned}
\frac{1}{1+qT_b} \\
&= 1-qT_b+O(q^2). \\
\end{aligned}
$$

于是：

$$
\begin{aligned}
\tilde\mu^{\mathrm{SSD}}(k) \\
&= \left[E(k)-q(k)(E(k)-1)\right] \\
\left[1-q(k)T_b+O(q^2)\right].
\end{aligned}
$$

保留一阶项：

$$
\begin{aligned}
\tilde\mu^{\mathrm{SSD}}(k) \\
\approx \\
E(k) \\
&- ## q(k)(E(k)-1) \\
q(k)E(k)T_b.
\end{aligned}
$$

所以：

$$
\begin{aligned}
\boxed{ \\
\tilde\mu^{\mathrm{SSD}}(k) \\
\approx \\
E(k) \\
&- q(k)\left[(E(k)-1)+E(k)T_b\right]. \\
}
\end{aligned}
$$

FOC leading form 变成：

$$
\begin{aligned}
E'(k^*) \\
\approx \\
q'(k^*) \\
\left[ \\
(E(k^*)-1)+E(k^*)T_b \\
\right].
\end{aligned}
$$

因为当 (k^*\to\infty)：

$$
E(k^*)\to \frac{1}{1-\alpha}.
$$

所以 (T_b) 只改变右边的常数倍，不改变主导的 (T_V) 指数平衡。

因此 leading order 仍然是：

$$
\begin{aligned}
\boxed{ \\
k^* \\
&= \frac{r}{\log(1/\alpha)}\log T_V \\
+ \\
O(\log\log T_V). \\
}
\end{aligned}
$$

也就是说：

> (T_b>0) 影响次阶常数，不影响主结论。

---

# 17. 最终可以写成哪些 theorem？

论文里我建议这样组织。

---

## Lemma 1：Miss probability is increasing

On the effective interval (\mathcal I),

$$
q'(k)>0.
$$

证明路线：

$$
\begin{aligned}
N'(k)>0,\quad D'(k)>0 \\
\Rightarrow \\
G'(k)>0.
\end{aligned}
$$

又因为：

$$
h(k)=\frac{bk}{T_V-ak}
$$

严格递增，所以：

$$
q(k)=G(k)h(k)^r
$$

严格递增。

---

## Proposition 1：FOC

Any interior maximizer (k^*) satisfies:

$$
\begin{aligned}
\boxed{ \\
\alpha^{k^*}\log(1/\alpha)p_{\mathrm{hit}}(k^*) \\
&= q'(k^*)(1-\alpha^{k^*}). \\
}
\end{aligned}
$$

---

## Assumption 1：Convex miss probability

On (\mathcal I),

$$
\begin{aligned}
\boxed{ \\
q''(k)\ge0. \\
}
\end{aligned}
$$

---

## Theorem 1：Conditional single-peakedness

Under Assumption 1, (\tilde\mu^{\mathrm{SSD}}(k)) is single-peaked on (\mathcal I).

证明路线：

$$
\begin{aligned}
\mathrm{MHB}(k) \\
&= \alpha^k\log(1/\alpha)p_{\mathrm{hit}}(k) \\
\end{aligned}
$$

严格递减；

$$
\begin{aligned}
\mathrm{MMC}(k) \\
&= q'(k)(1-\alpha^k) \\
\end{aligned}
$$

严格递增。

所以两者唯一交点 (k^*)，且 (u'(k)) 在交点前为正，交点后为负。

---

## Theorem 2：Large-(T_V) asymptotic

As (T_V\to\infty), in the unsaturated regime,

$$
\begin{aligned}
\boxed{ \\
k^* \\
&= \frac{r}{\log(1/\alpha)}\log T_V \\
+ \\
O(\log\log T_V). \\
}
\end{aligned}
$$

这个 theorem 不依赖 (q''(k)\ge0)。

---

## Corollary：Monotonicity

$$
\begin{aligned}
\boxed{ \\
\frac{\partial k^*}{\partial \alpha}>0, \\
\qquad \\
\frac{\partial k^*}{\partial T_V}>0, \\
\qquad \\
\frac{\partial k^*}{\partial r}>0, \\
\qquad \\
\frac{\partial k^*}{\partial b}<0. \\
}
\end{aligned}
$$

其中前三个来自 leading order，最后一个来自 second-order correction。

---

# 18. 最简直觉版

如果你觉得上面太长，可以记这个版本：

$$
u(k)=E(k)-q(k)(E(k)-1).
$$

其中：

$$
E(k)=\frac{1-\alpha^{k+1}}{1-\alpha}
$$

随 (k) 增加，但边际收益递减；

$$
q(k)=G(k)\left(\frac{bk}{T_V-ak}\right)^r
$$

随 (k) 增加，代表 miss 风险越来越大。

最优点满足：

$$
\begin{aligned}
\text{多看一层带来的 hit 收益} \\
&= \text{多看一层带来的 miss 成本}. \\
\end{aligned}
$$

也就是：

$$
\begin{aligned}
\alpha^{k^*}\log(1/\alpha)p_{\mathrm{hit}}(k^*) \\
&= q'(k^*)(1-\alpha^{k^*}). \\
\end{aligned}
$$

当 (T_V) 很大时，miss probability 近似：

$$
q(k)\approx G_\infty\left(\frac{bk}{T_V}\right)^r.
$$

于是：

$$
q'(k)\approx G_\infty rb^r\frac{k^{r-1}}{T_V^r}.
$$

FOC 变成：

$$
\begin{aligned}
\alpha^{k^*} \\
\approx \\
\frac{(k^*)^{r-1}}{T_V^r}.
\end{aligned}
$$

取 log 后主导平衡是：

$$
k^*\log(1/\alpha)\approx r\log T_V.
$$

所以：

$$
\begin{aligned}
\boxed{ \\
k^*\approx \frac{r}{\log(1/\alpha)}\log T_V. \\
}
\end{aligned}
$$

这就是 Block 1 / A2 最核心的结论。