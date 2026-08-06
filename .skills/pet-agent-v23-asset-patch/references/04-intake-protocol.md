# 需求收集协议（Intake Protocol）

本 Skill 被触发后，必须首先执行项目分析，然后明确宠物角色来源，最后输出制作确认单并等待用户确认。任何素材生成或项目修改必须在用户确认后进行。

## 1. 强制执行项目分析

在询问任何信息之前，优先读取并分析目标应用：

### 1.1 必须读取的文件

- `package.json`：确定框架、技术栈、依赖
- 项目入口：`src/App.tsx`、`src/main.tsx`、`src/routes.tsx` 等
- 主页面：`src/pages/`、`src/app/`、`src/views/` 下的主要页面文件
- 业务状态与类型：搜索类型定义、枚举、Hook、store
- 核心 Action：业务操作函数、事件处理函数
- 当前 UI 主题：`docs/DESIGN.md`、`tailwind.config.js`、`src/index.css` 等

### 1.2 分析输出

完成分析后，形成以下摘要：

```markdown
## 应用业务摘要

- 应用类型：<>
- 主页面：<>
- 主要业务模块：<>
- 主要业务状态：<>
- 可观察指标：<>
- 安全 Action：<>
- 推荐 Pet State：<>
- 推荐临时事件：<>
- UI 风格与宠物融合建议：<>
```

### 1.3 何时询问用户

仅在以下情况询问用户：

- 无法访问项目文件
- 业务状态机存在歧义（例妌同一个状态名在不同模块含义不同）
- 找不到任何可安全绑定的操作函数
- 用户明确要求宠物使用某个角色或风格

用户无需提供 React state、Hook、函数名等技术信息。

## 2. 必须确认角色来源

在任何图片生成之前，必须明确宠物角色来源。角色来源必须经过用户确认。

### 2.1 用户已主动提供参考图

- 确认图片内容
- 说明将基于该图片生成卡通风格 canonical reference
- 如果图片包含背景、水印或复杂场景，提示用户可能需要处理

### 2.2 用户已主动提供文字描述

- 确认文字描述
- 说明将先生成 canonical base pet 静态图
- 后续所有状态基于该 canonical base 生成

### 2.3 用户未提供任何角色信息

**必须询问**，不能直接决定：

```markdown
为了让宠物角色符合你的预期，请确认以下任一项：
1. 上传一张宠物参考图片（真实宠物、插画、吉祥物等均可）。
2. 描述你想要的角色，例如："一只卡通橘猫"、"机械小助手"、"Q 版机器人"。
3. 接受 Skill 推荐方案：<<当前推荐角色>>。

你倾向于哪一种？
```

- Skill 可以推荐角色，但不得未经确认直接开始生成。
- 如果用户选择推荐方案，仍需明确确认后再继续。

## 2.5 提取 Application Visual System（应用视觉系统）

为了让宠物像目标应用原有插画系统中本来就存在的角色，必须在项目分析阶段提取一套结构化的 **Application Visual System**，并写入制作确认单、传入图像生成 Prompt：

- 当前应用的主要色彩和饱和度
- 背景、卡片、控件色
- 现有人物/物体插画的形状语言
- 描边有无、粗细和颜色
- 是否使用阴影、渐变和材质
- 人物或角色的简化比例
- 圆角和几何特征
- 留白和构图密度
- 应禁止的视觉风格（如写实、3D、照片素材、通用贴纸）
- 宠物与现有人物/插画的关系

**参考来源区分**：

- **角色参考**（用户参考图 / 文字描述）→ 用于 identity。
- **应用画风参考**（应用截图 / 现有插画）→ 用于 visual style。
- 不复制其中的文字、UI 控件或完整场景；不将页面截图直接画入 Sprite Sheet。

## 3. 制作确认单

在生成素材或修改代码前，**必须**输出完整可读的《应用宠物制作确认单》并停止执行，等待用户明确回复。禁止在输出确认单后立即继续执行。完整模板见 `references/17-confirmation-sheet-template.md`，图片生成调用规范见 `references/16-image-generation-protocol.md`。

### 3.0 用户确认前的硬性禁令

用户只说“我想要一只橘猫”“帮我加个宠物”或上传参考图，都**不等同于**已确认制作方案。在收到明确肯定回复前，禁止：

- 调用图片生成能力；
- 生成 canonical base；
- 生成任何 Sprite Sheet；
- 修改宠物组件或业务代码；
- 使用 SVG、CSS、Emoji、图标、纯色圆点或手写代码制作临时宠物；
- 宣称“已经开始制作”或“已经完成”。

如果用户只给出零散需求，先进入下方的角色来源确认，再补齐确认单并等待确认。

### 3.1 确认单必须包含的内容

```markdown
## 应用宠物 Agent 制作确认单

### 项目分析
- 应用类型：
- 主页面：
- 主要业务状态：

### Application Visual System（V2.2 新增）
- 主色彩与饱和度：
- 背景/卡片/控件色：
- 描边（有无/粗细/颜色）：
- 阴影/渐变/材质：
- 形状语言与圆角：
- 简化比例：
- 禁止风格：
- 宠物与现有插画的关系：

### 宠物角色
- 来源：参考图 / 文字描述 / Skill 推荐
- 描述：
- 应用画风参考：截图/插画路径（用于 visual style）

### 宠物性格（V2.2 新增）
- archetype：<calm / playful / shy / proud / focused / warm>
- energy：<low / medium / high>
- warmth：<reserved / balanced / caring>
- doubleTap：<sway / hop / peek / chin-up / blink / nuzzle>
- bubbleStyle：<quiet / teasing / concise / encouraging>
- 性格一句话概括：

### 双击 Reaction 实现方式（V2.2 新增）
- 实现模式：CSS compact / CSS expressive / double-tap sprite
- 时长：
- 是否启用 CSS 几何粒子：
- 是否需要生成 sprite row：

### 推荐视觉状态
| 状态 | 生命周期 | 业务场景 | 循环 |
|------|----------|----------|------|
| idle | persistent | 默认空闲 | true |
| working | persistent | 专注中 | true |
| success | transient | 任务完成 / 学习完成 / 喝水 | false |
| remind | transient | 喝水提醒 | true |

### 自动气泡
- 学习开始：
- 学习完成：
- 任务完成：
- 喝水记录：
- 提醒出现：

### 交互
- 拖拽：是
- 点击气泡：是
- 位置记忆：是
- 双击 cooldown：900ms（忽略不排队）

### 临时事件
- task_completed：success，3s，repeatable，priority 40
- reminder：remind，5s，repeatable，priority 80

### 安全操作绑定
- idle：focusTaskInput
- success：focusTaskInput
- remind：drinkWater / dismissReminder

### 人格
- 默认：友好、简短、轻度活泼、有陪伴感，但不过度打扰用户。

---

请确认以上制作方案。只有你明确回复“确认”“开始”或“可以”后，我才会开始生成素材并接入应用。在此之前不会生成图片，也不会修改代码。
```

### 3.2 不需要确认的低风险参数

- 宠物默认尺寸（w-28 md:w-32）
- 默认位置（右下角，距边 16px）
- 默认动画帧率（idle 4fps、working 6fps、success 8fps、remind 4fps）
- 默认拖拽阈值（5px）
- 默认双击阈值（300ms）
- 默认双击 cooldown（900ms）

这些参数可以在确认单中列出，但不需要用户逐项确认。

## 4. 用户确认后的动作

只有在用户明确回复“确认”“可以”“开始”“没问题”等肯定词后，才**自动执行完整流程**：

1. **调用「图片生成与编辑（超级版）」Skill**生成 canonical base（内部生产与 QA 基准，**不再要求二次确认**）；详细调用规范见 `references/16-image-generation-protocol.md`。
2. **继续调用「图片生成与编辑（超级版）」Skill**，以 canonical base 为唯一身份参考生成各状态 Sprite Sheet
3. 运行素材标准化脚本
4. 运行 geometry QA / contact sheet / motion preview / Character Identity QA / Cross-State QA
5. 复制模板到项目
6. 编写应用专属 pet-config
7. 挂载 PetWidget
8. 运行 lint / type-check / build 与应用内预览（含 Application Visual Integration QA）

**交互边界**：

- 生成素材前必须有**一次**制作确认单确认。
- 用户确认后，Skill 自动执行完整流程，**不在 canonical base 完成后再次要求确认**。
- canonical base 是内部基准，不是新的人工阻断点。
- 只有 canonical base 明显违反用户确认的角色方向、应用画风或身份要求，且自动修复无法解决时，才暂停并请求用户意见。

如果用户回复包含修改要求，先更新确认单并再次确认。

## 5. 常见错误避免

- ❌ 不读取项目文件直接询问角色
- ❌ 未经确认直接生成默认角色
- ❌ 输出确认单后继续执行，不等待用户回复
- ❌ 将角色默认为机械小助手、机器人等与用户无关的形象
- ❌ 让用户提供 React state、Hook 等技术细节
- ❌ 未在确认单中确认宠物性格与双击模式
