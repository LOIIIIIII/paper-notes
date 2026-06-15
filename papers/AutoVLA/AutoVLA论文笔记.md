# AutoVLA 论文精读笔记

论文：**AutoVLA: A Vision-Language-Action Model for End-to-End Autonomous Driving with Adaptive Reasoning and Reinforcement Fine-Tuning**  
版本：arXiv:2506.13757v3，NeurIPS 2025 标注版本  
本笔记基于论文 PDF、前序逐段讲解和关于 codebook 的问答整理。

## 一句话总结

AutoVLA 用 physical action codebook 把低层连续轨迹变成离散 action tokens，从而把场景推理、动作生成和强化后训练统一进一个 autoregressive VLA 框架。

## 论文要解决的问题

- VLM 会理解和解释场景，但不天然会输出物理可执行轨迹。
- 直接输出文本 waypoint 或连续坐标容易数值不准、格式不稳、轨迹不平滑。
- 外接 planner 或 decoder 会让结构复杂，削弱统一端到端训练。
- 复杂场景需要 CoT reasoning，简单场景不需要每次都长推理。

## 主要创新点

1. **Physical action codebook**：把连续轨迹切成 0.5 秒 motion segments，并映射到 2048 个动作 token。
2. **Unified reasoning and action**：同一个 VLM 输出 reasoning tokens 和 action tokens。
3. **Fast / slow thinking**：SFT 同时训练 action-only 和 CoT-enhanced 输出。
4. **GRPO-based RFT**：用 `r = rDriving - λr rCoT` 同时优化驾驶质量和推理效率。

## 码本 Codebook 细读

codebook 是自动驾驶动作空间里的“词表”。普通 LLM 的词表里有文字 token；AutoVLA 的动作词表里有 `<action_0>` 到 `<action_2047>`。

每个 action token 背后存的是：

```text
ak = (Δx, Δy, Δθ)
```

其中 `Δx / Δy / Δθ` 是相对于当前 0.5 秒片段起点的局部运动变化：沿当前车体坐标前进多少、横向偏移多少、车头方向改变多少。

### 码本构建

- 从 WOMD 真实轨迹中采样 0.5 秒车辆运动片段。
- CARLA 因为动力学不同，单独从 CARLA-Garage 构建仿真码本。
- 每个 segment 用最终帧 bounding-box contour 表示。
- 用 K-disk clustering 选出 2048 个代表片段，阈值 `δ = 0.05 m`。
- 每个代表片段抽出 `(Δx, Δy, Δθ)`，成为一个 action token。

### 训练时怎么用

连续 GT 轨迹先切成 10 个 0.5 秒片段，每段映射到最近的码本 token：

```text
GT trajectory → <action_520><action_920>...<action_103>
```

于是 planning 从连续回归变成 next-token prediction。

### 推理时怎么用

模型自回归生成 action token 序列，再查表得到每个 token 对应的 `(Δx, Δy, Δθ)`，最后从当前 ego pose 开始逐段累加成未来 5 秒轨迹。

### 自回归时码本会变吗

不会。码本是固定查表结构。变化的是每一步模型的上下文和下一个 token 的概率分布：

```text
p(action_i | image, instruction, ego state, previous tokens)
```

同一个 token 的局部含义固定，但它作用在不断更新的 ego pose 上。

## 训练流程

### SFT

输出序列：

```text
x = [l1, ..., lL, a1, ..., aT]
```

其中 `l` 是 reasoning tokens，`a` 是 action tokens。

SFT loss：

```text
LSFT_i = wi · (LLM_i + λa Laction_i)
wi = λcot if CoT is present, otherwise 1
λa = 1, λcot = 40
```

CoT 数据由 Qwen2.5-VL-72B 自动蒸馏，GT driving action 作为 hint。

### RFT / GRPO

RFT 对同一场景采样一组候选输出，解码 action tokens 得到轨迹，再用 reward 比较好坏。

```text
r = rDriving - λr rCoT
```

NAVSIM 使用 PDMS 作为 `rDriving`，Waymo 使用 normalized ADE。`rCoT` 惩罚过长 reasoning。

## 实验结论

### NAVSIM / nuPlan

| Method | PDMS ↑ | Collision ↑ | Progress ↑ | TTC ↑ |
|---|---:|---:|---:|---:|
| AutoVLA One-shot | 80.54 | 96.89 | 75.82 | 88.06 |
| AutoVLA Post-RFT | 89.11 | 98.41 | 81.87 | 98.04 |
| AutoVLA Best-of-N | 92.12 | 99.14 | 87.55 | 97.12 |
| TrajHF | 93.95 | 99.30 | 90.39 | 98.02 |

RFT 显著提升 PDMS，但 AutoVLA 在 NAVSIM 表中不是绝对 SOTA。

### Bench2Drive / CARLA

| Method | Driving Score ↑ | Success Rate ↑ | Efficiency ↑ | Comfortness ↑ |
|---|---:|---:|---:|---:|
| ORION | 77.74 | 54.62 | 151.48 | 17.38 |
| AutoVLA | 78.84 | 57.73 | 146.93 | 39.33 |

AutoVLA 闭环表现略优于 ORION，尤其 comfortness 更高。

### 码本消融

| Codebook Size | ADE ↓ | FDE ↓ | Movement Coverage ↑ | Codebook Usage ↑ |
|---:|---:|---:|---:|---:|
| 256 | 0.0687 | 0.1034 | 86.47% | 100.0% |
| 1024 | 0.0253 | 0.0282 | 97.41% | 100.0% |
| 2048 | 0.0182 | 0.0203 | 99.42% | 100.0% |
| 4096 | 0.0141 | 0.0155 | 100.0% | 91.46% |

2048 是重建误差、覆盖率和码本使用率之间的折中点。

## 用户问答整理

### K-disk 是什么

K-disk 是一种覆盖式聚类/采样方法，从大量真实短时运动片段中选 K 个代表样本，并要求被选中的片段之间距离不能太近。AutoVLA 用 average contour distance 和 `δ = 0.05 m` 保证 2048 个 token 覆盖多样运动。

### 为什么是 Δx 和 Δy

`Δx / Δy / Δθ` 是相对于当前 0.5 秒 segment 起点的局部位姿变化。它不是全局坐标，也不是所有 token 都相对最初位置。

### 自回归过程中码本会不会变

不会。码本固定不变，变化的是模型每一步的概率分布和已经累积出来的 ego pose。

## 局限与疑问

- CoT 数据用了 GT decision 作为 hint，可能是事后解释。
- 码本受训练轨迹分布限制，极端 maneuver 可能覆盖不足。
- 离散 token 的单步误差可能在 10 步轨迹中累积。
- reward 偏 benchmark：nuPlan 用 PDMS，Waymo 用 ADE。
- 实时性仍有限，论文承认接近 1 Hz 且高度依赖 GPU。

## 对普通组的启发

最值得先复现的是 action codebook：

```text
1. 从轨迹数据切 0.5s motion segments
2. 聚类成 K=512/1024/2048 action codebook
3. 把 GT trajectory token 化
4. 训练小模型预测 action token sequence
5. 解码轨迹并比较 L2、collision、smoothness
```
