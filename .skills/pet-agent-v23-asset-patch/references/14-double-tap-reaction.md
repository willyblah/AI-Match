# 双击 Reaction 完整规范（V2.2）

## 1. 设计目标

V2.2 将双击从「通用轻量动画」升级为「角色性格驱动的导视觉反馈」，同时保持系统一致性。

## 2. 核心原则

- 双击不改变业务状态、不移动宠物最终位置、不影响 Sprite 循环。
- 双击实现方式由宠物性格决定，不是所有宠物共用固定模板。
- 禁止使用 emoji 或可读文字符作为粒子。
- 必须提供 `prefers-reduced-motion` 降级。
- 边界参数为指导范围，由平台视觉 QA 决定。

## 3. 宠物性格类型

```typescript
export type PetPersonality = {
  archetype: 'calm' | 'playful' | 'shy' | 'proud' | 'focused' | 'warm';
  energy: 'low' | 'medium' | 'high';
  warmth: 'reserved' | 'balanced' | 'caring';
  doubleTap: 'sway' | 'hop' | 'peek' | 'chin-up' | 'blink' | 'nuzzle';
  bubbleStyle: 'quiet' | 'teasing' | 'concise' | 'encouraging';
};
```

### 性格到 doubleTap 方向的推荐映射

| archetype | 推荐 doubleTap | 默认实现模式 |
|---|---|---|
| calm | sway | CSS compact |
| playful | hop | CSS compact/expressive |
| shy | peek | CSS 或 double-tap sprite |
| proud | chin-up | CSS 或 double-tap sprite |
| focused | blink | CSS compact |
| warm | nuzzle | CSS compact/expressive |

## 4. 三种实现模式

### CSS Compact（默认）

- 时长：450–700ms
- 特征：轻微弹性感，不带粒子
- 适合：大多数宠物，尤其是 calm / focused / energy:low

### CSS Expressive（用户明确启用）

- 时长：600–800ms
- 特征：可选 CSS 几何粒子（圆、菱形、线段），颜色取自应用品牌配色
- 适合：playful / proud + energy:high
- 必须经用户在确认单中明确同意

### double-tap Sprite Row（按需生成）

- 用于 CSS 无法表达局部姿势或面部变化的情况
- 经用户确认后执行，不计入默认 4 个业务状态
- 必须通过几何 QA 和 Character Identity QA

## 5. 粒子规范

- 禁止使用 emoji 、文字符号、箭头、星星等可读图形。
- 允许使用 CSS 几何图形：圆、菱形、小方块、短线段。
- 颜色应取自应用品牌配色，不使用默认红绿等常规状态色。
- 粒子数量由平台决定，一般建议 4–8 颗。
- 粒子动画应与主角色动画同步结束。

## 6. Cooldown 和节流

- 双击 cooldown 为 900ms。
- 冷却期内忽略新输入，不排队，不叠加。
- 可选极短本地反馈（100–150ms）表示已感知。
- 冷却期结束后，下一次双击正常触发完整 reaction。

## 7. 边界参数指导范围

- scale 幅度、位移像素值、粒子尺寸不是所有宠物的硬性要求。
- 由平台根据宠物实际尺寸、容器边界和应用布局自行判断安全值。
- compact 模式建议幅度较小；expressive 模式允许更明显动感，上限由视觉 QA 结果决定。
- 必须通过视觉 QA 验证不遮挡、不越界。

## 8. 降级与可访问性

- 必须使用 `prefers-reduced-motion` 媒体查询。
- 当用户偏好减少动画时，expressive 退回 compact 级别的微缩放，粒子隐藏。
- 应保留宠物存在感，但不过度刺激。

## 9. QA 检查项

- [ ] 双击不打开气泡、不改变业务状态、不移动位置
- [ ] 双击不影响当前循环播放的 Sprite
- [ ] 冷却期内双击不会叠加完整动画
- [ ] 粒子不含 emoji 或可读文字符
- [ ] 实际尺寸不遮挡、不越界
- [ ] `prefers-reduced-motion` 下动画降级，粒子隐藏
- [ ] 各状态下角色身份一致性保持

## 10. 向后兼容

旧配置 `style: 'wiggle' | 'scale' | 'shake' | 'bounce'` 可兼容映射为 **compact 模式** 的等效动画（`wiggle→sway`、`scale→chin-up`、`shake→nuzzle`、`bounce→hop`），**不能成为新项目默认值**，也**不能自动映射为 expressive 模式**。新项目必须由 `PetPersonality.doubleTap` 驱动，expressive 与 sprite 模式需用户在确认单中明确选择。

兼容映射时：
- 旧 `style` 仅决定 `profile`（对应 compact 动画名）。
- `mode` 默认强制为 `compact`。
- 若旧配置同时存在 `mode: 'expressive'` 或 `mode: 'sprite'`，必须重新走确认单，由用户明确同意。
