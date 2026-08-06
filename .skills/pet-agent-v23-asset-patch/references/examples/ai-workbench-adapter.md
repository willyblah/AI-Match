# AI 生成工作台接入案例

## 1. 应用信息

- **应用类型**：AI 生成工作台
- **主页面**：假设为 `src/pages/GenerationPage.tsx`
- **状态 Hook**：假设为 `src/hooks/useAIGenerator.ts`
- **业务状态类型**：`GenerationStatus`

## 2. 业务状态枚举

```typescript
export type GenerationStatus =
  | 'waiting_input'
  | 'generating'
  | 'success'
  | 'failed';
```

## 3. 业务状态到宠物视觉状态映射

| 业务状态 | 宠物视觉状态 | 说明 |
| --- | --- | --- |
| waiting_input | idle | 等待用户输入 |
| generating | working | 正在生成 |
| success | success | 生成成功 |
| failed | remind | 失败提醒，可重试 |

## 4. 推荐临时事件

| 事件 ID | 触发条件 | 覆盖状态 | 持续 | 冷却 |
| --- | --- | --- | --- | --- |
| generation_timeout | status === 'generating' && elapsedSeconds >= 30 | remind | 5 秒 | 30 秒 |

## 5. 气泡配置

| 业务状态 | 气泡话术 | 气泡按钮 | 调用函数 |
| --- | --- | --- | --- |
| waiting_input | 准备好灵感了吗？输入提示词即可开始。 | 聚焦输入 | focusInput |
| generating | 正在全力生成中，请稍候… | 取消生成 | cancelGeneration |
| success | 生成完成！满意这次的效果吗？ | 再生成一张 / 复制结果 | reGenerate / copyResult |
| failed | 生成遇到了一点小问题，要重试吗？ | 重试 / 查看错误 | reGenerate / viewError |
| timeout 事件 | 这次生成似乎有点慢，要重新试试吗？ | 重新生成 / 继续等待 | reGenerate / dismissEvent |

## 6. 配置示例

```typescript
const aiWorkbenchConfig: PetAppConfig<GenerationStatus> = {
  deriveBaseState: (status) => {
    if (status === 'generating') return 'working';
    if (status === 'success') return 'success';
    if (status === 'failed') return 'remind';
    return 'idle';
  },
  sharedStates: {
    idle: ['waiting_input'],
    working: ['generating'],
    success: ['success'],
    remind: ['failed'],
  },
  transientEvents: [
    {
      eventId: 'generation_timeout',
      targetPetState: 'remind',
      baseState: 'working',
      condition: (status, metrics) =>
        status === 'generating' && metrics.elapsedSeconds >= 30,
      durationMs: 5000,
      cooldownMs: 30 * 1000,
    },
  ],
  actions: {
    focusInput: 'focusInput',
    cancelGeneration: 'cancelGeneration',
    reGenerate: 'reGenerate',
    copyResult: 'copyResult',
    viewError: 'viewError',
  },
};
```

## 7. 接入说明

与番茄钟案例相同，通用组件直接复用，只需替换 `pet-config.ts` 和 `PetWidget` 的 props 绑定。
