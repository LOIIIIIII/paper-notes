# Paper Notes

这个仓库用于整理自动驾驶、VLA、World Model 等方向的论文阅读笔记。

## 项目与网址

| 项目 | 在线页面 | Markdown / 文档源码 |
|---|---|---|
| 首页 / LVDrive 精读页面 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/) | [index.html](./index.html) |
| LVDrive 论文笔记 | [Jekyll post 源文档](./_posts/2026-06-07-lvdrive.md) | [论文笔记 Markdown](./papers/LVDrive/LVDrive论文笔记.md), [Word 精读笔记](./papers/LVDrive/LVDrive论文精读笔记.docx) |
| GEM 生成式监督具身智能论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/gem.html) | [论文笔记 Markdown](./papers/GEM/GEM论文笔记.md), [HTML 页面](./gem.html) |
| World4Drive 意图感知 latent world model 论文笔记 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/world4drive.html) | [论文笔记 Markdown](./papers/World4Drive/World4Drive论文笔记.md), [HTML 页面](./world4drive.html) |
| MapAgent2CARLA 多智能体地图生成框架 | [GitHub Pages](https://loiiiiiii.github.io/paper-notes/mapagent2carla.html) | [框架 Markdown](./docs/mapagent2carla-framework.md), [博客 Markdown](./_posts/2026-06-09-mapagent2carla.md), [HTML 页面](./mapagent2carla.html) |

> GitHub Pages 更新可能有几十秒到几分钟延迟。如果在线页面暂时没刷新，可以先看仓库里的 HTML / Markdown 源文件。

## Current Focus

LVDrive 的核心思想是：不直接生成未来 RGB 图像，而是在 latent space 中预测未来视觉语义表示，并通过两阶段轨迹解码让这些未来语义显式参与轨迹精修。

MapAgent2CARLA 的核心思想是：从多源地图图像出发，通过多智能体协作生成 CARLA-ready 3D 地图、OpenDRIVE 路网、waypoint 与交通语义，并在 CARLA 中闭环验证和修复。

GEM 的核心思想是：用 depth map generation 作为生成式监督，让 Embodied VLM 的视觉 token 同时包含语义和几何结构，并迁移到 GEM-VLA 的机器人连续动作生成。

World4Drive 的核心思想是：让 latent world model 针对不同驾驶意图想象多个未来世界，并用 world model selector 评估和选择更合理的规划轨迹。
