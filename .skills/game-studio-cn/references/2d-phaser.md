# Phaser 2D 实现指南

## 推荐栈

- Phaser
- TypeScript
- Vite
- DOM HUD / DOM 菜单覆盖在 game canvas 上方

Phaser 路线适合大多数 2D 浏览器游戏：Sprite 动画、Tilemap、平台跳跃、俯视角动作、战棋、轻量物理和快速玩法原型。

## 推荐目录结构

```text
src/
  game/
    simulation/
      state.ts
      systems/
      entities/
    content/
      levels/
      tuning.ts
    input/
      inputMap.ts
    assets/
      manifest.ts
  phaser/
    boot/
      createGame.ts
    scenes/
      BootScene.ts
      PreloadScene.ts
      GameScene.ts
    view/
      sprites/
      cameras/
      effects/
    adapters/
      syncStateToScene.ts
  ui/
    hud/
    menus/
    overlays/
```

## Scene 分工

让 Scene 保持“薄”：

- `BootScene`：初始化 Phaser 配置、全局插件、基础缩放策略。
- `PreloadScene`：加载 manifest 中声明的素材，显示 loading 状态。
- `GameScene`：绑定输入、相机、渲染对象和 simulation tick。
- `UIScene` 可选：只在确实需要 Phaser 内 UI 时使用；文字和菜单仍默认走 DOM。

不要把玩法规则、角色成长、关卡目标、背包、任务等长生命周期状态塞进 Scene。Scene 可以销毁重建，游戏状态应该能继续存在。

## Gameplay state 与渲染对象

推荐关系：

- `game/simulation` 维护纯数据：位置、速度、生命值、状态机、分数、冷却、关卡目标。
- `phaser/view` 维护 Phaser 对象：Sprite、Container、TilemapLayer、Particle、Camera。
- `phaser/adapters` 负责把 simulation state 同步到渲染对象。

这样可以避免：

- Scene 重启后核心状态丢失
- UI 读取 Phaser 内部对象导致耦合
- Sprite 销毁后玩法逻辑断掉

## 输入映射

先定义动作，再绑定按键：

```text
left/right/up/down → move vector
space / buttonA → primary action
shift / buttonB → dash or secondary action
E / tap target → interact
Esc / menu button → pause
```

移动端需要独立考虑虚拟摇杆、触屏按钮和横竖屏布局，不要默认键盘输入等于完整输入模型。

## 相机模式

常见相机策略：

- 固定屏：适合 puzzle、arcade、单屏战斗。
- 跟随主角：适合平台跳跃、俯视角动作。
- 区域锁定：适合房间制、战斗场景、tactics。
- 轻微提前量：跟随移动方向，让玩家看到即将进入的区域。

相机移动要优先保证主动作可读，避免镜头抖动、缩放过猛或 HUD 遮挡。

## 常见 2D 类型处理

### 俯视角动作

- 优先调移动手感、攻击范围、敌人预警和受击反馈。
- 摄像机应保留玩家移动方向的可见空间。
- 敌人数量和弹幕数量需要有性能上限。

### 平台跳跃

- 先调跳跃高度、落地缓冲、土狼时间、重力和碰撞盒。
- 镜头下方不要被 HUD 遮挡，玩家需要看见落点。
- 动画可以晚于手感，但输入反馈不能晚。

### Grid tactics / 战棋

- simulation 应以格子、行动点、回合、状态效果为核心。
- 渲染层只显示路径、高亮、攻击范围和单位动画。
- DOM 面板适合放单位详情、技能描述、回合按钮。

## Sprite 与 Tilemap

- 使用稳定 asset key，不在玩法代码里硬编码路径。
- Sprite sheet 要明确帧宽高、锚点和动画名。
- Tilemap 要区分视觉层、碰撞层、触发层。
- 重要实体的碰撞盒不一定等于整张 Sprite，优先贴合玩法感受。

## DOM HUD 与菜单

DOM HUD 适合：

- 血量、分数、计时器、目标
- 暂停菜单、设置、关卡选择、结果页
- 文字说明、教程提示、对话框

布局原则：

- 中央 playfield 保持清晰。
- 下方中部尽量不放持久 UI，尤其是平台跳跃和俯视角移动游戏。
- 一个主要 HUD 区足够时，不要做多个常驻面板。

## 第一轮可试玩验收

最小原型至少验证：

- 进入页面后能很快看到可操作画面
- 主角移动或主动作响应稳定
- 有明确目标或失败条件
- 一次成功和一次失败都能被触发
- 暂停或重开路径可用
- HUD 不遮挡关键区域
- 视口变化后 canvas 和 DOM UI 仍对齐
