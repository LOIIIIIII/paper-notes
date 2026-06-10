# World4Drive 论文精读笔记

论文：**World4Drive: End-to-End Autonomous Driving via Intention-aware Physical Latent World Model**  
版本：arXiv:2507.00603v1，2025-07-01  
本笔记基于论文 PDF 与前序阅读讲解整理。

## 一句话总结

World4Drive 用视觉基础模型构造带空间、语义、时序信息的 physical latent world，再让 world model 针对多种驾驶意图预测未来 latent，并作为轨迹选择器来评估哪条规划更合理。

## 论文要解决的问题

端到端自动驾驶如果依赖 BEV、3D box、HD map 或 occupancy supervision，通常需要昂贵的人工感知标注。近年的 latent world model 尝试通过自监督学习摆脱这些标注，但已有方法常把当前图像压成单一 latent，再预测一个未来 latent。这种单一未来表示很难同时处理物理空间语义和驾驶意图的不确定性。

- 标注成本：很多 E2E-AD 方法效果依赖 perception annotations。
- latent 表示太薄：只从 raw image 学 latent，容易缺少深度、语义、可行驶区域等 planning 需要的物理信息。
- 未来是多模态的：左转、直行、绕行、等待会对应不同未来。
- world model 没有真正参与选择：很多方法用 world model 做辅助训练，但没有让它直接评估多条候选轨迹。

## 核心创新点

### 1. Intention-aware latent world model

相比 LAW 这类单一未来 latent 预测，World4Drive 把驾驶意图显式接入 world model。每一种 intention 都对应一个未来 latent world，让模型学习“不同行为会导致不同未来”。

### 2. World Model Selector

训练时比较预测 future latent 和真实 future latent 的距离，选出最合理的模态；推理时由 ScoreNet 给候选轨迹打分。这样 world model 直接参与 planning decision。

### 3. Physical latent encoding

用 Metric3D 这类深度模型提供 3D 空间 prior，用 Grounded-SAM 提供伪语义 prior，再聚合历史帧，让 latent world 同时包含空间、语义和时序信息。

### 4. Annotation-free but not prior-free

它不使用目标数据集里的人工 perception annotations，但借助视觉基础模型提供伪深度和伪语义。这个设计降低了标注成本，也解释了为什么它比纯 raw image latent 更稳。

## Method 细读

### 3.2 Driving World Encoding

Intention Encoder 先准备一个 trajectory vocabulary `V ∈ R^{N×S×2}`，其中 `N` 是轨迹数量，`S` 是每条轨迹的 waypoint 数。作者对轨迹终点做 k-means，得到三种 command 左转、右转、直行下的 intention points `P_I ∈ R^{3×K×2}`。默认设置中 `N=8192`，每种 command 下 `K=6` 个 intention。

```text
Q_plan = SelfAttention(Q_ego + Q_I)
```

Physical World Latent Encoder 负责构造带空间、语义和时序上下文的 world latent：

- 3D 空间 prior：用 metric depth model 估计深度，再反投影得到每个像素在 ego 坐标系下的 3D position map。
- 语义 prior：用 Grounded-SAM 产生高置信度伪 semantic mask，并用 `L_sem` 强化语义理解。
- 时序 prior：保留上一时刻 visual feature，通过 cross-attention 聚合历史信息。

```text
S_t = GroundedSAM(F_t)
E_t = MLP(SPE(P_t))
L_t = CrossAttention(F̂_t, F̂_{t-1})
```

### 3.3 Intention-aware World Model Dreamer

得到 `Q_plan` 和当前 world latent `L_t` 后，模型先生成 K 条多模态轨迹：

```text
T = MLP(CrossAttention(Q_plan, L_t))
```

然后用 action encoder 把这些 intention-aware trajectories 编成 action tokens `A ∈ R^{K×D}`。接着把 action tokens 和当前 world latent 拼接，预测每个 intention 对应的未来 world latent：

```text
L_{t+n} = CrossAttention(Q_future, Concat(A, L_t))
```

这一步是文章的核心：模型不是预测一个未来，而是预测“如果选择每个候选意图，未来世界会怎样”。

### World Model Selector

训练阶段，模型可以看到真实未来帧，因此能通过同一个 context encoder 得到真实未来 latent。对 K 个预测 future latents 分别计算与真实 future latent 的 MSE 距离，距离最小的模态被视为最合理的意图。对应轨迹被选为最终规划轨迹，同时这个最小距离作为 reconstruction loss。

推理阶段没有真实未来帧，所以用训练好的 ScoreNet 给每个候选模态打分，选择分数最高的轨迹。

### 训练目标

```text
L = α L_sem + β L_recon + γ L_score + η L_traj
α = 0.2, β = 0.2, γ = 0.5, η = 1.0
```

- `L_sem`：来自 Grounded-SAM 伪语义标签，增强 latent 的语义理解。
- `L_recon`：预测 future latent 与真实 future latent 的距离，对齐世界模型想象和真实未来。
- `L_score`：用 focal loss 训练 ScoreNet 选择正确模态。
- `L_traj`：最终选中轨迹和专家轨迹之间的 L1 规划损失。

## 实验结论

### nuScenes open-loop

| Method | Avg L2 ↓ | Avg Collision Rate ↓ | 是否需要人工感知标注 |
|---|---:|---:|---|
| VAD | 0.72 | 0.23 | 需要 |
| GenAD | 0.52 | 0.19 | 需要 |
| LAW perception-based | 0.49 | 0.19 | 需要 |
| LAW perception-free | 0.61 | 0.30 | 不需要 |
| World4Drive | 0.50 | 0.16 | 不需要 |

相比 perception-free LAW，World4Drive 的平均 L2 从 0.61 降到 0.50，平均碰撞率从 0.30% 降到 0.16%。

### NavSim closed-loop

| Method | Input | NC ↑ | DAC ↑ | TTC ↑ | EP ↑ | PDMS ↑ |
|---|---|---:|---:|---:|---:|---:|
| UniAD | C | 97.8 | 91.9 | 92.9 | 78.8 | 83.4 |
| LAW perception-free | C | 97.2 | 93.3 | 91.9 | 78.8 | 83.8 |
| DiffusionDrive | C&L | 98.2 | 96.2 | 94.7 | 82.2 | 88.1 |
| World4Drive | C | 97.4 | 94.3 | 92.8 | 79.9 | 85.1 |

World4Drive 在 camera-only 设置下超过 LAW 和 UniAD，但没有超过使用 camera + LiDAR 的 DiffusionDrive。

## 消融实验怎么看

| 设置 | Depth | Semantic | World Model | Intentions | L2 ↓ | Collision ↓ |
|---|---|---|---|---|---:|---:|
| LAW baseline | - | - | ✓ | - | 0.61 | 0.30 |
| + Intentions | - | - | ✓ | ✓ | 0.55 | 0.25 |
| + Depth | ✓ | - | ✓ | ✓ | 0.51 | 0.29 |
| Depth + Semantic + WM | ✓ | ✓ | ✓ | - | 0.49 | 0.26 |
| Depth + Semantic + Intentions only | ✓ | ✓ | - | ✓ | 0.61 | 0.36 |
| Full World4Drive | ✓ | ✓ | ✓ | ✓ | 0.50 | 0.16 |

最重要的结论：只有 intentions 但没有 world model，碰撞率反而变差；加上 world model selector 后，collision 从 0.36 降到 0.16。这说明多意图本身不是答案，必须有 world model 来评价和筛选。

## 局限与疑问

- 不是完全 prior-free：虽然不用人工 perception annotations，但依赖 Metric3D、Grounded-SAM 等预训练模型。
- selector 的泛化仍需验证：训练时用真实未来 latent 选模态，推理时靠 ScoreNet，二者之间可能存在分布差异。
- trajectory vocabulary 有约束：k-means intention 来自预定义轨迹词表，复杂交互场景下可能限制行为空间。
- open-loop 指标有限：nuScenes 的 L2 和 collision rate 不能完全代表真实闭环驾驶能力。
- 视觉基础模型成本：伪深度和伪语义虽省人工标注，但工程上仍需要额外模型、推理和清洗流程。

## 对 AD + World Model 的启发

- 先把 world model 定义成 planning evaluator，而不是 video generator。
- 用现成 depth / segmentation foundation model 做伪监督，降低人工标注依赖。
- 多模态轨迹必须配套 selection / scoring，否则候选越多不一定越安全。
- 可以从小实验开始：固定 backbone，比较 raw latent、depth-aware latent、semantic-aware latent 对轨迹评分的影响。

一句适合写进 related work 的话：

> World4Drive uses an intention-aware latent world model not only to predict future scene representations, but also to evaluate and rank multi-modal planning trajectories under different driving intentions.
