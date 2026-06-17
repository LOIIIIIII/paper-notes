# LeWorldModel 论文精读笔记

论文：LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels  
版本：arXiv:2603.19312v3, 2026-06-03  
作者：Lucas Maes, Quentin Le Lidec, Damien Scieur, Yann LeCun, Randall Balestriero  
笔记来源：本地 PDF 阅读 + 前序问答整理。

## 一句话总结

LeWorldModel 提出一个从 raw pixels 端到端训练的 JEPA 潜空间世界模型，用 next-embedding prediction 和 SIGReg 高斯分布正则两项损失避免 representation collapse，并在多个 2D/3D 控制任务上取得接近或优于 DINO-WM、PLDM 的表现。

## 论文要解决的问题

JEPA 类 world model 希望在 latent space 预测未来，而不是重建像素。但如果 encoder 和 predictor 同时训练，单纯的 latent prediction objective 有一个平凡最优解：

```text
z_t = encoder(o_t)
z_{t+1} = encoder(o_{t+1})
z_hat_{t+1} = predictor(z_t, a_t)

L_pred = || z_hat_{t+1} - z_{t+1} ||^2
```

如果：

```text
encoder(o) = c, for all o
predictor(c, a) = c, for all a
```

则：

```text
L_pred = || c - c ||^2 = 0
```

这就是 representation collapse：loss 很低，但 latent 不再包含任何状态信息。

## 核心方法

LeWM 的训练目标是：

```text
L_LeWM = L_pred + lambda * SIGReg(Z)
```

其中：

```text
L_pred = || predictor(encoder(o_t), a_t) - encoder(o_{t+1}) ||^2
```

SIGReg 要求 latent distribution 接近 isotropic Gaussian：

```text
P_Z ≈ N(0, I)
```

如果 latent collapse：

```text
z_i = c, for all i
P_Z = delta_c
Var(Z) = 0
```

这与标准高斯的：

```text
Var(N(0, I)) = I
```

矛盾。因此 collapse 不再是总损失的好解。

## SIGReg 细读

SIGReg 不直接做高维分布检验，而是随机采样多个单位方向：

```text
u^(1), u^(2), ..., u^(M)
```

然后投影：

```text
h^(m) = Z u^(m)
h_i^(m) = z_i · u^(m)
```

如果：

```text
z ~ N(0, I)
```

则任意单位方向上都有：

```text
z · u ~ N(0, 1)
```

每个一维投影通过 Epps-Pulley normality test 与标准高斯比较：

```text
phi_N(t; h) = (1 / N) * sum_{j=1}^N exp(i t h_j)
phi_0(t) = exp(-t^2 / 2)

T(h) = integral w(t) * | phi_N(t; h) - phi_0(t) |^2 dt
```

最终：

```text
SIGReg(Z) = (1 / M) * sum_{m=1}^M T(Z u^(m))
```

根据 Cramer-Wold theorem，如果所有一维方向上的投影分布都匹配，则高维联合分布也匹配。实际训练中用有限个随机方向近似，论文默认 M = 1024。

## Latent Planning

训练后使用 goal-conditioned latent MPC：

```text
z_1 = encoder(o_1)
z_g = encoder(o_g)
z_hat_{t+1} = predictor(z_hat_t, a_t)
C(z_hat_H) = || z_hat_H - z_g ||^2
a_1:H* = argmin C(z_hat_H)
```

动作序列用 CEM 优化。

## 实验结果

| 任务 | LeWM | PLDM | DINO-WM | 备注 |
|---|---:|---:|---:|---|
| Push-T | 96 | 78 | 74 | LeWM pixels-only 超过 DINO-WM+prop 的 92 |
| Reacher | 86 | 78 | 79 | LeWM 小幅领先 |
| OGBench-Cube | 74 | 65 | 86 | DINO-WM 受益于 DINOv2 预训练 |
| Two-Room | 87 | 100 | 97 | 低维简单环境可能不适合高维高斯 prior |

其他关键结果：

- 模型约 15M 参数。
- 单 GPU 数小时可训练。
- 规划最高比 DINO-WM 快约 48x。
- lambda 在 [0.01, 0.2] 区间比较稳。
- 加 reconstruction loss 反而降低 Push-T 成功率。

## 物理理解

作者通过 probing 发现 LeWM latent 包含 agent location、block location、block angle、end-effector position、cube position 等物理变量。Violation-of-expectation 实验中，物体 teleport 会产生明显 prediction error spike，而颜色突变影响较弱，说明模型更敏感于物理连续性破坏。

## 局限与疑问

- 规划仍是短 horizon，长程推理未解决。
- 依赖 action-labeled offline trajectories。
- Two-Room 结果说明 isotropic Gaussian prior 不总是合适。
- OGBench-Cube 中旋转、速度等细粒度动态信息不如 DINO-WM。
- physical understanding 的证据主要来自 probing 和 surprise，还不能等同于强物理推理。

## 对自动驾驶 World Model 的启发

LeWM 对自动驾驶的价值是训练范式层面的：端到端 latent dynamics 很容易 collapse，因此需要显式分布约束；同时评价 latent world model 时，不应只看图像重建，而要看它是否支持预测、规划、风险评估和反事实推演。

自动驾驶中真正有价值的 latent 应隐含：

- 道路拓扑和可行驶区域；
- 动态实体的位置、速度、朝向；
- 交互关系和意图；
- 物理约束与碰撞风险；
- 交通规则和信号状态；
- 遮挡和未来多模态不确定性。
