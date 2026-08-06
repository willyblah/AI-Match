# 浏览器游戏素材管线

## 2D Sprite 原则

2D 动画素材优先按整条流程处理，不要零散生成孤立帧。

核心原则：

- 从一个已认可的 in-game seed frame 开始。
- 生成完整 animation strip，而不是独立散帧。
- 对整条 strip 使用共享缩放比例。
- 使用统一锚点，通常是 bottom-center。
- 导入游戏前先预览，确认节奏、轮廓和方向。

## Sprite 工作流

1. 确认 seed frame：必须是已经能在游戏里成立的一帧，包含最终视角、比例、线条密度和调色方向。
2. 扩展透明画布：围绕 seed frame 留出动作空间，避免挥手、武器、跳跃等动作被裁切。
3. 一次生成完整 strip：例如 idle、run、attack、hurt、death，每个动作独立成条。
4. 统一归一化：将 strip 切成固定宽高帧，使用同一 scale 和 anchor。
5. 必要时锁回第一帧：如果第 1 帧必须和游戏内 seed frame 完全一致，就在归一化后替换回 seed。
6. 生成预览：用 sheet 或 GIF 检查动画节奏、脚底滑动、轮廓闪烁和锚点漂移。
7. 进入引擎检查：在 Phaser 中实际播放，确认碰撞盒和视觉帧匹配。

## Sprite 规格清单

每个 Sprite 动作至少记录：

- 角色或物体名
- 动作名：idle、run、jump、attack、hit、death 等
- 帧数
- 帧宽高
- FPS 或每帧时长
- 锚点：例如 bottom-center
- 碰撞盒建议
- 是否循环
- 是否有关键帧事件：命中帧、落地帧、发射帧

## 3D 资产原则

浏览器 3D 默认使用 GLB 或 glTF 2.0。源文件可以来自 Blender 等 DCC 工具，但交付运行时前必须清理、压缩、验证和实际加载测试。

不要把“能打开模型”当作“可以上线”。浏览器里还要关心加载大小、贴图格式、材质数量、动画命名、pivot、scale、碰撞体和 LOD。

## 3D GLB / glTF 工作流

1. 在 DCC 工具清理源资产：删除隐藏垃圾、未使用材质、重复网格和错误层级。
2. 统一比例和朝向：确认单位、模型高度、pivot、地面对齐和前向方向。
3. 导出 GLB 或 glTF 2.0：静态模型、骨骼动画、材质和贴图按项目需求导出。
4. 用 glTF Transform 验证和优化：prune、dedup、weld、resize、compress、inspect。
5. 选择压缩策略：几何可用 DRACO 或 Meshopt，纹理可用 KTX2 / Basis。
6. 准备碰撞体：优先手工 proxy 或简单 primitive，不默认用高模网格碰撞。
7. 制定 LOD：远距离、低端设备或大场景需要不同复杂度模型。
8. 运行时加载测试：在 Three.js 或 R3F 中加载，检查动画、材质、比例、阴影和性能。

## 纹理与材质

- 复用材质，避免每个小物体一个独立材质。
- 控制贴图尺寸，优先 512 / 1024，只有主角或特写物体才考虑更高。
- 浏览器项目优先考虑 KTX2 / Basis 压缩。
- 避免过多透明材质和昂贵 shader。
- 命名要能表达用途：`hero_body_mat`、`crate_baseColor`、`level01_wall_normal`。

## 碰撞体和 LOD

碰撞体优先为玩法服务：

- 角色：capsule 或 box
- 子弹 / 道具：sphere 或 box
- 地形：简化 mesh 或 tile-based proxy
- 门、墙、障碍：box 或 convex hull

LOD 关注：

- 距离阈值
- 材质和贴图是否也降级
- 动画是否需要远距离简化
- 切换是否产生明显 pop

## 资产命名约定

建议命名包含：

```text
角色/物体_动作/用途_版本
hero_run_v01
hero_attack_v02
enemy_slime_idle_v01
level01_wall_glb_v03
ui_icon_key_v01
```

资产 key 应稳定，文件名可演进。玩法代码引用 key，manifest 映射到具体路径。

## 验收清单

2D：

- 帧宽高一致
- 锚点一致
- 没有裁切和漂移
- 关键动作帧清晰
- 在目标背景上轮廓可读
- Phaser 中实际播放正常

3D：

- GLB / glTF 能在运行时加载
- scale、pivot、朝向正确
- 材质和贴图没有缺失
- 文件大小符合预算
- 碰撞体与玩法匹配
- LOD 或压缩没有破坏视觉
- 低端设备或限制模式下仍可接受
