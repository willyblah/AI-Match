---
name: sora-video-generation
description: Sora 2 视频生成（高级版），支持文生视频、图生视频、视频 Remix，含任务查询；适合需要 AI 视频创作、参考图驱动生成或对已有视频进行局部编辑的场景。
license: MIT
---

## 能力概述

基于 Azure OpenAI Sora 2 模型的高质量视频生成服务，提供四个核心接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| Create Video | POST | 文生视频 / 图生视频（可选参考图 input_reference） |
| Video from Reference | POST | 以参考图像为首帧锚点生成视频（强制匹配分辨率） |
| Remix Video | POST | 对已完成视频做局部修改，保留原始结构 |
| Query Status | POST | 查询任务进度，获取 video_url |

**支持分辨率：** `720x1280`（竖屏）、`1280x720`（横屏）
**支持时长：** 4 / 8 / 12 秒
**内容限制：** 仅限 18 岁以下适龄内容，不得包含版权角色/真实人物/背景音乐版权内容

**典型工作流：**
1. 调用 Create Video / Video from Reference / Remix Video 获得 `video_id`
2. 轮询 Query Status 直至 `status === "completed"`
3. 从 `video_url` 下载视频并转存至 Supabase Storage

**平台差异：**

| 项 | Web | MiniProgram |
|----|-----|-------------|
| 视频展示 | `<video src={publicUrl}>` | `<Video src={publicUrl}>` (Taro) |
| 文件上传（参考图） | `FormData + File` | `Taro.chooseImage → uploadFile` |
| Edge Function 调用 | `fetch` 或 `supabase.functions.invoke` | `supabase.functions.invoke` |

---

## 生成期用法（Agent 直接调用）

适用于 Agent 在代码生成阶段直接发起 HTTP 请求，无需 Edge Function 中转。
生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

**Create Video（文生视频 / 图生视频）：**

```bash
python3 <skill-path>/scripts/generate_sora_video.py --prompt "A cat riding a motorcycle at night" \
  --size 1280x720 --seconds 8 --output /path/to/output.mp4
```

可选传入 `--image /path/to/ref.jpg` 或 `--image-url "https://..."` 作为 `input_reference`（图生视频）。

**Video from Reference（以参考图为首帧锚点，强制匹配分辨率）：**

```bash
python3 <skill-path>/scripts/generate_sora_video.py --from-reference \
  --prompt "..." --image /path/to/ref.jpg --size 720x1280 --output /path/to/output.mp4
```

**Remix Video（对已完成视频做局部编辑）：**

```bash
python3 <skill-path>/scripts/generate_sora_video.py --remix-video-id video_abc123 \
  --prompt "把光照调暗" --output /path/to/output.mp4
```

三种提交模式互斥：不带 `--from-reference`/`--remix-video-id` 时默认走 Create Video；`--from-reference` 触发 Video from Reference；`--remix-video-id` 触发 Remix Video。

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","video_id":"...","url":"https://...","file":"/path/to/output.mp4"}
```

如果脚本在安全时限内还没完成，它会正常退出并输出：

```json
{"status":"processing","video_id":"<video_id>"}
```

**必须串行调用，禁止并行发起：** 提交脚本（`generate_sora_video.py`）与 `query_sora_video.py` 存在先后依赖，必须等提交脚本的 Bash 工具调用返回并拿到 `video_id` 后，才能发起 `query_sora_video.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时不要重新提交任务，改用只查询脚本继续等待：

```bash
python3 <skill-path>/scripts/query_sora_video.py --video-id <video_id> --output /path/to/output.mp4
```

`query_sora_video.py` 不会重新提交任务，适合在任务已经进入队列但生成未完成时继续查询。脚本内部已处理提交（`generate_sora_video.py`）、轮询、状态判断及下载到本地的完整流程；`video_url` 有时效性，脚本会在获取后立即下载。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内调用需通过 Supabase Edge Function 中转，平台密钥 `INTEGRATIONS_API_KEY` 仅在服务端可见。
生成完成后视频 URL 转存至 Supabase Storage，向客户端返回持久化的 `publicUrl`。

**各接口完整实现详见：**
`references/sora-video-generation-api.md`

**前端调用摘要（Web）：**

```typescript
// 发起视频生成，获取 video_id
const { data, error } = await supabase.functions.invoke("sora-create-video", {
  body: { prompt: "A cat riding a motorcycle at night", size: "1280x720", seconds: 8 },
});
if (error) throw error;
const videoId = data.videoId;

// 轮询状态
const POLL_INTERVAL_MS = 8000;
while (true) {
  await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  const { data: statusData } = await supabase.functions.invoke("sora-query-video", {
    body: { video_id: videoId },
  });
  if (statusData.status === "completed") {
    setVideoUrl(statusData.publicUrl); // Supabase Storage URL
    break;
  }
  if (statusData.status === "failed") throw new Error("Video generation failed");
  if (statusData.status === "cancelled") throw new Error("Video generation cancelled");
  setProgress(statusData.progress);
}
```

**前端调用摘要（MiniProgram/Taro）：**

```typescript
// 同 Web，supabase.functions.invoke 在 Taro 中可用
// 视频展示使用 Taro <Video> 组件
import { Video } from "@tarojs/components";
<Video src={videoUrl} controls autoPlay={false} />
```

详细的 Edge Function 代码（含 Supabase Storage 转存）、参考图上传（图生视频）、
Remix 接口用法见 `references/sora-video-generation-api.md`。
