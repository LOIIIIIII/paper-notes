# DLWM 论文笔记

论文：**DLWM: Dual Latent World Models enable Holistic Gaussian-centric Pre-training in Autonomous Driving**  
来源：arXiv:2604.00969v1，本笔记基于本地 PDF 阅读整理。

## 一句话总结

DLWM 为 Gaussian-centric 自动驾驶模型设计两阶段自监督预训练：Stage 1 用 depth/semantic rendering 学 3D Gaussian 几何语义，Stage 2 用两个任务导向的 latent world models 分别增强 perception/forecasting 和 planning。

## 论文要解决的问题

- Voxel/BEV 表征要么计算重，要么损失高度细节。
- Sparse query 表征高效，但场景几何和语义不够完整。
- 3D Gaussian-centric 表征兼具稀疏和 3D 几何表达，但缺少完整自监督预训练框架。
- 不同帧 Gaussian queries 没有天然一一对应关系，直接做 query feature supervision 会受到 permutation equivalence 影响。

## 核心方法

### Stage 1：Gaussian Representation Learning

多视角图像经过 image encoder/FPN 和 Gaussian perception module，输出 3D semantic Gaussians。训练时通过 rendering 重建 depth map 和 semantic map：

```text
L_rec = ω1 L_d + ω2 L_pd + ω3 L_sem
ω1 = 1.0, ω2 = 0.05, ω3 = 1.0
```

监督来源包括 LiDAR sparse depth、Metric3D pseudo dense depth、Grounded-SAM pseudo semantic labels。

### Stage 2-A：Gaussian-flow-guided latent world model

预测每个 Gaussian 的动态位移 `Δμ`，再结合 ego motion 对齐到下一帧：

```text
μ_{t+1} = T_ego^{t→t+1}( μ_t + Δμ_t )
```

传播后的 Gaussians 被 rasterize 成 future BEV latent，并用下一帧图像经过 frozen Gaussian perception module 得到的 BEV latent 监督：

```text
L_bev = || B̂_{t+1} - B_{t+1} ||_2
```

该分支主要提升 3D occupancy perception 和 4D occupancy forecasting。

### Stage 2-B：Ego-planning-guided latent world model

当前 3D Gaussians rasterize 成 latent BEV，再抽取 scene queries。Waypoint queries 通过 cross-attention 读取 scene queries 并预测 ego trajectory。预测轨迹通过 Motion-Aware Layer Normalization 调制 scene queries，用于 future latent prediction。

```text
L_reg = || T̂ - T ||_1
L_plan = L_reg + L_bev
```

该分支主要提升 motion planning。

## 创新点

1. Holistic Gaussian-centric pre-training：把 3D Gaussian 作为统一底座，覆盖 perception、forecasting、planning。
2. Rendering-based self-supervision：用 depth/semantic rendering 学几何语义，不直接依赖人工 occupancy label。
3. Gaussian-flow-guided latent world model：用 Gaussian flow 学时序 3D 表征，服务 perception/forecasting。
4. Ego-planning-guided latent world model：用 ego trajectory condition future latent，服务 motion planning。
5. Dual design：不强行用一个 world model 统一所有任务，降低学习复杂度。

## 实验结论

| 任务 | Baseline | DLWM | 提升 |
|---|---|---|---|
| 3D occupancy perception | IoU 31.77 / mIoU 20.83 | IoU 34.61 / mIoU 21.85 | +2.84 IoU / +1.02 mIoU |
| 4D occupancy forecasting | Avg IoU 25.65 / Avg mIoU 15.09 | Avg IoU 30.60 / Avg mIoU 17.77 | +4.95 IoU / +2.68 mIoU |
| Motion planning | Avg L2 0.55m / Col. 0.24% | Avg L2 0.46m / Col. 0.19% | L2 约下降 16% |

## 关键消融

Dual vs Unified：

| 设计 | mIoU ↑ | L2 ↓ | Col. ↓ |
|---|---:|---:|---:|
| Unified | 18.9 | 0.58 | 0.22 |
| Dual | 19.3 | 0.46 | 0.19 |

说明 Gaussian flow 和 ego planning 的目标不同，强行统一会增加 planning 分支学习负担。

## 局限与疑问

- 工程链条复杂，依赖 Metric3D、Grounded-SAM、Gaussian perception、BEV rasterization 等多个组件。
- 两个 world model 分开训练，说明所谓 holistic 仍不是完全统一的端到端世界模型。
- 附录显示 future frame 数量 N=1 最好，更多未来帧性能下降，长时预测仍难。
- 复现成本不低，25,600 Gaussians 和两阶段预训练对普通实验室有门槛。

## 组会汇报建议

短讲时不要按公式展开，建议讲：

1. 为什么 Gaussian-centric 需要 pre-training。
2. Stage 1 怎么用 rendering 学几何语义。
3. Stage 2 为什么拆成 Gaussian-flow-guided 和 ego-planning-guided 两个 world model。
4. 三个任务的关键提升数字。
5. 自己的理解：Dual 解耦比 SOTA 数字更值得学习。
