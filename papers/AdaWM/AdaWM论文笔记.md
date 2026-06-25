# AdaWM 论文精读笔记

论文：AdaWM: Adaptive World Model Based Planning for Autonomous Driving  
会议：ICLR 2025  
作者：Hang Wang, Xin Ye, Feng Tao, Chenbin Pan, Abhirup Mallik, Burhaneddin Yaman, Liu Ren, Junshan Zhang  
笔记来源：本地 PDF 阅读 + 前序问答整理。

## 一句话总结

AdaWM 解决的是预训练 world model 和 policy 迁移到新驾驶任务时的在线微调问题：它每一步先判断主要性能下降来自 dynamics model mismatch 还是 policy mismatch，再选择性、轻量地更新对应模块。

## 论文要解决的问题

World model based RL 通常先预训练一个 latent dynamics model，再训练 planning policy。但迁移到新任务时，性能会因为 distribution shift 下降。关键问题不是“要不要微调”，而是：

```text
当前应该微调 world model，还是微调 policy？
```

盲目 model-only、policy-only 或交替更新，可能让另一个模块的 mismatch 更严重。

## 方法框架

预训练阶段：

```text
offline dataset -> pretrained dynamics model WM_phi
                -> pretrained planning policy pi_omega
```

在线微调阶段：

```text
collect new-task samples
estimate dynamics mismatch
estimate policy mismatch
update only the dominant mismatch side
```

DreamerV3 风格 model state：

```text
z_t ~ q_phi(z_t | h_t, s_t)
x_t = [h_t, z_t]
```

dynamics model：

```text
x_{t+1} ~ WM_phi(x_{t+1} | x_t, a_t)
```

policy：

```text
a_t ~ pi_omega(a_t | x_t)
```

## 性能下降拆解

迁移到新任务后的 performance gap：

```text
eta - eta_hat
= E_{x~rho_0}[ V^pi_{WM(P)}(x) - V^pi_{WM(P_hat)}(x) ]
```

预测误差分解：

```text
epsilon_k = (x_k - x_bar_k) + (x_bar_k - x_hat_k)
```

其中：

```text
x_k - x_bar_k       = 新任务与预训练任务的 distribution shift
x_bar_k - x_hat_k   = pretrained dynamics model 的预测误差
```

Theorem 1 的上界中有两类关键项：

```text
dynamics model mismatch: E_max, E_P_hat
policy mismatch: E_pi
```

## AdaWM 具体怎么微调

每个 finetuning step 收集新任务数据：

```text
W = {(x, a, r)}
```

保留预训练 replay buffer：

```text
B = pretraining replay buffer
```

估计 dynamics mismatch：

```text
M_model = D_TV(P | P_hat)
```

估计 policy mismatch：

```text
M_policy = D_TV(pi_t | pi_omega)
```

更新规则：

```text
if D_TV(P | P_hat) > C * D_TV(pi_t | pi_omega):
    update dynamics model
else:
    update policy
```

### 更新 dynamics model

使用 LoRA/NoLa 风格低秩更新：

```text
phi = (B Z)^T Phi
phi' = (B' Z)^T Phi
```

只更新 B。

### 更新 policy

把 policy network 写成多个 sub-units 的凸组合：

```text
omega = sum_i delta_i * omega_i
omega = Delta^T Omega
```

只更新组合权重：

```text
Delta -> Delta'
```

## World Model 和 Policy 怎么协同

world model 是“脑内模拟器”，policy 是“决策者”。policy 在 world model 里 imagination rollout：

```text
x_t
  -> policy picks a_t
  -> world model predicts x_{t+1}, r_t
  -> policy picks a_{t+1}
  -> world model predicts x_{t+2}, r_{t+1}
```

policy 最大化 imagined return：

```text
V^pi_WM(x_t)
= E[ sum_{i=1}^K gamma^i r(x_{t+i-1}, a_{t+i-1})
     + gamma^K Q(x_{t+K}, a_{t+K}) ]
```

如果 world model 想象错了，policy 会基于错误未来做决策；如果 world model 准但 policy 动作不适合，也会失败。AdaWM 的价值就是在线判断该修哪一个。

## 实验结果

环境：CARLA / Bench2Drive  
观察：128x128 BEV semantic segmentation  
预训练：12h on V100  
在线微调：1h on V100  
指标：Success Rate, Time-to-Collision

主任务：

| 任务 | DreamerV3 SR | AdaWM SR | AdaWM TTC |
|---|---:|---:|---:|
| ROM03 | 0.40 | 0.82 | 2.05 |
| RTD12 | 0.32 | 0.66 | 1.25 |
| LTM03 | 0.28 | 0.72 | 1.32 |
| LTD03 | 0.35 | 0.70 | 1.92 |

微调策略对比：

| 方法 | ROM03 SR | RTD12 SR | LTM03 SR | LTD03 SR |
|---|---:|---:|---:|---:|
| No finetuning | 0.40 | 0.32 | 0.28 | 0.35 |
| Policy-only | 0.72 | 0.63 | 0.61 | 0.61 |
| Model-only | 0.60 | 0.48 | 0.68 | 0.63 |
| Model+Policy | 0.52 | 0.50 | 0.60 | 0.58 |
| AdaWM | 0.82 | 0.66 | 0.72 | 0.70 |

补充场景：

| 任务 | DreamerV3 SR | AdaWM SR |
|---|---:|---:|
| HC13 | 0.33 | 0.73 |
| HE12 | 0.52 | 0.89 |
| YE12 | 0.15 | 0.52 |
| BI12 | 0.42 | 0.59 |
| VT11 | 0.58 | 0.88 |

## 局限与疑问

- 输入是 BEV semantic segmentation，不是 raw camera。
- 实验仍在 CARLA/Bench2Drive 仿真环境内。
- TV distance 在真实车端如何稳定估计仍有难度。
- 理论假设较强，主要用于指导设计。
- VAD/UniAD 没有被同样 online finetuning，baseline 并非完全同类公平比较。

## 对 AD World Model 的启发

AdaWM 的关键启发是：新场景表现差时，不能只问 policy 怎么改，还要诊断 world model 对新动态是否预测错。部署型 world model 系统应有能力判断：

```text
当前失败主要来自 dynamics mismatch 还是 policy mismatch？
```

这和 LeWorldModel、Drive-OccWorld 形成互补：LeWorldModel 关注稳定训练 latent world model，Drive-OccWorld 关注未来 occupancy 如何服务规划，AdaWM 关注预训练 world model 和 policy 如何在线适应新任务。
