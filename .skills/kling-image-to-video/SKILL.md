---
name: kling-image-to-video
description: Generate AI videos from static images using Kling's Image-to-Video API with audio-visual sync. Use this skill whenever the user wants to animate an image, convert a photo to video, create an AI video from a picture, add motion to a still image, generate video from image with camera movement or voice, or use Kling image2video — even if they don't say "Kling" explicitly.
license: MIT
---

# Kling Image-to-Video (Audio-Visual Sync)

Generate high-quality videos from static images using Kling AI. Supports multiple model versions (kling-v1 through kling-v2-6), professional quality mode, camera control, motion brush trajectories, end-frame control, and voice synthesis. Videos can be 5s or 10s.

This is an **async** skill: submitting the task returns a `task_id` immediately; the video becomes available only after polling until `task_status` is `succeed`.

> Read `references/create-task-api.md` for the full submit-task specification and Edge Function code.
> Read `references/query-task-api.md` for the full query-task specification and Edge Function code.

---

## End-to-End Workflow

生成期（Agent 直接调用场景）使用 Python 脚本完成"提交任务 → 脚本内轮询 → 下载结果"全流程，不再使用内联 TypeScript 调用代码。

> **重要**：调用以下脚本时，Bash 工具超时必须设置为 `600000`（毫秒），因为脚本内部会轮询最长 550 秒（安全余量，避免撞到 Bash 工具 600s 超时）。

**提交并等待结果：**

```bash
python3 managed/kling-image-to-video/scripts/generate_image_to_video.py \
  --image /path/to/first_frame.jpg \
  --prompt "宇航员站起身走了" \
  --model-name kling-v2-6 \
  --mode pro \
  --duration 5 \
  --output /path/to/output.mp4
```

也支持 `--image-url`（直接传图片 URL）、`--image-tail`/`--image-tail-url`（尾帧，可选）。

- 成功时 stdout 输出一行 JSON，并已将视频下载到 `--output`：
  ```json
  {"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4"}
  ```
- 若达到脚本内部安全时限（550 秒）仍未完成，输出（退出码 0，不是失败）：
  ```json
  {"status":"processing","task_id":"..."}
  ```
  此时应使用下方查询脚本继续轮询。
- 失败时 stderr 输出错误信息，退出码 1。

**必须串行调用，禁止并行发起：** `generate_image_to_video.py` 与 `query_image_to_video.py` 存在先后依赖，必须等 `generate_image_to_video.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_image_to_video.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

**继续查询未完成的任务：**

```bash
python3 managed/kling-image-to-video/scripts/query_image_to_video.py \
  --task-id <task_id> \
  --output /path/to/output.mp4
```

输出格式与上面一致。

脚本参数、字段含义详见 `references/image2video-api.md`。

---

## Post-generation usage (in-app via Edge Function)

For production apps, use two Edge Functions — one per endpoint — so the platform API key never reaches the browser. After the query Edge Function retrieves the video URL, transfer it to Supabase Storage for persistence.

> Read `references/create-task-api.md` for the complete submit Edge Function (`edge-functions/kling-submit-image2video.ts`).
> Read `references/query-task-api.md` for the complete query Edge Function (`edge-functions/kling-query-image2video.ts`) including Supabase Storage transfer.

**Frontend polling loop:**

```typescript
// 1. Submit task via Edge Function
const { data: submitData, error: submitError } = await supabase.functions.invoke(
  "kling-submit-image2video",
  { body: { image, prompt, model_name: "kling-v2-6", mode: "pro", duration: "5" } }
);
if (submitError) throw submitError;
const taskId: string = submitData.data.task_id;

// 2. Poll via Edge Function until done
const POLL_INTERVAL_MS = 7000;
const TIMEOUT_MS = 10 * 60 * 1000;
const deadline = Date.now() + TIMEOUT_MS;

while (Date.now() < deadline) {
  await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));

  const { data: queryData, error: queryError } = await supabase.functions.invoke(
    "kling-query-image2video",
    { body: { task_id: taskId } }
  );
  if (queryError) throw queryError;

  const { task_status, task_status_msg, task_result } = queryData.data;
  if (task_status === "succeed") {
    // task_result.videos[].url is now a persistent Supabase Storage URL
    return task_result.videos;
  }
  if (task_status === "failed") throw new Error(`Generation failed: ${task_status_msg}`);
}
throw new Error("Timed out waiting for video generation");
```

---

## Parameter Summary

For full parameter tables, see `references/create-task-api.md` (submit) and `references/query-task-api.md` (query).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | string | Yes | Reference image (Base64 or URL), jpg/jpeg/png, ≤10MB, ≥300px, aspect ratio 1:2.5~2.5:1 |
| `prompt` | string | No | Positive text prompt, ≤2500 characters |
| `model_name` | string | No | Model version, default `kling-v2-6` |
| `mode` | string | No | Generation mode: `std` / `pro`, default `pro` |
| `duration` | string | No | Video duration (seconds): `5` or `10`, default `5` |
| `image_tail` | string | No | End-frame control image, same format requirements as `image` |
| `static_mask` | string | No | Static motion brush mask image (Base64 or URL); aspect ratio must match `image` |
| `camera_control` | object | No | Camera movement control; mutually exclusive with `image_tail` and `dynamic_masks`/`static_mask` |
| `camera_control.type` | string | No | Preset type: `simple` (custom) / `down_back` / `forward_up` / `right_turn_forward` / `left_turn_forward` |
| `camera_control.config.horizontal` | number | No | Left/right translation [-10, 10]; only when `type=simple`, only one config field may be non-zero |
| `camera_control.config.vertical` | number | No | Up/down translation [-10, 10] |
| `camera_control.config.pan` | number | No | Pitch [-10, 10] |
| `camera_control.config.tilt` | number | No | Yaw [-10, 10] |
| `camera_control.config.roll` | number | No | Roll [-10, 10] |
| `camera_control.config.zoom` | number | No | Focal length [-10, 10] |

---

## Notes

- **Key security**: `INTEGRATIONS_API_KEY` must only be read server-side in Edge Functions; never expose it to the frontend.
- **Error handling**: Always handle 429 (quota exceeded) and 402 (insufficient balance).
- **Billing**: The submit task endpoint (`api-eLMlJj3KJD89`) has billing enabled and is billed per call. The query endpoint (`api-rLobzpqX85m9`) is free. Avoid re-submitting duplicate tasks to minimise unnecessary charges.
- **Mutually exclusive parameters**: `image+image_tail`, `dynamic_masks/static_mask`, and `camera_control` cannot be used simultaneously.
- **Base64 format**: Do not include the `data:image/xxx;base64,` prefix in Base64 image data; pass only the encoded string itself.
- **Mask images**: The aspect ratio of a mask image must match the input `image`; otherwise the task will fail.
- **Video expiry**: Generated video CDN links are automatically cleared after 30 days — download or transfer to Supabase Storage promptly.
