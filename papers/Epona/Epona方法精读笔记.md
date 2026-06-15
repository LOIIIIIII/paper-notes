# Epona 方法精读笔记

本笔记基于用户粘贴的 Epona Method 3.1-3.5、Figure 2/3/4 及追问整理。

## 一句话总结

Epona 把 driving world model 重写成连续 latent 空间中的自回归下一帧预测问题：MST 建模历史因果动态，TrajDiT 生成未来轨迹，VisDiT 生成动作条件下一帧，并用 chain-of-forward training 缓解长时漂移。

## 方法范式

传统 GPT-style world model：

```text
连续图像 → 离散 token → next-token prediction
```

问题是 quantization 会损伤高频细节，token-by-token 建模削弱空间相关性。

传统 video diffusion：

```text
历史帧 → 一次性生成固定长度未来 n 帧
```

问题是长度固定，长时生成要反复调用，容易 error accumulation 和 content drift。

Epona：

```text
continuous latent autoregression + diffusion generation
```

既保留 autoregressive 的长度灵活性，也保留 diffusion 的生成质量。

## 总体结构

```text
历史图像 {O_t} + 历史轨迹 {a_{t-1→t}}
        ↓
DCAE Encoder + MST
        ↓
compact latent F
     ↙              ↘
TrajDiT            VisDiT
未来 3 秒轨迹       动作条件下一帧图像
```

## MST

MST 输入视觉 latent `Z ∈ R^{B×T×L×C}` 和动作 `a ∈ R^{B×T×3}`，拼接后得到：

```text
E ∈ R^{B×T×(L+3)×D}
```

它交替使用 causal temporal attention 和 multimodal spatial attention。前者保证时间因果结构，后者融合视觉场景和历史动作。

## TrajDiT / VisDiT

TrajDiT 用 rectified flow 生成未来轨迹：

```text
L_traj = E[ || v_traj(a_t, t) - (a - ε) ||² ]
```

VisDiT 生成下一帧图像 latent，并额外接收动作控制 `a_{T→T+1}`。总 loss：

```text
L = L_traj + L_vis
```

## 3.4 Chain-of-Forward Training

普通 teacher forcing 的问题：

```text
训练时：真实历史 → 预测下一帧
推理时：模型预测历史 → 继续预测下一帧
```

这个 domain gap 会导致 error accumulation。Epona 周期性地把模型自己预测的 latent 反馈回去作为后续条件，让模型训练时见到推理阶段的不完美历史。

为了效率，作者不用完整 diffusion sampling，而是用 velocity 一步估计 clean latent：

```text
x̂_(0) = x_(t) + t v_Θ(x_(t), t)
```

注意：这不是消灭误差累计，只是缓解 autoregressive drift。

## 3.5 Temporal-aware DCAE Decoder

DCAE 压缩效率高，能减少 latent tokens 并支持更长历史上下文。但它是 image autoencoder，逐帧 decode 容易 flickering。

Epona 在 DCAE decoder 前加入 spatiotemporal self-attention layers，让多帧 latent 先交互，再解码成更一致的视频帧。encoder 固定，尽量复用预训练参数。

## 用户问题整理

### variable-length long-range prediction 的问题是不是误差累计？

是其中一个核心原因。固定长度 video diffusion 生成更长视频时通常要反复调用模型，前段生成的小错误会进入后段条件，导致 error accumulation 和 content drift。

### Epona 怎么解决？

它改用 continuous latent 中的 autoregressive next-frame prediction，并通过 chain-of-forward training 让模型适应自生成历史。

### 这样不也会误差累计吗？

会。只要是 autoregressive，就仍然可能误差累计。Epona 的贡献是缓解，不是从理论上消灭。

## 值得学习的点

- 把固定长度视频生成改成 sequential local prediction。
- 把视频生成和轨迹规划分成两个 DiT 分支，但共享 temporal latent。
- 用训练策略处理 exposure bias，而不是只在推理时硬 rollout。
- 讨论论文时要把 “solve error accumulation” 改成更严谨的 “mitigate autoregressive drift”。
