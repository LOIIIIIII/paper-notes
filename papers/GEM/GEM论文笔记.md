# GEM 论文精读笔记

## 基本信息

- 论文标题：GEM: Generative Supervision Helps Embodied Intelligence
- 作者单位：Tsinghua University, Tencent Hunyuan
- arXiv：2605.28548v1，2026-05-27
- 主题：Embodied VLM、Vision-Language-Action、depth generative supervision、robot manipulation

## 一句话总结

GEM 用 depth map generation 作为生成式辅助监督，让 Embodied VLM 的 visual tokens 不只对齐文本语义，也包含距离、几何结构和空间关系；再将该 backbone 扩展成 GEM-VLA，用于机器人连续动作生成。

## 论文要解决的问题

现有 Embodied VLM 主要通过 VQA、caption、instruction tuning 学语义理解，但机器人执行任务需要低层几何和物理结构。普通 VLM 的 final-layer visual tokens 可能知道“物体是什么”，但不一定保留“物体多远、前后关系如何、可操作空间在哪里”。GEM 的目标是在 VLM 预训练阶段直接注入空间结构监督。

## 核心创新

- **Depth generative supervision**：用 depth generation 而非 RGB reconstruction 作为辅助目标，因为 depth 更直接表达距离、遮挡和几何布局。
- **Hybrid autoregressive-diffusion architecture**：保留 autoregressive VLM 做语言理解，接 DiT depth head 做结构生成监督。
- **Progressive training recipe**：先训练 connector，再训练 connector + DiT，最后联合训练，避免直接混训不稳定。
- **GEM-VLA**：把经过 depth supervision 增强的 GEM 表征接入 action expert，验证其能迁移到机器人操作。

## Method 精读

普通 VLM 将图像 `o` 和语言指令 `l` 编码为：

```text
h = (ho, hl) = Mθ(o, l)
```

其中 `ho` 是 visual tokens，`hl` 是 language tokens。标准训练使用：

```text
LCE = - Σ log pθ(yi | y<i, ho, hl)
```

GEM 认为这个目标主要强化语义理解，不保证 visual tokens 保留几何结构。因此加入 depth generation：

```text
c = Cϕ(ho)
Lflow = E || vt(xt, c) - ut(xt | d) ||²
```

`Cϕ` 是 connector，`Gψ` 是 DiT-based depth generative head，`d` 是真实或伪深度图。Stage 3 总损失：

```text
Ltotal = LCE + λLflow
```

其中 λ = 0.1。

### Progressive Training

1. **Stage 1 Connector Initialization**：冻结 VLM 和 DiT，只训练 connector，用 `Lflow` 对齐 feature space。
2. **Stage 2 Generative Head Initialization**：冻结 VLM，训练 connector + DiT，让 depth head 适应 VLM 条件特征。
3. **Stage 3 Joint Training**：解冻可训练模块，同时优化 `LCE + λLflow`。
4. **Stage 4 GEM-VLA**：用 GEM 的 K/V tokens 条件化 DiT-based action expert，优化 `Laction + λLflow`。

## GEM-4M 数据

- Embodied grounding：约 1M QA pairs，覆盖 object detection、instruction localization、affordance recognition。
- Physical / spatial reasoning：整合 MindCube、ViCA、SPAR、VSI-590K、RoboVQA、Robo2VLM、RefSpatial 等。
- Spatiotemporal planning：从机器人视频中构造 sub-task / trajectory planning QA，约 50K samples。

## 实验结论

### Embodied reasoning

GEM 相比 Qwen3-VL-SFT 继续提升，尤其是 VSI-Bench 距离和空间关系相关指标：

- Qwen3-VL-2B-SFT VSI-Bench All：60.0
- GEM-2B VSI-Bench All：62.8
- Qwen3-VL-8B-SFT VSI-Bench All：68.6
- GEM-8B VSI-Bench All：70.6

### LIBERO

GEM-VLA 在 LIBERO 上平均成功率 96.1，高于 Qwen3VL-SFT-VLA 的 94.9、DepthVLA 的 94.9 和 π0 reported 的 94.2。

### Real-world tasks

真实 UR5 任务包括 cloth folding、unzipping、table bussing。GEM-VLA All Task Average 为 43.0，高于 π0.5 的 28.7 和 π0-FAST 的 22.3。

## 消融

Table 4 表明：

- Depth supervision 优于 RGB supervision。
- Progressive training 优于 direct end-to-end co-training。
- GEM 在 CV-Bench、VSI-Bench、RoboSpatial 上取得更好结果。

## 局限

- 训练资源高：VLM 预训练 32 张 A800，VLA 微调 8 张 A800。
- 部分 depth label 来自 DepthAnythingv3 伪标签。
- GEM-4M 数据构建流程复杂。
- 真实机器人任务范围仍有限。
- “学到物理知识”应谨慎表述，更准确是学习到更强几何/结构表征。

## 对 AD + World Model 的启发

GEM 和 LVDrive 共同说明：生成监督的关键不是生成图像本身，而是选择与下游动作/规划相关的结构目标来塑造 representation。

```text
Robotics: depth supervision -> geometry-aware visual tokens
Autonomous driving: BEV / occupancy / future latent -> planning-aware scene tokens
```

