# V1 → V2 修改清单（V2.1 已在基础上收紧互动与视觉一致性）

## 1. 能力新增

### 1.1 General Interaction Layer

- 单击宠物打开/关闭当前状态气泡。
- 双击宠物触发轻量 reaction（CSS 动效，300–500ms）。
- 拖拽宠物移动位置（V2.1：松开即稳定停留，不触发 reaction）。
- 长时间无交互时低频主动气泡（V2.1：≥60s、随机 60–120s 冷却、同类去重、操作期间不弹出）。
- 页面切换后保持位置和角色，更新上下文话术。
- 连续点击节流。

### 1.2 Interruption Policy

- 自动气泡 cooldown。
- 短时间窗口内最多一次非用户触发气泡。
- 用户输入/高频操作时降低打扰。
- 高优先级业务事件覆盖普通闲聊。
- 同类主动气泡去重。
- 用户主动点击不受普通自动气泡冷却限制。

### 1.3 Sprite Geometry Contract

- 每个 pet run 建立统一的 canonical frame specification。
- 所有状态使用统一 frame canvas、visual scale、anchor。
- 默认 bottom-center anchor。
- 禁止因动作更宽而自动缩小角色。
- 禁止跨状态 size popping。

### 1.4 Cross-State Registration QA

- 检查 `idle → working`、`working → success`、`working → failed/remind/attention`、`transient → base state` 切换。
- 检测 size popping、baseline jump、center shift、silhouette scale mismatch。
- 几何 QA 失败时只修复失败状态。

### 1.5 几何检测

- 每帧非透明 bounding box。
- 主体宽高、bottom anchor、centerX。
- 相邻帧主体尺寸变化。
- 跨状态基准帧主体尺寸变化。

### 1.6 Contact Sheet + Motion Preview

- 生成 cross-state contact sheet。
- 生成每个状态的动画 preview。
- 作为 QA 必检输出物。

## 2. 设计变更

### 2.1 Reaction 不强制新增 Sprite

- 默认使用 CSS transform（bounce/wiggle/scale/shake）。
- 可复用已有动画时才复用。
- 只有用户明确要求更丰富动画时才增加新的 reaction Sprite。

### 2.2 后处理脚本升级

- 从「按帧 fit-to-frame」改为「共享 scale + bottom-center anchor」。
- 新增 `canonical` 字段写入 `pet-sprites.json`。
- 新增 `geometry_qa.py` 几何检测。
- 新增 `generate_contact_sheet.py` 和 `generate_preview.py` 输出物。

### 2.3 模板升级

- `usePetBehavior.ts.template`：新增交互状态、主动气泡、reaction、打断策略。
- `PetWidget.tsx.template`：支持单击/双击/拖拽/reaction，区分 drag 与 click。
- `pet-sprite-data.ts.template`：扩展 `PetInteractionConfig`、`ProactiveBubbleConfig`、`ReactionConfig` 类型。

## 3. 保持不变的 V1 能力

- 动态 Pet State。
- Base State + Transient Event。
- Event Priority。
- repeatable transient。
- canonical character。
- 逐状态生成。
- 安全操作绑定。
- 自动/点击气泡。
- 拖拽和位置记忆。
- 失败回退。
- 番茄钟和两个 Workspace Reference。

## 4. 文件变更

### 新增文件

- `references/09-interaction-layer.md`
- `references/10-interruption-policy.md`
- `references/11-sprite-geometry.md`
- `references/12-cross-state-qa.md`
- `references/13-v1-v2-diff.md`
- `scripts/geometry_qa.py`
- `scripts/generate_contact_sheet.py`
- `scripts/generate_preview.py`

### 修改文件

- `SKILL.md`：升级为 V2 版本。
- `references/02-core-components.md`：更新类型说明。
- `references/03-asset-spec.md`：加入几何规范。
- `references/06-generation-workflow.md`：加入 cross-state QA 和 contact sheet。
- `references/07-qa-checklist.md`：加入 V2 验收项。
- `templates/usePetBehavior.ts.template`：新增交互与打断逻辑。
- `templates/PetWidget.tsx.template`：新增交互识别。
- `templates/pet-sprite-data.ts.template`：扩展类型。
- `scripts/process_sprites.py`：共享 scale + canonical spec。

## 5. 哪些尺寸问题现在会被自动阻止

- 单帧尺寸不一致：所有状态统一 frameWidth/frameHeight。
- 按帧 fit-to-frame 导致的缩放：改为共享 scale。
- 角色主体被裁切：alpha bbox 检测 + 空帧检测。
- 明显 size popping：主体高度变化 ≥ 10% 报告 blocker。
- 明显 baseline jump：纵向偏移 ≥ 5% frameHeight 报告 blocker。
- 空帧 / 边缘越界：几何检测直接发现。

## 6. 哪些情况仍需要人工视觉 QA

- 角色身份漂移（毛色、发型、服装、道具）。
- 画风一致性。
- 表情/眼神一致性。
- 动画语义是否清晰。
- 细微的比例/姿态异常（自动化阈值内但仍不自然）。
- 自动化检测通过但视觉上仍有明显跳动的边缘案例。
