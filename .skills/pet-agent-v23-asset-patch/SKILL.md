---
name: pet-agent-v23-asset-patch
description: 为秒哒 Web/H5 应用生成和接入能够感知业务状态、支持拖拽、性格化互动与透明 Sprite 素材规范的陪伴式应用宠物。适用于添加应用宠物、桌宠、宠物 Agent、状态反馈角色，或修复和升级应用宠物素材流程。
license: MIT
---

# 应用宠物 Agent Skill V2.3

## 1. 设计目标与产品定位

**产品定位**：为秒哒 Web/H5 应用生成和接入一只符合该应用形象、能够感知业务状态并与用户进行轻量互动的**陪伴式应用宠物**。

它**不是**：系统级桌面宠物、独立桌宠应用、通用游戏角色系统、Codex 完整九状态宠物包，或单纯贴在页面上的装饰图标。

关键边界：

- 宠物**嵌入目标秒哒应用内部**，不跨出应用窗口。
- 不默认拥有与目标应用无关的移动、行走、审阅等状态；视觉状态由目标应用的**实际业务语义**决定。
- 默认推荐 `idle / working / success / remind` 四种状态，可按业务调整。
- “桌宠 / 桌面宠物”可作为用户自然语言触发词，但生成的始终是**应用内陪伴宠物**。

让任何秒哒 Web/H5 应用都能快速拥有一只低侵入、可拖拽、会主动反馈状态、支持通用轻交互、并复用已有业务操作的宠物 Agent。

V2.2 在 V2.1 基础上新增**性格化双击 reaction 体系**：双击不再是所有宠物共用的固定轻动画，而是根据宠物性格（archetype / energy / warmth）选择合适的表现方式，并将性格配置纳入制作确认单。

## 2. 核心原则

- **项目分析优先**：先读取目标应用代码，自动推断应用类型、业务状态、状态流转、关键指标和安全操作函数。
- **阻断条件明确**：只有三项真正阻断：① 无法访问目标应用上下文；② 宠物角色来源未经确认；③ 用户未确认制作方案。
- **角色来源唯一**：用户必须提供参考图或明确的文字角色描述。Skill 可以推荐，但不得未经确认直接替用户决定角色并开始生成。
- **制作方案确认单强制确认**：在生成任何素材或修改项目前，必须输出完整可读的《应用宠物制作确认单》并等待用户确认。用户确认后自动执行完整流程，**不在 canonical base 之后再次要求确认**。用户只说“我想要一只橘猫”“帮我加个宠物”或上传参考图，**不等同于已确认**；必须收到“确认”“开始”“可以”等肯定词后才能继续。
- **性格配置纳入确认单**：确认单必须包含 archetype / energy / warmth / doubleTap 方向，由用户确认或覆盖 Skill 推荐。
- **确认后必须调用官方图片生成 Skill**：正式宠物角色、canonical base 以及所有 Sprite Sheet 必须通过秒哒平台提供的「图片生成与编辑（超级版）」Skill 生成。禁止自己手写 SVG、CSS、Emoji、图标、纯色圆点、临时占位角色或任何非官方图片生成能力替代；禁止因图片生成失败或 Sprite 处理失败就改成“简单矢量角色”并宣称完成；禁止跳过 canonical base 直接分别生成互不一致的状态；禁止先写接入组件再用占位资产完成接入。
- **状态灵活**：默认推荐 idle / working / success / remind 四种视觉状态，允许根据应用调整。
- **业务与视觉分离**：多个业务状态可共享同一个宠物动画，使用不同气泡话术。
- **Base State 始终存在**：宠物始终有一个由当前业务状态推导出的 Base State。Transient State 只是临时覆盖在其之上。
- **Transient State 有生命周期**：success、remind、failed 等短暂反馈必须配置 duration、repeatable、cooldown，结束后自动恢复为当前最新 Base State。
- **Event Identity 去重**：所有 transient event 按 event identity 去重——同一 identity 只触发一次。
- **事件优先级**：多个临时事件同时触发时，高优先级覆盖低优先级，事件结束后恢复当前最新 Base State。
- **只调用安全操作**：宠物按钮只能绑定目标应用已存在的安全函数，不复制主业务逻辑。
- **双击不改变业务状态**：reaction 仅为纯视觉反馈，不触发任何业务操作，不改变保存位置。
- **失败不破坏应用**：宠物组件用 Error Boundary 隔离，资源失败时隐藏宠物、不阻塞主应用；**不用占位角色替代正式宠物**。
- **Sprite 几何必须一致**：所有状态统一单帧尺寸、共享 scale、bottom-center anchor，跨状态无明显跳动。
- **继承目标应用画风**：宠物应像目标应用原有插画系统中本来就存在的角色，使用同一套视觉语言绘制，而非通用卡通素材或贴纸。

## 3. 工作流

### Step 1: 强制执行项目分析

读取并分析（优先顺序）：

1. `package.json`：框架、技术栈、依赖
2. 项目入口：`src/App.tsx`、`src/main.tsx`、`src/routes.tsx` 等
3. 主页面：`src/pages/`、`src/app/`、`src/views/` 下的主页面文件
4. 业务状态与类型：类型定义、枚举、Hook、store
5. 核心 Action：业务操作函数
6. 当前 UI 主题：`docs/DESIGN.md`、tailwind 配置、全局样式

只有无法可靠判断时才询问用户。

### Step 2: 信息推断与确认

自动形成应用类型、业务状态、状态映射、安全操作函数列表，并向用户确认：宠物角色来源、存在歧义的状态机、操作授权问题、用户偏好（状态数量、**宠物性格**）。

### Step 3: 输出制作确认单并等待确认

确认单必须完整、可读，完整模板见 `references/17-confirmation-sheet-template.md`。确认单必须包含：

- 应用类型与主页面
- 宠物角色来源（参考图 / 文字描述 / Skill 推荐方案）
- 推荐视觉状态及生命周期
- 自动气泡策略、交互能力、临时事件列表、安全操作绑定
- **宠物性格**（archetype / energy / warmth / doubleTap 方向 / 互动强度）
- **双击 Reaction 实现模式**（CSS compact / CSS expressive / double-tap sprite）

**确认单结尾必须明确提示：**

> 请确认以上制作方案。只有你明确回复“确认”“开始”或“可以”后，我才会开始生成素材并接入应用。在此之前不会生成图片，也不会修改代码。

**禁止：输出确认单后立即继续执行。在用户明确确认前，禁止调用图片生成、生成 canonical base、生成 Sprite Sheet、修改代码或使用 SVG/CSS/Emoji/图标/临时占位角色制作宠物。**

### Step 4: 调用「图片生成与编辑（超级版）」生成 canonical base

- **只有收到用户明确确认后才能执行本步骤。**
- 调用秒哒平台提供的「图片生成与编辑（超级版）」Skill 生成 `canonical-base-pet.png`。
- 基于用户确认的角色来源 + 应用画风参考；若用户上传参考图，使用图生图（`--images canonical-input.png`）保留身份。
- canonical base 是内部生产与 QA 基准，**不是新的默认人工阻断点**；用户确认制作方案后自动继续，不要求二次确认。
- 生成失败时重试、修正提示词或暂停报告；禁止用 SVG/CSS/Emoji/图标/占位角色替代。
- 详见 `references/06-generation-workflow.md` §1、`references/16-image-generation-protocol.md`。

### Step 5: 继续调用「图片生成与编辑（超级版）」以 canonical base 为唯一身份参考生成状态 Sprite Sheet

- 推荐生成 idle / working / success / remind 四种状态。
- 每个状态图生图时必须使用 `--images` 传入已生成的 `canonical-base-pet.png`，作为唯一身份参考。
- 不同状态必须共享单帧尺寸、scale、bottom-center anchor，避免跨状态跳动。
- 详见 `references/06-generation-workflow.md` §2、`references/11-sprite-geometry.md`、`references/16-image-generation-protocol.md`。

### Step 6: 素材处理、透明背景与统一几何规范化

- 运行素材标准化脚本 `scripts/process_sprites.py`。
- 用 `scripts/geometry_qa.py` 验证跨状态几何一致性。
- 详见 `references/06-generation-workflow.md` §3、`references/11-sprite-geometry.md` 。

### Step 7: QA（几何 / contact sheet / motion preview / Identity / Cross-State / Application Visual Integration）

- 运行 `scripts/geometry_qa.py`、`scripts/generate_contact_sheet.py`、`scripts/generate_preview.py`。
- 执行 Character Identity QA、Cross-State QA、Application Visual Integration QA。
- 详见 `references/07-qa-checklist.md`、`references/12-cross-state-qa.md`、`references/15-application-visual-integration-qa.md`。

### Step 8: 代码接入（仅正式资产通过 QA 后，Application Visual Integration QA 未通过不得宣称接入完成）

- 复制 `templates/` 中的模板到项目。
- 编写应用专属 `pet-config.ts`，绑定业务状态、安全 Action、宠物性格。
- 在主应用中挂载 `PetWidget`。
- 在真实应用页面预览中执行 Application Visual Integration QA；**未通过时，不得进入最终交付阶段或宣称宠物接入完成**。
- 详见 `references/06-generation-workflow.md` §4、`references/02-core-components.md` 、`references/15-application-visual-integration-qa.md`。

### Step 9: lint / type-check / build / 应用内预览

- 运行 lint、type-check、build，并在真实应用页面预览中验证 Application Visual Integration QA。

## 4. 通用轻交互层（V2.2 更新）

完整规范见 `references/09-interaction-layer.md`。
双击 Reaction 完整规范见 `references/14-double-tap-reaction.md`。

要点：

- 单击宠物打开/关闭当前状态气泡。
- **双击宠物触发 reaction，根据宠物性格选择实现方式**（CSS compact / CSS expressive / double-tap sprite）；不是所有宠物共用固定动画。
- 拖拽宠物移动位置，松开后稳定停留，不触发 reaction。
- 长时间无交互时，允许低频主动气泡（Interruption Policy 约束）。
- 页面切换后，宠物保持位置和角色，根据页面上下文更新气泡文案。
- 双击 cooldown 900ms：冷却期内忽略新输入，**不排队，不叠加**；可选极短本地反馈（100–150ms）表示已感知。
- scale 和位移安全范围由平台视觉 QA 决定，不统一规定。
- 提供 `prefers-reduced-motion` 降级（expressive → compact 微缩放，粒子隐藏）。

## 5. 宠物性格配置（V2.2 新增）

```typescript
export type PetPersonality = {
  archetype: 'calm' | 'playful' | 'shy' | 'proud' | 'focused' | 'warm';
  energy: 'low' | 'medium' | 'high';
  warmth: 'reserved' | 'balanced' | 'caring';
  doubleTap: 'sway' | 'hop' | 'peek' | 'chin-up' | 'blink' | 'nuzzle';
  bubbleStyle: 'quiet' | 'teasing' | 'concise' | 'encouraging';
};
```

性格到 doubleTap 方向的推荐映射：

| archetype | 推荐 doubleTap | 实现方式 |
|---|---|---|
| calm | sway | CSS compact |
| playful | hop | CSS compact/expressive |
| shy | peek | CSS 或 double-tap sprite |
| proud | chin-up | CSS 或 double-tap sprite |
| focused | blink | CSS compact |
| warm | nuzzle | CSS compact/expressive |

## 6. 双击 Reaction 三种模式（V2.2 新增）

### CSS Compact（默认）
时长 450–700ms，轻微弹性感，不带粒子。适合大多数宠物。

### CSS Expressive（用户明确启用）
时长 600–800ms，可选 CSS 几何粒子（禁用 emoji）。适合 playful/proud + energy:high，需用户在确认单中明确选择。

### double-tap Sprite Row（按需生成）
仅在 CSS 无法表达局部姿势或面部变化时生成，经用户确认后执行，不计入默认 4 个业务状态。必须通过几何 QA 和 Character Identity QA。

## 7. Interruption Policy

详见 `references/10-interruption-policy.md`。

## 8. Sprite Geometry Contract

详见 `references/11-sprite-geometry.md`。

## 9. Cross-State QA

详见 `references/12-cross-state-qa.md`。

## 10. 参考文档

所有参考文档均位于本 skill 的 `references/` 目录下：

- `references/01-overview.md`：Skill 总体介绍
- `references/02-core-components.md`：Core 模板与类型
- `references/03-asset-spec.md`：素材规范
- `references/04-intake-protocol.md`：项目分析与确认单（V2.2：新增性格字段）
- `references/05-state-mapping.md`：业务状态映射
- `references/06-generation-workflow.md`：视觉生产流程
- `references/07-qa-checklist.md`：QA 检查清单
- `references/08-fallback-rules.md`：失败与降级规则
- `references/09-interaction-layer.md`：通用轻交互层（V2.2：性格化双击）
- `references/10-interruption-policy.md`：主动互动控制
- `references/11-sprite-geometry.md`：Sprite 几何规范
- `references/12-cross-state-qa.md`：跨状态 QA
- `references/13-v1-v2-diff.md`：V1 → V2 修改清单
- `references/14-double-tap-reaction.md`：双击 Reaction 完整规范（V2.2 新增）
- `references/15-application-visual-integration-qa.md`：应用视觉集成 QA（V2.2 新增）

## 11. 模板与脚本

所有模板和脚本均位于本 skill 目录下：

- `templates/PetWidget.tsx.template`
- `templates/SpriteAnimator.tsx.template`
- `templates/usePetBehavior.ts.template`
- `templates/usePetPosition.ts.template`
- `templates/pet-sprite-data.ts.template`
- `scripts/process_sprites.py`
- `scripts/geometry_qa.py`
- `scripts/generate_contact_sheet.py`
- `scripts/generate_preview.py`

## 12. 何时使用

- 用户希望为 Web/H5 应用添加可交互宠物角色。
- 用户希望宠物根据业务状态反馈、自动提醒、鼓励用户。
- 用户希望宠物支持单击、双击、拖拽、主动互动。
- 用户希望宠物的双击 reaction 符合角色性格，而不是通用轻动画。
- 用户提到「宠物」「陪伴」「桌面宠物」「状态反馈」「性格化互动」等关键词。

即使应用未提前准备宠物，也可以使用本 Skill。

## 13. 变更记录

### V2.2（本轮）：定位明确 + 资产流程收紧 + 画风继承 + 集成 QA + 性格化双击进入模板

- **产品定位明确**：明确为“应用内陪伴宠物”，非系统级桌面宠物；视觉状态由目标应用业务语义决定。
- **资产流程收紧**：正式宠物必须经过角色生成 + Sprite 生产流程；禁止 SVG/CSS 圆点/图标/占位角色替代；禁止跳过 canonical base；禁止先写接入再用占位资产。
- **取消 canonical base 二次确认**：用户确认制作方案后自动执行完整流程，canonical base 仅作内部基准，非人工阻断点。
- **失败与降级重写**：canonical base 失败则停止接入；单状态失败只重做该状态；处理失败不切 SVG；运行时失败隐藏宠物，均不用占位角色。
- **强化画风继承**：制作确认单与生成 Prompt 新增结构化 Application Visual System，宠物须像应用原有插画系统中的角色。
- **新增 Application Visual Integration QA**（`references/15`）：在实际页面预览中检查视觉系统一致性、风格漂移、页面集成协调性。
- **性格化双击进入模板**：`PetWidget`/`usePetBehavior`/`pet-sprite-data` 模板改为由 `PetPersonality` + `DoubleTapReactionConfig` 驱动，移除固定 wiggle 默认值。
- **清理旧尺寸约束**：`2848×1152`、`792×903`、固定 FPS 等标注为示例，非默认值。
- **输出物命名统一**：统一使用 `pet-sprites.json`。

### V2.2（前序）：双击 Reaction 性格化 + 冷却语义明确 + 边界参数指导化

- **双击 reaction 由性格驱动**：新增 `PetPersonality` 类型，制作确认单新增性格确认字段（archetype / energy / warmth / doubleTap / bubbleStyle）。
- **两种 CSS 实现模式**：compact（默认，450–700ms）和 expressive（用户明确启用，600–800ms，可选 CSS 几何粒子）。
- **按需生成 double-tap sprite row**：仅在 CSS 无法表达局部姿势时，经用户确认后生成。
- **粒子规范**：禁止使用 emoji 或可读文字符号；允许 CSS 几何图形（圆/菱形/线段），颜色取自应用配色。
- **Cooldown 语义明确**：900ms 冷却期内忽略新输入，不排队，不叠加；可选极短本地反馈（100–150ms）表示已感知。
- **边界参数为指导范围**：scale 和位移数值不是硬性规则，由平台根据宠物尺寸、容器和布局判断安全值，通过视觉 QA 验证。
- **`prefers-reduced-motion` 降级**：expressive 模式必须提供（退回 compact 微缩放，粒子隐藏）。
- **新增参考文档**：`references/14-double-tap-reaction.md`（双击完整规范与 QA 检查项）。
- **向后兼容**：旧 `style: 'wiggle' | 'scale' | 'shake' | 'bounce'` 仅映射为 compact 模式动画；expressive 与 sprite 模式需重新经确认单明确选择，不得由旧 style 自动推导为高表现力模式。

### V2.1：互动克制 + 视觉一致性强化

- 移除拖拽结束自动动画；降低主动气泡打扰；双击 reaction 轻量化（300–500ms）。
- Canonical Silhouette Preservation；道具不能控制人物 scale；新增 Character Identity QA 与对应 blocker。

### V2：通用轻交互层 + 打断策略 + 几何契约 + 跨状态 QA

- 引入通用轻交互层（单击、轻量双击、拖拽、主动气泡）。
- 新增 Interruption Policy：主动气泡受 60s 冷却、同类文案去重、用户操作期间不弹出。
- 新增 Sprite Geometry Contract：统一单帧尺寸、共享 scale、bottom-center anchor。
- 新增 Cross-State QA 与对应脚本 `geometry_qa.py`、`generate_contact_sheet.py`、`generate_preview.py`。
- 新增 `references/13-v1-v2-diff.md`。

### V1：基础应用宠物

- 让秒哒 Web/H5 应用快速拥有可交互、会根据业务状态反馈、会自动提醒/鼓励的宠物角色。
- 核心模板：`PetWidget`、`SpriteAnimator`、`usePetBehavior`、`usePetPosition`、`pet-sprite-data`。
- 主要解决 V0 在第一次 Blind Test 中暴露的问题：角色稳定性、状态管理、跨页面一致性、错误降级、气泡内容策略。

### Transient Event Lifecycle Bugfix

对所有 transient event 统一按 event identity 去重；`repeatable: true` 仅允许新的 occurrence 再次触发。

### V2.3：Asset Reliability Patch（仅修复图片后处理与 QA，不改变产品/确认/性格/接入逻辑）

- **Alpha-first**：处理前先检查源图是否已含有效透明通道；有则直接保留原始 alpha、跳过 RGB 抠背景，禁止把透明 PNG 四角的黑色 RGB 当成黑色背景。
- **明确的背景模式**：`preserve-alpha` / `chroma` / `auto`；优先级 有效 alpha → preserve-alpha，明确纯色背景 → chroma，无法确定 → 暂停并报告；禁止默认采样四角抠除。
- **正确羽化方向 0→255**：基于到外部背景的距离做羽化；已有 alpha 时绝不覆盖原始 alpha。
- **自适应身体色填充**：同时支持黑色角色与白色角色（身体色取自明显非背景色的不透明像素中位数）。
- **真正统一角色尺寸**：以 canonical/idle neutral frame 为参考建立 canonical body scale，对整个状态统一缩放、保持基线与中心，禁止逐帧单独 fit。
- **素材完整性 QA**：比较处理前后的面积/主体高度/主体宽度/主要连通区域/头部-耳朵-身体内部 alpha 覆盖率；主体面积或高度灾难性减少(≥50%)直接判 blocker；并检测透明洞、黑色线稿、白色贴纸外壳、异常边缘膨胀，不能仅因剩余部分几何一致就通过。
- 新增 `references/18-transparency-rules.md`；更新 `process_sprites.py`、`geometry_qa.py`。
