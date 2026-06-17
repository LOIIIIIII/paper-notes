# CoWorld-VLA 论文精读笔记

论文：**CoWorld-VLA: Thinking in a Multi-Expert World Model for Autonomous Driving**  
来源：arXiv:2605.10426v2  
代码：论文中写明将发布到 `github.com/AFARI-Research/CoWorld-VLA`  
阅读范围：基于论文 PDF 正文、实验表、appendix，以及本轮对 JEPA token 和 expert 权重的问答整理。

## 一句话总结

CoWorld-VLA 把 VLA 的中间推理从自然语言 CoT 改成 **Multi-Expert Latent CoT**：用 semantic、geometry、dynamic、trajectory 四类 expert tokens 承载不同世界知识，并通过 HMEF diffusion planner 将这些 latent conditions 融合成连续轨迹。

## 论文要解决的问题

现有 VLA / world model 自动驾驶方法主要有三个不足：

- 直接 action prediction 缺少显式中间 reasoning state。
- 文本 CoT 可解释但难保留连续空间、几何和运动信息，且推理慢。
- 单一 latent world representation 不够完整，并且很多 future representation 只作为辅助监督，不在推理时显式影响 planner。

论文核心判断是：自动驾驶需要 planner-accessible 的中间世界表征，而不是只会说话的文本推理或只用于训练的 future prediction。

## 核心创新

### 1. Multi-Expert Latent CoT

作者在 VLM latent space 中插入四类 expert tokens：

- `H_sem`：semantic interaction token，建模语义交互和高层意图。
- `H_geo`：geometric structure token，建模道路结构、空间约束和 3D 几何。
- `H_dyn`：dynamic evolution token，建模未来视觉动态和时序演化。
- `H_traj`：ego trajectory token，建模自车行为目标和轨迹先验。

这相当于把一个整体 future latent 分解为多种 planning-relevant factors。

### 2. 多源专家监督

四类 token 分别由不同专家模型或任务监督：

- `H_sem` 对齐 frozen V-JEPA 从未来观测提取的 semantic / predictive features。
- `H_geo` 对齐 frozen VGGT 的 geometric features。
- `H_dyn` 作为 Wan world model 的条件，监督未来视频生成。
- `H_traj` 通过 MLP 回归未来 trajectory。

总损失为：

```text
L_total = w_dyn L_dyn + w_sem L_sem + w_geo L_geo + w_traj L_traj
```

### 3. HMEF diffusion planner

Stage 3 使用 Hierarchical Multi-Expert Fusion planner，在 normalized action space 中从噪声轨迹开始 denoising。每个 expert branch 预测一条轨迹，再用 learned fusion weights 融合：

```text
A_final = Σ α_e A_e
```

其中 `α = softmax(w)` 是训练学习得到的。

## 方法细读

### Stage 1：Action-conditioned Predictive World Model

第一阶段用 Wan2.2-5B 训练未来视频世界模型。这里的 action-conditioned 不是低层控制，而是文本 prompt 条件，包括：

- Scene
- Speed
- Navigation
- Trajectory

视频序列被 frozen Wan VAE 编码为历史 latent 和未来 latent：

```text
z = E_vae(x) = [z_h, z_f]
```

训练时只对未来 segment 加噪：

```text
z_f,σ = (1 - σ) z_f + σ ε
v_target = ε - z_f
```

用 flow matching 学习未来 latent 的速度场。历史 latent 保持 clean，作为已观测上下文。

### Stage 2：Multi-Expert Representation Learning

输入当前图像、驾驶 prompt 和四类 expert action tokens，经 Qwen3-VL 后得到：

```text
{H_ctx, H_sem, H_geo, H_dyn, H_traj}
  = πθ(e_img, e_txt, t_sem, t_geo, t_dyn, t_traj)
```

关键点：这些 expert token hidden states 不当成文本输出，而是 continuous latent reasoning states。

JEPA 分支不是“JEPA token”，而是用 V-JEPA feature 监督 semantic token：

```text
Z_sem = Pool(E_sem(o_fut))
H_sem -> Adapter -> Z_hat_sem
L_sem = SmoothL1(Z_hat_sem, Z_sem) + cosine loss
```

VGGT 分支类似，用几何特征监督 `H_geo`。Wan 分支用 `H_dyn` 条件化 future scene generation。Trajectory 分支用 `H_traj` 直接回归轨迹。

### Stage 3：Hierarchical Multi-Expert Fusion

HMEF 使用 scene tokens 和 expert action tokens 作为条件，在 normalized trajectory space 中做 diffusion denoising：

```text
Aτ = (1 - τ) ε + τ A_norm
```

每个 expert branch 生成一个 trajectory prediction，最终由 learned fusion weights 加权。appendix 报告权重从均匀初始化 0.25 收敛到大约：

- dynamic evolution：0.35
- trajectory expert：0.31
- semantic interaction：0.19
- geometric structure：0.15

因此，token 类型是人工定义的，但融合权重是学习来的。

## 实验数据

### NAVSIM v1 planning

CoWorld-VLA 在 single-frame front-camera-only 设置下报告：

- NC：99.2
- DAC：96.8
- TTC：96.6
- Comfort：100
- EP：83.6
- PDMS：89.8

对比：

- ResWorld：89.0 PDMS
- DriveLaW：89.1 PDMS
- Uni-World VLA：89.4 PDMS
- CoWorld-VLA：89.8 PDMS

### Video generation

FVD 越低越好：

- SVD：227.5
- GenAD：184.0
- DrivingGPT：142.6
- Epona：61.3
- DriveLaW：55.6
- CoWorld-VLA：32.7

### Expert token 消融

- 只用 Ego Trajectory token：83.7 PDMS
- + Geometry：85.1
- + Semantic：87.7
- + Dynamic：88.7

说明四类 expert token 具有互补性。

### Progressive planner 消融

- Stage 2 VLM SFT：88.7
- + ReCogDrive action expert：89.1
- + HMEF：89.8

说明 multi-expert latent representation 已经有效，HMEF 能进一步把这些条件转化为更优轨迹。

## 用户问过的问题

### 四种 token 的权重是学习来的还是人工定义的？

四类 token 类型是人工定义的，分别对应 semantic、geometry、dynamic、trajectory。最终 planner 中的融合权重 `α = softmax(w)` 是学习来的。论文报告 dynamic 和 trajectory expert 权重最高。

### 什么叫 JEPA token？

更准确地说，CoWorld-VLA 没有“JEPA 格式 token”。`H_sem` 是 VLM 里的 semantic expert token hidden state；作者用 frozen V-JEPA 从未来观测中提取 teacher feature，再监督 `H_sem` 对齐它。训练时用未来帧，推理时只用当前帧。

## 与我的研究思路的关系

CoWorld-VLA 对“因子码本 + 门控 planner”非常有启发：

- 它证明多因子 world representation 比单一 latent 更适合规划。
- 它把不同 future knowledge 通过明确 token 接口送进 planner。
- 它的 expert 类别是人工定义的，尚未形成可检索的 factor codebook。
- 它的权重更像全局 learned fusion weights，不是强场景自适应 gate。

因此可以提出差异化方向：

```text
CoWorld-VLA manually defines four continuous expert tokens,
while our factor-codebook approach learns planning-guided factor prototypes
and performs scene-adaptive factor selection for trajectory planning.
```

## 局限与疑问

- 训练成本极高：Stage 1 用 64 张 A800 约 74 小时，Stage 2 用 32 张 A800 约 70 小时，Stage 3 用 16 张 A800 约 20 小时。
- 当前模型 limited to single-image inputs，动态理解可能受限。
- NAVSIM 是 non-reactive open-loop protocol，不能直接等价于真实闭环驾驶。
- 系统依赖 V-JEPA、VGGT、Wan、Qwen3-VL 等多个强专家模型，复现门槛高。
- expert hidden states 的可解释性还需要更多可视化和验证。

## 值得学习的点

- 把文本 CoT 替换为 Latent CoT 的写法很适合 VLA 自动驾驶。
- 多源监督让不同 expert token 分工明确，是构造 planning-relevant latent 的有效路径。
- 消融表设计清晰，逐步证明 trajectory、geometry、semantic、dynamic 四类因子的互补性。
- 对你的研究而言，下一步可以从 continuous expert tokens 走向 factor codebook 和 scene-adaptive gating。
