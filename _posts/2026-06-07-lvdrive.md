---
layout: post
title: "LVDrive: Latent Future Visual Representation Learning for VLA Autonomous Driving"
date: 2026-06-07
categories: [paper-notes, autonomous-driving, vla, world-model]
tags: [LVDrive, VLA, Bench2Drive, latent-world-model, trajectory-planning]
---

# LVDrive 论文笔记

> **一句话**：LVDrive 不生成未来 RGB 图像，而是在 latent space 中预测未来视觉语义表示，并用两阶段轨迹解码让未来语义显式参与轨迹精修。

## Why It Matters

现有 VLA 自动驾驶模型常常只依赖 sparse action labels。它们能学到“应该怎么开”，但不一定学到“为什么这样开”以及“未来场景会怎样变化”。World-model 路线试图预测未来图像，但像素级重建成本高，也可能偏离 motion planning 真正需要的语义动态。

LVDrive 的主张是：**规划不需要生成逼真的未来图像，规划需要能预测未来语义和动态关系的 latent representation。**

## Core Idea

```text
Multi-view images + instruction
        ↓
VLA / LLM reasoning
        ↓
Future visual placeholder hidden states
        ↓
Latent future visual features
        ↓
Coarse trajectory → future-aware trajectory refiner
        ↓
Final trajectory
```

## Method

### Latent Future Visual Prediction

LVDrive 使用特殊 tokens 表示未来视觉 latent：

```text
<img_start> <img_0> ... <img_N> <img_end>
```

每个 `<img_i>` 在 LLM 最后一层对应一个 hidden state。第 `t+j` 个未来帧的 hidden states 组成：

```text
H_{t+j} ∈ R^{N × D}
```

`H_{t+j}` 不是 Vision Backbone 的输出，而是模型基于当前/历史图像和文本指令推理出来的未来视觉表示。它经过 `VISθ` 得到预测 latent visual feature，再与 frozen Vision Backbone 从真实未来帧提取的 teacher feature 对齐。

### Two-stage Trajectory Decoding

LVDrive 不把未来视觉任务简单拼到规划任务上，而是采用两阶段解码：

1. **Coarse Proposal**：planning embedding 通过 VAE-based generative planner 生成粗轨迹。
2. **Trajectory Refiner**：ego motion queries cross-attend future visual embeddings，输出 fine-grained final trajectory。

这个设计避免了视觉预测和动作规划直接混训造成的 feature-space 冲突。

## Key Results

| Method | DS | SR | Avg. L2 |
|---|---:|---:|---:|
| ORION | 77.74 | 54.62% | 0.68 |
| UniDrive-WM-AR | 79.22 | 56.36% | 0.64 |
| UniDrive-WM-AR+Diff | 79.31 | 56.42% | 0.63 |
| **LVDrive** | **80.71** | **58.26%** | 0.63 |

LVDrive 在 Bench2Drive closed-loop evaluation 上取得最高 DS 和 SR。

## Ablation Takeaways

| Variant | Main Change | DS | SR |
|---|---|---:|---:|
| Mbase | action-only baseline | 65.25 | 4/10 |
| Mvis | add latent future prediction | 66.31 | 3/10 |
| Mone | one-stage fusion | 60.43 | 3/10 |
| LVDrive | two-stage decoding | 82.39 | 7/10 |

最重要的结论：**latent future prediction 本身不够，关键是 two-stage decoding 如何把 future semantics 稳定地接入 trajectory generation。**

## Strengths

- 避免 pixel-level future image reconstruction。
- 用 dense visual supervision 弥补 sparse action supervision。
- single forward process 比 autoregressive visual/action token generation 快很多。
- 在 closed-loop driving score 和 success rate 上表现强。

## Limitations

- Front-view future prediction 可能导致后方交互能力不足，Give Way skill 只有 20.00。
- 训练资源很高：论文使用 32 张 NVIDIA H20 96GB。
- 消融主要基于 Dev10，小规模评测的统计稳定性有限。
- Teacher backbone 选择对性能影响很大。
- Open-loop L2 不是最优，因此不能简单说所有指标全面领先。

## My Reading Note

LVDrive 值得学习的不是“用更大模型刷分”，而是一个很清楚的 mechanism story：

```text
future prediction should be semantic, not pixel-perfect;
future representation should condition planning, not just supervise it;
visual-action alignment needs careful decoding design.
```

对资源有限的组，可以把这个思想迁移到更小的 planner：冻结 backbone，只训练 future latent predictor、adapter 或 trajectory refiner，并在 CARLA/Bench2Drive 子集上验证机制。

