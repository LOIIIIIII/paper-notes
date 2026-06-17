# UniTrans 论文精读笔记

论文：**One Model to Translate Them All: Universal Any-to-Any Translation for Heterogeneous Collaborative Perception**  
方法：**UniTrans**  
来源：ICML 2026 / arXiv:2605.17907v1  
代码：论文给出 `https://github.com/CheeryLeeyy/UniTrans`  
阅读范围：基于论文 PDF 正文、实验表和本轮关于 Figure 2、MIE 损失的问答整理。

## 一句话总结

UniTrans 先学习一个 modality-intrinsic latent space 来描述不同中间特征的模态风格，再根据 source-target 模态关系动态组合 Translator Parameter Bank，从而无需重新训练即可对新异构 agent 进行 zero-shot any-to-any feature translation。

## 论文要解决的问题

协同感知中常用 intermediate fusion，即 agent 之间共享 BEV intermediate features。但现实中不同车辆和路侧设备可能有不同传感器、不同 backbone、不同 feature space：

- PointPillars feature
- SECOND feature
- VoxelNet feature
- Camera LSS feature
- RSU high-resolution LiDAR feature

这些 feature 直接融合会造成跨 agent domain shift。已有方法主要有：

- one-to-one adapter：每个 source-target pair 训练一个 adapter，扩展性差。
- protocol-space 方法：映射到统一协议空间，但新模态出现时协议空间可能不合适。

UniTrans 的问题设定是：能否训练一次，在推理时对任意新模态现场实例化 translator？

## 核心创新

### 1. Modality-Intrinsic Encoder, MIE

MIE 将高维 intermediate feature 映射到低维 intrinsic code：

```text
z = MIE(F)
```

这个 code 希望表达 feature 的模态风格，而不是具体场景内容。MIE 使用 channel mean、channel std、global response、Gram matrix / channel correlation 等统计描述。

### 2. Modality Mapping Router, MMR

MMR 根据 source 和 target 的 intrinsic code 估计模态映射关系，并输出参数组合权重：

```text
δ_{j→i} = g(z_j, z_i)
α_{j→i} = softmax(h(δ_{j→i}))
```

### 3. Translator Parameter Bank, TPB

TPB 存储多个 translator expert parameters 和一个 shared expert：

```text
TPB = {Θ^(1), ..., Θ^(K)}, Θ^(0)
```

推理时根据 `α` 组合参数：

```text
φ_{j→i} = Θ0 + Σ_k α_k Θ_k
```

然后实例化 translator：

```text
F_{j→i} = T_{φ_{j→i}}(F_j)
```

关键区别：UniTrans 组合的是参数，不是多个 expert 输出，因此只需一次 forward。

## Figure 2 详解

### Stage 1：MIE 预训练

左上图表示从 Scene Repository 和 Model Repository 中采样场景和 encoder，得到 intermediate feature。MIE 将 feature 映射成 intrinsic code，并在 modality-intrinsic latent space 中形成结构：

- 同一 modality 的 code 被拉近。
- 不同 modality 的 code 被推远。
- code 还要能预测自己的 modality label。

### Stage 2：Translator Expert Learning

右上图中，ego agent `i` 和 neighbor agents `j/k` 分别得到 `F_i, F_j, F_k`。MIE 提取 `z_i, z_j`，MMR 输出映射权重 `α`，然后 TPB/MCT-Block 生成对应 translator，把 `F_j` 翻译成 `F_{j→i}`。

### Inference

下方图表示推理阶段新异构 agent 直接进入系统：

```text
F_j -> UniTrans -> F_{j→i}
F_i + F_{j→i} + F_{k→i} -> Fusion Network -> Task Head
```

不需要为新模态重新训练 adapter。

## MIE 第一阶段两个损失

Stage 1 的目标：

```text
L_stage1 = L_IC + λ_IS L_IS
```

### L_IC：Intrinsic Contrastive Loss

`L_IC` 是 InfoNCE-style contrastive loss。对 anchor `z_a`：

- positive：同一 modality 的 code。
- negative：不同 modality 的 code。

目标是：

```text
同模态拉近，不同模态推远
```

直观公式：

```text
L_IC = Σ_a -log
       [Σ_{p∈P(a)} exp(sim(z_a, z_p)/τ)]
       /
       [Σ_{b≠a} exp(sim(z_a, z_b)/τ)]
```

它负责让 latent space 有几何结构。

### L_IS：Surrogate Modality Classification Loss

`L_IS` 是辅助模态分类损失：

```text
p_hat(m | z) = softmax(q(z))
L_IS = - E log p_hat(m | z)
```

它要求 intrinsic code 能判断自己来自哪种 modality。它负责让 code 有清晰的 modality identity。

总结：

```text
L_IC 学空间结构
L_IS 学模态身份
```

## Stage 2 损失

Stage 2 训练 MMR 和 TPB，目标包括：

- `L_task`：下游 3D detection task loss。
- `L_feat`：feature distillation loss，让翻译后的 feature 接近 ego encoder 对同一 observation 生成的 teacher ego-domain feature。
- `L_ctr`：routing contrastive loss，让相同 mapping 的 routing vector 接近。
- `L_r`：router regularization / load balancing，避免 expert collapse。

总损失：

```text
L_stage2 = L_task + λ_feat L_feat + λ_ctr L_ctr + λ_r L_r
```

## 实验结果

数据集：

- OPV2V-H：仿真异构协同感知。
- DAIR-V2X：真实车路协同数据集。

作者构造 30 种 modality，并把 `m7, m13, m17, m25, m27, m30` 作为 inference-time emerging modalities。

### OPV2V-H

- NegoCollab：0.662 / 0.538
- Classic MoE：0.653 / 0.544
- UniTrans：0.716 / 0.605

### DAIR-V2X

- NegoCollab：0.509 / 0.389
- Classic MoE：0.523 / 0.388
- UniTrans：0.553 / 0.421

### 效率

- MPDA：124.6 GFLOPs，46.814 ms CUDA
- Classic MoE：245.5 GFLOPs，141.352 ms CUDA
- UniTrans：109.3 GFLOPs，53.760 ms CUDA

UniTrans 比 Classic MoE 更高效，因为它不执行多个 expert，而是先组合参数得到单个 translator。

## 消融实验

完整模型：

```text
0.716 / 0.605
```

去掉 `L_IC`：

```text
0.685 / 0.575
```

去掉 `L_IS`：

```text
0.694 / 0.583
```

两个都去掉：

```text
0.662 / 0.540
```

去掉 `L_feat`：

```text
0.653 / 0.531
```

结论：MIE 的 intrinsic space 和 feature distillation 都是核心。

## 与我的研究方向的关系

这篇论文对“因子码本 + gate + planner”很有启发。它的范式是：

```text
feature -> modality intrinsic code -> mapping router -> translator parameters
```

可以迁移为：

```text
future scene -> planning factor code -> factor gate/router -> planner adapter/refiner
```

关键启发是：gate 不一定只做 feature 加权，也可以做 parameter conditioning。

## 局限与疑问

- 它解决的是感知 feature translation，不直接验证规划安全。
- zero-shot 泛化依赖训练阶段见过足够多的 modality。
- MIE 是否真正 scene-invariant 还需要更多验证。
- `L_feat` 需要 paired teacher ego-domain feature，现实跨厂商部署可能不易获得。
- baseline 原本未必为 zero-shot any-to-any 设置设计，比较需要谨慎解读。

## 值得学习的表达

UniTrans 最值得学习的不是检测 AP 本身，而是这个机制：

**先学习一个 intrinsic relation space，再用 router 将 relation 转化为可执行模块参数。**
