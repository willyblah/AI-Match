---
name: minimax-text-to-image
description: 调用 MiniMax 文生图接口，根据文本描述生成图片并转存至 Supabase Storage，适用于创意设计、海报生成、游戏场景绘制等场景。
license: MIT
---

## 能力概述

通过 MiniMax 文生图 API 将文本描述转换为图片，支持 `image-01` 和 `image-01-live` 两种模型，以及多种宽高比与批量生成。

- `image-01`：通用文生图模型，支持自定义宽高（512–2048 px）、`21:9` 超宽比例及 URL/base64 两种返回格式。
- `image-01-live`：真实感增强模型，适合人物写实风格，支持通过 `style` 参数指定画风（`漫画`/`元气`/`中世纪`/`水彩`），不支持自定义宽高和 `21:9` 比例。

| 项目 | 值 |
|------|-----|
| Endpoint | `POST https://app-dvtmyuucfs3l-api-DLEO7vB8pQba-gateway.appmiaoda.com/v1/image_generation` |
| 认证模式 | `platform_managed`（密钥由平台注入，无需用户配置） |
| Content-Type | `application/json` |
| 支持平台 | Web、MiniProgram |

Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。


**核心能力：**
- 文本 prompt 最长 1500 字符，支持 prompt 自动优化
- 宽高比：`1:1`（默认）/ `16:9` / `4:3` / `3:2` / `2:3` / `3:4` / `9:16` / `21:9`
- 自定义宽高（512–2048 px，需为 8 的倍数，仅 `image-01`）
- 单次最多生成 9 张，返回格式支持 url / base64
- API 返回的图片 URL 有效期 24 小时，**Edge Function 需将其转存至 Supabase Storage**

**响应示例：**
```json
{
  "id": "03ff3cd0820949eb8a410056b5f21d38",
  "data": {
    "image_urls": ["https://...storage_public_url..."]
  },
  "metadata": { "success_count": 3, "failed_count": 0 },
  "base_resp": { "status_code": 0, "status_msg": "success" }
}
```

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成请求/下载代码。

```bash
python3 <skill-path>/scripts/generate_image.py --prompt "A scenic mountain landscape at sunset, ultra-realistic, 8K." --output /path/to/output.png
```

生成多张图片时改用 `--output-dir`（脚本内部通过 `--n` 一次请求生成多张，无需多次调用）：

```bash
python3 <skill-path>/scripts/generate_image.py --prompt "..." --n 3 --aspect-ratio 16:9 --output-dir /path/to/images
```

**单条命令限制：每次 Bash 工具执行的 `command` 中只能包含 1 个 `generate_image.py` 调用。** 如果用户需要多批次/多组不同 prompt 的图片，必须拆成多次 Bash 工具调用，每次单独执行一条 `generate_image.py ... --output-dir <不同目录>` 命令；禁止在同一条命令里用 `&&`、`;` 或换行串联多个 `generate_image.py`，避免单次执行耗时过长导致 Bash 工具超时。

脚本内部会调用上游接口获取图片 URL（有效期 24 小时）并立即下载到本地，成功时 stdout 输出一行 JSON：

```json
{"files":["/path/to/output.png"],"urls":["https://..."],"metadata":{"success_count":1,"failed_count":0},"base_resp":{"status_code":0,"status_msg":"success"}}
```

**脚本使用约束（生成图片时严格遵守）：**
- **禁止新增脚本**：只能执行 `scripts/` 目录中已有的脚本（`generate_image.py`），不得为本次任务创建任何新的 Python/Shell/Node 脚本或临时封装。
- **禁止改名**：脚本文件名是固定的，不得重命名，也不得复制成其他文件名后再调用。
- **非必要不修改**：除非用户明确要求修复脚本 Bug，否则不得修改脚本源码；所有行为差异通过命令行参数控制。

## 生成后用法（应用内通过 Edge Function 调用）

应用内通过 Supabase Edge Function 代理调用，平台密钥由服务端注入，不暴露给客户端。

Edge Function 在拿到上游 `image_urls` 后，调用 `streamMediaToStorage` 将图片转存至 Supabase Storage，返回持久化的公开 URL。

Web 和 MiniProgram 均使用 `supabase.functions.invoke` 调用，返回结构相同。

详见 [references/image-generation-api.md](references/image-generation-api.md) — Edge Function 及前端代码一节。
