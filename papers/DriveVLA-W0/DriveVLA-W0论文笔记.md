# DriveVLA-W0 论文笔记

论文：**DriveVLA-W0: World Models Amplify Data Scaling Law in Autonomous Driving**

状态：ICLR 2026 conference paper；本笔记基于本地 PDF、论文方法/实验原文摘录，以及本轮阅读问答整理。

## 一句话总结

DriveVLA-W0 的核心观点是：自动驾驶 VLA 若只用稀疏 action/trajectory labels 训练，会遇到 supervision deficit；加入 future visual world modeling 作为密集自监督目标，才能让大模型真正从大规模数据中学到可迁移的动态世界表征。

## 论文要解决的问题

传统端到端自动驾驶方法大致有两类：

- BEV/专用结构模型：有强几何先验，工程上实用，但难以直接复用通用 VLM/VLA 的大规模预训练能力。
- VLA 大模型：可以接入语言、视觉和动作序列，但训练时通常只监督几个未来 waypoint 或 action tokens。

问题在于，输入是高维图像、语言和历史动作，监督却只有低维轨迹。论文称之为 **supervision deficit**。大模型容量很大，但 action-only supervision 太稀疏，容易让模型只学数据集动作分布，而不是学习场景动态、交通交互和 ego action 后果。

## 核心贡献

1. **World modeling 作为 dense self-supervision**
   - Prior limitation：action-only VLA 监督稀疏，scale 数据时容易饱和。
   - Proposed change：训练时加入视觉未来/当前场景预测任务。
   - Intended mechanism：每帧图像或 latent 提供大量 token/feature-level supervision，迫使 backbone 学到 predictive dynamics。
   - Evidence：Table 3 中 70M frames 下，VQ 版本 ADE 改善 28.8%，ViT 版本 collision rate 改善 15.9%。

2. **同时适配 VQ-style 和 ViT-style VLA**
   - VLA-VQ 使用 Emu3 8B，把图像离散化成 visual tokens，因此用 AR World Model 做 next-token prediction。
   - VLA-ViT 使用 Qwen2.5-VL 7B，把图像编码成连续 visual features，因此用 Diffusion World Model 做 latent denoising。

3. **Action Expert / MoE 解决实时推理**
   - 大 VLA Expert 负责多模态理解，小 Action Expert 负责高效动作输出。
   - 通过 Joint Attention 拼接两边 Q/K/V，让小 expert 读取大 VLA 的 rich context。
   - latency 从 117.8ms 降到 74.3ms，同时 PDMS 从 85.6 提到 88.4。

4. **发现 action decoder 的 scaling 反转**
   - 小数据 NAVSIM 上 query-based 最好。
   - 大数据 70M frames 上 autoregressive action expert 最好，collision rate 相比 query-based 改善 34.9%。

## Method 细读

### 3.1 VLA Baseline

输入包括：

```text
L_t: language instruction，例如 "go straight", "turn left"
V_t: front-view image
A_{t-1}: past action / previous trajectory
```

历史 H 步被拼成 interleaved sequence：

```text
S_t = [L_{t-H}, V_{t-H}, A_{t-H-1}, ..., L_t, V_t, A_{t-1}]
```

两种 backbone：

| 版本 | Backbone | 视觉表示 | 对应 world model |
|---|---|---|---|
| VLA-VQ | Emu3 8B | VQGAN/VQ tokenizer 离散 visual tokens | AR World Model |
| VLA-ViT | Qwen2.5-VL 7B | ViT 连续 visual embeddings | Diffusion World Model |

动作使用 FAST tokenizer 转成 action tokens，action loss 是标准 autoregressive cross entropy：

```text
L_Action = - sum_i log P(a_i | S_t, a_<i)
```

### 3.2 AR World Model

AR World Model 适用于 VLA-VQ。因为图像已经被 VQGAN/VQ tokenizer 变成离散 visual tokens：

```text
Image -> VQGAN Encoder -> codebook lookup -> [v_1, ..., v_N]
```

所以可以像语言模型一样训练视觉 next-token prediction：

```text
L_WM-AR = - sum_i log P(v_i | S_<Vt, v_<i)
```

总目标：

```text
L_Total = L_Action + alpha * L_WM-AR
```

推理驾驶时通常绕过 visual token generation；该分支主要用于训练阶段塑造 backbone 表征，可视化时才经 MoVQGAN decoder 生成图像。

### 3.2 Diffusion World Model

Diffusion World Model 适用于 VLA-ViT。ViT 输出的是连续 embedding，没有离散 visual vocabulary，因此不能直接做 visual token cross entropy。

训练流程：

```text
Image_{t+1}
  -> VAE Encoder
  -> future latent z_{t+1}
  -> add Gaussian noise
  -> noised latent z_{t+1,k}
  -> Denoiser predicts noise
```

Denoiser 的条件来自当前时刻 VLA 特征：

```text
Condition = [F_t^V, F_t^A]
```

目标是 diffusion 常见的 noise prediction MSE：

```text
L_WM-Diff = E || epsilon - epsilon_hat(z_{t+1,k}, k, F_t^V, F_t^A) ||^2
```

这里容易误解的一点是：干净 latent 是 `t+1` 的未来图像，不是当前 `t` 图像；`t` 时刻特征只作为 condition。训练样本里当然包含 `V_{t+1}`，否则无法监督 future generation，但预测 `I_{t+1}` 时 condition 不能偷看 `V_{t+1}`。如果 causal mask 或特征取法让 `F_t^V, F_t^A` attend 到 `V_{t+1}`，那就是信息泄漏。

为什么预测未来而不是重建当前？因为 ViT backbone 已经看到当前图像，如果做 current reconstruction，容易退化成 copying/reconstruction。预测 `I_{t+1}` 才会迫使模型学习：

```text
current scene + ego/action context -> next visual state
```

总目标：

```text
L_Total = L_Action + beta * L_WM-Diff
```

推理驾驶时 diffusion 也被绕过，只保留训练得到的表征和 action expert。

### 3.3 Action Expert / MoE

大 VLA backbone 表征强但推理慢。DriveVLA-W0 引入 500M Action Expert，与 8B VLA Expert 组成 MoE。

Joint Attention 的核心是把两边 Q/K/V 沿 token 维拼起来：

```text
Q = [Q_VLA; Q_AE]
K = [K_VLA; K_AE]
V = [V_VLA; V_AE]
```

attention 后再拆回各自 expert。这样小 Action Expert 能直接读取大 VLA 的多模态上下文，同时比让大 VLA 全量生成动作更快。

三种 action expert：

| 方法 | 动作表示 | 优点 | 风险 |
|---|---|---|---|
| Query-based | 连续 waypoint，一次性 MLP 回归 | 快、稳定、小数据精度好 | 多峰动作分布下可能平均化 |
| Autoregressive | 离散 action tokens，逐 token 生成 | teacher forcing 清晰，大数据下 scale 好 | tokenization 有量化误差，生成较慢 |
| Flow Matching | 从噪声动作经 vector field 流到真实动作 | 连续、多模态表达力强 | 学复杂条件流场，sample efficiency 可能不如 AR |

我们讨论过的 Flow Matching sample efficiency：它要学习整个连续动作空间里的条件向量场，而 AR 每个 token 都有明确 teacher-forced 分类监督。在同等训练预算下，复杂大规模驾驶分布上 AR 更容易稳定收敛。

## 实验数据与结论

### NAVSIM v1/v2

NAVSIM v1 指标包括 NC、DAC、TTC、Comfort、EP，并用 PDMS 综合评估。NAVSIM v2 增加 DDC、TLC、LK、HC、EC 等指标，用 EPDMS 综合评估。

Table 1 中 DriveVLA-W0 在 NAVSIM v1 最高达到：

```text
NC = 99.3
DAC = 97.4
TTC = 97.0
Comfort = 99.9
EP = 88.3
PDMS = 93.0
```

Table 2 中 DriveVLA-W0 在 NAVSIM v2：

```text
EPDMS = 86.1
```

超过 DiffusionDrive 84.5、ARTEMIS 83.1、DriveSuprem 83.1 等。不过 EC = 58.9 较低，说明它不是所有细分指标都强。

### Scaling Law：Table 3

私有 in-house dataset 用 70k、700k、70M frames 三个规模评估。

70M frames 下：

| 模型 | ADE ↓ | Collision ↓ | 结论 |
|---|---:|---:|---|
| VLA (VQ) baseline | 1.4829 | 0.0488 | action-only 已接近饱和 |
| VLA (VQ) + WM | 1.0563 | 0.0392 | ADE 改善 28.8%，Collision 改善 19.7% |
| VLA (ViT) baseline | 1.1051 | 0.0359 | ViT baseline 已较强 |
| VLA (ViT) + WM | 1.0640 | 0.0302 | ADE 改善 3.7%，Collision 改善 15.9% |

需要注意：小数据/中等数据下 world model 并非每项都赢。论文真正支持的命题是“大数据规模下 dense world modeling 更能释放 scaling 收益”，不是“任何规模都无条件提升”。

### Action Expert：Table 4

小数据 NAVSIM：

```text
Query-based PDMS = 88.4
Flow Matching PDMS = 87.2
Autoregressive PDMS = 85.3
```

大数据 70M frames：

```text
Query-based Collision = 0.0453
Flow Matching Collision = 0.0398
Autoregressive Collision = 0.0295
```

结论：小数据看连续回归精度，大数据看复杂动作分布建模能力。

### Ablation

Vision-only vs Vision-Action：

```text
No pretrain -> 2VA: PDMS 80.7
6V -> 2VA:        PDMS 84.1
6VA -> 2VA:       PDMS 85.6
```

说明只有视觉序列监督有帮助，但加入 action-conditioned sequence 更好。

Sequence length：

```text
VA:  PDMS 83.3
2VA: PDMS 84.2
6VA: PDMS 85.6
```

说明较长历史上下文对动态建模和规划更有帮助。

## 用户已问过的问题与当前理解

- **为什么未来视觉比当前视觉更有利于规划？**  
  因为规划关心“如果我这样开，未来会发生什么”，未来预测逼模型学习动态、交互、风险提前量和 action-conditioned outcomes。

- **如何证明不是普通正则化？**  
  需要 action-only、current reconstruction、future prediction、action-conditioned future prediction 四组对照；再配合 counterfactual rollout、dynamic probing、破坏性实验。

- **VLA-VQ 和 VLA-ViT 的区别？**  
  VLA-VQ 把图像离散成 visual tokens，可直接做 AR next-token prediction；VLA-ViT 把图像编码成连续 features，更适合 latent diffusion denoising。

- **Diffusion target 是不是 t+1？这样可以吗？**  
  是的。conditional diffusion 的 target 是未来 `z_{t+1}`，condition 是当前 `F_t^V, F_t^A`。这就是学习 `p(z_{t+1} | F_t^V, F_t^A)`。

- **图中输入包含 `V_{t+1}`，会不会偷看？**  
  完整训练序列包含 `V_{t+1}`，但它应作为 supervision target，而不是 condition。正确实现必须依赖 causal mask 或特征选择避免 `F_t` 看见未来。

- **Flow Matching sample efficiency 不够是什么意思？**  
  它要学习复杂连续动作分布上的条件 vector field，相比 AR 的 token-level teacher forcing，监督更间接、收敛更依赖训练预算。

## 仍然存疑 / 值得核查

- 70M frames scaling 证据来自 in-house dataset，外部复现难。
- NAVSIM 属于 benchmark/simulation-style evaluation，不等于真实车 closed-loop 安全验证。
- Diffusion world model 是否真正学到强 counterfactual dynamics，还需要更量化的 action-conditioned rollout 实验。
- Table 3 中小数据下 world model 有时不稳定，说明 auxiliary loss 权重、数据规模和训练阶段可能敏感。
- NAVSIM v2 的 EC 指标较低，舒适性方面可能仍有问题。

## 值得学习的写法与实验设计

- 用 supervision deficit 解释 VLA scale 不起来的问题，比单纯说“加 world model 提升性能”更有机制感。
- 同时覆盖 VQ 和 ViT 两类 VLA，证明方法不是绑定某个 backbone。
- Table 3 的 scaling ablation 是全篇最强证据，直接支撑标题里的 “World Models Amplify Data Scaling Law”。
- Table 4 的 action decoder reversal 很有论文价值：不仅提出方法，还观察到 scale regime 改变最优 decoder。

## 复读建议

优先精读：

1. Figure 2：两种 world model 的整体数据流。
2. Section 3.2：AR WM 和 Diffusion WM 的 loss、target、inference bypass。
3. Figure 3 / Section 3.3：MoE Action Expert 和三种 decoder。
4. Table 3：world model 与 data scaling。
5. Table 4：action expert performance reversal。
6. Table 5/6：vision-action sequence 与 sequence length 的消融。
