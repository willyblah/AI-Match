# Kling 3.0 Turbo 统一任务查询 API

## API 基本信息

| 属性 | 值 |
|------|----|
| Plugin ID | `56017df0-1c14-4bdb-8ead-d1bfbd65db08` |
| API ID | `api-baBwmdOB6lG9` |
| Endpoint | `GET https://app-dvtmyuucfs3l-api-baBwmdOB6lG9-gateway.appmiaoda.com/tasks` |
| Auth 模式 | `platform_managed`（`traefik: true`） |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| third_part_domain | `app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com` |

秒哒生成应用时必须使用此完整 Endpoint，不得自行猜测或拼接其他网关基址。

Query 参数：

| 参数 | 类型 | 规则 |
|------|------|------|
| `task_ids` | string | 系统任务 ID；多个 ID 用逗号分隔 |
| `external_task_ids` | string | 用户自定义任务 ID；多个 ID 用逗号分隔 |

两种参数至少且只能使用一种，不能同时传，也不能都不传。

```text
GET /tasks?task_ids=893605946402811985
GET /tasks?external_task_ids=video-20260806-001
```

## 响应

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": [
    {
      "id": "893605946402811985",
      "status": "succeeded",
      "message": "",
      "create_time": 1781080778802,
      "update_time": 1781080794151,
      "external_id": "video-20260806-001",
      "outputs": [
        {
          "type": "video",
          "id": "video-id",
          "url": "https://example.com/video.mp4",
          "watermark_url": "https://example.com/video-watermark.mp4",
          "duration": "5"
        }
      ]
    }
  ]
}
```

状态：

- `submitted`：已提交；
- `processing`：处理中；
- `succeeded`：成功；
- `failed`：失败，读取 `message`。

查询可能返回多个任务。调用方必须按目标 `id` 或 `external_id` 精确匹配，不能直接取 `data[0]`。

成功后只从 `outputs` 中选择 `type=video`。如果成功但没有视频输出，保留完整任务信息并报响应不完整，不重新创建任务。

上游响应可能包含内部计费明细。Skill、CLI、Edge Function 和普通应用响应均不得向用户展示或原样转发该字段；计费只由平台受控配置和审计系统处理。

## 生成后查询后端契约

查询后端属于异步任务基础设施，由应用后端/API Plugin 配置完成。前端与查询 Edge Function 之间必须使用 POST body；前端不得依赖 Edge Function 的 GET query string 传参，因为 `supabase.functions.invoke()` 的调用链可能不会把 GET 查询参数传递给 Edge Function。

前端调用示例：

```typescript
const { data, error } = await supabase.functions.invoke("kling-3-turbo-query", {
  method: "POST",
  body: {
    task_id: "893605946402811985",
    // 或 external_task_id: "video-20260806-001"
  },
});
if (error) throw error;
```

查询 Edge Function 必须只解析一次 body，并要求 `task_id` 与 `external_task_id` 至少且只能传一个；随后由 Edge Function 将 body 转换为上游 GET query：

```typescript
const body = await req.json();
const taskId = body.task_id ? String(body.task_id) : undefined;
const externalTaskId = body.external_task_id ? String(body.external_task_id) : undefined;

if ((taskId && externalTaskId) || (!taskId && !externalTaskId)) {
  return Response.json({ error: "task_id 和 external_task_id 必须二选一" }, { status: 400 });
}

const query = taskId
  ? `task_ids=${encodeURIComponent(taskId)}`
  : `external_task_ids=${encodeURIComponent(externalTaskId!)}`;
const upstream = await fetch(`${TASKS_ENDPOINT}?${query}`, {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    "X-Gateway-Authorization": `Bearer ${apiKey}`,
  },
});
```

后端据此查询上游并返回规范化状态。上游 HTTP 或业务错误必须结构化透传安全的 `error`、`code`、`message`、`request_id` 和 HTTP 状态，不得统一返回“未知错误”。

后端需要：

1. 仅允许 `task_ids` 与 `external_task_ids` 二选一；
2. 在上游数组响应中按目标 ID 精确匹配任务，不能直接取第一项；
3. 将 `submitted`、`processing`、`succeeded`、`failed` 映射为应用统一状态；未知状态保持处理中并继续轮询，不能直接标记失败；
4. 成功时只选择 `outputs[type=video]`；
5. 以 `task.id + output.id` 为幂等键，将临时视频 URL 流式转存到应用存储；
6. 仅向前端返回任务状态、失败提示和持久化视频 URL；不得返回密钥、网关地址、API ID、计费字段或原始 Plugin 配置；
7. 转存失败时保留原任务状态并重试转存，不重新创建视频。

视频 URL 30 天后清理。只有完成转存后才能把持久化 URL 作为最终结果。

## 生成期查询与完整轮询代码

```typescript
const TASKS_ENDPOINT =
  "https://app-dvtmyuucfs3l-api-baBwmdOB6lG9-gateway.appmiaoda.com/tasks";
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

interface TurboTaskOutput {
  id: string;
  url: string;
  watermarkUrl?: string;
  duration?: string;
}

interface TurboTaskResult {
  taskId: string;
  externalTaskId?: string;
  status: "submitted" | "processing" | "succeeded" | "failed";
  message?: string;
  outputs: TurboTaskOutput[];
}

async function queryTurboVideoTask(
  taskId?: string,
  externalTaskId?: string,
): Promise<TurboTaskResult> {
  if ((taskId && externalTaskId) || (!taskId && !externalTaskId)) {
    throw new Error("taskId 和 externalTaskId 必须二选一");
  }

  const query = taskId
    ? `task_ids=${encodeURIComponent(taskId)}`
    : `external_task_ids=${encodeURIComponent(externalTaskId!)}`;

  const response = await fetch(`${TASKS_ENDPOINT}?${query}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
  });
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
    outputs: (task.outputs ?? [])
      .filter((output: { type?: string }) => output.type === "video")
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
): Promise<TurboTaskResult> {
  const intervalMs = 7000;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    const result = await queryTurboVideoTask(taskId);
    if (result.status === "succeeded" || result.status === "failed") return result;
  }

  throw new Error(`任务 ${taskId} 超时（等待超过 10 分钟）`);
}
```

---

## Edge Function 代码（含 Supabase Storage 转存）

```typescript
// supabase/functions/kling-3-turbo-query/index.ts
import { serve } from "https://deno.land/std/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const ENDPOINT = "https://app-dvtmyuucfs3l-api-baBwmdOB6lG9-gateway.appmiaoda.com/tasks";
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function transferVideo(taskId: string, output: { id: string; url: string }) {
  const response = await fetch(output.url);
  if (!response.ok || !response.body) throw new Error(`下载视频失败：${response.status}`);

  const path = `kling-3-turbo/${taskId}-${output.id}.mp4`;
  const { error } = await supabase.storage
    .from("generated-media")
    .upload(path, response.body, {
      contentType: response.headers.get("content-type") ?? "video/mp4",
      upsert: true,
    });
  if (error) throw error;

  return supabase.storage.from("generated-media").getPublicUrl(path).data.publicUrl;
}

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") return Response.json({ error: "Method Not Allowed" }, { status: 405 });

  try {
    const body = await req.json();
    const taskId = body.task_id ? String(body.task_id) : undefined;
    const externalTaskId = body.external_task_id ? String(body.external_task_id) : undefined;
    if ((taskId && externalTaskId) || (!taskId && !externalTaskId)) {
      return Response.json({ error: "task_id 和 external_task_id 必须二选一" }, { status: 400 });
    }

    const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!apiKey) return Response.json({ error: "视频服务配置缺失" }, { status: 500 });
    const authorization = apiKey.startsWith("Bearer ") ? apiKey : `Bearer ${apiKey}`;
    const query = taskId
      ? `task_ids=${encodeURIComponent(taskId)}`
      : `external_task_ids=${encodeURIComponent(externalTaskId!)}`;

    const upstream = await fetch(`${ENDPOINT}?${query}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": authorization,
      },
    });
    const data = await upstream.json().catch(() => ({}));

    if (!upstream.ok || data.code !== 0) {
      return Response.json({
        error: data.message || "查询视频任务失败",
        type: upstream.status >= 500 ? "upstream_unavailable" : "upstream_error",
        code: data.code,
        message: data.message,
        request_id: data.request_id,
      }, { status: upstream.status || 502 });
    }

    const tasks = Array.isArray(data.data) ? data.data : [];
    const task = tasks.find((item: { id?: string; external_id?: string }) =>
      taskId ? String(item.id) === taskId : item.external_id === externalTaskId
    );
    if (!task) return Response.json({ error: "查询响应中未找到目标任务" }, { status: 502 });

    if (task.status === "failed") {
      return Response.json({ status: "failed", task_id: String(task.id), message: task.message });
    }
    if (task.status !== "succeeded") {
      return Response.json({ status: task.status, task_id: String(task.id) });
    }

    const outputs = (task.outputs ?? []).filter((output: { type?: string; url?: string }) =>
      output.type === "video" && output.url
    );
    if (!outputs.length) {
      return Response.json({ error: "任务成功但响应中没有视频输出" }, { status: 502 });
    }

    try {
      const videos = await Promise.all(outputs.map(async (output: { id: string; url: string; duration?: string }) => ({
        id: output.id,
        url: await transferVideo(String(task.id), output),
        duration: output.duration,
      })));
      return Response.json({ status: "succeeded", task_id: String(task.id), videos });
    } catch (error) {
      console.error("[kling-3-turbo-query transfer]", error);
      return Response.json({
        status: "processing",
        transfer_status: "pending",
        message: "视频已生成，正在转存，请稍后继续查询",
      });
    }
  } catch (error) {
    console.error("[kling-3-turbo-query]", error);
    return Response.json({ error: "查询服务异常", type: "gateway_error" }, { status: 502 });
  }
});
```

---

## 前端轮询代码

```typescript
async function queryTurboTask(taskId: string) {
  const { data, error } = await supabase.functions.invoke("kling-3-turbo-query", {
    method: "POST",
    body: { task_id: taskId },
  });
  if (error) throw error;
  return data;
}

async function waitForTurboTask(taskId: string) {
  const deadline = Date.now() + 10 * 60 * 1000;
  while (Date.now() < deadline) {
    const result = await queryTurboTask(taskId);
    if (result.status === "succeeded") return result;
    if (result.status === "failed") throw new Error(result.message || "视频生成失败");
    await new Promise((resolve) => setTimeout(resolve, 7000));
  }
  throw new Error("视频生成超时，可稍后使用任务 ID 继续查询");
}
```

## 历史任务游标查询

新版还提供 `POST /tasks` 游标查询，但它不是生成主链路。本 Skill 暂不封装该能力，以免把创作 Skill 变成任务管理工具。
