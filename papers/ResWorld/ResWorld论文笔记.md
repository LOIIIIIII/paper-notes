# ResWorld 论文笔记

论文：**ResWorld: Temporal Residual World Model for End-to-End Autonomous Driving**  
来源：ICLR 2026 conference paper，本笔记基于本地 PDF 阅读整理。

## 一句话总结

ResWorld 用 temporal residual 提取动态对象，让 world model 避免重复预测静态背景；再用 Future-Guided Trajectory Refinement 让 future BEV features 显式修正轨迹。

## 研究问题

已有 end-to-end AD world model 常把 future scene prediction 当 proxy task，但存在：

- 静态区域重复建模：道路、建筑、地面短时间内基本不变。
- 动态对象建模不足：车辆、行人等对规划最关键，但不依赖检测/跟踪时较难显式识别。
- 未来表征和轨迹交互弱：future feature 只作为辅助任务，未直接用于 trajectory refinement。

## 核心贡献

1. 使用当前 BEV 坐标系表示未来 BEV，静态对象直接继承，避免冗余建模。
2. 通过 temporal residual 抽取动态对象信息，不依赖检测和跟踪辅助任务。
3. 提出 TR-World，只输入 temporal residual，预测动态对象未来空间分布。
4. 提出 FGTR，用 prior trajectory 作为 reference points，让 waypoint queries 和 future BEV features 显式交互。
5. 在 nuScenes 和 NAVSIM 上取得强 planning 表现。

## 方法框架

### Prior Trajectory Prediction

多时刻多视角图像经 GeoBEV 得到 BEV features：

```text
{B_t, B_{t-1}, ..., B_{t-k}}
```

历史 BEV 被对齐到当前 BEV 坐标系并融合：

```text
B_fuse = Conv(Concat(B_t, B_{t-1}, ..., B_{t-k}))
```

TokenLearner 从 dense BEV 中提取 sparse scene queries，再与 waypoint queries cross-attention，得到 prior trajectory：

```text
T_prior = MLP(CrossAttention(W, S_fuse, S_fuse))
```

### Temporal Residual Extraction

使用融合 BEV 生成 spatial attention map，对每个 timestamp 提取 sparse scene queries：

```text
S_i = AvgPool(SA(B_fuse) ⊙ B_i)
```

相邻 timestamp 的 scene queries 相减得到 temporal residuals：

```text
{R_t, R_{t-1}, ..., R_{t-k+1}}
```

### TR-World

TR-World 只处理 temporal residual：

```text
R_hat = Σ SelfAttention(R_i)
B_future = TokenFuser(R_hat, B_fuse) + B_fuse
```

静态区域由 `B_fuse` 保留，动态未来由 residual world model 更新。

### FGTR

FGTR 用 prior trajectory 作为 future BEV 上的 reference points：

```text
W = DeformAttention(W, B_future, T_prior)
T_final = MLP(W)
```

这个过程既修正轨迹，也对 future BEV 提供 sparse spatio-temporal supervision，缓解 world model collapse。

### Loss

训练只使用 prior 和 final trajectory 的 L1 loss：

```text
L = L1(T_prior, T_GT) + L1(T_final, T_GT)
```

作者不使用真实未来 BEV dense label 监督 `B_future`，因为它会把未来表征限制到某个单一 timestamp。

## 实验结论

### nuScenes

| 方法 | Auxiliary Task | Avg L2 ↓ | Avg Col. ↓ |
|---|---|---:|---:|
| SSR∗‡ | None | 0.39 | 0.15 |
| LAW‡ | None | 0.61 | 0.30 |
| Drive-OccWorld‡ | Occ | 0.47 | 0.11 |
| ResWorld‡ | None | 0.35 | 0.07 |
| ResWorld♢‡ | None + ego status | 0.30 | 0.06 |

### NAVSIM

| 方法 | Auxiliary Task | PDMS ↑ |
|---|---|---:|
| LAW | None | 84.6 |
| World4Drive | None | 85.1 |
| DiffusionDrive | Det&Map | 88.1 |
| ResWorld | Det&Map | 88.3 |
| ResWorld⋆ | Det&Map + historical frame | 89.0 |

## 关键消融

TR-World 与 FGTR 都有效。使用 ego status 时：

| TR-World | FGTR | Avg L2 ↓ | Avg Col. ↓ |
|---|---|---:|---:|
| 否 | 否 | 0.65 | 0.28 |
| 是 | 否 | 0.61 | 0.25 |
| 否 | 是 | 0.61 | 0.22 |
| 是 | 是 | 0.59 | 0.17 |

TR-World 不使用 real future supervision 最好：

| World Model | Future Supervision | Avg L2 ↓ | Avg Col. ↓ |
|---|---|---:|---:|
| Normal WM | 是 | 0.61 | 0.23 |
| Normal WM | 否 | 0.61 | 0.21 |
| TR-World | 是 | 0.61 | 0.21 |
| TR-World | 否 | 0.59 | 0.17 |

## 局限与疑问

- TR-World 不能充分捕获潜在动态对象，例如还没动的行人、停靠车辆。
- temporal residual 依赖高质量 BEV 对齐，底层 BEV 几何误差会影响动态残差。
- 不监督 future BEV 是创新点也是风险点，future representation 的语义可解释性仍有限。
- NAVSIM 的不同配置要谨慎比较，ResWorld⋆ 使用 historical frame。

## 值得学习的写法

- 把 world model 的负担从“预测完整未来”缩小成“预测规划真正缺的动态残差”。
- 用 prior trajectory 作为 reference points 让 future feature 直接服务轨迹，而不是只做辅助 loss。
- 用消融证明“不用 dense future supervision 反而更好”这个反直觉设计。
