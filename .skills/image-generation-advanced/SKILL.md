---
name: image-generation-advanced
description: 高级图片生成与编辑，支持文生图、图生图、多图合成，异步任务轮询。需要 AI 生成图片、对图片做内容编辑或风格转换时优先使用该工具。
license: MIT
---

## 能力概述

图片生成与编辑（高级版）提供高质量的图片生成与精细编辑能力，支持以下三种模式：

| 模式 | 说明 |
|------|------|
| 文生图 | 仅提供文字提示词，生成对应图片 |
| 图生图 | 上传一张图片 + 提示词，进行风格转换或编辑 |
| 多图生图 | 上传多张图片 + 提示词，智能合成 |

**两个接口（异步任务模型）：**

| 接口 | 方法 | Endpoint |
|------|------|----------|
| 提交任务 | POST | `https://app-dvtmyuucfs3l-api-ra5EZDjVKkXa-gateway.appmiaoda.com/image-generation/submit` |
| 查询状态 | POST/GET | `https://app-dvtmyuucfs3l-api-VaOwP2jDmAga-gateway.appmiaoda.com/image-generation/task` |

任务状态：`PENDING` → `PROCESSING` → `SUCCESS` / `FAILED`

完成后返回 `imageUrl`（CDN 链接，建议转存至 Supabase Storage 保持持久性）。

**平台差异：**

| 平台 | 查询接口调用方式 | 说明 |
|------|----------------|------|
| Web | POST body `{ taskId }` | 标准用法 |
| MiniProgram | GET 查询参数 `?taskId=...` | Miaoda 代理会丢弃小 POST body，改用 GET 参数 |
| App | POST body `{ taskId }` | 同 Web；图片上传需使用 `expo/fetch` + ArrayBuffer 方式转存至 Supabase Storage |

详见 `references/image-generation-api.md`。

---

## 使用前决策

调用本工具前，先判断场景是否真的需要 AI 生成：

| 场景 | 推荐方案 |
|------|---------|
| 根据文字描述生成全新图片 | ✅ 本工具（文生图） |
| 上传图片 + 提示词做风格转换或内容编辑 | ✅ 本工具（图生图） |
| 多张图片智能合成新图 | ✅ 本工具（多图生图） |
| 图片内容审核 / 质量评分 | ❌ 改用视觉模型直接分析，无需生成 |

---

## Prompt 编写规范

底层模型（Gemini Imagen 系列）**对英文提示词的输出质量明显优于中文**，请始终先将用户需求翻译/改写为英文后再提交 API。

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

**图生图额外建议：**
- 先描述希望**保留**的内容，再描述希望**改变**的内容
- 风格迁移时明确目标风格，例如 `"convert to anime style"` 或 `"oil painting style"`

---

## 生成期用法（Agent 直接调用）

适用于 Agent 脚本直接调用，密钥由平台注入。

> **在调用脚本之前，先将用户需求翻译/改写为英文提示词**，底层 Gemini Imagen 系列模型对英文输入的图像质量明显优于中文。

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

**文生图：**

```bash
python3 <skill-path>/scripts/generate_image_advanced.py --prompt "a ginger cat sitting in a sunlit garden, high quality, detailed" --output /path/to/output.png
```

**图生图 / 多图合成（可重复传入 `--image`）：**

```bash
python3 <skill-path>/scripts/generate_image_advanced.py \
  --prompt "convert to anime style" \
  --image /path/to/input1.png --image /path/to/input2.jpg \
  --output /path/to/output.png
```

**单条命令限制：每次 Bash 工具执行的 `command` 中只能包含 1 个 `generate_image_advanced.py` 调用。** 如果用户需要生成多张图片，必须拆成多次 Bash 工具调用，每次单独执行一条 `generate_image_advanced.py ... --output <不同文件>` 命令；禁止在同一条命令里用 `&&`、`;` 或换行串联多个 `generate_image_advanced.py`，避免单次执行耗时过长导致 Bash 工具超时。

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","task_id":"...","image_url":"https://...","file":"/path/to/output.png"}
```

如果脚本在安全时限内还没完成，它会正常退出并输出：

```json
{"status":"processing","task_id":"<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_image_advanced.py` 与 `query_image_advanced.py` 存在先后依赖，必须等 `generate_image_advanced.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_image_advanced.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时不要重新提交任务，改用只查询脚本继续等待：

```bash
python3 <skill-path>/scripts/query_image_advanced.py --task-id <task_id>
```

`query_image_advanced.py` 不会重新提交任务，适合在任务已经进入队列但生成未完成时继续查询。

**空间位置描述（生成期 Prompt 增强）：**

在提示词中加入空间位置词可显著提高构图准确性：

| 位置关键词 | 说明 | 示例 |
|-----------|------|------|
| `centered` / `in the center` | 主体居中 | `"a red rose, centered, white background"` |
| `in the top-left / bottom-right corner` | 角落定位 | `"logo in the top-left corner"` |
| `in the foreground / background` | 前景/背景层次 | `"flowers in the foreground, mountains in the background"` |
| `on the left side / right side` | 左右分布 | `"person on the left, product on the right"` |
| `filling the entire frame` | 占满画面 | `"texture filling the entire frame"` |

完整参数说明（含图生图、多图合成）详见 `references/image-generation-api.md`。

**脚本使用约束（生成图片时严格遵守）：**
- **禁止新增脚本**：只能执行 `scripts/` 目录中已有的脚本（`generate_image_advanced.py`、`query_image_advanced.py`），不得为本次任务创建任何新的 Python/Shell/Node 脚本或临时封装。
- **禁止改名**：脚本文件名是固定的，不得重命名，也不得复制成其他文件名后再调用。
- **非必要不修改**：除非用户明确要求修复脚本 Bug，否则不得修改脚本源码；所有行为差异通过命令行参数控制。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内通过 Edge Function 代理调用，密钥不暴露给前端。

**平台实现差异：**

| 平台 | Edge Function 差异 | 前端调用方式 |
|------|-------------------|-------------|
| Web | 查询接口用 POST body | `supabase.functions.invoke` |
| MiniProgram | 查询接口用 GET + URL 参数（绕过代理 body 丢失问题） | `supabase.functions.invoke("query-task?taskId=...")` with `method: "GET"` |

完整 Edge Function 代码和前端调用代码详见 `references/image-generation-api.md`。

