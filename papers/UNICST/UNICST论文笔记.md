# UNICST 论文笔记

## 一句话总结

UNICST 提出一个 next-scale latent prediction 的多视角视频世界模型：把多视角多帧视频表示成统一连续 4D latent hierarchy，并按 coarse-to-fine 尺度生成，从而提升多视角一致性、时间连贯性和推理速度。

## 论文要解决的问题

自动驾驶世界模型需要同时满足：

```text
视觉真实
多视角空间一致
跨帧时间连续
条件可控
推理足够快
```

现有 diffusion 模型质量较高但慢；显式几何条件模型依赖 HD map、3D box、depth、occupancy、LiDAR 等预处理和标注；普通 token autoregressive 方法又会让视频 token 序列太长。

## 什么叫尺度 scale

UNICST 里的 scale 不是多个视角，也不是未来帧，而是同一张图像或视频帧在 latent token 空间里的不同分辨率层级。

```text
scale 1: 粗分辨率 token map，负责全局结构
scale 2: 中等分辨率 token map，补充布局
...
scale K: 高分辨率 token map，补充细节
```

三种维度：

```text
scale: 同一图像从粗到细的多分辨率层级
spatial / view: 不同相机视角
temporal: 不同时间帧
```

## 核心方法

单图 next-scale prediction：

```text
p(R_1, R_2, ..., R_K) = Π_k p(R_k | R_1, R_2, ..., R_{k-1})
```

多视角多帧的解耦形式：

```text
p(R_{v0,t0}^{1:K}) =
Π_k p(R_{v0,t0}^k | R_{v0,t0}^{1:k-1}, R_{v≠v0,t0}^k, R_{v0,1:t0-1}^k)
```

其中：

```text
scale reliance: R_{v0,t0}^{1:k-1}
spatial reliance: R_{v≠v0,t0}^k
temporal reliance: R_{v0,1:t0-1}^k
```

## 统一 4D Ray 表示

UNICST 用相机内外参把每个 visual token 提升到 3D ray，并附加时间维度。

```text
p_{k,j}^{cam} = (u_j * d_j * s_k^w, v_j * d_j * s_k^h, d_j, 1)
p_{k,j}^{v,0} = K_v^{-1} p_{k,j}^{cam}
p_{k,j}^{v,t} = T_{v,t} p_{k,j}^{v,0}
position embedding = (p_{k,j}^{v,t}, t)
```

直觉：不同相机或不同时间看到同一物理点时，在统一 4D space 中更容易对齐。

## SST Blocks

Spatial condition：

```text
R_{k,out}^{v,t} = R_{k,in}^{v,t} + Masked-SA(R_{k,in}^{v,t}, R_{k,in}^{1:V,t})
```

Temporal condition：

```text
R_{k,out}^{v,t} = R_{k,in}^{v,t} + Masked-SA(R_{k,in}^{v,t}, R_{k,in}^{v,1:t-1})
```

作用：

```text
spatial attention -> 多视角一致
temporal attention -> 时间连贯
scale attention -> 粗到细生成
```

## Action Token

每帧最高尺度后加入 learnable action token：

```text
r_{act,out}^t = r_{act,in}^t + Masked-SA(r_{act,in}^t, R_{K,in}^{1:V,t})
r_{act,out}^t = r_{act,in}^t + Masked-SA(r_{act,in}^t, r_{act,in}^{1:t-1})
```

最后用 classification head 预测 trajectory cluster。但论文核心实验仍是视频生成质量和速度，不是闭环规划。

## 实验结果

训练数据：

```text
nuScenes: 约 4.7 小时
nuPlan: 约 55.6 小时
总训练: 约 59.5 小时
验证: nuScenes 约 0.8 小时
```

单视角 FID：

| 方法 | 数据规模 | FID |
|---|---:|---:|
| Vista | 1740h | 6.9 |
| DrivingWorld | 3456h | 7.4 |
| UNICST single-view | 60h | 4.5 |

多视角结果：

| 方法 | 类型 | FID | FVD | Throughput |
|---|---|---:|---:|---:|
| MagicDrive | Diffusion | 16.2 | - | 1.76 |
| X-Drive | Diffusion | 16.0 | - | 0.83 |
| DriveDreamer | Diffusion | 14.9 | 341 | 0.37 |
| Panacea | Diffusion | 17.0 | 139 | 0.67 |
| UNICST | Next-scale AR | 14.5 | 134 | 2.17 |

## 消融

View embedding：

```text
None: FID 24.7, FVD 280.5
Learnable: FID 23.4, FVD 248.8
Ray: FID 21.7, FVD 240.8
```

Time embedding：

```text
None: FID 23.2, FVD 257.7
Learnable: FID 25.1, FVD 261.3
Continuous: FID 21.7, FVD 240.8
```

Spatial / Temporal condition：

```text
Only temporal: FID 26.0, FVD 247.8
Only spatial: FID 21.9, FVD 270.3
Spatial + temporal: FID 21.7, FVD 240.8
```

## 局限与疑问

- 主要证明生成质量和速度，不是闭环规划能力。
- FID/FVD 不能充分证明物理正确性、交通规则和 agent interaction。
- 3B 模型、64 A100，训练成本高。
- “minimal inductive bias”应谨慎理解：它减少固定传感器拓扑偏置，但 Plücker ray、camera pose、ego motion 都是强几何先验。
- PDF 是 anonymous ICCV 2025 submission，引用时需要核查公开版本。

## 和其他论文的位置关系

```text
Drive-WM: future RGB video generation for visual forecasting/planning
Drive-OccWorld: future occupancy + flow for occupancy-based planning
Latent-WAM: compact latent world representation for trajectory planning
LMGenDrive: LLM instruction following + video generation supervision
UNICST: next-scale 4D latent generation backbone for efficient multi-view video world modeling
```
