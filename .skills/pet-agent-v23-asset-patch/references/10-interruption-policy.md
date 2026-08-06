# Interruption Policy

V2 引入统一的主动互动控制策略，防止宠物在不合适的时间无节制地出现气泡、动画或提醒。目标是增加陪伴感，而不是增加打扰。

## 1. 核心规则

### 1.1 单例气泡

任何时刻，**最多只显示一个气泡**。新的气泡出现时，旧的必须关闭。

### 1.2 主动气泡 Cooldown

- 自动气泡（业务状态变化触发）显示后，进入 `autoBubbleCooldownMs` 冷却期。
- 主动气泡（长时间 idle 触发）显示后，进入 `proactiveBubbleCooldownMs` 冷却期。
- 冷却期内，同类型的主动气泡不会再次触发。

### 1.3 短时间窗口上限

在任意连续 `windowMs`（默认 8000ms）内：

- 最多只允许一次非用户触发气泡（自动气泡或主动气泡）。
- 高优先级业务事件可重置窗口，覆盖低优先级气泡。

### 1.4 用户输入/高频操作保护

- 用户正在输入时，不触发主动气泡。
- 用户最近 5000ms 内有过操作时，降低主动气泡触发概率。
- 用户连续点击、滚动、拖拽时，禁止触发主动气泡。

### 1.5 优先级覆盖

| 优先级 | 事件类型 | 行为 |
| --- | --- | --- |
| 100+ | 错误/失败反馈 | 可覆盖所有其他气泡 |
| 80-99 | 关键业务完成 | 可覆盖普通业务提醒 |
| 40-79 | 普通业务完成/提醒 | 可覆盖闲聊主动气泡 |
| 0-39 | 主动闲聊/鼓励 | 最低优先级，易被覆盖 |

### 1.6 用户点击不受普通冷却限制

- 用户主动点击宠物时，立即打开/关闭气泡，不受自动气泡冷却限制。
- 但用户点击仍然受 `clickCooldownMs` 限制，防止连续快速点击导致气泡刷屏。

### 1.7 同类去重

- 通过 `proactiveBubble.id` 或 `transientEvent.eventId` 识别同类气泡。
- 同一类主动气泡在 `cooldownMs` 内不重复触发，即使触发条件一直满足。
- 临时事件通过 `getIdentity` 区分不同实例，避免同一个任务反复触发。

### 1.8 拖拽与气泡互斥

- 拖拽开始时关闭气泡。
- 拖拽结束时不自动打开气泡。

## 2. 状态机

```text
                    +------------------+
                    |   无气泡显示      |
                    +--------+---------+
                             |
          +------------------+------------------+
          |                                     |
   业务状态变化 / 临时事件                   长时间 idle + 未打扰
          |                                     |
          v                                     v
   +--------------+                     +----------------+
   | 自动气泡显示  |                     | 主动气泡显示    |
   +------+-------+                     +--------+-------+
          |                                      |
          | 持续时间到 / 用户点击外部            | 持续时间到 / 用户交互
          v                                      v
          +------------------+------------------+
                             |
                             v
                    +------------------+
                    | 进入 cooldown    |
                    +------------------+
```

## 3. 配置字段

在 `PetAppConfig` 中：

```typescript
export interface PetAppConfig<TAppStatus extends string> {
  // ... V1 fields
  interaction?: Partial<PetInteractionConfig<TAppStatus>>;
}
```

`PetInteractionConfig` 中与打断策略相关的字段：

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| `clickCooldownMs` | 600 | 连续点击节流 |
| `doubleClickThresholdMs` | 300 | 双击判定窗口 |
| `idleProactiveMinIdleMs` | 20000 | 用户无操作多久后才允许主动气泡 |
| `userTypingGraceMs` | 5000 | 用户输入结束后多久解除保护 |
| `proactiveBubbleWindowMs` | 8000 | 非用户触发气泡的最短间隔 |
| `autoBubbleCooldownMs` | 3000 | 自动气泡冷却 |
| `proactiveBubbleCooldownMs` | 30000 | 主动气泡冷却 |

## 4. 实现要求

- 所有时间戳使用 `Date.now()` 或 `performance.now()` 记录，避免与 React render 时间混淆。
- `usePetBehavior` 负责维护所有时间戳和 cooldown 状态。
- `PetWidget` 只负责调用 `recordInteraction()` 和 `triggerReaction()`，不直接管理 cooldown。
- 任何新的气泡出现前，必须先调用 `closeBubble()` 关闭旧气泡。

## 5. 与业务事件的关系

- 业务事件（如 `task_success`、`task_failed`）默认视为高优先级，可以覆盖主动气泡。
- 应用 Adapter 可以通过 `isBusinessEvent: true` 标记关键业务事件。
- 主动气泡不会覆盖业务事件，业务事件结束后恢复当前 Base State。
