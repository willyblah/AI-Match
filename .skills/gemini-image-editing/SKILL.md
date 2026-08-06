---
name: gemini-image-editing
description: 基于 Gemini 模型的 AI 图片生成与编辑，支持文本指令驱动背景替换、元素修改、风格调整，返回 Base64 图片。适合应用内高频图片生产场景。
license: MIT
---

## 能力概述

调用 Google Gemini 多模态模型对图片进行 AI 驱动的智能编辑，支持通过中文文本指令实现背景替换、元素修改、风格调整等操作，返回 Base64 编码的 PNG 图片及 Token 消耗统计。

| 属性 | 值 |
|------|-----|
| Endpoint | `POST https://app-dvtmyuucfs3l-api-o9wN0AExZQ8a-gateway.appmiaoda.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent` |
| Content-Type | `application/json` |
| 认证模式 | `platform_managed`（密钥由平台注入，读取 `INTEGRATIONS_API_KEY`） |
| 响应格式 | JSON，图片以 Base64 编码内嵌于 `candidates[].content.parts[].inlineData.data` |
| 支持平台 | Web、MiniProgram |

**平台差异概览：**

| 平台 | Edge Function 返回 | 前端获取图片方式 |
|------|-------------------|----------------|
| Web | JSON（含 Base64） | 解析 JSON，构造 `data:image/png;base64,...` URI 或用 Blob 渲染 |
| MiniProgram | JSON（含 Base64） | 解析 JSON，写临时文件后用 `<image>` 组件展示 |

详细参数说明、代码示例及两平台完整实现见 [references/gemini-image-edit-api.md](references/gemini-image-edit-api.md)。

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成 Base64 编码、请求和解码保存代码。

```bash
python3 <skill-path>/scripts/generate_image_edit.py \
  --input /path/to/source.jpg \
  --instruction "把背景替换为海边日落，保持主体不变" \
  --output /path/to/edited.png
```

**单条命令限制：每次 Bash 工具执行的 `command` 中只能包含 1 个 `generate_image_edit.py` 调用。** 如果用户需要编辑多张图片，必须拆成多次 Bash 工具调用，每次单独执行一条 `generate_image_edit.py ... --output <不同文件>` 命令；禁止在同一条命令里用 `&&`、`;` 或换行串联多个 `generate_image_edit.py`，避免单次执行耗时过长导致 Bash 工具超时。

脚本内部会读取本地图片、完成 Base64 编码、调用 Gemini 接口、从响应 `candidates[0].content.parts` 中提取 `inlineData.data` 并解码写入本地文件。成功时 stdout 只输出一行 JSON：

```json
{"file":"/path/to/edited.png","mimeType":"image/png","logText":null,"usage":{"promptTokenCount":0,"candidatesTokenCount":0,"totalTokenCount":0}}
```

> **注意**：Base64 图片数据绝不进入模型上下文，必须通过脚本完成文件读取、编码、解码和保存。

**脚本使用约束（生成图片时严格遵守）：**
- **禁止新增脚本**：只能执行 `scripts/` 目录中已有的脚本（`generate_image_edit.py`），不得为本次任务创建任何新的 Python/Shell/Node 脚本或临时封装。
- **禁止改名**：脚本文件名是固定的，不得重命名，也不得复制成其他文件名后再调用。
- **非必要不修改**：除非用户明确要求修复脚本 Bug，否则不得修改脚本源码；所有行为差异通过命令行参数控制。

---

## 生成后用法（应用内通过 Edge Function 调用）

前端将图片 Base64 和编辑指令发送给 Edge Function，Edge Function 注入平台密钥后转发至上游，将 Base64 图片 JSON 原路返回给前端。

Web 和 MiniProgram 的 Edge Function 逻辑相同（均返回 JSON），前端处理图片的方式略有不同：
- **Web**：直接用 Base64 构造 `<img>` 的 `src`，或转 Blob 展示。
- **MiniProgram**：需写入临时文件后用 `<image>` 组件展示（weapp 真机不支持 `data:` URI 直接渲染）。

完整 Edge Function 代码、前端调用代码及错误处理见 [references/gemini-image-edit-api.md](references/gemini-image-edit-api.md) 的「Edge Function 代码」和「前端调用代码」章节。
