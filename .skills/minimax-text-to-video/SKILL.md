---
name: minimax-text-to-video
description: 基于 MiniMax 模型将文本描述生成短视频，支持运镜控制、多分辨率及异步轮询获取结果，适用于短视频创作、广告制作等场景。
license: MIT
---

## 能力概述

通过 MiniMax API，根据文本描述自动生成视频内容，支持 MiniMax-Hailuo-02 等模型，可配置视频时长（6 秒或 10 秒）、分辨率（768P/1080P，MiniMax-Hailuo-02 模型），并支持 15 种运镜控制指令。

| 项目 | 说明 |
|------|------|
| 认证模式 | `platform_managed`（密钥由平台注入，无需用户配置） |
| 第三方域名 | `app-dvtmyuucfs3l-api-V9gDzg15D7BL-gateway.appmiaoda.com` |
| 支持平台 | Web、MiniProgram |
| 计费 | 仅创建任务接口计费，查询和下载接口不计费 |

**接口列表：**

| 接口 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 创建文生视频任务 | POST | `/v1/video_generation` | 提交生成任务，返回 `task_id` |
| 查询任务状态 | GET | `/v1/query/video_generation` | 轮询任务状态，成功后返回 `file_id` |
| 视频文件下载 | GET | `/v1/files/retrieve` | 通过 `file_id` 获取视频下载链接 |

**工作流：**

```
用户提交 prompt
    ↓
POST /v1/video_generation  →  返回 task_id
    ↓
每 7 秒轮询 GET /v1/query/video_generation?task_id=xxx
    ↓
status == "Success"  →  获取 file_id
    ↓
GET /v1/files/retrieve?file_id=xxx  →  获取 download_url（有效期 1 小时）
    ↓
将视频 URL 转存至 Supabase Storage（原始链接仅 1 小时有效）
```

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

```bash
python3 <skill-path>/scripts/generate_text_to_video.py --prompt "[推进] A cat runs through a garden" --output /path/to/output.mp4
```

也可以指定模型、时长、分辨率：

```bash
python3 <skill-path>/scripts/generate_text_to_video.py --prompt "..." --duration 10 --resolution 768P --output /path/to/output.mp4
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4","filename":"output_aigc.mp4"}
```

如果脚本在安全时限内还没完成，它会正常退出并输出：

```json
{"status":"processing","task_id":"<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_text_to_video.py` 与 `query_text_to_video.py` 存在先后依赖，必须等 `generate_text_to_video.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_text_to_video.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时不要重新提交任务，改用只查询脚本继续等待：

```bash
python3 <skill-path>/scripts/query_text_to_video.py --task-id <task_id> --output /path/to/output.mp4
```

`query_text_to_video.py` 不会重新提交任务，适合在任务已经进入队列但生成未完成时继续查询。脚本内部已处理提交、轮询、`file_id` 获取下载链接及下载到本地的完整流程，`download_url` 有效期仅 1 小时，脚本会在获取后立即下载。

---

## 生成后用法（应用内通过 Edge Function 调用）

本 API 为异步接口，Edge Function 设计原则：

- **创建任务** Edge Function：立即返回 `task_id` 给前端，**不在 Edge Function 内部轮询**。
- **查询任务** Edge Function：前端每 7 秒调用一次，直到 `status` 为 `Success` 或 `Fail`。
- 当状态为 `Success` 时，通过 `file_id` 调用 **获取下载链接** Edge Function，将视频转存至
  Supabase Storage（原始下载链接有效期仅 1 小时）。

**平台差异：**

| 平台 | 调用方式 | 说明 |
|------|----------|------|
| Web | `supabase.functions.invoke` 或原生 `fetch` | 标准 JSON 调用 |
| MiniProgram | `supabase.functions.invoke` | 标准 JSON 调用 |

详见：
- `references/video-generation-api.md`（三个 Edge Function 完整实现 + 前端轮询代码 + Supabase Storage 转存）
