---
name: kling-3-turbo-video-generation
description: 使用可灵 Kling 3.0 Turbo 模型创建视频生成任务，支持文生视频、首帧图生视频、异步轮询和视频结果转存；仅使用本 Skill 定义的 Turbo 接口，不引入其他 Skill 或未声明能力。
license: MIT
---

## 能力概述

基于可灵 Kling 3.0 Turbo 模型的视频生成能力，支持：

- **文生视频**：使用文本提示词生成视频
- **图生视频**：使用一张首帧图片和可选提示词生成视频
- **Prompt 多镜头视频**：通过官方固定 Prompt 格式生成 1-6 个镜头，不使用独立多镜头 API 参数
- **异步任务**：提交任务 → 查询状态 → 获取结果
- **视频转存**：将上游临时视频 URL 转存至应用存储

| 属性 | 值 |
|------|----|
| 服务商 | KlingAI（快手可灵） |
| 模型 | Kling 3.0 Turbo（由请求路径确定） |
| 响应方式 | 异步轮询（提交任务 → 轮询状态 → 获取结果） |
| 视频时长 | 3–15 秒 |
| 文生视频比例 | 16:9、9:16、1:1 |
| 视频分辨率 | 720p、1080p |
| 视频返回 | 视频 URL，需及时转存至应用存储 |
| 说明 | 提交任务后按任务 ID 查询，避免重复提交 |

**端点：**

- 文生创建任务：`POST https://app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com/text-to-video/kling-3.0-turbo`
- 图生创建任务：`POST https://app-dvtmyuucfs3l-api-eLMlzO5Veyw9-gateway.appmiaoda.com/image-to-video/kling-3.0-turbo`
- 统一查询任务：`GET https://app-dvtmyuucfs3l-api-baBwmdOB6lG9-gateway.appmiaoda.com/tasks`

所有请求使用：

```text
X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}
```

`INTEGRATIONS_API_KEY` 只允许在服务端或 Edge Function 中读取，不能暴露到前端、Skill 输出或日志。

---

## 能力边界

本 Skill 只使用本 Skill 定义的 Kling 3.0 Turbo 三条接口：文生创建、首帧图生创建和统一任务查询。不要引入其他 Skill、其他模型或未在本 Skill references 中声明的能力。

Turbo 当前支持：

- 普通文本提示词文生视频；
- 通过固定 Prompt 格式生成 1-6 个镜头的视频；
- 单张首帧图生视频；
- 异步任务查询与视频结果转存。

Turbo 的多镜头是 **Prompt 级能力**，不是 Omni 那种独立 API 控制参数。请求体仍然只使用 `prompt/settings/options` 或 `contents/settings/options`，不得添加 `multi_shot`、`shot_type`、`multi_prompt` 等字段。

Turbo 不支持尾帧、多参考图、参考视频、主体库或视频编辑参数。不要生成这些未声明能力的 UI、请求字段、数据库字段或响应结构。

用户提出本 Skill 未声明的能力时，明确说明当前 Turbo 接口不支持，不自动切换或引入其他 Skill。只使用本 Skill references 中定义的 Turbo 请求体。

---

## 完整异步工作流

此 API 为**异步**模式，必须先提交任务获取系统任务 ID，再轮询查询接口直到任务完成或失败。

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

interface TurboVideoTask {
  taskId: string;
  externalTaskId?: string;
  status: "submitted" | "processing" | "succeeded" | "failed";
}

interface TurboVideoOutput {
  id: string;
  url: string;
  watermarkUrl?: string;
  duration?: string;
}

interface TurboVideoResult extends TurboVideoTask {
  outputs?: TurboVideoOutput[];
  message?: string;
}

async function queryTurboVideoTask(
  taskId?: string,
  externalTaskId?: string,
): Promise<TurboVideoResult> {
  if ((taskId && externalTaskId) || (!taskId && !externalTaskId)) {
    throw new Error("taskId 和 externalTaskId 必须二选一");
  }

  const query = taskId
    ? `task_ids=${encodeURIComponent(taskId)}`
    : `external_task_ids=${encodeURIComponent(externalTaskId!)}`;

  const response = await fetch(
    `https://app-dvtmyuucfs3l-api-baBwmdOB6lG9-gateway.appmiaoda.com/tasks?${query}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
    },
  );

  const json = await response.json();
  if (!response.ok || json.code !== 0) {
    throw new Error(`API 错误 ${json.code ?? response.status}：${json.message ?? "查询失败"}`);
  }

  const tasks = Array.isArray(json.data) ? json.data : [];
  const task = tasks.find((item: { id?: string; external_id?: string }) =>
    taskId ? String(item.id) === String(taskId) : item.external_id === externalTaskId
  );

  if (!task) throw new Error("查询响应中未找到目标任务");

  return {
    taskId: String(task.id),
    externalTaskId: task.external_id,
    status: task.status,
    message: task.message,
    outputs: task.outputs
      ?.filter((output: { type?: string }) => output.type === "video")
      .map((output: { id: string; url: string; watermark_url?: string; duration?: string }) => ({
        id: output.id,
        url: output.url,
        watermarkUrl: output.watermark_url,
        duration: output.duration,
      })),
  };
}

async function pollTurboVideoTask(
  taskId: string,
  timeoutMs = 10 * 60 * 1000,
): Promise<TurboVideoResult> {
  const pollIntervalMs = 7000;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    const result = await queryTurboVideoTask(taskId);

    if (result.status === "succeeded" || result.status === "failed") {
      return result;
    }
  }

  throw new Error(`任务 ${taskId} 超时（等待超过 10 分钟）`);
}
```

创建任务后必须保存 `data.id`。查询接口返回数组时必须按目标 `id` 或 `external_id` 精确匹配，不能直接使用 `data[0]`。

---

## 生成期用法（Agent 直接调用）

使用平台注入的 `INTEGRATIONS_API_KEY` 调用对应的 API Plugin Endpoint。不要自行拼接网关基址，也不要使用 `/v1/videos/...` 旧路径。

### 文生视频

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

const createResp = await fetch(
  "https://app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com/text-to-video/kling-3.0-turbo",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      prompt: "一只橘猫在草地上慵懒地打滚",
      settings: {
        resolution: "1080p",
        aspect_ratio: "16:9",
        duration: 5,
      },
      options: {
        external_task_id: "unique-text-task-id",
        watermark_info: { enabled: false },
      },
    }),
  },
);

const createJson = await createResp.json();
if (!createResp.ok || createJson.code !== 0) {
  throw new Error(`API 错误 ${createJson.code ?? createResp.status}：${createJson.message ?? "创建失败"}`);
}

const taskId = createJson.data.id;
const result = await pollTurboVideoTask(taskId);
console.log("视频 URL：", result.outputs?.[0]?.url);
```

### 图生视频

```typescript
const createResp = await fetch(
  "https://app-dvtmyuucfs3l-api-eLMlzO5Veyw9-gateway.appmiaoda.com/image-to-video/kling-3.0-turbo",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      contents: [
        { type: "prompt", text: "人物缓慢转头看向镜头" },
        { type: "first_frame", url: "https://example.com/first-frame.png" },
      ],
      settings: {
        resolution: "1080p",
        duration: 5,
      },
      options: {
        external_task_id: "unique-image-task-id",
        watermark_info: { enabled: false },
      },
    }),
  },
);

const createJson = await createResp.json();
if (!createResp.ok || createJson.code !== 0) {
  throw new Error(`API 错误 ${createJson.code ?? createResp.status}：${createJson.message ?? "创建失败"}`);
}

const taskId = createJson.data.id;
const result = await pollTurboVideoTask(taskId);
console.log("视频 URL：", result.outputs?.[0]?.url);
```

生成接口返回的 URL 是临时链接，获得后应立即下载或转存至应用存储。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内需要两个 Edge Function：

| Edge Function | 文件 | 说明 |
|---------------|------|------|
| `kling-3-turbo-create` | `references/text-to-video-api.md`、`references/image-to-video-api.md` | 校验参数，提交文生或图生任务，返回 `data.id` |
| `kling-3-turbo-query` | `references/task-query-api.md` | 查询任务状态；成功时将视频转存至 Supabase Storage 并返回持久化 URL |

前端实现**提交 + 轮询**两步 UI：

1. 点击“生成”按钮 → 调用 `kling-3-turbo-create`，获取 `data.id`；
2. 保存任务 ID，每 7 秒通过 POST body 调用 `kling-3-turbo-query`；不要使用 GET query string 调用 Edge Function；
3. 查询 Edge Function 接收 `task_id` 或 `external_task_id`，再转换为上游 GET `/tasks` 查询；
4. 返回 `submitted` / `processing` 时继续轮询；
5. 返回 `succeeded` 且视频转存成功后展示视频；
6. 返回 `failed` 时展示任务 `message`，不重新创建。

创建 Edge Function 不在一次请求内阻塞轮询、下载或转存。查询 Edge Function 不创建新任务。

---

## 提示词与参数约束

### 文生视频

- `prompt` 必填，最大 3072 字符；
- `settings.resolution` 只能是 `720p` 或 `1080p`；
- `settings.aspect_ratio` 只能是 `16:9`、`9:16` 或 `1:1`；
- `settings.duration` 为 3–15 的整数；
- Prompt 多镜头格式：`镜头 n, m, words; 镜头 n, m, words;`；
- `n` 为分镜序号，最多 6 个、最少 1 个；
- `m` 为该分镜时长，每段不少于 1 秒，所有分镜时长之和必须等于 `settings.duration`；
- `words` 为该分镜提示词，每段最大 512 字符；
- 该能力仅通过 `prompt` 文本表达，不添加独立 `multi_shot`、`shot_type` 或 `multi_prompt` 字段。

### 图生视频

- `contents` 必填且只能包含一个 `first_frame`；
- 提示词单独使用 `{ type: "prompt", text: "..." }`；
- 首帧单独使用 `{ type: "first_frame", url: "..." }`；
- 首帧支持 jpg/jpeg/png，最大 50MB；
- 图片宽高均不小于 300px，宽高比范围为 1:2.5 至 2.5:1；
- 不支持尾帧、参考视频、主体库或视频编辑；
- Base64 不进入日志、控制台、错误信息或 LLM 上下文。

---

## 错误处理与透传

Edge Function 不得把所有错误统一包装成“未知错误”。创建和查询失败时，应保留安全的结构化错误：

```json
{
  "error": "安全的用户提示",
  "type": "gateway_error",
  "code": 1200,
  "message": "上游错误信息",
  "request_id": "request-id"
}
```

- 参数校验失败：返回 HTTP 400 和字段级错误；
- 上游 400、401、403、404、429、5xx：保留 HTTP 状态；
- HTTP 200 但业务 `code != 0`：按失败处理，保留 `code`、`message`、`request_id`；
- 网络错误或非 JSON 响应：返回 `gateway_error` 或 `upstream_unavailable`；
- 前端只展示安全的 `error`，将 `code`、`request_id` 和 HTTP 状态用于诊断；
- 不得返回 API Key、Authorization、内部网关 URL、API ID、价格、计费字段或 Plugin 原始配置。

---

## 注意事项

- **密钥安全**：`INTEGRATIONS_API_KEY` 只在 Edge Function 或服务端读取；
- **异步任务**：提交后必须查询，不要重复创建；
- **临时 URL**：生成结果 URL 30 天后清理，成功后及时转存；
- **转存幂等**：使用 `task.id + output.id` 作为转存幂等键；
- **失败重试**：查询可有限退避，创建不盲目重试，转存失败只重试转存；
- **计费**：计费由 API Plugin 后端处理，Skill 不展示价格或计费明细。
