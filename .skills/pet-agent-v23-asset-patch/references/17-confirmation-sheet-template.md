# 应用宠物制作确认单模板

本确认单必须在生成任何素材、修改任何代码前输出，并等待用户明确回复后才能继续。确认单应完整、可读、无歧义。

## 确认单结构

```markdown
## 应用宠物 Agent 制作确认单

### 项目分析
- 应用类型：<>
- 主页面：<>
- 主要业务模块：<>
- 主要业务状态：<>
- 可观察指标：<>
- 安全 Action：<>
- 推荐 Pet State：<>
- 推荐临时事件：<>

### Application Visual System（应用画风）
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
- 角色描述：
- 应用画风参考：截图/插画路径
- 标志性轮廓（耳朵/帽子/发型/尾巴/服装等）：

### 宠物性格
- archetype：<calm / playful / shy / proud / focused / warm>
- energy：<low / medium / high>
- warmth：<reserved / balanced / caring>
- doubleTap：<sway / hop / peek / chin-up / blink / nuzzle>
- bubbleStyle：<quiet / teasing / concise / encouraging>
- 性格一句话概括：

### 双击 Reaction 实现方式
- 实现模式：<CSS compact / CSS expressive / double-tap sprite>
- 时长：
- 是否启用 CSS 几何粒子：
- 是否需要生成 sprite row：
- 用户是否已明确同意 expressive / sprite：

### 推荐视觉状态
| 状态 | 生命周期 | 业务场景 | 循环 | 说明 |
|------|----------|----------|------|------|
| idle | persistent | 默认空闲 | true | |
| working | persistent | 专注/进行中 | true | |
| success | transient | 任务完成 | false | 单次庆祝 |
| remind | transient | 提醒/鼓励 | true | 短暂提示 |

### 自动气泡策略
- 学习/工作开始：
- 学习/工作完成：
- 任务完成：
- 提醒出现：
- 其他：

### 交互能力
- 拖拽：是
- 单击气泡：是
- 双击 reaction：是（cooldown 900ms）
- 位置记忆：是
- 主动气泡：低频（受 Interruption Policy 约束）

### 临时事件
| 事件 | 对应状态 | 持续时间 | 可重复 | 优先级 |
|------|----------|----------|--------|--------|
| task_completed | success | 3s | 是 | 40 |
| reminder | remind | 5s | 是 | 80 |

### 安全操作绑定
| 宠物状态 | 可触发操作 | 说明 |
|----------|------------|------|
| idle | focusTaskInput | 聚焦输入 |
| success | focusTaskInput | 回到任务 |
| remind | drinkWater / dismissReminder | 完成提醒 |

### 人格与话术基调
- 默认：友好、简短、轻度活泼、有陪伴感，但不过度打扰用户。

---

请确认以上制作方案。只有你明确回复“确认”“开始”或“可以”后，我才会开始生成素材并接入应用。在此之前不会生成图片，也不会修改代码。
```

## 确认规则

- 用户说“我想要一只橘猫”“帮我加个宠物”或上传参考图，**不等于**已经确认方案。
- 必须收到用户明确回复（“确认”“开始”“可以”“没问题”）后，才能继续。
- 如果用户回复包含修改要求，先更新确认单并再次确认，直到用户明确肯定。
- 确认单中高风险项必须确认，低风险参数可列出但不需要逐项确认。

## 用户确认前的禁令

在收到明确确认前，绝对禁止：

- 调用图片生成能力；
- 生成 canonical base；
- 生成任何 Sprite Sheet；
- 修改宠物组件或业务代码；
- 使用 SVG、CSS、Emoji、图标、纯色圆点或手写代码制作临时宠物；
- 宣称已经开始制作或已经完成。

## 用户确认后的流程

1. 调用秒哒平台提供的「图片生成与编辑（超级版）」Skill。
2. 使用该 Skill 生成 canonical base。
3. 继续使用官方脚本，以 canonical base 为唯一身份参考生成各状态 Sprite Sheet。
4. 处理透明背景与统一几何。
5. 执行全部 QA。
6. 通过 QA 后接入代码。

## 相关文档

- `references/04-intake-protocol.md`：需求收集与确认流程。
- `references/16-image-generation-protocol.md`：官方图片生成调用规范。
- `references/08-fallback-rules.md`：失败与降级规则。
