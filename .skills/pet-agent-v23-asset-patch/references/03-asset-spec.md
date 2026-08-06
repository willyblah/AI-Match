# 宠物素材规范

## 1. Skill 强制规范

| 规范 | 说明 |
| --- | --- |
| 横向 1×N 排列 | 每帧等宽，从左到右排列 |
| 每帧等宽 | 源图总宽度必须能被 frameCount 整除 |
| 透明背景 | 处理后的 PNG 必须带透明通道，避免遮挡页面 |
| 角色基线稳定 | 同一状态内各帧角色大小、位置、姿态基线一致 |
| 状态间基线稳定 | 不同状态间角色比例、画风、主体大小、底部位置一致 |
| 统一单帧 canvas | 同一个 pet run 的所有状态 frameWidth/frameHeight 必须一致 |
| 统一 scale | 所有状态使用共享 scale，不因动作更宽而自动缩小角色 |
| 统一 anchor | 默认 bottom-center anchor |
| 配置真实 | `pet-sprites.json` 中记录真实的 `frameWidth`、`frameHeight`、`frameCount`、`fps`、`loop` 和 `canonical` 字段 |

> **单帧尺寸、帧数和 FPS 不是固定值**：由实际角色、动作语义和目标应用运行环境决定；同一个 pet run 内必须统一几何。

## 2. 历史尺寸示例（仅参考，非默认）

下表为某历史项目曾使用的素材参数，**只用于说明文件命名和目录结构，不构成默认值**。新项目不得直接套用这些尺寸。

| 状态 | 源文件 | 输出文件 | 帧数 | 源尺寸 | 处理后单帧 | 循环 |
| --- | --- | --- | --- | --- | --- | --- |
| idle | `tasks/idle-spritesheet.png` | `public/images/pet/idle.png` | 4 | 2848×1152 | 792×903 | 是 |
| working | `tasks/working-spritesheet.png` | `public/images/pet/working.png` | 4 | 2848×1152 | 792×903 | 是 |
| success | `tasks/success-spritesheet.png` | `public/images/pet/success.png` | 6 | 2848×1152 | 792×903 | 否 |
| remind | `tasks/remind-spritesheet.png` | `public/images/pet/remind.png` | 4 | 2848×1152 | 792×903 | 是 |

> ⚠️ `2848×1152`、`792×903`、帧数 4/6 等均为历史示例，**非默认推荐**。实际项目必须在生成流程中通过真实预览和 QA 确定尺寸。

## 3. Skill 可动态调整部分

| 项目 | 是否固定 | 说明 |
| --- | --- | --- |
| 单帧画布尺寸 | 一个 pet run 内统一 | 根据角色实际生成结果决定 |
| 总尺寸 | 动态 | 由帧数、单帧尺寸决定 |
| 帧数 | 动态 | 每个状态可独立设置 2–8 帧 |
| FPS | 动态 | 根据动画语义调整，建议 4–12 |
| 是否循环 | 动态 | 呼吸等循环，庆祝等单次 |
| 角色朝向 | 动态 | 坐姿/站姿/正面/侧面均可 |
| 画风 | 动态 | 写实、卡通、像素等均可 |

## 4. 生成流程

### 4.1 角色基准（必须，不可跳过）

1. 如果用户有参考图，使用参考图作为 `canonical reference`。
2. 如果用户只有文字描述，先生成一张 `canonical-base-pet.png`。
3. 角色基准应包含角色最清晰、最稳定的形象，通常是 idle 或正面站姿。
4. **必须先有 canonical base，再以其为唯一身份参考生成各状态**；禁止跳过 canonical base 直接分别生成互不一致的状态。
5. canonical base 是内部生产与 QA 基准，**不是新的默认人工阻断点**（见 `references/04-intake-protocol.md`）。

### 4.2 分状态生成

每个状态独立生成一张 1×N 横向 Sprite Sheet：

```
<state>-spritesheet.png
```

示例：

- `idle-spritesheet.png`
- `working-spritesheet.png`
- `success-spritesheet.png`
- `remind-spritesheet.png`

### 4.3 生成提示词要点

- 始终使用同一个 canonical reference 作为唯一身份参考。
- 明确指定角色身份、姿态、表情、画风。
- 明确指定每帧动作语义，避免歧义。
- 指定背景色（如 light off-white），便于后续去背景。
- 指定每帧等宽、角色居中、无文字/水印/网格线。
- 指定角色主体大小在跨状态间保持一致。
- 指定角色底部 anchor 尽量对齐 canonical reference。
- **继承目标应用画风**：将应用截图或现有插画作为“应用画风参考”传入，要求宠物像应用原有插画系统中本来就存在的角色（同一套色彩、描边、阴影、形状语言）。角色参考用于 identity，应用画风参考用于 visual style，两者分开标注；不复制其中的文字、UI 控件或完整场景，不将页面截图直接画入 Sprite Sheet。
- **V2.1：保持标志性轮廓**——明确要求保持耳朵/帽子/发型/尾巴/翅膀/角/服装等特征的相对长度、比例、位置与视觉重量，禁止跨状态漂移。
- **V2.1：道具为次要元素**——先锁定角色本体 canonical scale 再容纳道具；道具过大时优先缩小/简化道具而非缩小人物；禁止默认加入大桌子/大椅子/大背景场景（除非用户明确要求）。

### 4.4 素材处理与几何规范化

使用参数化脚本 `scripts/process_sprites.py`：

```bash
python3 scripts/process_sprites.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet
```

处理步骤：

1. 读取配置中的每张源图。
2. 自动采样背景色并去除背景。
3. 羽化边缘，避免白边。
4. 按内容列切帧，自动识别帧数。
5. 提取每帧非透明 bounding box。
6. 计算所有帧中最大的主体尺寸，确定统一 `canonical frame spec`。
7. 使用共享 scale 将所有帧统一到底部中心 anchor 位置。
8. 输出为透明 PNG：`idle.png`、`working.png`、`success.png`、`remind.png`。
9. 生成 `pet-sprites.json`，包含 `canonical` 字段。

### 4.5 几何 QA 脚本

```bash
python3 scripts/geometry_qa.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet \
  --report /path/to/geometry-report.json
```

输出：

- 每帧非透明 bounding box
- 每帧主体宽高、bottom anchor、centerX
- 相邻帧尺寸变化
- 跨状态基准帧尺寸变化
- blocker 列表

### 4.6 可视化输出

```bash
python3 scripts/generate_contact_sheet.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet

python3 scripts/generate_preview.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet
```

输出：

- `contact-sheet.png`：所有状态第一帧并排展示
- `motion-preview.png`：每个状态的动画预览

## 5. 资源配置文件

文件名统一为 `pet-sprites.json`（不要写成 `pet.json`）。以下数值为示例：

```json
{
  "canonical": {
    "frameWidth": 792,
    "frameHeight": 903,
    "anchor": "bottom-center",
    "anchorX": 396,
    "anchorY": 903,
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
  },
  "working": { "..." : "同结构" },
  "success": { "..." : "同结构" },
  "remind": { "..." : "同结构" }
}
```

## 6. 视觉 QA 检查项

- [ ] 角色身份在各状态保持一致
- [ ] 角色比例、画风、主体大小一致
- [ ] 宠物与目标应用视觉系统一致（见 `references/15-application-visual-integration-qa.md`）
- [ ] 角色底部基线对齐
- [ ] 背景已完全透明
- [ ] 无白边、锯齿、裁切
- [ ] 帧数、FPS、循环配置与动画语义匹配
- [ ] 循环动画无缝衔接
- [ ] 单次动画停留在最后一帧
- [ ] 同一状态内角色不发生整体位移
- [ ] 同一个 pet run 所有状态单帧尺寸一致
- [ ] 所有状态使用共享 scale
- [ ] 跨状态切换无明显 size popping / baseline jump / center shift

## 7. 失败处理

- 如果某个状态生成失败，**只重试该状态**。
- 如果某个状态无法生成，**不用静态占位图冒充**；必要状态仍失败则停止接入并报告（见 `references/08-fallback-rules.md`）。
- 如果某个状态几何 QA 失败，只修复该状态，不无理由重做全部素材。
- 如果源素材比例差异过大，只重新生成失败状态。
- 如果全部状态失败，停止接入宠物并告知用户。
