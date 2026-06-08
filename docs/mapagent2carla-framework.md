# MapAgent2CARLA: 多智能体闭环生成 CARLA 可运行地图的框架设想

## 一句话总结

MapAgent2CARLA 旨在从卫星图、航拍图、平面地图、3D 俯视图等多源视觉输入出发，通过多个专责智能体协作，自动生成 CARLA 可运行的 3D 场景、OpenDRIVE 路网、waypoint、障碍物和交通语义，并利用 CARLA 仿真结果进行闭环检测与修复。

这个方向的核心不是“生成一张好看的 3D 地图”，而是生成一个 **simulator-ready map**：它既有视觉上合理的城市/道路环境，也有自动驾驶仿真所需的可驾驶语义结构。

## 背景与动机

CARLA、RoadRunner、Unreal Engine 等工具已经能支持高质量自动驾驶仿真，但地图构建仍然需要大量人工建模、语义标注和反复调试。对于自动驾驶研究而言，仅有 3D 视觉资产是不够的，仿真地图还需要：

- 连续、合法的道路拓扑；
- 正确的车道方向、路口连接和 waypoint；
- 可加载的 OpenDRIVE / XODR 文件；
- 合理的建筑、障碍物、路侧设施和交通灯；
- 能在 CARLA 中跑通的车辆、行人和交通流。

因此，一个更有研究价值的问题是：

> 能否让多智能体系统从多源地图图像中自动构建、验证并修复 CARLA-ready 的城市地图？

## 总体框架

```text
Multi-source Map Input
        ↓
Perception Agent
        ↓
Topology Agent
        ↓
Semantic Configuration Agent
        ↓
Builder Agent
        ↓
Simulation Agent
        ↓
Inspector Agent
        ↓
Repair Agent
        ↺
```

系统采用生成、仿真、检查、修复的闭环流程：

```text
Generate → Simulate → Inspect → Repair → Regenerate
```

每一轮迭代都会把地图从“视觉上可能合理”推进到“语义上可驾驶、仿真中可运行”。

## 输入层：Multi-Source Map Input

系统支持多种输入：

- 卫星图；
- 航拍图；
- 传统平面地图；
- 3D 俯视图或鸟瞰截图；
- 手绘草图或规划图；
- 可选的 OSM / GIS / CAD 辅助数据。

这些输入首先需要被对齐到一个统一坐标系，并转换成带尺度、方向和语义标签的中间表示。这个中间表示可以称为：

- Geo-aligned semantic map；
- Map intermediate representation；
- Simulator-ready map specification。

## Agent 1：Perception Agent

Perception Agent 负责理解输入图像，输出结构化语义结果。

可调用的工具包括：

- SAM / SAM2：道路、建筑、绿地、水体等区域分割；
- 遥感道路提取模型：提取道路 mask 与道路边界；
- OCR / VLM：识别地图中的文字、箭头、图例和标记；
- depth / height estimation：估计建筑高度和地形起伏；
- image registration：对齐不同来源的图像或地图。

典型输出：

```json
{
  "road_mask": "binary mask or polygon list",
  "building_mask": "building footprints",
  "sidewalk_mask": "sidewalk polygons",
  "vegetation_mask": "vegetation polygons",
  "obstacle_candidates": "static obstacle candidates",
  "uncertainty_map": "low-confidence regions"
}
```

关键要求是：Perception Agent 不只输出可视化图片，而要输出后续 agent 能消费的结构化数据。

## Agent 2：Topology Agent

Topology Agent 是框架的核心之一。它负责把道路区域转换成可驾驶拓扑。

主要任务：

- 从 road mask 中提取道路中心线；
- 生成 road graph 和 lane graph；
- 推断车道数量、车道宽度和行驶方向；
- 构建 intersection / junction graph；
- 生成 spawn points 和 waypoint graph；
- 标记不确定或拓扑断裂区域。

典型输出：

```json
{
  "roads": [
    {
      "id": "road_01",
      "centerline": [[0, 0], [20, 0], [40, 5]],
      "lanes": 2,
      "lane_width": 3.5,
      "direction": "bidirectional"
    }
  ],
  "junctions": [
    {
      "id": "junction_01",
      "connected_roads": ["road_01", "road_02", "road_03"]
    }
  ],
  "waypoints": [
    {
      "id": "wp_001",
      "road_id": "road_01",
      "lane_id": 1,
      "position": [10.0, 0.0, 0.0]
    }
  ]
}
```

这一步决定地图能不能在 CARLA 中被车辆正确导航。视觉层可以后期修饰，但拓扑错误会直接导致车辆卡死、断路、逆行或路口行为异常。

## Agent 3：Semantic Configuration Agent

Semantic Configuration Agent 把感知和拓扑结果转换成统一的地图配置文件。

这个配置文件连接图像理解、OpenDRIVE 生成、3D 建模和 CARLA 仿真。

示例：

```yaml
scene:
  name: campus_intersection_01
  scale: 1.0
  coordinate_system: local_enu

roads:
  - id: road_01
    type: urban
    lanes: 2
    lane_width: 3.5
    speed_limit: 40
    centerline: [[0, 0], [30, 0], [60, 8]]

buildings:
  - id: building_01
    footprint: [[12, 8], [28, 8], [28, 24], [12, 24]]
    floors: 5
    style: residential

traffic:
  - type: traffic_light
    location: [55, 3, 0]
    affected_lanes: ["road_01_lane_1"]

obstacles:
  - type: static_vehicle
    location: [35, -4, 0]
    orientation: 90
```

这一层是论文中很重要的中间表示。它使不同工具之间解耦：前端感知模型可以替换，后端建模工具也可以替换。

## Agent 4：Builder Agent

Builder Agent 负责把地图配置文件转换成 CARLA 可用资产。

它可以分成两条构建线：

```text
语义路网层：OpenDRIVE / XODR / waypoint graph / traffic config
视觉场景层：3D mesh / buildings / terrain / vegetation / props
```

可调用工具：

- OpenDRIVE / XODR 生成器；
- RoadRunner；
- Unreal Engine；
- Blender；
- Marble-like 3D world generation model；
- CARLA map package 工具链。

输出：

- `.xodr` / OpenDRIVE 文件；
- 3D scene assets；
- waypoint graph；
- spawn point config；
- traffic light config；
- CARLA 可加载地图包。

这里不建议把 Marble 或某一个具体 3D 工具写成唯一核心。更稳妥的表述是：Builder Agent 能调用多种外部 3D 生成或建模工具，根据配置文件生成视觉层资产。

## Agent 5：Simulation Agent

Simulation Agent 负责把生成地图放入 CARLA 中真实运行。

主要任务：

- 导入地图；
- 检查 CARLA 是否能成功加载；
- 生成车辆、行人和交通流；
- 运行 route planning；
- 检查 waypoint 连通性；
- 检查车辆是否 off-road、卡死、碰撞或无法完成路线；
- 记录仿真日志和截图。

关键指标：

- Import success rate；
- Route completion rate；
- Waypoint connectivity；
- Collision rate；
- Deadlock rate；
- Off-road rate；
- Traffic flow stability。

这一步让系统区别于普通 3D 生成：最终评价不是图片好不好看，而是地图能不能承载自动驾驶闭环仿真。

## Agent 6：Inspector Agent

Inspector Agent 负责综合判断地图质量。

输入包括：

- CARLA 截图；
- 鸟瞰图；
- OpenDRIVE 解析结果；
- 仿真日志；
- 车辆轨迹；
- 碰撞、卡死、断路等失败事件。

输出不是简单评分，而是可修复的问题报告：

```json
{
  "problem": "lane discontinuity",
  "location": [42.5, 12.0],
  "severity": "high",
  "evidence": "ego vehicle stopped before junction_02 for more than 15 seconds",
  "suggested_fix": "connect road_03 lane_1 to junction_02"
}
```

Inspector Agent 可以分成三个子维度：

- 视觉质量：建筑、道路、植被、障碍物是否合理；
- 拓扑质量：lane graph、junction、waypoint 是否合法；
- 运行质量：CARLA 中车辆是否能完成任务。

## Agent 7：Repair Agent

Repair Agent 根据 Inspector Agent 的反馈修改地图。

可修复对象：

- road graph；
- lane connection；
- junction topology；
- building placement；
- obstacle placement；
- OpenDRIVE 文件；
- traffic light config；
- waypoint graph。

修复后重新交给 Builder Agent 生成地图，并再次进入 Simulation Agent 验证。这个闭环是框架最重要的研究贡献之一。

## 与现有工作的区别

已有工作通常集中在以下几类：

- OSM / GIS 到 CARLA；
- RoadRunner 手工建图；
- 卫星图道路分割；
- 3D world generation；
- CARLA traffic scenario generation；
- 多智能体交通参与者仿真。

MapAgent2CARLA 的区别在于：

- 目标不是单纯道路分割，而是生成 CARLA-ready map；
- 不是只生成视觉 3D 场景，而是同时生成语义路网；
- 不是一次性 pipeline，而是多智能体闭环修复；
- 评价不只看 IoU 或视觉效果，而看 CARLA 中能否运行。

## 潜在论文贡献

1. 提出一个从多源地图图像到 CARLA-ready 城市地图的多智能体生成框架。
2. 设计一个连接感知、拓扑、OpenDRIVE 和 3D 场景构建的中间地图表示。
3. 引入 simulation-in-the-loop validation and repair，用 CARLA 运行结果自动发现并修复地图错误。
4. 同时生成视觉 3D 环境和可驾驶语义路网，区别于只做图像分割或只做 3D 场景生成的方法。

## 最小可行原型

第一阶段不建议直接做完整城市。可以选择 10 到 50 个小区域：

- 直路；
- T 字路口；
- 十字路口；
- 校园道路；
- 园区道路；
- 停车场入口。

最小系统目标：

```text
输入一张航拍/卫星图
        ↓
输出 road graph + scene config
        ↓
生成 OpenDRIVE
        ↓
导入 CARLA
        ↓
跑通一条或多条 route
        ↓
检测并修复失败点
```

## 实验设计

可以设置以下 baseline：

- OSM-to-CARLA；
- RoadRunner 人工建图；
- 单智能体 pipeline；
- 无修复闭环版本；
- 只用分割、不做拓扑修复版本。

评价指标：

| 维度 | 指标 |
|---|---|
| 感知质量 | road IoU, building IoU, boundary F1 |
| 拓扑质量 | graph connectivity, lane continuity, junction validity |
| CARLA 可运行性 | import success rate, route completion rate |
| 交通稳定性 | collision rate, deadlock rate, off-road rate |
| 人工成本 | manual correction time, editing steps |
| 闭环收益 | repair success rate, iterations to pass |

## 可能标题

- MapAgent2CARLA: Multi-Agent Generation and Validation of CARLA-Ready Urban Maps
- AgentMap: A Multi-Agent Framework for Simulator-Ready 3D Map Generation
- From Aerial Maps to CARLA: Multi-Agent Construction, Validation, and Repair of Drivable Urban Digital Twins

## 推荐定位

如果投多智能体或 AI 会议，重点强调：

- agent decomposition；
- agent communication；
- inspector-repair feedback loop；
- tool-using agents；
- simulation-grounded validation。

如果投自动驾驶仿真方向，重点强调：

- CARLA-ready map generation；
- OpenDRIVE validity；
- route completion；
- digital twin construction；
- reduction of manual map-building cost。

## 最终表述

这个框架可以被概括为：

> We propose a multi-agent generate-validate-repair framework that converts multi-source aerial and planar maps into CARLA-ready urban digital twins with both visual 3D assets and drivable OpenDRIVE semantics.

