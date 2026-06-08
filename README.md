# Paper Notes

这个仓库用于整理自动驾驶、VLA、World Model 等方向的论文阅读笔记。

## Notes

- [LVDrive 论文笔记](./papers/LVDrive/LVDrive论文笔记.md)
- [LVDrive GitHub Pages 版](./_posts/2026-06-07-lvdrive.md)
- [LVDrive Word 精读笔记](./papers/LVDrive/LVDrive论文精读笔记.docx)
- [MapAgent2CARLA 博客页面](./mapagent2carla.html)
- [MapAgent2CARLA 框架 Markdown](./docs/mapagent2carla-framework.md)

## Current Focus

LVDrive 的核心思想是：不直接生成未来 RGB 图像，而是在 latent space 中预测未来视觉语义表示，并通过两阶段轨迹解码让这些未来语义显式参与轨迹精修。

MapAgent2CARLA 的核心思想是：从多源地图图像出发，通过多智能体协作生成 CARLA-ready 3D 地图、OpenDRIVE 路网、waypoint 与交通语义，并在 CARLA 中闭环验证和修复。
