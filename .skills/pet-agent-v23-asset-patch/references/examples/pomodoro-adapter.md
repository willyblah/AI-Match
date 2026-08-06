# 番茄钟接入案例

## 1. 应用信息

- **应用类型**：极简番茄钟
- **主页面**：`src/pages/PomodoroPage.tsx`
- **状态 Hook**：`src/hooks/usePomodoro.ts`
- **业务状态类型**：`TimerStatus`
- **已验证版本**：v3.1

## 2. 业务状态枚举

```typescript
export type TimerStatus = 'idle' | 'running' | 'paused' | 'completed' | 'resting';
```

## 3. 业务状态到宠物视觉状态映射

| 业务状态 | 宠物视觉状态 | 说明 |
| --- | --- | --- |
| idle | idle | 尚未开始 |
| running | working | 正在专注 |
| paused | idle | 与 idle 共享视觉，话术不同 |
| completed | success | 一轮专注完成 |
| resting | idle | 与 idle 共享视觉，话术不同 |

## 4. 宠物状态动画配置

| 状态 | 帧数 | FPS | 循环 | 语义 |
| --- | --- | --- | --- | --- |
| idle | 4 | 4 | 是 | 呼吸/眨眼 |
| working | 4 | 6 | 是 | 专注中 |
| success | 6 | 8 | 否 | 庆祝完成 |
| remind | 4 | 4 | 是 | 疲劳提醒 |

## 5. 可被宠物调用的安全操作

```typescript
interface PomodoroActions {
  startTimer: () => void;
  pauseTimer: () => void;
  resumeTimer: () => void;
  resetTimer: () => void;
  startRest: () => void;
}
```

## 6. 气泡与操作绑定

| 业务状态 | 气泡话术 | 气泡按钮 | 调用函数 |
| --- | --- | --- | --- |
| idle | 准备好就开始吧。 | 开始专注 | startTimer |
| running | 我陪你一起专注，这轮还剩 XX 分钟。 | 暂停专注 | pauseTimer |
| paused | 暂停中，要继续吗？ | 继续专注 | resumeTimer |
| completed | 完成一轮啦，休息一下吧。 | 开始休息 | startRest |
| remind 临时事件 | 已经专注很久了，起来活动一下吧。 | 开始休息 / 稍后提醒 | startRest / dismissRemind |

## 7. 自动气泡配置

| 业务状态变化 | 自动气泡话术 | 持续时长 |
| --- | --- | --- |
| 进入 running | 我陪你一起专注。 | 3 秒 |
| 进入 paused | 暂停中，要继续吗？ | 3 秒 |
| 进入 completed | 完成一轮啦，休息一下吧。 | 5 秒 |
| 触发 remind | 已经专注很久了，起来活动一下吧。 | 5 秒 |

## 8. 临时事件配置

```typescript
{
  eventId: 'focus_overtime',
  targetPetState: 'remind',
  baseState: 'working',
  condition: (status, metrics) =>
    status === 'running' && metrics.elapsedFocusSeconds >= 50 * 60,
  durationMs: 5000,
  cooldownMs: 15 * 60 * 1000,
}
```

测试模式：

```typescript
{
  condition: (status, metrics) =>
    status === 'running' && metrics.elapsedFocusSeconds >= 15,
  durationMs: 5000,
  cooldownMs: 10 * 1000,
}
```

## 9. 为什么 remind 是临时事件

番茄钟的长期业务状态只有 `idle/running/paused/completed/resting`。`remind` 不是持久状态，而是当 `running` 超过阈值时短暂覆盖在 `working` 之上的视觉与气泡事件。它有明确的开始、持续、结束和冷却，结束后恢复到 `working`。

## 10. 代码接入位置

```typescript
// src/pages/PomodoroPage.tsx
import { PetWidget } from '@/components/pet/PetWidget';

<PetWidget
  timerStatus={timerStatus}
  remainingSeconds={remainingSeconds}
  elapsedFocusSeconds={elapsedFocusSeconds}
  mode={mode}
  onStartFocus={startTimer}
  onPauseFocus={pauseTimer}
  onResumeFocus={resumeTimer}
  onStartRest={startRest}
/>
```

## 11. 番茄钟专属放宽

为了让 remind 中的"开始休息"按钮可生效，放宽了 `startRest` 的守卫：

```typescript
// 允许从 running / paused / completed 进入休息
const startRest = useCallback(() => {
  if (
    timerStatus !== 'running' &&
    timerStatus !== 'paused' &&
    timerStatus !== 'completed'
  ) {
    return;
  }
  // ...
}, [...]);
```

这是番茄钟专属适配，不是 Skill 通用规则。Skill 在其他应用中应严格遵守"只调用已有安全操作"的原则。

## 12. 参考文件

- 通用组件：`src/components/pet/SpriteAnimator.tsx`
- 行为 Hook：`src/components/pet/usePetBehavior.ts`
- 位置 Hook：`src/components/pet/usePetPosition.ts`
- 组件：`src/components/pet/PetWidget.tsx`
- 素材：`public/images/pet/`
