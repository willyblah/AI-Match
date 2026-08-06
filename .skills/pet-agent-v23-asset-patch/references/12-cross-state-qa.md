# Cross-State Registration QA

V2 在 V1 单状态 QA 基础上，增加跨状态 registration 检查。确保角色在不同状态之间切换时不会出现明显的跳动、缩放或漂移。

## 1. 检查状态组合

必须检查以下典型切换：

- `idle → working`
- `working → success`
- `working → failed / remind / attention`
- `transient → base state`

## 2. 检查维度

对每个切换组合，检查以下维度：

| 维度 | 说明 | 允许范围 |
| --- | --- | --- |
| size popping | 角色主体整体大小突然变化 | 高度变化 < 10% |
| baseline jump | 角色底部 anchor 位置明显跳动 | 纵向偏移 < 5% frameHeight |
| center shift | 角色水平中心明显偏移 | 横向偏移 < 5% frameWidth |
| silhouette scale mismatch | 角色轮廓比例不一致 | 宽高比变化 < 10% |
| identity drift | 角色毛色/肤色/服装/道具变化 | 必须人工检查 |
| cropping | 角色主体被裁切 | 不允许 |
| edge overflow | 角色超出 frame 边界 | 不允许 |

## 3. 自动化检测

`geometry_qa.py` 脚本通过 alpha 通道分析实现轻量检测：

1. 读取每个状态的 Sprite Sheet。
2. 提取每帧的非透明 bounding box。
3. 计算每个状态第一帧（或稳定帧）的几何中心、底部 anchor、主体宽高。
4. 计算相邻帧之间的变化率。
5. 计算不同状态基准帧之间的变化率。
6. 输出 JSON 报告。

### 检测指标

```json
{
  "idle": {
    "frames": [
      {
        "bbox": [120, 100, 600, 880],
        "width": 480,
        "height": 780,
        "centerX": 396,
        "bottomAnchor": 880,
        "anchorX": 396,
        "anchorY": 863
      }
    ],
    "bodyHeight": 780,
    "bodyWidth": 480,
    "baseline": 880,
    "centerX": 396
  }
}
```

## 4. Blocker 列表

出现以下情况时，该状态不得直接通过：

- 明显 size popping（主体高度变化 ≥ 10%）
- 明显 baseline jump（纵向偏移 ≥ 5% frameHeight）
- 跨状态整体比例明显变化（宽高比变化 ≥ 10%）
- 角色身份漂移（需要人工视觉 QA）
- 角色主体被裁切
- 某状态为了容纳动作导致人物本体明显缩小
- 后处理造成的跨帧抖动
- **V2.1 新增 blocker**（必须经过 Character Identity QA 后才能最终通过）：
  - 标志性轮廓明显变化（耳朵/帽子/发型/尾巴/翅膀/角等比例漂移）
  - 头身比例明显变化
  - 头饰 / 耳朵 / 发型比例漂移
  - 道具导致角色本体缩小
  - 同一角色在不同状态看起来像不同版本
  - 虽然 bbox 通过，但人眼可明显察觉 identity drift

## 5. 修复策略

| 问题 | 优先策略 |
| --- | --- |
| 单状态几何问题 | 调整 `process_sprites.py` 参数，重新处理该状态 |
| 源素材比例差异过大 | 只重新生成该状态 |
| 跨状态 size popping | 优先重新 normalize，若无效则重新生成偏差状态 |
| 角色身份漂移 | 重新生成该状态，加强 canonical reference 使用 |

## 6. 人工视觉 QA

自动化无法可靠判断以下项目时，Agent 必须做一次视觉检查：

- 角色身份（毛色、发型、服装、道具）
- 画风一致性
- 表情/眼神一致性
- 动画语义是否清晰
- 是否有明显的视觉异常

## 7. 输出物

每次素材准备完成后，应生成：

- `cross-state-geometry-report.json`：跨状态几何检测报告
- `contact-sheet.png`：所有状态第一帧并排展示
- `motion-preview.gif` 或 `motion-preview.png`：每个状态的动画预览

## 8. 验收标准

- 同一角色所有状态单帧尺寸一致。
- 所有状态使用共享 scale。
- baseline 基本一致。
- cross-state 切换无明显跳动。
- success 起始/结束与 canonical anchor 兼容。
- 不同 frameCount 状态仍使用相同单帧 canvas。
- 某一状态几何 QA 失败时只修复该状态。

## 9. Character Identity QA（V2.1）

在原有 Geometry QA 之外，增加一个明确的**人工视觉检查阶段**。每个状态的 contact sheet 必须比较：

- 脸型
- 头身比
- 标志性配饰
- 发型 / 耳朵 / 帽子
- 服装
- 配色
- 尾巴或其他突出结构
- 角色整体 silhouette

**判定规则**：如果角色的关键身份特征明显漂移，**即使自动 geometry 指标通过，也应判定该状态失败**，只重新生成失败状态。

contact sheet 应提供统一参考辅助（相同 canvas、相同 baseline、相同 center line、canonical character reference），方便一眼比较各状态是否发生角色比例漂移。
