---
name: minimax-image-to-video
description: 使用 MiniMax 图生视频 API，通过首帧图片或首尾帧图片生成视频；适用于需要将静态图片转化为动态视频的场景，支持运镜控制、自定义时长和分辨率
license: MIT
---

## 能力概述

**图生视频（MiniMax）** 提供四个接口，构成完整的异步视频生成工作流：

| 步骤 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 1. 提交任务 | 单帧图生视频 | POST `/v1/video_generation` | 通过首帧图片 + 文本描述生成视频 |
| 1. 提交任务 | 首尾帧生成视频 | POST `/v1/video_generation` | 通过首帧+尾帧图片生成过渡视频 |
| 2. 查询状态 | 查询任务状态 | GET `/v1/query/video_generation` | 轮询任务进度，等待 Success/Fail |
| 3. 获取文件 | 视频下载 | GET `/v1/files/retrieve` | 通过 file_id 获取下载链接（有效期 1 小时）|

**认证方式：** `platform_managed`，密钥由平台注入，Edge Function 中通过 `Deno.env.get("INTEGRATIONS_API_KEY")` 读取，header 统一为 `X-Gateway-Authorization: Bearer <key>`。

**支持平台：** Web、MiniProgram

**核心约束（MiniMax-Hailuo-02 模型）：**
- `resolution` 仅支持 `768P` 和 `1080P`（`720P`/`512P` 会返回 2013 错误），默认 `768P`
- `duration`：`768P` 支持 6s 或 10s；`1080P` 仅支持 6s（不可传 3s/5s）
- 默认 `duration=6`；如 UI 提供时长选择器，当 `resolution=1080P` 时需自动重置为 6 并禁用其他选项
- 首尾帧模式不支持 512P 分辨率

**视频获取流程（2 步）：**
1. 轮询查询接口直到 `status=Success`，获得 `file_id`
2. 调用 `files/retrieve?file_id=...` 获取 `download_url`（有效期仅 1 小时）
3. **必须立即**将 `download_url` 上传到 Supabase Storage，使用持久化的 `publicUrl` 存入数据库

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

**单帧模式（首帧图片 + 文本描述）：**

```bash
python3 <skill-path>/scripts/generate_image_to_video.py --first-frame /path/to/first.jpg --prompt "..." --output /path/to/output.mp4
```

**首尾帧组合模式（从起始画面过渡到结束画面）：**

```bash
python3 <skill-path>/scripts/generate_image_to_video.py --first-frame /path/to/first.jpg --last-frame /path/to/last.jpg --prompt "产品从展示台缓缓移动到使用场景，镜头平稳推进" --output /path/to/output.mp4
```

也支持图片 URL 输入（`--first-frame-url` / `--last-frame-url`），以及 `--duration`（6 或 10）、`--resolution`（768P 或 1080P）参数。

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4","filename":"output_aigc.mp4"}
```

如果脚本在安全时限内还没完成，它会正常退出并输出：

```json
{"status":"processing","task_id":"<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_image_to_video.py` 与 `query_image_to_video.py` 存在先后依赖，必须等 `generate_image_to_video.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_image_to_video.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时不要重新提交任务，改用只查询脚本继续等待：

```bash
python3 <skill-path>/scripts/query_image_to_video.py --task-id <task_id> --output /path/to/output.mp4
```

`query_image_to_video.py` 不会重新提交任务，适合在任务已经进入队列但生成未完成时继续查询。脚本内部已处理提交、轮询、`file_id` 获取下载链接及下载到本地的完整流程，`download_url` 有效期仅 1 小时，脚本会在获取后立即下载。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内需部署 **三个 Edge Function**：

| Edge Function | 对应接口 | 说明 |
|--------------|---------|------|
| `submit-image-to-video` | 单帧 或 首尾帧 POST | 提交视频生成任务 |
| `query-video-status` | GET query | 轮询任务状态 |
| `retrieve-video-file` | GET files/retrieve | 获取下载链接并转存 Supabase Storage |

**平台差异：**
- GET 接口的 Edge Function 调用在 H5/MiniProgram 中必须把参数放在 URL 中，不可放在 body（H5 会静默忽略 GET 请求的 body）
- 前端轮询计数器必须用 `useRef`，不可用 `useState`（useState 触发重渲染会使轮询失控）
- `download_url` 有效期仅 1 小时，**必须立即**转存到 Supabase Storage

详细 Edge Function 代码、前端代码及注意事项，见：
- `references/video-generation-api.md`（提交接口）
- `references/video-query-retrieve-api.md`（查询 + 下载接口）
