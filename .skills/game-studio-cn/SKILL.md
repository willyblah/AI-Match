---
name: game-studio-cn
description: 浏览器游戏开发工作流助手。当用户提到设计游戏、做原型、实现玩法、搭建 Phaser、Three.js、React Three Fiber、Sprite 管线、glTF 资产、HUD、菜单、试玩、浏览器游戏 QA、2D、3D 等时触发。先判断合适的浏览器游戏技术栈，再给出实现、素材和验收路径。
license: MIT
packageType: instruction-skill
instructionOnly: true
---

# Game Studio 中文版

## 概览

这是一个面向浏览器游戏的工作流 Skill，用来帮助用户从想法、原型、玩法实现、素材管线、HUD/菜单到试玩 QA 形成一条可落地路径。

默认采用 2D-first 策略：除非用户明确要求 3D、WebGL、Three.js 或 React Three Fiber，否则优先建议 Phaser + TypeScript + Vite。3D 需求明确后，再在 plain Three.js 和 React Three Fiber 之间做选择。

## 何时使用

当用户提出以下任意需求时使用本 Skill：

- 设计或拆解一个浏览器游戏玩法、核心循环、关卡节奏
- 做 Phaser 2D、Sprite、Tilemap、平台跳跃、战棋、俯视角动作游戏
- 做 Three.js、React Three Fiber、WebGL、3D 场景、相机、物理或 GLB 加载
- 规划 2D Sprite 或 3D glTF / GLB 资产管线
- 设计 HUD、菜单、覆盖层、暂停页、失败页、低遮挡 3D UI
- 做浏览器试玩、截图检查、可读性检查、性能和 WebGL QA

## 不要停留在这里的情况

- 用户明确要原生 Unity、Unreal、Godot 或主机游戏工作流时，说明本 Skill 只覆盖浏览器游戏。
- 用户只要求生成图片、精修素材或产出单张美术图时，应转向图像/素材生成流程，而不是完整游戏架构。
- 用户只要求 Web 页面无障碍、表单、暗色模式或通用 UX 审查时，应优先使用 Web UI 质量审查流程。
- 用户明确指定 Babylon.js 或 PlayCanvas 时，可以做客观比较，但不要把它们变成默认路径。

## 路由规则

先判断用户的问题属于哪一类，再读取对应参考资料：

| 用户意图 | 默认路线 | 参考资料 |
|---|---|---|
| 没指定 3D 的游戏原型、2D、Sprite、Tilemap、平台跳跃、战棋 | Phaser 2D | `references/2d-phaser.md` |
| 明确 3D、WebGL、Three.js、plain TS/Vite | Three.js | `references/3d-runtime.md` |
| React 应用里嵌入 3D、共享 React 状态、声明式场景 | React Three Fiber | `references/3d-runtime.md` |
| 只问架构、引擎选择、输入/状态/保存边界 | Foundations | `references/foundations.md` |
| 2D Sprite、动画条、GLB、glTF、压缩、碰撞体、LOD | Assets | `references/assets.md` |
| HUD、菜单、覆盖层、试玩、截图、可读性、QA | UI / Playtest | `references/ui-playtest.md` |

## 默认工作流

1. 先锁定游戏方向：玩家幻想、核心动作、主要失败状态、目标时长、输入方式、平台限制。
2. 再选技术路线：默认 Phaser 2D；明确 3D 时选择 Three.js 或 React Three Fiber。
3. 定义边界：simulation/rendering 分离、input map、asset manifest、save/debug/perf 边界。
4. 拆玩法实现：核心循环、实体状态、碰撞/交互、关卡或内容配置、胜负条件。
5. 同步规划素材：Sprite 尺寸、锚点、动画帧；3D 模型比例、命名、压缩、碰撞体。
6. 设计 UI：DOM HUD 优先，保护 playfield，避免把文字密集 UI 强塞进 canvas/WebGL。
7. 最后安排试玩 QA：启动、主动作、失败恢复、截图、视口变化、性能和 WebGL 检查。

## 2D 路线

2D 默认使用 Phaser + TypeScript + Vite。建议保持 gameplay state 独立于 Phaser Scene，让 Scene 只负责生命周期、资源绑定、相机和渲染对象。HUD、菜单、暂停页和文字密集交互默认使用 DOM 覆盖层。

处理 2D 请求时优先说明：

- 游戏状态放在哪里，Scene 只做什么
- 输入如何映射到游戏动作
- Sprite、Tilemap、相机和碰撞如何组织
- HUD 如何与 canvas 分层
- 第一轮可试玩原型应该覆盖哪些主动作

详细规则见 `references/2d-phaser.md`。

## 3D 路线

明确 3D 后先分支：

- plain TypeScript / Vite / 非 React：用 Three.js，保留直接 render loop 和 imperative scene control。
- React 应用内的 3D：用 React Three Fiber，让 3D 场景和 React 状态、DOM UI 协作。

3D 默认资产格式是 GLB 或 glTF 2.0。加载、相机、物理、后处理和 HUD 都需要先定边界，避免过早堆效果。3D UI 默认低 chrome：中心 playfield 保持清晰，目标、状态、提示尽量小而短暂。

详细规则见 `references/3d-runtime.md`。

## 素材管线

2D Sprite 要从已认可的 in-game seed frame 开始，生成完整动画条，再统一归一化为固定尺寸帧，使用共享缩放和统一锚点，最后预览确认。

3D 资产要从 DCC 工具清理源文件，导出 GLB / glTF 2.0，经过 glTF Transform 做验证、裁剪、去重、压缩和贴图处理，再检查 pivot、scale、collision proxy、LOD 与运行时加载。

详细规则见 `references/assets.md`。

## UI 与试玩

文字密集 UI 默认放在 DOM 层。正常游玩时保持中央和下方中部 playfield 清晰，只保留一个主要持久 HUD 区和少量次要状态信息。试玩必须验证主动作是否明显、反馈是否及时、暂停/失败/恢复是否可用，以及不同视口下 HUD 是否挡住玩法。

详细规则见 `references/ui-playtest.md`。

## 输出预期

根据用户需求输出下列一种或多种结果：

- 技术栈选择与理由
- 可实现的目录结构和模块边界
- 核心玩法循环、状态机、输入映射或场景拆分
- 素材规格、命名、锚点、压缩和验收清单
- HUD / 菜单 / 覆盖层布局建议
- 试玩 QA 清单、复现步骤、问题优先级

## 常见坑

- 不要在用户没要求 3D 时主动把项目升级成 3D。
- 不要把所有状态都塞进 Phaser Scene 或 Three.js 对象里。
- 不要让 UI 遮挡核心游玩区域，尤其是中心和下方中部。
- 不要把 Sprite 单帧分散生成；优先完整动画条再统一归一化。
- 不要把 GLB 当作无需验证的最终资产；比例、pivot、贴图和碰撞体都要检查。
- 不要把 playtest 放到最后才想起来；每个可试玩增量都应有 QA 清单。

## 参考资料

- `references/foundations.md`：引擎选择、架构边界、输入、保存、调试和性能边界
- `references/2d-phaser.md`：Phaser 2D 项目结构、Scene 设计、相机、Sprite、DOM HUD
- `references/3d-runtime.md`：Three.js / React Three Fiber 选择、3D 架构、加载器、物理、性能
- `references/assets.md`：2D Sprite 与 3D GLB / glTF 资产管线
- `references/ui-playtest.md`：HUD、菜单、playfield 保护、试玩和浏览器 QA
