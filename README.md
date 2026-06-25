# Paper Notes

这个仓库用于整理自动驾驶、VLA、World Model 等方向的论文阅读笔记。

## 项目与网址

| 项目 | 在线页面 | Markdown / 文档源码 |
|---|---|---|
| 首页 / LVDrive 精读页面 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/) | [index.html](./index.html) |
| LVDrive 论文笔记 | [Jekyll post 源文档](./_posts/2026-06-07-lvdrive.md) | [论文笔记 Markdown](./papers/LVDrive/LVDrive论文笔记.md), [Word 精读笔记](./papers/LVDrive/LVDrive论文精读笔记.docx) |
| GEM 生成式监督具身智能论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/gem.html) | [论文笔记 Markdown](./papers/GEM/GEM论文笔记.md), [HTML 页面](./gem.html) |
| World4Drive 意图感知 latent world model 论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/world4drive.html) | [论文笔记 Markdown](./papers/World4Drive/World4Drive论文笔记.md), [HTML 页面](./world4drive.html) |
| AutoVLA 动作码本与自适应推理论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/autovla.html) | [论文笔记 Markdown](./papers/AutoVLA/AutoVLA论文笔记.md), [HTML 页面](./autovla.html) |
| Epona 自回归扩散 world model 方法笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/epona.html) | [论文笔记 Markdown](./papers/Epona/Epona方法精读笔记.md), [HTML 页面](./epona.html) |
| DLWM Gaussian-centric 预训练论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/dlwm.html) | [论文笔记 Markdown](./papers/DLWM/DLWM论文笔记.md), [HTML 页面](./dlwm.html) |
| LeWorldModel 端到端 JEPA 潜空间世界模型笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/leworldmodel.html) | [论文笔记 Markdown](./papers/LeWorldModel/LeWorldModel论文笔记.md), [HTML 页面](./leworldmodel.html) |
| AdaWM 自适应 world model 微调规划笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/adawm.html) | [论文笔记 Markdown](./papers/AdaWM/AdaWM论文笔记.md), [HTML 页面](./adawm.html) |
| ResWorld Temporal Residual World Model 论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/resworld.html) | [论文笔记 Markdown](./papers/ResWorld/ResWorld论文笔记.md), [HTML 页面](./resworld.html) |
| CoWorld-VLA 多专家 Latent CoT 论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/coworld-vla.html) | [论文笔记 Markdown](./papers/CoWorld-VLA/CoWorld-VLA论文笔记.md), [HTML 页面](./coworld-vla.html) |
| UniTrans 异构协同感知特征翻译论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/unitrans.html) | [论文笔记 Markdown](./papers/UniTrans/UniTrans论文笔记.md), [HTML 页面](./unitrans.html) |
| DriveVLA-W0 世界模型增强 VLA scaling 论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/drivevla-w0.html) | [论文笔记 Markdown](./papers/DriveVLA-W0/DriveVLA-W0论文笔记.md), [HTML 页面](./drivevla-w0.html) |
| LMGenDrive 理解-生成统一闭环驾驶笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/lmgendrive.html) | [论文笔记 Markdown](./papers/LMGenDrive/LMGenDrive论文笔记.md), [HTML 页面](./lmgendrive.html) |
| UNICST next-scale 4D 世界生成笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/unicst.html) | [论文笔记 Markdown](./papers/UNICST/UNICST论文笔记.md), [HTML 页面](./unicst.html) |
| MapAgent2CARLA 多智能体地图生成框架 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/mapagent2carla.html) | [框架 Markdown](./docs/mapagent2carla-framework.md), [博客 Markdown](./_posts/2026-06-09-mapagent2carla.md), [HTML 页面](./mapagent2carla.html) |

> GitHub Pages 更新可能有几十秒到几分钟延迟。如果在线页面暂时没刷新，可以先看仓库里的 HTML / Markdown 源文件。

## Current Focus

LVDrive 的核心思想是：不直接生成未来 RGB 图像，而是在 latent space 中预测未来视觉语义表示，并通过两阶段轨迹解码让这些未来语义显式参与轨迹精修。

MapAgent2CARLA 的核心思想是：从多源地图图像出发，通过多智能体协作生成 CARLA-ready 3D 地图、OpenDRIVE 路网、waypoint 与交通语义，并在 CARLA 中闭环验证和修复。

GEM 的核心思想是：用 depth map generation 作为生成式监督，让 Embodied VLM 的视觉 token 同时包含语义和几何结构，并迁移到 GEM-VLA 的机器人连续动作生成。

World4Drive 的核心思想是：让 latent world model 针对不同驾驶意图想象多个未来世界，并用 world model selector 评估和选择更合理的规划轨迹。

AutoVLA 的核心思想是：用 physical action codebook 把连续轨迹变成 VLM 可生成的 action tokens，并通过 SFT/RFT 学会快慢思考和更高效的轨迹生成。

Epona 的核心思想是：用 continuous latent autoregression 和 diffusion generation 结合长时世界建模、动作条件视频生成与实时轨迹规划，并通过 chain-of-forward 训练缓解长时漂移。

DLWM 的核心思想是：用两阶段 Gaussian-centric 自监督预训练学习 3D Gaussian 几何语义和任务导向时序 latent，并用 dual latent world models 分别提升 occupancy perception/forecasting 与 motion planning。

LeWorldModel 的核心思想是：用 next-embedding prediction 加 SIGReg 高斯分布正则，从 raw pixels 端到端稳定训练 JEPA 潜空间世界模型，并避免 representation collapse。

AdaWM 的核心思想是：在线迁移时先诊断性能下降主要来自 dynamics model mismatch 还是 policy mismatch，再选择性低秩微调 world model 或重组 policy 子模块。

ResWorld 的核心思想是：用 temporal residual 让 world model 聚焦动态对象，避免冗余静态建模，并通过 Future-Guided Trajectory Refinement 让未来 BEV 特征显式修正轨迹。

CoWorld-VLA 的核心思想是：把 VLA 的中间推理从文本 CoT 改成 semantic、geometry、dynamic、trajectory 四类 multi-expert latent CoT，并用 HMEF diffusion planner 将这些世界知识显式融合进轨迹生成。

UniTrans 的核心思想是：先学习 modality-intrinsic latent space 描述不同中间特征的模态风格，再根据 source-target 模态关系动态组合 Translator Parameter Bank，实现无需重训的 zero-shot any-to-any feature translation。

DriveVLA-W0 的核心思想是：把自动驾驶 VLA 的瓶颈定义为 supervision deficit，并用 future visual world modeling 提供密集自监督，让大规模数据真正转化为更强的动态世界表征和规划能力。

LMGenDrive 的核心思想是：把 LLM 指令理解和 generative video world model 放进同一个闭环驾驶框架，用 world query/action query 解耦未来视频生成与动作输出；但它和 DriveVLA-W0 一样，本质上主要把 world modeling 当成 dense supervision。

UNICST 的核心思想是：把多视角多帧驾驶视频放进统一连续 4D latent space，用 next-scale prediction 按尺度从粗到细生成，并通过 scale/spatial/temporal 解耦 attention 提升多视角一致性、时序连贯性和推理速度。
