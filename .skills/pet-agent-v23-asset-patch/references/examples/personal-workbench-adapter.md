# 参考案例 2：个人工作台 Lite（Personal Workbench Lite）

## 1. 应用概述

- **应用类型**：个人效率 Dashboard
- **技术栈**：React + Vite + Tailwind CSS + shadcn/ui
- **主页面**：`src/pages/Dashboard.tsx`
- **数据层**：`src/lib/storage.ts`，本地 `localStorage` 持久化
- **UI 主题**：工程蓝图风格（深蓝 #0D47A1、纯白线条、网格背景、monospace 字体）

## 2. 业务模块与状态

### 2.1 今日任务

- 数据结构：`Task[]`，每个任务有 `id`、`text`、`completed`、`createdAt`
- 关键操作：`addTask`、`toggleTask`、`deleteTask`
- 可观察指标：`pendingTasks`、`completedTasks`

### 2.2 专注学习

- 类型：`StudyStatus = 'idle' | 'learning' | 'completed'`
- 关键操作：`startStudy`、`completeStudy`、`cancelStudy`
- 可观察指标：`study.status`

### 2.3 生活记录（喝水）

- 数据：`waterCount`、`waterReminderEnabled`
- 关键操作：`addWater`、`drinkFromReminder`、`dismissReminder`、`toggleReminder`
- 可观察指标：`waterCount`、`reminderVisible`

## 3. 推荐 Pet State

| 视觉状态 | 生命周期 | 业务场景 |
|----------|----------|----------|
| idle | persistent | 默认空闲 |
| working | persistent | 专注学习 `learning` |
| success | transient | 任务完成 / 学习完成 / 喝水记录 |
| remind | transient | 喝水提醒弹窗 |

## 4. 业务状态 → 宠物状态映射

```typescript
export type DashboardPetStatus =
  | 'idle'
  | 'learning'
  | 'completed'
  | 'task-completed'
  | 'water-added'
  | 'reminder';

const deriveBaseState = (status: DashboardPetStatus): PetState => {
  if (status === 'task-completed' || status === 'completed' || status === 'water-added') {
    return 'success';
  }
  if (status === 'learning') return 'working';
  if (status === 'reminder') return 'remind';
  return 'idle';
};
```

## 5. 临时事件配置

```typescript
const transientEvents = [
  {
    eventId: 'task_completed',
    targetPetState: 'success',
    baseState: 'idle',
    priority: 40,
    condition: (status, metrics) => metrics.lastTaskCompletedAt > 0,
    getIdentity: (status, metrics) => metrics.lastTaskCompletedAt.toString(),
    durationMs: 3000,
    cooldownMs: 0,
    repeatable: true,
  },
  {
    eventId: 'study_completed',
    targetPetState: 'success',
    baseState: 'idle',
    priority: 40,
    condition: (status, metrics) => metrics.lastStudyCompletedAt > 0,
    getIdentity: (status, metrics) => metrics.lastStudyCompletedAt.toString(),
    durationMs: 5000,
    cooldownMs: 0,
    repeatable: true,
  },
  {
    eventId: 'water_added',
    targetPetState: 'success',
    baseState: 'idle',
    priority: 40,
    condition: (status, metrics) => metrics.lastWaterAt > 0,
    getIdentity: (status, metrics) => metrics.lastWaterAt.toString(),
    durationMs: 3000,
    cooldownMs: 0,
    repeatable: true,
  },
  {
    eventId: 'reminder',
    targetPetState: 'remind',
    baseState: 'idle',
    priority: 80,
    condition: (status, metrics) => metrics.reminderVisible === 1,
    durationMs: 5000,
    cooldownMs: 10000,
    repeatable: true,
  },
];
```

## 6. 自动气泡配置

```typescript
const autoBubbles = {
  learning: {
    durationMs: 3000,
    shouldShow: (prev, current) => prev !== 'learning' && current === 'learning',
    getText: () => '我陪你一起学习吧！',
  },
  completed: {
    durationMs: 5000,
    shouldShow: (prev, current) => prev !== 'completed' && current === 'completed',
    getText: () => '学习完成，真棒！',
  },
  'task-completed': {
    durationMs: 3000,
    shouldShow: (prev, current) => current === 'task-completed',
    getText: () => '完成一项任务，继续保持！',
  },
  'water-added': {
    durationMs: 3000,
    shouldShow: (prev, current) => current === 'water-added',
    getText: () => '喝水记录成功，注意健康~',
  },
  reminder: {
    durationMs: 5000,
    shouldShow: (prev, current) => prev !== 'reminder' && current === 'reminder',
    getText: () => '该喝水啦，休息一下~',
  },
};
```

## 7. 安全操作绑定

```typescript
const actions = {
  focusTaskInput: () => inputRef.current?.focus(),
  drinkWater: () => drinkFromReminder(),
  dismissReminder: () => dismissReminder(),
};

const bubbles = {
  idle: {
    getText: () => '准备好就开始吧。',
    getActions: (_, actions) => [
      { label: '新增任务', onClick: actions.focusTaskInput },
    ],
  },
  working: {
    getText: () => '我陪你一起学习，保持专注。',
    getActions: () => [],
  },
  success: {
    getText: (status) => {
      if (status === 'task-completed') return '任务完成，继续保持！';
      if (status === 'water-added') return '喝水记录成功，注意健康~';
      return '学习完成，真棒！';
    },
    getActions: (_, actions) => [
      { label: '再来一次', onClick: actions.focusTaskInput, variant: 'outline' },
    ],
  },
  remind: {
    getText: () => '该喝水啦，起来活动一下吧。',
    getActions: (_, actions) => [
      { label: '已喝水', onClick: actions.drinkWater },
      { label: '稍后', onClick: actions.dismissReminder, variant: 'outline' },
    ],
  },
};
```

## 8. 页面挂载

```typescript
const [petStatus, setPetStatus] = useState<DashboardPetStatus>('idle');

// 学习状态
useEffect(() => {
  if (data.study.status === 'learning') setPetStatus('learning');
  else if (data.study.status === 'completed') setPetStatus('completed');
  else setPetStatus('idle');
}, [data.study.status]);

// 任务完成 -> 触发 metrics 更新，由 transientEvents 处理

// 喝水记录 -> 触发 metrics 更新，由 transientEvents 处理

// 提醒弹窗
useEffect(() => {
  if (reminderVisible) setPetStatus('reminder');
  else if (petStatus === 'reminder') {
    setPetStatus(data.study.status === 'learning' ? 'learning' : 'idle');
  }
}, [reminderVisible, data.study.status, petStatus]);

<PetWidget<DashboardPetStatus>
  config={DASHBOARD_PET_CONFIG}
  appStatus={petStatus}
  metrics={{
    pendingTasks,
    waterCount: data.waterCount,
    studyCompletedCount: data.studyCompletedCount,
    lastTaskCompletedAt: data.lastTaskCompletedAt,
    lastStudyCompletedAt: data.lastStudyCompletedAt,
    lastWaterAt: data.lastWaterAt,
    reminderVisible: reminderVisible ? 1 : 0,
  }}
  actions={actions}
/>
```

## 9. 踩坑记录与修复

### 9.1 角色来源默认错误

**问题**：Agent 最初直接默认了“机械小助手”角色，没有先询问用户是否有参考图。

**修复**：在 Intake Protocol 中强制要求：如果用户未提供角色来源，必须询问“是否有参考图 / 希望什么角色 / 是否接受推荐方案”。

### 9.2 Success 状态长期停留

**问题**：完成专注学习后，宠物一直停留在 `success` 状态，不会自动回到 `idle`。

**原因**：V0 将 `completed` 视为稳定 Base State，没有配置生命周期。

**修复**：

- 为 `success` 添加 `lifecycle: 'transient'`。
- 在 `usePetBehavior` 中支持 Transient Event 自动恢复当前最新 Base State。
- 将 `completed` 也作为 transient 处理，持续 5 秒后恢复。

### 9.3 重复事件无法触发

**问题**：完成第一个任务后，宠物反馈成功；完成第二个任务后，宠物不再反馈。

**原因**：V0 `usePetBehavior` 使用一次性 `triggeredRef`，事件触发后无法再次触发。

**修复**：

- 添加 `repeatable: boolean` 配置。
- 添加 `getIdentity` 识别每次触发。
- 记录 `lastIdentityRef` 和 `cooldownUntilRef`，支持相同事件多次触发。

### 9.4 类型设计导致必须修改 Core

**问题**：`PetWidget` 和 `usePetBehavior` 的泛型与 `PetAppConfig` 不完全匹配，导致必须为 Dashboard 具体化类型。

**修复**：

- `PetAppConfig<TAppStatus extends string>` 明确约束。
- `PetWidget<TAppStatus extends string>` 保持一致。
- `usePetBehavior<TAppStatus extends string>` 保持一致。
- 在 Adapter 中明确使用 `PetAppConfig<DashboardPetStatus>` 和 `PetWidget<DashboardPetStatus>`。
- 如果仍不匹配，优先调整 Adapter 类型，而不是修改 Core。

### 9.5 拖拽边界使用固定尺寸

**问题**：`usePetPosition` 使用固定 `PET_SIZE = 128`，实际宠物高度约 150px，移动端可能贴底。

**修复**：`usePetPosition` 接收 `elementRef`，使用 `getBoundingClientRect()` 获取真实尺寸。

### 9.6 process_sprites.py 路径硬编码

**问题**：脚本依赖 `.skills/app-pet-agent/...` 硬编码路径。

**修复**：使用 `--config` 和 `--output-dir` 参数化。

## 10. 最终效果

- 宠物基于用户上传的橘猫参考图生成卡通形象。
- 完成学习、完成任务、喝水记录时宠物播放 success 动画并鼓励用户。
- 喝水提醒弹窗出现时宠物切换到 remind 状态。
- 所有临时事件结束后自动恢复当前 Base State。
- 宠物可拖拽、点击气泡、位置记忆。
