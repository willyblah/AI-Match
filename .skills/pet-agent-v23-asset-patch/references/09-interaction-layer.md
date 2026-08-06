# General Interaction Layer

V2.2 在 V1 的「业务状态反馈」与 V2.1 的「轻量双击」基础上，增加一套由宠物性格驱动的通用轻交互层。它让宠物在任何 Web/H5 应用中都更像「活着的应用宠物」，而不是单纯的业务状态指示器。

## 1. 设计原则

- **通用优先**：所有交互语义与业务状态解耦，任何应用都可复用同一套 Core。
- **轻量**：默认优先使用 CSS 动效，不引入新的 Sprite Sheet。
- **不打断**：交互反馈不得干扰主应用操作，也不得改变业务状态。
- **性格化**：双击 reaction 不是固定模板，而是由宠物性格选择实现方式（CSS compact / CSS expressive / double-tap sprite）。
- **可配置**：应用 Adapter 可以通过 `interaction` 和 `personality` 字段覆盖默认行为，但 Core 不强制要求配置。

## 2. 默认支持的交互

| 交互 | 触发方式 | 默认行为 | 说明 |
| --- | --- | --- | --- |
| 单击 | 指针抬起且未触发拖拽 | 打开/关闭当前状态气泡 | 第一次打开，再次点击关闭 |
| 双击 | 300ms 内连续两次点击 | 触发性格化 reaction | 见 `references/14-double-tap-reaction.md` 完整规范；不打开气泡，不改变业务状态 |
| 拖拽 | 按住移动超过阈值 | 移动宠物位置 | 拖拽期间不触发点击/双击；松开后稳定停留，不触发 reaction |
| 长按 | 暂不默认支持 | 未来可扩展 | V2.2 不强制实现 |
| 自动气泡 | 业务状态变化 | 显示临时提示 | 由 V1 自动气泡扩展而来 |
| 主动气泡 | 长时间无交互（≥60s） | 低频出现闲聊/鼓励 | 受 Interruption Policy 限制，同类文案去重，随机 60–120s 冷却 |

## 3. Reaction 语义（V2.2 更新）

Reaction 是宠物对双击的回应，属于纯视觉反馈，不触发业务逻辑。

### 性格化双击体系

- **CSS Compact（默认）**：时长 450–700ms，轻微弹性感，不带粒子。适合大多数宠物。
- **CSS Expressive（用户在确认单中明确启用）**：时长 600–800ms，可选 CSS 几何粒子（禁用 emoji）。适合 playful/proud + energy:high，但必须经用户确认。
- **double-tap Sprite Row（按需生成）**：仅在 CSS 无法表达局部姿势或面部变化时生成，经用户确认后执行，不计入默认 4 个业务状态。

### 配置接口

```typescript
// V2.2：双击 reaction Sprite 是独立命名空间，不混入业务状态
export type ReactionSpriteState = 'double-tap';

export type PetPersonality = {
  archetype: 'calm' | 'playful' | 'shy' | 'proud' | 'focused' | 'warm';
  energy: 'low' | 'medium' | 'high';
  warmth: 'reserved' | 'balanced' | 'caring';
  doubleTap: 'sway' | 'hop' | 'peek' | 'chin-up' | 'blink' | 'nuzzle';
  bubbleStyle: 'quiet' | 'teasing' | 'concise' | 'encouraging';
};

export interface ReactionConfig {
  enabled: boolean;
  durationMs?: number;
  mode: 'compact' | 'expressive' | 'sprite';
  profile?: PetPersonality['doubleTap'];
  cooldownMs?: number;
  // V2.2：spriteState 属于 ReactionSpriteState，避免与业务状态 PetState 混淆
  spriteState?: ReactionSpriteState;
  particles?: boolean;
  particleCount?: number;
  reducedMotionFallback?: boolean;
}
```

### 实现要求

- 优先使用 CSS transform / keyframes；只有在用户明确要求时才引入新的 reaction sprite。
- Reaction 期间不影响当前 `displayPetState` 的播放。
- Reaction 结束后自动恢复，不调用任何业务 action。
- **Reaction 不改变业务状态、不移动最终宠物位置、不影响 Sprite 播放。**
- **拖拽结束不得自动触发 reaction**（见 §8）。
- **双击 cooldown 900ms：冷却期内忽略新输入，不排队，不叠加；可选极短本地反馈（100–150ms）表示已感知。**
- **边界参数为指导范围：scale 和位移幅度由平台根据宠物尺寸、容器边界和应用布局自行判断安全值，通过视觉 QA 验证不遮挡、不越界。**
- 提供 `prefers-reduced-motion` 降级：expressive 退回 compact 微缩放，粒子隐藏。

## 4. 通用交互配置

```typescript
export interface PetInteractionConfig<TAppStatus extends string> {
  singleClickOpensBubble: boolean;
  doubleClickReaction: boolean;
  dragMoves: boolean;
  idleProactiveBubbles: boolean;
  clickCooldownMs: number;
  doubleClickThresholdMs: number;
  dragThresholdPx: number;
  idleProactiveMinIdleMs: number;
  userTypingGraceMs: number;
  userActivityEvents: string[];
  proactiveBubbleWindowMs: number;
  autoBubbleCooldownMs: number;
  proactiveBubbleCooldownMs: number;
  proactiveBubbleMaxCooldownMs: number;
  proactiveActivityGraceMs: number;
  reaction: ReactionConfig;
  proactiveBubbles?: ProactiveBubbleConfig<TAppStatus>[];
  personality?: PetPersonality;
}
```

### 默认参数（V2.2）

```typescript
const PET_INTERACTION_DEFAULTS: PetInteractionConfig<string> = {
  singleClickOpensBubble: true,
  doubleClickReaction: true,
  dragMoves: true,
  idleProactiveBubbles: true,
  clickCooldownMs: 600,
  doubleClickThresholdMs: 300,
  dragThresholdPx: 5,
  idleProactiveMinIdleMs: 60000,
  userTypingGraceMs: 5000,
  userActivityEvents: ['mousedown', 'keydown', 'touchstart', 'scroll'],
  proactiveBubbleWindowMs: 8000,
  autoBubbleCooldownMs: 3000,
  proactiveBubbleCooldownMs: 60000,
  proactiveBubbleMaxCooldownMs: 120000,
  proactiveActivityGraceMs: 15000,
  reaction: {
    enabled: true,
    durationMs: 700,
    mode: 'compact',
    profile: 'sway', // 由 personality.doubleTap 驱动
    cooldownMs: 900,
    particles: false,
    particleCount: 0,
    reducedMotionFallback: true,
  },
  personality: {
    archetype: 'playful',
    energy: 'medium',
    warmth: 'balanced',
    doubleTap: 'sway',
    bubbleStyle: 'concise',
  },
};
```

## 5. 用户活动检测

为降低打扰，Core 需要感知用户是否正在操作页面。

- 监听 `mousedown`、`keydown`、`touchstart`、`scroll` 等事件。
- 记录最近一次活动时间 `lastUserActivityAt`。
- 当用户正在输入时（`document.activeElement` 为 `input`、`textarea`、`[contenteditable]`），视为 typing 状态。
- 如果用户处于 typing 或高频操作窗口内，**不触发**主动气泡、不触发低优先级自动气泡。
- V2.1：主动气泡额外受 `proactiveActivityGraceMs` 约束——用户近 15s 内有点击/滚动/输入等操作时不主动弹出闲聊，避免打扰主任务。高优先级业务提醒（transient event）不受此闲聊规则限制。

## 6. 页面上下文感知

页面切换后：

- 宠物位置和角色保持不变。
- 气泡文案根据当前页面上下文更新（由 `metrics.page` 驱动，已在 V1 支持）。
- 如果当前正在显示一个页面相关气泡，页面切换后自动关闭，避免展示过期上下文。

## 7. 事件节流

- 连续快速点击宠物时，只响应一次。
- 自动气泡触发后，同类型主动气泡在 `cooldownMs` 内不会重复出现。
- V2.1：普通 proactive bubble 之间保持较长冷却（随机 `proactiveBubbleCooldownMs`–`proactiveBubbleMaxCooldownMs`，默认 60–120s），且同类闲聊文案去重，避免连续重复同一句。
- V2.2：双击事件独立 cooldown 900ms，冷却期内忽略新输入，不排队。
- 用户主动点击宠物不受普通自动气泡冷却限制，但仍然受 `clickCooldownMs` 防止连点刷屏。
- 整体原则：**业务反馈优先，陪伴闲聊克制。** 高优先级业务提醒（transient event）不受普通闲聊规则限制。

## 8. 与业务 Action 的隔离

- 拖动超过阈值不得触发 click。
- 双击不得触发两次单击。
- 拖动时关闭气泡。
- **V2.1：拖拽结束不得自动触发 reaction**，宠物立即稳定停留在最终位置并保存位置（无 bounce/settle/landing/rebound 等自动反馈）。
- Reaction 不改变主应用业务状态。
- 气泡按钮只调用 Adapter 传入的安全 action。

## 9. 输出要求

PetWidget 必须暴露以下内部能力：

- `handleSingleClick`
- `handleDoubleClick`
- `handleDragStart`
- `handleDragMove`
- `handleDragEnd`
- 区分 click 与 drag 的阈值判断

这些函数不暴露为组件 Props，但必须在组件内部正确实现。
