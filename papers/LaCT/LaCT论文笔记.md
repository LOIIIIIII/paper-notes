# LaCT 论文笔记

论文：Test-Time Training Done Right
arXiv:2505.23884v1，2025-05-29
作者：Tianyuan Zhang, Sai Bi, Yicong Hong, Kai Zhang, Fujun Luan, Songlin Yang, Kalyan Sunkavalli, William T. Freeman, Hao Tan

## 一句话总结

LaCT 并没有改变 TTT“通过训练快速权重来存储记忆”的基本原理，而是把传统的小批量频繁更新改成超大块并行更新，使 TTT 能够高效利用 GPU、扩大记忆容量，并适用于语言、图像和视频等不同模态。

## 研究背景

原始 TTT 将快速权重 `W` 作为隐藏状态，通过自监督梯度下降不断写入历史信息：

```text
W_{t+1} = W_t - eta * grad_W L_t
o_t = f_{W_t}(q_t)
```

传统实现的问题主要有三点：

1. 小批量频繁更新，单次矩阵计算太小，GPU 利用率很低。
2. 更强的非线性快速权重，例如 MLP，在小块更新下计算和实现成本较高。
3. 细粒度顺序更新更适合一维文本，对图像集合、视频网格、多视角输入等多维结构不够自然。

LaCT 的关键思路是改变快速权重更新粒度：从 16-64 token 的小更新，变成 2K-1M token 的大 chunk 聚合更新。

## 核心创新

### 1. 超大块更新

LaCT 让一个 chunk 内的所有 token 基于同一份快速权重计算损失，并聚合梯度后统一更新：

```text
g = grad_W sum_i eta_i L(f_W(k_i), v_i)
W_new = weight-update(W, g)
```

这样做把大量零碎更新变成大矩阵计算，显著提升 GPU 吞吐，并降低频繁更新带来的调度开销。

### 2. 更大的非线性快速权重

LaCT 使用 SwiGLU-MLP 作为快速权重函数：

```text
f_W(x) = W_2 [ SiLU(W_1 x) o (W_3 x) ]
```

相比线性快速权重，SwiGLU-MLP 能学习更复杂的 key-value 关联。论文探索了最高相当于主模型参数量约 40% 的快速权重规模。

### 3. Update 和 Apply 解耦

LaCT 将写入记忆和读取记忆拆开调度，对应多种依赖模式：

| 模式 | 信息依赖 | 典型用途 |
|---|---|---|
| Full | 整段序列全局依赖 | 非因果数据处理 |
| Block-Wise | 当前块与历史块 | 块级因果建模 |
| Shifted | 当前块先读旧记忆，再写入当前信息 | 自回归语言模型 |
| Strided | 选择性写入，按需读取 | 新视角合成、视频扩散 |

### 4. 非线性更新与 Window Attention

论文探索了带归一化的快速权重更新：

```text
W_new = L2Normalize(W - g)
W_new = L2Normalize(W - Muon(g))
```

同时，由于大块 TTT 不直接保留块内局部顺序和空间结构，LaCT 引入 window attention。局部结构由窗口注意力建模，非局部历史由快速权重压缩记忆。

### 5. 上下文并行

LaCT 的大 chunk 可以沿序列长度切分到多张 GPU 上，各设备分别计算局部梯度，然后 all-reduce 聚合：

```text
g = sum_j g_j
```

因为所有分片基于同一份快速权重计算梯度，这与单设备处理完整 chunk 在数学上等价。

## 与传统 TTT 的区别

| 维度 | 传统 TTT | LaCT |
|---|---|---|
| 基本原理 | 自监督更新快速权重 | 保留相同原理 |
| 更新粒度 | 常见 16-64 token | 2K-1M token |
| 更新方式 | 小批量频繁更新 | 大块聚合更新 |
| GPU 利用率 | 许多实现低于 5% peak FLOPs | 论文报告最高约 70% |
| 快速权重规模 | 受小块更新效率限制 | 支持更大非线性 state |
| 快速权重结构 | Linear 或 MLP | SwiGLU-MLP |
| 优化方法 | 简单在线梯度更新更常见 | L2 normalization、Muon |
| 局部结构 | 侧重顺序建模 | 结合 window attention |
| 信息依赖 | 细粒度顺序更新 | Update/Apply 灵活调度 |
| 多模态支持 | 早期主要验证语言序列 | 图像集合、语言、视频 |

## 实验验证

论文在三类任务中验证 LaCT：

| 任务 | 数据结构 | 规模 | 结论 |
|---|---|---|---|
| Novel View Synthesis | Image set | 最高约 1M tokens，128 张输入图像，560 x 536 | 低延迟下接近 full attention，并能扩展到大规模输入 |
| Language Modeling | 1D sequence | 2K/4K chunk，32K 序列评估 | 长 token 位置 loss 更低，needle retrieval 更强 |
| Autoregressive Video Diffusion | Image sequence | 14B 模型，约 56K visual tokens | 接近 full attention，并优于若干滑窗基线 |

## 汇报总结

传统 TTT 的核心想法是把快速权重当作记忆，但小批量频繁更新导致 GPU 利用率低、非线性记忆难扩展，也难以自然表达多维数据依赖。LaCT 通过超大块聚合更新重写 TTT 的计算组织方式，并结合 SwiGLU-MLP、Muon、window attention 和上下文并行，把 TTT 从小步在线序列记忆机制扩展成可处理长上下文和多模态数据的混合架构。

如果只保留一个最值得记住的创新：大 chunk 不只是提升速度的工程技巧，它改变了 TTT 的计算组织方式，使更大的记忆网络、更复杂的更新算法、多 GPU 并行和不同模态的信息调度能够同时实现。
