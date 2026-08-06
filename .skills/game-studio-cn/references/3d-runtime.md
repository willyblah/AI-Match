# 3D 浏览器运行时指南

## 先选择 3D 分支

3D 不要泛泛地写成 WebGL 指南，先判断项目宿主：

| 场景 | 推荐 |
|---|---|
| plain TypeScript / Vite、非 React、需要直接控制 render loop | Three.js |
| React 应用内嵌 3D、需要共享 React 状态、声明式组合场景 | React Three Fiber |
| 只是做 3D 模型资产、GLB、压缩、LOD | 先看 `assets.md` |
| 用户没明确要求 3D | 回到 Phaser 2D 默认路线 |

## Three.js 路线

推荐栈：

- `three`
- TypeScript
- Vite
- GLB 或 glTF 2.0 资产
- `GLTFLoader`、`DRACOLoader`、`KTX2Loader`
- Rapier JS 用于需要物理的项目
- SpectorJS 用于 GPU / frame debugging
- DOM overlays 用于 HUD、菜单和设置

推荐模块：

```text
src/
  game/
    simulation/
    content/
    input/
    save/
  render/
    app/
    loaders/
    objects/
    materials/
    lights/
    post/
    adapters/
  physics/
  diagnostics/
  ui/
```

Three.js 适合需要直接掌控 renderer、scene、camera、animation loop、资源加载和调试工具的项目。保持 render loop 清晰，不要让业务状态散落在 Mesh 的自定义字段里。

## React Three Fiber 路线

推荐栈：

- `@react-three/fiber`
- `three`
- `@react-three/drei`
- `@react-three/rapier`
- `@react-three/postprocessing`
- `@react-three/a11y`：当交互可访问性重要时使用
- DOM overlays 保持在正常 React tree 中

R3F 适合：

- 3D 只是 React 产品的一部分
- UI、设置、面板和状态已经在 React 中
- 需要声明式组合场景、组件化模型、React state 协调

避免在 R3F 中绕过 React 生命周期大量手动 new / dispose；如果需要强 imperative 控制，Three.js 路线可能更合适。

## 相机和控制

先确定相机承担什么玩法职责：

- 追随角色：动作、探索、平台类 3D
- 固定角度：棋盘、展示、轻策略
- 轨道控制：编辑器、模型查看、沙盒
- 第一人称 / 第三人称：需要更严格的碰撞、遮挡和输入处理

相机 QA 要检查：

- 目标是否被遮挡
- 深度关系是否容易读
- 快速移动时是否晕眩
- UI 是否挡住准星、目标或路径
- 视口变化后相机和 HUD 是否仍合理

## 加载器与资产边界

3D 默认使用 GLB 或 glTF 2.0。加载层应集中处理：

- DRACO / Meshopt 几何压缩
- KTX2 / Basis 纹理压缩
- 加载进度和错误状态
- 模型命名、动画 clip、材质复用
- 运行时缓存和销毁

不要让各个 gameplay 组件直接散落加载文件路径。用 asset key 或集中 manifest 管理。

## 物理边界

需要物理时，先区分：

- 玩法碰撞：命中、触发、移动阻挡
- 展示物理：掉落、碎片、摆动
- 角色控制器：坡面、台阶、地面检测、跳跃

大多数游戏不需要把所有模型网格都变成精确碰撞体。优先使用 box、capsule、sphere、convex hull 或手工 collision proxy。

## 低 chrome 3D UI

3D UI 默认低遮挡：

- 中央 playfield 保持清晰。
- 使用一个小目标 chip 和一个小状态区。
- 长文本、设置、背包、任务详情放 DOM 面板。
- 战斗中只显示短暂提示，不常驻大面积覆盖层。
- 重要 3D 目标附近的标签要有距离、遮挡和重叠处理。

## WebGL 调试与性能

调试顺序：

1. 先捕获问题，再猜原因。
2. 逐步减少场景，找到性能断崖。
3. 先关闭后处理，再重写核心渲染。
4. 检查资产管线，再怀疑 renderer。
5. 把 context loss 当浏览器要求处理，不当作极端边缘情况。

常见检查项：

- draw calls、triangles、纹理大小、材质数量
- 阴影数量、实时光数量、后处理链
- GLB 是否过大，是否缺少压缩
- 动画 mixer 和物理 step 是否过多
- 是否在每帧创建对象导致 GC 抖动

## 3D 可试玩验收

- 首屏加载有进度或反馈，不是空白等待。
- 相机能稳定展示主目标。
- 主要输入响应清晰。
- 3D 与 DOM HUD 不互相遮挡。
- 资源加载失败有可读错误。
- WebGL context loss 或低性能设备有降级策略。
