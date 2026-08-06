---
name: text-to-video
description: 基于文本描述生成短视频（5s/10s），适用于电商营销、创意宣传、教育讲解等场景，异步轮询获取结果。
license: MIT
---

## 能力概述

通过百度千帆平台 Kling 模型，根据文字提示词自动生成 5 秒或 10 秒的视频内容（不含声音）。

| 项目 | 说明 |
|------|------|
| 认证模式 | `platform_managed`（密钥由平台注入，无需用户配置） |
| 第三方域名 | `app-dvtmyuucfs3l-api-o9wN672BkyMa-gateway.appmiaoda.com` |
| 支持平台 | Web、MiniProgram |
| 说明 | 创建任务接口用于提交任务，查询接口用于轮询结果 |

**接口列表：**

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建文生视频任务 | POST | `/beta/video/generations/kling/text2video` | 提交生成任务，返回 `task_id` |
| 查询任务状态 | GET | `/beta/video/generations/kling/text2video` | 轮询任务状态，成功后返回视频 URL |

**工作流：**

```
用户提交 prompt
    ↓
POST /text2video  →  返回 task_id
    ↓
每 5 秒轮询 GET /text2video?task_id=xxx
    ↓
task_status == "succeed"  →  获取 videos[0].url
    ↓
将视频 URL 转存至 Supabase Storage（视频链接 30 天后失效）
```

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

```bash
python3 <skill-path>/scripts/generate_text_to_video.py --prompt "一只猫在草地上奔跑" --output /path/to/output.mp4
```

也可以指定时长和模型：

```bash
python3 <skill-path>/scripts/generate_text_to_video.py --prompt "..." --duration 10 --model-name kling-v2-master --output /path/to/output.mp4
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4"}
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

`query_text_to_video.py` 不会重新提交任务，适合在任务已经进入队列但生成未完成时继续查询。脚本内部已处理提交、轮询及下载到本地的完整流程；返回的视频 URL 30 天后失效，如需长期保留请及时使用 `--output` 下载。

---

## 生成后用法（应用内通过 Edge Function 调用）

本 API 为异步接口，Edge Function 设计原则：

- **创建任务** Edge Function：立即返回 `task_id` 给前端，**不在 Edge Function 内部轮询**。
- **查询任务** Edge Function：前端每 5 秒调用一次，直到 `task_status` 为 `succeed` 或 `failed`。
- 当状态为 `succeed` 时，将 `task_result.videos[0].url` 转存至 Supabase Storage（原始视频链接 30 天后失效）。

**平台差异：**

| 平台 | 调用方式 | 说明 |
|------|----------|------|
| Web | `supabase.functions.invoke` 或原生 `fetch` | 标准 JSON 调用 |
| MiniProgram | `supabase.functions.invoke` | 标准 JSON 调用 |

详见：
- `references/submit-api.md`（创建任务 Edge Function + 前端代码）
- `references/query-api.md`（查询任务 Edge Function + 前端轮询代码 + Supabase Storage 转存）
