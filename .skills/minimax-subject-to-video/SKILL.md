---
name: minimax-subject-to-video
description: 基于 MiniMax S2V-01 模型，上传人物主体图片和文本描述生成动态视频；支持异步轮询获取结果和下载链接。
license: MIT
---

## 能力概述

基于 MiniMax S2V-01 模型的主体参考视频生成服务，支持上传人像图片并结合文本描述生成动态视频。整体流程分为三步：

1. **提交任务**（POST）— 上传主体参考图片和文本描述，创建视频生成任务，返回 `task_id`
2. **查询状态**（GET）— 轮询任务状态直到 `Success` 或 `Fail`，成功后返回 `file_id`
3. **获取下载链接**（GET）— 通过 `file_id` 获取视频文件下载 URL（有效期 1 小时）

| 项目 | 说明 |
|------|------|
| 模型 | S2V-01 |
| 主体类型 | character（人物面部） |
| 图片格式 | JPG / JPEG / PNG / WebP，小于 20MB，短边 > 300px，长宽比 2:5 ~ 5:2 |
| 输出视频 | 最高 1920×1080，MP4 格式 |
| 视频下载链接有效期 | 1 小时 |
| 计费 | 仅提交任务接口计费（`api-oLpZbv47qvea`），查询状态和文件获取免费 |

详见各接口规格：
- `references/video-generation-api.md` — 提交任务接口
- `references/query-video-generation-api.md` — 查询任务状态接口
- `references/retrieve-file-api.md` — 获取视频下载链接接口

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

```bash
python3 <skill-path>/scripts/generate_subject_video.py --image /path/to/face.jpg --prompt "A girl runs toward the camera and winks with a smile." --output /path/to/output.mp4
```

也可以直接传图片 URL：

```bash
python3 <skill-path>/scripts/generate_subject_video.py --image-url "https://example.com/face.jpg" --prompt "..." --output /path/to/output.mp4
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4","filename":"output_aigc.mp4"}
```

如果脚本在安全时限内还没完成，它会正常退出并输出：

```json
{"status":"processing","task_id":"<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_subject_video.py` 与 `query_subject_video.py` 存在先后依赖，必须等 `generate_subject_video.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_subject_video.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时不要重新提交任务，改用只查询脚本继续等待：

```bash
python3 <skill-path>/scripts/query_subject_video.py --task-id <task_id> --output /path/to/output.mp4
```

`query_subject_video.py` 不会重新提交任务，适合在任务已经进入队列但生成未完成时继续查询。脚本内部已处理提交、轮询、`file_id` 获取下载链接及下载到本地的完整流程，`download_url` 有效期仅 1 小时，脚本会在获取后立即下载，不会把该临时链接遗留给后续步骤。

---

## 生成后用法（应用内通过 Edge Function 调用）

前端通过 Edge Function 调用，密钥在服务端注入，不暴露到客户端。支持 Web 和 MiniProgram 两个平台，Edge Function 实现相同，前端调用方式相同。

返回的视频 `download_url` 有效期仅 1 小时，建议应用在获取后立即使用或转存到 Supabase Storage。

详见：
- `references/video-generation-api.md` — 提交任务 Edge Function + 前端代码
- `references/query-video-generation-api.md` — 查询状态 Edge Function + 前端代码
- `references/retrieve-file-api.md` — 获取下载链接 Edge Function + 前端代码

### 平台差异说明

| 平台 | Edge Function | 前端调用 | 视频播放 |
|------|--------------|---------|---------|
| Web | 标准 JSON 响应 | `supabase.functions.invoke` 或原生 `fetch` | `<video src={downloadUrl}>` |
| MiniProgram | 标准 JSON 响应 | `supabase.functions.invoke` | `Taro.createVideoContext` 或 `<Video src={downloadUrl}>` |

> 注意：下载链接 `download_url` 有效期 1 小时，视频生成完成后请及时保存或转存。

---

## 注意事项

- **密钥安全**：`INTEGRATIONS_API_KEY` 仅在 Edge Function 服务端读取，严禁暴露到前端。
- **计费**：仅提交任务接口（`api-oLpZbv47qvea`）计费，查询状态和文件获取接口免费，以平台实际定价为准。
- **错误处理**：务必处理 429（配额超限）、402（余额不足）和 `base_resp.status_code` 非 0 的业务错误。
- **视频下载链接有效期**：`download_url` 有效期仅 1 小时，建议生成后立即转存至 Supabase Storage（参见模板 Appendix A）。
- **轮询超时**：视频生成时长不定，建议轮询间隔 7 秒，总超时设为 10 分钟。
- **图片要求**：JPG/JPEG/PNG/WebP，小于 20MB，短边 > 300px，长宽比在 2:5 ~ 5:2 之间。
