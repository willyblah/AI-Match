# 浏览器游戏基础架构

## 先问清楚的问题

在给实现建议前，先尽量锁定这些信息：

- 玩家幻想：玩家应该觉得自己在扮演什么、完成什么？
- 核心动作：移动、躲避、射击、解谜、收集、建造、对话、经营中的哪几个是主动作？
- 核心循环：一次短循环包含哪些输入、反馈、奖励或失败？
- 失败状态：死亡、时间耗尽、资源耗尽、被发现、任务失败等如何表现？
- 目标时长：30 秒原型、3 分钟关卡、长线进度还是可重复挑战？
- 输入方式：键鼠、触屏、手柄，是否需要移动端适配？
- 平台限制：浏览器、React 宿主、纯 TS/Vite、静态部署、资源大小限制。

## 引擎选择

默认选择要保守，先满足当前游戏形态，不为假设中的复杂需求过度设计。

| 场景 | 推荐 |
|---|---|
| 2D、Sprite、Tilemap、平台跳跃、俯视角、战棋、动作原型 | Phaser |
| 明确 3D、WebGL-first、plain TypeScript / Vite、需要直接控制渲染循环 | Three.js |
| 3D 场景嵌在 React 产品中，需要共享 React 状态和 DOM UI | React Three Fiber |
| 渲染抽象本身成为问题，需要学习或调试底层管线 | raw WebGL |
| 用户指定 Babylon.js / PlayCanvas | 做客观比较，不作为默认 |

如果用户没有明确说 3D，优先使用 Phaser 2D。这样更快形成可试玩原型，也更适合多数浏览器小游戏。

## 架构原则

### 1. 分离 simulation 和 rendering

游戏规则、生命值、分数、冷却、碰撞意图、胜负状态属于 simulation。Phaser Sprite、Three.js Mesh、相机、材质和后处理属于 rendering。

这样做的好处是：

- 玩法状态可以单元测试或直接调试
- 切场景、销毁渲染对象时不丢失核心状态
- UI 可以读取稳定状态，而不是读取渲染对象内部字段

### 2. 显式维护 input map

不要在多个 Scene、组件或事件回调里散落输入逻辑。先定义“输入 → 游戏动作”的映射，例如：

- `moveLeft` / `moveRight`
- `jump`
- `dash`
- `interact`
- `pause`

这样可以更容易支持键鼠、触屏和手柄，也能在试玩时判断主动作是否响应及时。

### 3. 把 asset loading 当作一等系统

玩法代码应引用稳定的 asset key，而不是到处写文件路径。素材清单至少需要记录：

- key
- 类型：image、spritesheet、tilemap、audio、glb、texture
- 源路径
- 帧尺寸或模型比例
- 是否需要压缩、预加载或延迟加载

### 4. 提前定义 save / debug / perf 边界

即使是原型，也要知道哪些状态需要保存、哪些 debug 信息要显示、性能目标是什么。

- Save：进度、关卡、分数、设置、已解锁内容
- Debug：FPS、碰撞框、实体数量、当前状态机、资产加载状态
- Perf：初始加载大小、目标帧率、最大实体数量、移动端是否支持

### 5. DOM HUD 是默认策略

文字密集、按钮密集或表单式 UI 默认用 DOM 覆盖层，不要强行画在 canvas 或 WebGL 里。Canvas/WebGL 负责游戏世界，DOM 负责菜单、HUD、设置、说明和结果页。

## 推荐模块边界

2D Phaser 项目可使用：

```text
src/
  game/
    simulation/
    content/
    input/
    assets/
  phaser/
    boot/
    scenes/
    view/
    adapters/
  ui/
    hud/
    menus/
    overlays/
```

3D Three.js 项目可使用：

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

## 数据流

推荐数据流：

1. 输入层收集键鼠、触屏或手柄状态。
2. input map 转换为游戏动作。
3. simulation 根据动作和时间步更新游戏状态。
4. rendering 读取状态并更新 Sprite、Mesh、相机和特效。
5. DOM UI 读取状态并显示 HUD、菜单和结果。
6. QA 记录截图、性能指标和可复现问题。

## 实现前检查

- 是否已经说明为什么选择 Phaser、Three.js 或 React Three Fiber？
- simulation 是否不依赖 Phaser Scene 或 Three.js Object3D？
- 输入是否集中映射，而不是散落在多个事件里？
- 资产是否通过 manifest key 引用？
- HUD 是否默认走 DOM 层？
- 是否安排了第一次可试玩验证？
