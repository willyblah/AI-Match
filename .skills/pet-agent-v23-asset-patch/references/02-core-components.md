# 通用核心组件

本 Skill 在目标项目中生成的代码应基于以下通用组件模板。Skill 自身不直接修改这些模板，而是将 `templates/` 目录中的文件拷贝到目标项目并注入应用专属配置。

通用核心组件保持业务无关。具体业务类型只出现在 Adapter 的 `pet-config.ts` 中。

## 1. SpriteAnimator.tsx

### 功能

- 使用 `background-position` 播放横向 1×N Sprite Sheet。
- 支持任意帧数、FPS、循环/单次播放。
- 通过 `ResizeObserver` 自适应容器宽度，避免溢出或裁切。
- 通过 `key` 重新挂载实现状态切换时从第一帧重新播放。

### 核心 Props

```typescript
interface SpriteAnimatorProps {
  src: string;
  frameWidth: number;
  frameHeight: number;
  frameCount: number;
  fps: number;
  loop: boolean;
  stateKey: string;
}
```

### 关键行为

- 每帧宽度 = `frameWidth`。
- 总宽度 = `frameWidth * frameCount`。
- 通过 `requestAnimationFrame` 切换 `background-position`。
- `loop=false` 时，播放完最后一帧后停在最后一帧。
- 容器尺寸根据 `ResizeObserver` 动态计算，保持原始宽高比。

## 2. usePetPosition.ts

### 功能

- 鼠标/触摸统一拖拽（Pointer Events）。
- 位置持久化到 `localStorage`。
- 使用实际 DOM 尺寸计算 Viewport 边界限制。
- 页面尺寸变化后自动校准。
- 点击与拖动区分（默认 5px 阈值）。

### V1 变化

- 不再依赖固定 `PET_SIZE = 128`。
- 接收 `elementRef: RefObject<HTMLElement>`，通过 `getBoundingClientRect()` 获取真实尺寸。

### 输入

```typescript
function usePetPosition(elementRef: RefObject<HTMLElement | null>)
```

### 输出

```typescript
interface UsePetPositionReturn {
  position: { x: number; y: number };
  isDragging: boolean;
  beginDrag: (x: number, y: number) => void;
  updateDrag: (x: number, y: number) => void;
  endDrag: () => void;
  didMove: () => boolean;
}
```

### 关键行为

- `beginDrag` 记录起始点和初始位置。
- `updateDrag` 计算偏移，移动超过 5px 标记为 `moved`。
- `endDrag` 保存位置并做边界 clamp（使用当前真实 DOM 尺寸）。
- 窗口 resize 时重新 clamp 已保存位置。
- 默认不超出屏幕四边，默认边距 16px。

## 3. usePetBehavior.ts

### 功能

- 管理宠物基础视觉状态。
- 管理临时覆盖事件（如 remind、success feedback）。
- 支持事件优先级、重复触发、唯一身份识别。
- 事件结束后恢复当前最新 Base State，不缓存旧状态。
- 自动气泡调度、点击气泡调度、主动气泡调度。
- 通用轻交互：reaction、用户活动记录、主动气泡控制。
- 主动互动打断策略（Interruption Policy）。

### V2 变化

- 新增 `reactionActive`、`reactionMode`、`reactionProfile`、`reactionSpriteState`（`ReactionSpriteState`，不混入 `PetState`）、`reactionParticleCount`、`triggerReaction`、`recordInteraction`。
- `bubbleSource` 扩展为 `'auto' | 'click' | 'proactive' | null`。
- 增加主动气泡 `proactiveBubbles` 调度。
- 增加用户活动检测与输入保护。
- 增加自动气泡冷却、主动气泡冷却、去重与优先级覆盖。
- 默认配置通过 `mergeInteractionConfig` 合并，应用可覆盖。

### 输入

```typescript
function usePetBehavior<TAppStatus extends string>(
  config: PetAppConfig<TAppStatus>,
  appStatus: TAppStatus,
  metrics: Record<string, number>,
  actions: Record<string, () => void>,
): UsePetBehaviorReturn<TAppStatus>
```

### 输出

```typescript
interface UsePetBehaviorReturn<TAppStatus extends string> {
  basePetState: PetState;
  displayPetState: PetState;
  bubbleOpen: boolean;
  bubbleSource: 'auto' | 'click' | 'proactive' | null;
  reactionActive: boolean;
  reactionMode: 'compact' | 'expressive' | 'sprite';
  reactionProfile: PetPersonality['doubleTap'];
  reactionSpriteState?: ReactionSpriteState;
  reactionParticleCount: number;
  openClickBubble: () => void;
  closeBubble: () => void;
  dismissTransientEvent: (eventId: string) => void;
  triggerReaction: () => void;
  recordInteraction: () => void;
}
```

### 关键行为

- `basePetState` 由当前业务状态推导。
- `displayPetState` 在临时事件激活时取当前最高优先级事件状态，否则取当前 Base State。
- 业务状态变化时触发自动气泡，持续指定时间。
- 临时事件触发时显示覆盖动画和自动气泡，持续 `durationMs` 或直到用户操作。
- 临时事件按 **event identity** 去重：同一 identity 只触发一次，`durationMs` 结束后恢复当前最新 Base State（调用 `deriveBaseState(currentAppStatus)`），不会被旧 condition 重新触发。
- 临时事件结束后进入冷却期（`cooldownMs`），冷却期结束后**新的不同 identity** 事件可再次触发。
- 主动气泡在长时间 idle 后触发，受 cooldown、用户活动、输入状态限制。
- reaction 通过 CSS 动效实现，不引入新 Sprite，不改变业务状态。

## 4. PetWidget.tsx

### 功能

整合拖拽、动画、气泡、reaction 的顶层组件。

### V2 变化

- 支持单击打开/关闭气泡。
- 支持双击触发 reaction。
- 拖拽与 click/double-click 区分。
- 拖拽时关闭气泡。
- 连续点击节流。
- 保持业务无关。

### 输入

```typescript
interface PetWidgetProps<TAppStatus extends string> {
  config: PetAppConfig<TAppStatus>;
  appStatus: TAppStatus;
  metrics: Record<string, number>;
  actions: Record<string, () => void>;
}
```

### 关键行为

- 使用 `usePetPosition` 管理拖拽位置。
- 使用 `usePetBehavior` 管理显示状态、气泡、reaction。
- 使用 `SpriteAnimator` 播放当前显示状态动画。
- 气泡显示在宠物上方或下方，不超出屏幕。
- 点击宠物时打开/关闭点击气泡。
- 双击宠物时触发 reaction。
- 拖动时关闭气泡，避免跟随抖动。
- 拖动超过阈值不触发点击/双击。

### 交互识别

- `pointerDown` 开始拖拽并捕获指针。
- `pointerMove` 更新拖拽位置。
- `pointerUp` 结束拖拽。
- 如果移动距离超过阈值，视为拖拽，不触发 click/double-click。
- 如果移动距离未超过阈值，通过 click 时间间隔区分单击/双击。

## 5. pet-config.ts（应用 Adapter）

### 功能

集中管理宠物所有状态的 Sprite 配置、生命周期、气泡配置、业务事件映射、交互配置。

### V2 扩展类型

```typescript
export type PetState = 'idle' | 'working' | 'success' | 'remind';
// V2.2：双击 reaction Sprite 是独立命名空间，不混入业务状态
export type ReactionSpriteState = 'double-tap';
export type PetStateLifecycle = 'persistent' | 'transient';

export interface ProactiveBubbleConfig<TAppStatus> {
  id: string;
  intervalMs: number;
  cooldownMs: number;
  maxPerSession: number;
  condition: (status: TAppStatus, metrics: Record<string, number>, lastInteractionAt: number) => boolean;
  getText: (status: TAppStatus, metrics: Record<string, number>) => string;
  priority: number;
}

export interface ReactionConfig {
  enabled: boolean;
  durationMs: number;
  mode: 'compact' | 'expressive' | 'sprite';
  profile?: PetPersonality['doubleTap'];
  durationMs?: number;
  cooldownMs?: number;
  spriteState?: string;
  particles?: boolean;
  particleCount?: number;
  reducedMotionFallback?: boolean;
}

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
  proactiveBubbleMaxCooldownMs: number;    // V2.1：闲聊冷却随机区间上限
  proactiveActivityGraceMs: number;        // V2.1：用户近期操作后不主动弹出的宽限
  reaction: ReactionConfig;
  proactiveBubbles?: ProactiveBubbleConfig<TAppStatus>[];
}

export interface PetAppConfig<TAppStatus extends string> {
  deriveBaseState: (status: TAppStatus) => PetState;
  stateMeta: Record<PetState, PetStateMeta>;
  sprites: Record<PetState, SpriteConfig>;
  // V2.2：双击 reaction Sprite 单独存放，避免与业务状态混淆
  reactionSprites?: Record<ReactionSpriteState, SpriteConfig>;
  bubbles: Record<PetState, BubbleConfig>;
  autoBubbles?: Partial<Record<TAppStatus, AutoBubbleConfig<TAppStatus>>>;
  proactiveBubbles?: ProactiveBubbleConfig<TAppStatus>[];
  transientEvents?: TransientEventConfig<TAppStatus>[];
  interaction?: Partial<PetInteractionConfig<TAppStatus>>;
  personality?: PetPersonality;
}
```

### 业务类型留在 Adapter

```typescript
export type DashboardPetStatus =
  | 'idle'
  | 'learning'
  | 'completed'
  | 'task-completed'
  | 'water-added'
  | 'reminder';

export const DASHBOARD_PET_CONFIG: PetAppConfig<DashboardPetStatus> = { ... };

// 使用
<PetWidget<DashboardPetStatus>
  config={DASHBOARD_PET_CONFIG}
  appStatus={petStatus}
  metrics={...}
  actions={...}
/>
```

## 6. 目录生成建议

目标项目通常生成以下结构：

```
src/components/pet/
  ├── SpriteAnimator.tsx
  ├── PetWidget.tsx
  ├── usePetPosition.ts
  ├── usePetBehavior.ts
  └── pet-config.ts
public/images/pet/
  ├── canonical-base-pet.png
  ├── idle.png
  ├── working.png
  ├── success.png
  ├── remind.png
  ├── pet-sprites.json
  ├── contact-sheet.png
  └── motion-preview.png
```

## 7. 与主应用的关系

- 宠物组件只作为订阅者读取业务状态，不改变业务状态。
- 宠物组件只作为事件触发器调用外部传入的 action，不实现业务逻辑。
- 宠物组件挂载在推荐主页面的边缘位置，不遮挡核心操作。

## 8. 最小修改边界

- **通用 Core 不应修改**：`SpriteAnimator.tsx`、`usePetPosition.ts`、`usePetBehavior.ts`、`PetWidget.tsx` 保持业务无关。
- **允许修改**：`pet-config.ts` 中的业务类型、映射、气泡、事件配置、交互配置。
- **如果通用 Core 模板类型仍不匹配**：优先调整 Adapter 中的类型声明，而不是修改 Core 模板。
