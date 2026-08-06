# Sprite Geometry Contract

V2 强制统一每个宠物 run 的几何规范。参考 hatch-pet 的 deterministic normalization 思路，不再只依赖生图 prompt 保证角色大小一致，而是通过后处理和 QA 约束强制统一。

## 1. 核心目标

同一个宠物的所有视觉状态必须满足：

- **统一 frame canvas**：所有状态单帧尺寸相同。
- **统一 visual scale**：所有状态使用同一套 scale，不因动作不同而缩放角色。
- **统一 anchor**：默认使用 `bottom-center` 作为 anchor。
- **角色主体视觉大小一致**：不同状态间角色不能突然变大或变小。
- **起始/结束静态姿势对齐 canonical character**：idle、working 等循环状态的每一帧都应尽量接近 canonical anchor；success 等 transient 状态的第一帧和最后一帧应接近 canonical anchor 或稳定结束姿势。

## 2. 不要求的项目

- **Sprite Sheet 总尺寸**：不同状态帧数不同，总宽度可以不同。
- **局部动作**：允许抬手、跳跃、眨眼等局部姿态变化。
- **动画离开 baseline**：success 庆祝可以短暂离开 baseline，但动画完成后应回到稳定姿势。

## 3. Canonical Frame Specification

每个宠物 run 在处理前必须先确定 `canonical frame specification`（以下数值为示例，非默认值）：

```json
{
  "frameWidth": 792,
  "frameHeight": 903,
  "anchor": "bottom-center",
  "anchorX": 396,
  "anchorY": 903,
  "bottomOffset": 40,
  "canonicalScale": 1.0,
  "canonicalBodyHeight": 720
}
```

该规范由 `process_sprites.py` 在第一次处理时自动计算并写入 `pet-sprites.json` 的 `canonical` 字段。

## 4. 共享 Scale 与 Anchor

### 4.1 禁止 fit-to-frame

V1 脚本中按帧独立裁剪并统一画布的方式可能导致 size popping。V2 改为：

1. 读取所有状态的源 Sprite Sheet。
2. 提取每一帧的非透明 bounding box。
3. 计算所有帧中**最大的**主体宽度和高度。
4. 以 canonical character 的主体高度为基准，确定统一的 `canonicalScale`。
5. 所有帧按统一 scale 缩放，然后放置到底部中心 anchor 位置。
6. 不允许因为某一帧动作更宽而自动缩小整个人物。

### 4.2 Bottom-Center Anchor

- 每个 frame 的 `anchorX = frameWidth / 2`。
- 每个 frame 的 `anchorY = frameHeight - bottomOffset`。
- 角色主体底部应贴近 `anchorY`，但允许因动作需要短暂离开。

### 4.3 保持视觉大小

- 以 `canonicalBodyHeight` 作为基准，所有状态的主体高度差异应小于 5%。
- 如果某个状态的主体高度与基准差异超过 10%，则视为 blocker。

### 4.4 Canonical Silhouette Preservation（V2.1）

除了整体 bounding box 之外，还必须尽量保持角色的**标志性轮廓和身体比例**。

对于具有明显角色特征的宠物（长耳朵、帽子、发型、尾巴、翅膀、角、固定服装、标志性头饰等），跨状态生成时必须保持这些特征的：

- 相对长度 / 相对宽度
- 与头部 / 身体的比例
- 固定位置
- 视觉重量

**禁止出现**：

- 某状态耳朵 / 尾巴 / 翅膀突然明显变短或变小
- 头部大小变化
- 帽子或发型比例漂移
- 尾巴大小差异明显
- 因为增加道具而整体缩小人物
- 某状态变成不同头身比
- 同一角色在不同状态看起来像不同版本

> 即使自动 geometry 指标（bbox / scale）通过，若人眼可明显察觉 identity drift，仍判定该状态失败（见 Character Identity QA）。

### 4.5 道具不能控制人物 Scale（V2.1）

working、success 等状态可能出现的书、笔、电脑、文件等小道具属于 **secondary prop**。

统一原则：

- **先锁定角色本体的 canonical scale，再容纳道具。**
- 不得为了把道具完整塞进画布而缩小角色本体。
- 如果道具过大：**优先缩小或简化道具，而不是缩小人物。**
- 禁止默认加入大桌子、大椅子、大背景场景，除非用户明确要求。

道具是次要元素，角色本体比例优先级最高。

## 5. 输出规范

处理后的每个状态 PNG：

```
总宽度 = frameCount * frameWidth
总高度 = frameHeight
```

`pet-sprites.json` 应包含：

```json
{
  "canonical": {
    "frameWidth": 792,
    "frameHeight": 903,
    "anchor": "bottom-center",
    "bottomOffset": 40,
    "canonicalBodyHeight": 720,
    "canonicalScale": 1.0
  },
  "idle": {
    "src": "/images/pet/idle.png",
    "frameCount": 4,
    "frameWidth": 792,
    "frameHeight": 903,
    "fps": 4,
    "loop": true
  }
}
```

## 6. 失败处理

| 问题 | 处理方式 |
| --- | --- |
| 单个状态几何 QA 失败 | 只修复该状态，不无理由重做全部素材 |
| 源素材比例差异过大 | 只重新生成失败状态 |
| 后处理造成跨帧抖动 | 调整脚本参数，只重新处理该状态 |
| 角色主体被裁切 | 扩大 frame canvas 或重新生成 |

## 7. 几何 QA 指标

后处理脚本必须记录并输出：

- 每帧非透明 bounding box
- 每帧主体宽度、高度
- 每帧 bottom anchor 位置
- 每帧 centerX
- 相邻帧主体尺寸变化率
- 不同状态基准帧之间的主体尺寸变化率

这些数据用于自动化检测 blocker。
