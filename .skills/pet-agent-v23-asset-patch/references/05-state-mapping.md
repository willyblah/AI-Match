# 状态与事件模型

## 1. 核心概念

### 1.1 Base State

Base State 是宠物始终存在的基础视觉状态，由当前业务状态推导而来。

- 每个应用状态都必须映射到一个 Base State。
- Base State 不能同时有多个。
- 没有 Transient Event 激活时，`displayPetState === basePetState`。

### 1.2 Transient State

Transient State 是临时覆盖在 Base State 之上的视觉状态，用于反馈短暂事件。

- 例如：success（庆祝）、remind（提醒）、failed（失败提示）。
- 有生命周期，结束后必须恢复当前最新 Base State。
- 同一个视觉状态可以表达多个业务事件，但气泡、优先级、操作可以不同。

### 1.3 Transient Event

Transient Event 是触发 Transient State 的业务事件。每个事件包含：

```typescript
interface TransientEventConfig<TAppStatus extends string> {
  eventId: string;
  targetPetState: PetState;   // 要显示什么视觉状态
  baseState: PetState;        // 事件结束后恢复哪个 Base State 的参考（实际恢复 deriveBaseState(currentAppStatus)）
  priority: number;           // 事件优先级，高优先级可覆盖低优先级
  condition: (status: TAppStatus, metrics: Record<string, number>) => boolean;
  getIdentity?: (status: TAppStatus, metrics: Record<string, number>) => string;
  durationMs: number;         // 事件持续时间
  cooldownMs: number;          // 事件结束后多久可再次触发
  repeatable: boolean;         // 是否允许新的 occurrence 重复触发（见 §3.2）
  isBusinessEvent?: boolean;   // 是否为业务事件（可覆盖普通气泡）
}
```

### 1.4 生命周期语义

每个视觉状态都应有生命周期：

```typescript
export type PetStateLifecycle = 'persistent' | 'transient';

export interface PetStateMeta {
  lifecycle: PetStateLifecycle;
  defaultDurationMs?: number;
}
```

- `persistent`：作为 Base State 长期存在，没有固定结束时间。
- `transient`：作为临时反馈存在，通常持续 3s–5s，结束后恢复当前 Base State。

## 2. 事件优先级模型

### 2.1 默认优先级参考

优先级数字越大越优先：

| 优先级 | 事件类型 | 示例 |
|--------|----------|------|
| 100 | 错误 / 失败 | `failed`, `error` |
| 80 | 提醒 / 超时 | `remind`, `timeout`, `waiting_for_user` |
| 60 | 活跃工作 | `working`, `running`, `generating` |
| 40 | 成功反馈 | `success`, `completed` |
| 0 | 基础状态 | `idle` |

### 2.2 优先级规则

- 当多个事件同时满足条件时，选择优先级最高的事件。
- 如果当前已有激活事件，新事件优先级更高时才能打断当前事件。
- 事件结束后，恢复当前最新 Base State，而不是事件触发前缓存的旧状态。

### 2.3 为什么恢复当前最新 Base State

业务状态可能在 Transient Event 持续期间发生变化。例如：

- 用户开始学习，宠物处于 `working`。
- 用户完成一个任务，触发 `success` transient。
- 在 `success` 持续 3 秒内，用户又开始学习，业务状态变为 `learning`。
- `success` 结束后，宠物应回到 `working`，而不是 `idle`。

因此，事件结束后必须调用 `deriveBaseState(currentAppStatus)`，而不是 `event.baseState`。

## 3. 重复触发模型（Event Identity 去重）

### 3.1 核心原则：同一 identity 只触发一次

**所有** transient event（无论 `repeatable` 是否为 `true`）都必须记录当前已消费的 **event identity**。同一个 identity 只能触发一次。

- 触发一次后，即使 `condition` 仍然为 `true`，也不得再次触发。
- 只有 identity 发生变化（即产生了新的 occurrence），才允许再次触发。

> ⚠️ **关键 Bugfix**：早期实现仅对 `repeatable: false` 的事件按 identity 去重，导致 `repeatable: true` 的事件在 `condition` 持续为 `true` 时，每轮 `durationMs` 结束后被立即重新触发，宠物无法回到 Base State。正确实现是对**所有**事件统一按 identity 去重。

### 3.2 repeatable 的正确定义

- `repeatable: false`：该 transient 在当前生命周期内最多触发一次。
- `repeatable: true`：允许**新的 event occurrence** 重复触发。

`repeatable` **绝不表示**：「只要 `condition` 保持为 `true`，就每次 `durationMs` 结束后重新触发」。

### 3.3 Event Identity（事件身份）

优先从业务事件中读取可区分不同 occurrence 的值：

- `timestamp`（如 `lastSuccessAt` / `lastFailAt`）
- `event id` / `occurrenceId` / `sequence number`
- `task id + completion timestamp`
- `request id` / `result id`

```typescript
getIdentity: (status, metrics) => metrics.lastSuccessAt.toString(),
```

- Skill 保存最近已消费的 identity，只有 identity 变化时才能再次触发相同 `repeatable` 事件。
- 如果未提供 `getIdentity`，则使用 `eventId` 作为身份，事件触发一次后即无法再次触发。

### 3.4 Boolean Condition 陷阱与 Rising-Edge Fallback

如果 transient 的 `condition` 只是 `status === "success"` 这类持续布尔状态，且该状态会长期保持，则仍有重复触发风险。

**优先级**（分析应用时应优先选择前者）：

1. event occurrence / timestamp / requestId（最佳）
2. 状态变化 edge（`false → true`）
3. 持续 boolean condition（最弱）

如果只能获取 boolean 状态，必须实现 **rising-edge detection**：

- `false → true` 时触发一次。
- 保持 `true` 时不重复触发。
- 必须再次 `true → false → true` 才视为新的 occurrence。

### 3.5 冷却期

- 事件持续 `durationMs` 后进入 `cooldownMs` 冷却期。
- 冷却期内，相同身份的事件不会再次触发。
- 冷却期结束后，**新的不同身份**事件可以再次触发。

### 3.6 典型事件配置

#### 任务完成（success）

```typescript
{
  eventId: 'task_success',
  targetPetState: 'success',
  baseState: 'idle',
  priority: 40,
  condition: (status, metrics) => metrics.lastSuccessAt > 0,
  getIdentity: (status, metrics) => metrics.lastSuccessAt.toString(),
  durationMs: 1500,
  cooldownMs: 0,
  repeatable: true,
}
```

#### 任务失败（failed）

```typescript
{
  eventId: 'task_failed',
  targetPetState: 'failed',
  baseState: 'idle',
  priority: 100,
  condition: (status, metrics) => metrics.lastFailAt > 0,
  getIdentity: (status, metrics) => metrics.lastFailAt.toString(),
  durationMs: 4000,
  cooldownMs: 3000,
  repeatable: true,
}
```

#### 提醒弹窗

```typescript
{
  eventId: 'reminder',
  targetPetState: 'remind',
  baseState: 'idle',
  priority: 80,
  condition: (status, metrics) => metrics.reminderVisible === 1,
  durationMs: 5000,
  cooldownMs: 10000,
  repeatable: true,
}
```

## 4. 业务状态与视觉状态映射

### 4.1 映射原则

- 多个业务状态可共享同一个视觉状态。
- 同一个视觉状态可表达多个业务事件，但使用不同气泡/优先级/操作。
- 不要因为新增业务事件就必然生成新的 Sprite。

### 4.2 映射示例：个人工作台

| 业务状态 / 事件 | 视觉状态 | 生命周期 |
|-----------------|----------|----------|
| idle | idle | persistent |
| learning | working | persistent |
| completed | success (transient) | transient |
| task-completed | success (transient) | transient |
| water-added | success (transient) | transient |
| reminder | remind | transient |

### 4.3 映射示例：番茄钟

| 业务状态 / 事件 | 视觉状态 | 生命周期 |
|-----------------|----------|----------|
| idle, paused | idle | persistent |
| running | working | persistent |
| completed | success (transient) | transient |
| focus_timeout | remind | transient |

## 5. 自动气泡

### 5.1 触发时机

- 业务状态变化时触发。
- 临时事件触发时触发。
- 用户点击宠物时触发。

### 5.2 配置

```typescript
interface AutoBubbleConfig<TAppStatus> {
  durationMs: number;
  shouldShow: (prev: TAppStatus, current: TAppStatus) => boolean;
  getText: (status: TAppStatus) => string;
}
```

### 5.3 注意

- 自动气泡只在 `appStatus` 变化时触发。
- 如果 `appStatus` 不变，重复触发同一业务事件不会触发自动气泡，需要依赖临时事件气泡。
- 点击气泡不受 `shouldShow` 限制，始终显示。

## 6. 安全操作绑定

### 6.1 原则

- 只绑定目标应用已存在的、低影响的操作函数。
- 不绑定删除、支付、发布、账号变更、不可逆提交。
- 如果找不到安全操作，只显示状态反馈，不生成按钮。

### 6.2 推荐安全操作

- 聚焦输入框
- 开始/暂停计时器
- 完成/取消任务
- 记录/确认喝水
- 关闭提醒弹窗
- 打开某个面板或 Tab

## 7. V1 暂时不做

- 复杂事件队列与排队
- 多宠物同时存在
- 自主行走
- 声音/语音反馈
- 宠物与用户长期学习
