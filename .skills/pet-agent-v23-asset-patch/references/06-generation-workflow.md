# 视觉生产流程

## 1. 参考 hatch-pet 的工作流思想

本 Skill 参考 hatch-pet 的 canonical-reference-first 生产流程，但丢弃其 Codex 专属实现（8×9 atlas、192×208 cell、九种固定状态）：

- 先生成统一角色基准。
- 后续所有动画状态都基于该基准生成。
- 每个状态单独生成、单独检查。
- 某一个状态失败，只重做该状态。
- 最终有统一的视觉 QA、几何 QA 和动画 QA。
- 角色身份、比例、画风、主体大小、底部 anchor、动画语义必须保持一致。

## 2. 生产步骤

> **正确顺序**：① 分析目标应用 → ② 输出制作确认单 → ③ 等待用户明确确认（必须回复“确认”“开始”“可以”等肯定词） → ④ 调用「图片生成与编辑（超级版）」Skill 生成 canonical base → ⑤ 继续调用「图片生成与编辑（超级版）」Skill，以 canonical base 为唯一身份参考生成各状态 Sprite Sheet → ⑥ 素材处理、透明背景与统一几何规范化 → ⑦ geometry QA / contact sheet / motion preview / Character Identity QA / Cross-State QA / Application Visual Integration QA → ⑧ 正式资产通过 QA 后才接入代码 → ⑨ lint / type-check / build / 应用内预览。
>
> **硬性规则**：
> - 未获得用户明确确认前，禁止调用任何图片生成能力、生成 canonical base、生成 Sprite Sheet 或修改代码。
> - 正式宠物素材必须来自「图片生成与编辑（超级版）」Skill，禁止用 SVG、CSS、Emoji、图标、纯色圆点或手写代码制作临时宠物。
> - 图片生成失败时，优先重试、修正提示词或暂停并报告；不得自动降级为 SVG/CSS/占位角色。

### Step 1: 调用「图片生成与编辑（超级版）」生成角色基准

**前提**：已通过《应用宠物制作确认单》获得用户明确确认。

**输入**：用户参考图或文字描述 + Application Visual System（应用画风参考）。

**输出**：`tasks/canonical-base-pet.png`（或 `public/images/pet/canonical-base-pet.png`）。

**操作**：

1. 调用秒哒平台提供的「图片生成与编辑（超级版）」Skill。
2. 使用该 Skill 生成图片：
   - 文生图：用户只有文字描述时，使用纯文本提示词。
   - 图生图：用户上传参考图时，传入参考图，提示词要求角色形象卡通化/风格化，并保留参考图身份特征。
   - 提示词必须同时包含：角色身份、稳定姿态、应用画风继承、纯色/透明背景、高质量。
3. 生成成功后，将 Base64 解码结果保存到本地，文件名不得覆盖原图（图生图使用 `_v2` 等后缀）。

**要求**：

- 角色形象清晰、稳定。
- 通常采用角色最自然的姿态（如 idle 坐姿或正面站姿）。
- 背景简洁，便于后续去背景。
- 作为所有后续状态的唯一身份参考。
- **必须先有 canonical base**，禁止跳过它直接分别生成互不一致的状态。
- canonical base 是内部生产与 QA 基准，**不是新的人工阻断点**：用户确认制作方案后自动继续，不要求二次确认。
- **失败处理**：若生成失败或结果不符合已确认方向，重试、修正提示词或暂停报告用户；禁止用 SVG/CSS/占位图替代。

### Step 2: 确定状态集合

根据应用业务状态，确定需要生成的宠物视觉状态：

- 默认：`idle`、`working`、`success`、`remind`
- 可调整：如 `idle / thinking / success / failed`

### Step 3: 调用「图片生成与编辑（超级版）」逐个生成 Sprite Sheet

对每个状态生成一张 1×N 横向 Sprite Sheet：

```
<state>-spritesheet.png
```

**生成顺序**：

1. `idle-spritesheet.png`
2. `working-spritesheet.png`
3. `success-spritesheet.png`
4. `remind-spritesheet.png`

**操作**：

1. 每次调用秒哒平台提供的「图片生成与编辑（超级版）」Skill 生成一张状态源图。
2. 图生图时，必须传入已生成的 `canonical-base-pet.png`，让后续状态以 canonical base 为唯一身份参考。
3. 每次生成保存到 `tasks/<state>-spritesheet.png`，禁止覆盖原图。

**每个状态的提示词必须包含**：

- 角色基准引用（唯一身份参考，强制传入 canonical-base-pet.png）
- 应用画风参考（visual style，要求像应用原有插画系统中的角色）
- 状态语义说明
- 每帧动作描述
- 横向 1×N 布局要求
- 每帧等宽、角色居中、无文字/水印
- 简洁背景色（便于去背景）
- 角色主体大小与 canonical reference 一致
- 角色底部 anchor 与 canonical reference 对齐
- **禁止要求**：不得让角色为了道具或横向布局而缩小，不得加入大桌子/大椅子/大背景场景（除非用户明确要求）。

**失败处理**：单个状态失败只重试该状态；若反复失败，暂停并报告，禁止用占位图/SVG/CSS 填充该状态。

### Step 4: 处理每张 Sprite Sheet

使用参数化脚本 `scripts/process_sprites.py`：

```bash
python3 scripts/process_sprites.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet
```

处理步骤：

1. 自动采样背景色并去除背景。
2. 羽化边缘。
3. 按内容列切帧，识别帧数。
4. 提取每帧非透明 bounding box。
5. 计算统一的 `canonical frame spec`（共享 scale、bottom-center anchor）。
6. 所有帧按统一 scale 和 anchor 放置到统一画布。
7. 输出透明 PNG 到 `--output-dir`。
8. 生成 `pet-sprites.json`，包含 `canonical` 字段。

### Step 5: 几何 QA 与可视化

```bash
python3 scripts/geometry_qa.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet \
  --report /path/to/geometry-report.json

python3 scripts/generate_contact_sheet.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet

python3 scripts/generate_preview.py \
  --config /path/to/sprites-config.json \
  --output-dir /path/to/public/images/pet
```

输出：

- `geometry-report.json`：几何检测报告
- `contact-sheet.png`：跨状态 contact sheet
- `motion-preview.png`：每个状态的动画预览

### Step 6: 生成资源配置

文件名统一为 `pet-sprites.json`（不要写成 `pet.json`）。以下数值为示例：

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
  "idle": { "..." : "同结构" },
  "working": { "..." : "同结构" },
  "success": { "..." : "同结构" },
  "remind": { "..." : "同结构" }
}
```

### Step 7: 应用接入（仅正式资产通过 QA 后）

将通用组件模板拷贝到目标项目，注入应用专属配置，挂载到主页面。**只有正式资产通过全部 QA 后才接入代码。**

### Step 8: 视觉与动画 QA

按 `references/07-qa-checklist.md`、`references/12-cross-state-qa.md` 和 `references/15-application-visual-integration-qa.md` 执行检查，并在真实应用页面预览中验证视觉集成。

## 3. 失败与重试规则

| 失败场景 | 处理方式 |
| --- | --- |
| canonical base 生成失败 | 重新生成或修复；无法得到合格 canonical base 时**停止接入并报告**，不用 SVG/CSS/占位角色 |
| 单个状态生成失败 | **仅重试该状态**，不影响已通过的其他状态 |
| 帧数识别失败 | 检查提示词是否清晰，重试或手动切帧 |
| 背景去除不净 | 调整 process_sprites.py 参数或重试生成 |
| 角色一致性差 | 重新检查提示词中 canonical reference 是否被正确使用 |
| 单个状态几何 QA 失败 | 只修复该状态，重新处理或重新生成该状态 |
| 跨状态 size popping | 优先重新 normalize，无效则重新生成偏差状态 |
| Sprite 处理失败 | 检查帧数/背景/切帧/canonical geometry，修复处理流程；仍失败则停止动画接入并报告，**不切 SVG/CSS 宠物** |

详见 `references/08-fallback-rules.md`。

## 4. 生成顺序图

```text
确定角色基准 → 生成 idle → 生成 working → 生成 success → 生成 remind
     ↓              ↓            ↓              ↓              ↓
  处理素材      处理素材     处理素材      处理素材      处理素材
     ↓              ↓            ↓              ↓              ↓
  几何 QA      几何 QA       几何 QA       几何 QA       几何 QA
     ↓              ↓            ↓              ↓              ↓
  生成配置      动画 QA      动画 QA       动画 QA       动画 QA
     ↓              ↓            ↓              ↓              ↓
  contact sheet + preview + cross-state QA
```

## 5. 一致性检查

每生成一个新状态，与 canonical reference 对比：

- 角色毛色/肤色是否一致
- 角色体型比例是否一致
- 角色面部特征是否一致
- 角色姿态是否自然
- 画风是否一致
- 主体高度是否与 canonical reference 接近
- 底部 anchor 是否对齐

不一致时，优先修改提示词，重新生成该状态。如果通过后处理可以解决，优先调整 `process_sprites.py` 参数。

## 6. 资源路径

目标项目中的默认输出路径：

```
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

`*-spritesheet.png` 源文件可保留在 `tasks/` 目录作为备份，但不需要打包到目标应用发布。
