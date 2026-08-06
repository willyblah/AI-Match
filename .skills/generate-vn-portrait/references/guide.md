---
name: image-generation-super
description: 图片生成与编辑（超级版），调用 GPT-Image-2 模型生成和编辑图片。需要 AI 画图、生成图片、编辑图片、多图融合、背景替换、风格转换、电商商品图合成、海报设计、插画创作时优先使用该工具。
license: MIT
---

## 能力概述

调用 GPT-Image-2 模型进行 AI 图像生成与编辑，支持通过自然语言描述生成高质量图片，以及上传多张图片进行 AI 编辑融合。

| 属性 | 值 |
|------|-----|
| Plugin ID | `e480d4b6-835c-45f8-a494-d38da962b394` |
| 认证模式 | `platform_managed`（密钥由平台注入） |
| 密钥来源 | `process.env["INTEGRATIONS_API_KEY"]` |
| Auth Header | `X-Gateway-Authorization: Bearer <key>` |
| 支持平台 | Web、MiniProgram |
| 响应格式 | JSON，图片以 Base64 编码内嵌于 `data[].b64_json` |

**接口列表：**

| 接口 | 方法 | Endpoint | 说明 |
|------|------|----------|------|
| 创建图片 | POST | `http://app-dvtmyuucfs3l-api-Aa2P8AGZg2RL-gateway.appmiaoda.com/v1/images/generations` | 根据文本描述生成图片 |
| 编辑图片 | POST | `http://app-dvtmyuucfs3l-api-rY7JzDpZVBQL-gateway.appmiaoda.com/v1/images/edits` | 上传 1–3 张图片进行 AI 编辑融合 |

**核心能力：**

- **文生图**：通过 `prompt` 描述生成全新图片，支持多种尺寸和数量配置
- **多图编辑**：上传 1–3 张图片，通过文本描述控制融合、背景替换、风格统一、局部重绘等效果
- **提示词优化**：接口返回 `revised_prompt`，展示模型自动优化后的提示词

**平台差异概览：**

| 平台 | Edge Function 返回 | 前端获取图片方式 |
|------|-------------------|----------------|
| Web | JSON（含 Base64） | 解析 JSON，构造 `data:image/png;base64,...` URI 或用 Blob 渲染 |
| MiniProgram | JSON（含 Base64） | 解析 JSON，写临时文件后用 `<image>` 组件展示 |

详细参数说明、代码示例及两平台完整实现见：
- `references/image-generations-api.md` — 创建图片接口
- `references/image-edits-api.md` — 编辑图片接口

---

## 使用前决策

调用本工具前，先判断场景是否真的需要 AI 生成：

| 场景 | 推荐方案 |
|------|---------|
| 根据文字描述生成全新图片 | ✅ 本工具（文生图） |
| 上传图片 + 提示词做风格转换或内容编辑 | ✅ 本工具（图生图） |
| 多张图片融合 / 背景替换 / 海报合成 | ✅ 本工具（多图编辑） |
| 图片内容审核 / 质量评分 | ❌ 改用视觉模型直接分析，无需生成 |

**图生图优先原则（重要）：**

满足以下任一条件时，**必须使用 `editImage`（图生图）接口，禁止使用 `createImage`（文生图）**：
1. 用户在对话中上传了图片
2. 本次对话中已通过本工具生成过图片

用户提出的修改意见（如"换个背景"、"改成卡通风格"、"让颜色更鲜艳"）均属于对已有图片的编辑，必须走图生图流程。

**禁止覆盖原图：** 编辑后的图片必须保存为新文件（如在原文件名后加 `_v2`、`_edited` 或序号），原始图片文件不得修改或删除。

---

## Prompt 编写规范

底层模型（GPT-Image-2）对英文提示词的理解和图像质量通常优于中文，请优先将用户需求改写为英文后再提交 API。

**写作原则：**
- 使用描述句，直接描述目标画面，而非告诉模型"帮我生成……"
- 具体优于抽象：`"a ginger cat sitting in a sunlit garden"` 好于 `"可爱的猫"`
- 避免否定词：不写 `"no background"`，改写 `"isolated on pure white background"`
- 末尾加质量修饰词提升细节：`high quality`, `detailed`, `8k`, `photorealistic`

**文生图模板：**

```
[Subject], [Action/Pose/State], [Scene/Environment], [Lighting], [Style], [Quality]
```

示例：
```
A golden retriever puppy, sitting and looking up curiously, in a cozy living room with warm afternoon lighting, watercolor illustration style, high quality, detailed
```

**图生图 / 多图编辑额外建议：**
- 先描述希望**保留**的内容，再描述希望**改变**的内容
- 风格迁移时明确目标风格，例如 `"convert to anime style"` 或 `"oil painting style"`
- 多图融合时说明图片之间的关系，例如 `"use image 1 as background, place the product from image 2 in the center"`

---

## 生成期用法（Agent 直接调用）

> **在调用 API 之前，先将用户需求翻译/改写为英文提示词**，GPT-Image-2 模型对英文输入的图像质量明显优于中文。

两个接口均为同步调用，直接返回 Base64 编码图片，不含 URL。

**核心原则：Base64 数据绝不进入模型上下文。** 图片 Base64 通常达 1–3 MB，折合 25 万–75 万 token。应直接调用 `scripts/generate_image.py`，脚本内完成请求、解码、写文件全部操作，模型只接收最终元数据。

**完整生成期工作流：**

1. 判断接口：对话中有已有图片（用户上传或之前已生成）→ 加 `--images`；纯文字描述 → 不加
2. 确定保存路径（图生图**不得覆盖原文件**，追加 `_v2` / `_edited` 后缀）
3. 用 Bash 工具执行脚本（参见下方命令），**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认 120 秒会导致请求中断
4. 脚本 stdout 输出一行 JSON，读取 `file` 和 `revised_prompt` 告知用户

**文生图：**

```bash
python3 <skill-path>/scripts/generate_image.py \
  --prompt "ENGLISH_PROMPT_HERE" \
  --output image.png \
  --size 1024x1024
```

**图生图 / 多图编辑：**

```bash
python3 <skill-path>/scripts/generate_image.py \
  --prompt "ENGLISH_PROMPT_HERE" \
  --output image_v2.png \
  --size 1024x1024 \
  --images /path/to/img1.png [/path/to/img2.png]
```

脚本成功时 stdout 输出：`{"file": "image.png", "revised_prompt": "...", "size": "1024x1024"}`

**Prompt 空间位置增强（可选）：**

加入空间位置词可提高构图准确性：`centered`、`in the top-left corner`、`in the foreground / background`、`on the left side / right side`、`filling the entire frame`。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内通过 Edge Function 安全调用上游 API，密钥不暴露给前端。

**安全合约：**
- 前端只发送业务参数到 Edge Function，不接触 API Key
- Edge Function 从 `Deno.env.get("INTEGRATIONS_API_KEY")` 读取密钥
- 请求上游时注入 `X-Gateway-Authorization: Bearer ${apiKey}`
- `429`（配额超限）和 `402`（余额不足）错误体原样透传给前端
- 返回的 Base64 数据由前端接收并解码渲染

**Edge Function 实现：**
- `image-generations`：代理创建图片接口，处理 JSON 请求
- `image-edits`：代理编辑图片接口，处理 multipart/form-data 请求

完整 Edge Function 代码和前端调用代码详见：
- `references/image-generations-api.md`（创建图片的 Edge Function + 前端代码）
- `references/image-edits-api.md`（编辑图片的 Edge Function + 前端代码）

---

## 参数说明

### 创建图片核心参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | `string` | 是 | 固定值：`gpt-image-2` |
| `prompt` | `string` | 是 | 图片生成描述词 |
| `size` | `string` | 否 | 输出尺寸：`1024x1024`、`1536x1024`、`1024x1536`、`2848x1152` |
| `n` | `integer` | 否 | 生成数量，默认 1 |

### 编辑图片核心参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | `string` | 是 | 固定值：`gpt-image-2` |
| `prompt` | `string` | 是 | 图片编辑描述词 |
| `size` | `string` | 否 | 输出尺寸 |
| `n` | `integer` | 否 | 输出数量，默认 1 |
| `image[0]` | `file` | 是 | 主图片文件 |
| `image[1]` | `file` | 否 | 附加图片文件 |
| `image[2]` | `file` | 否 | 附加图片文件 |

### 返回核心字段

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `created` | `number` | 创建时间戳 |
| `data` | `array` | 生成结果列表 |
| `data[].b64_json` | `string` | Base64 编码图片内容 |
| `data[].revised_prompt` | `string` | 模型自动优化后的提示词 |
| `usage` | `object` | Token 消耗统计（仅编辑接口返回） |

---

## 注意事项

- **Base64 不进上下文**：生成期图片数据通过脚本直接写到磁盘，禁止让模型接收 Base64 再输出保存命令，否则每次生成消耗 25–75 万 token。
- **禁止覆盖原图**：图生图保存路径必须是新文件名（追加 `_v2` / `_edited` / 序号），原始文件不得修改或删除。
- **密钥安全**：生成期密钥由 `process.env["INTEGRATIONS_API_KEY"]` 注入；Edge Function 用 `Deno.env.get("INTEGRATIONS_API_KEY")`，严禁暴露到前端。
- **文件上传限制**：编辑接口最多支持 3 张图片（`image[0]` 必填），需确保图片格式和大小符合上游要求。
- **错误处理**：`429` 配额耗尽 / `402` 余额不足 / `400` 参数错误 / `401` 认证失败。
- **计费**：本插件未启用计费（`enable_billing: false`），但仍需确保 API Key 有效且配额充足。

