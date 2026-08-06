# Kling 3.0 Turbo 图生视频 API

## API 基本信息

| 属性 | 值 |
|------|----|
| Plugin ID | `56017df0-1c14-4bdb-8ead-d1bfbd65db08` |
| API ID | `api-eLMlzO5Veyw9` |
| Endpoint | `POST https://app-dvtmyuucfs3l-api-eLMlzO5Veyw9-gateway.appmiaoda.com/image-to-video/kling-3.0-turbo` |
| Auth 模式 | `platform_managed`（`traefik: true`） |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Content-Type | `application/json` |
| third_part_domain | `app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com` |
| 返回 | 异步任务；读取 `data.id` |

上游密钥只保存在 API Plugin 后端；前端和 Skill 不保存真实密钥。秒哒生成应用时必须使用此完整 Endpoint，不得自行猜测或拼接其他网关基址。

## 请求体

```json
{
  "contents": [
    { "type": "prompt", "text": "人物缓慢转头看向镜头" },
    { "type": "first_frame", "url": "https://example.com/first-frame.png" }
  ],
  "settings": {
    "resolution": "1080p",
    "duration": 5
  },
  "options": {
    "external_task_id": "image-video-20260807-001",
    "watermark_info": { "enabled": false }
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `contents` | array | 是 | 包含提示词和首帧素材 |
| `contents[].type` | string | 是 | `prompt` 或 `first_frame` |
| `contents[].text` | string | 条件必填 | `type=prompt` 时使用；最大 2500 字符 |
| `contents[].url` | string | 条件必填 | `type=first_frame` 时使用；URL 或纯 Base64 |
| `settings.resolution` | string | 否 | `720p` 或 `1080p`；默认 `720p` |
| `settings.duration` | integer | 否 | 3–15 秒；默认 5 |
| `options.callback_url` | string | 否 | 服务端 HTTPS Callback 地址 |
| `options.external_task_id` | string | 否 | 单用户内唯一，用于查询与创建查重 |
| `options.watermark_info.enabled` | boolean | 否 | 是否生成含水印结果；默认 `false` |

`contents` 必须包含且只能包含一个 `first_frame`。可选提示词使用 `contents` 中的 `type=prompt` 对象；如果提示词使用官方多镜头格式，也只能作为该对象的普通 `text` 字段提交，不添加独立多镜头字段。当前不支持尾帧、视频参考或 `model` 字段。秒哒生成应用时，Edge Function 必须按 HTTP 状态和 JSON `code` 检查结果；失败时保留安全的 `error`、`code`、`message` 和 `request_id`，不得统一返回“未知错误”。首帧支持 jpg/jpeg/png，最大 50MB，宽高均不小于 300px，宽高比范围为 1:2.5 至 2.5:1。Base64 不得写入日志、终端摘要或 LLM 上下文。

## 创建响应

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "id": "893605946402811985",
    "status": "submitted",
    "create_time": 1781080778802,
    "update_time": 1781080794151,
    "external_id": "image-video-20260807-001"
  }
}
```

`data.id` 是后续查询使用的系统任务 ID。

---

## 生成期代码（Agent 直接调用）

```typescript
const IMAGE_ENDPOINT =
  "https://app-dvtmyuucfs3l-api-eLMlzO5Veyw9-gateway.appmiaoda.com/image-to-video/kling-3.0-turbo";
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

interface CreateTurboImageParams {
  firstFrame: string;
  prompt?: string;
  resolution?: "720p" | "1080p";
  duration?: number;
  callbackUrl?: string;
  externalTaskId?: string;
  watermarkEnabled?: boolean;
}

async function createTurboImageTask(params: CreateTurboImageParams): Promise<{
  taskId: string;
  externalTaskId?: string;
  status: "submitted" | "processing";
}> {
  if (!params.firstFrame) throw new Error("firstFrame 不能为空");
  if (params.prompt && params.prompt.length > 2500) throw new Error("prompt 不能超过 2500 字符");

  const contents: Array<Record<string, string>> = [];
  if (params.prompt?.trim()) contents.push({ type: "prompt", text: params.prompt.trim() });
  contents.push({ type: "first_frame", url: params.firstFrame });

  const response = await fetch(IMAGE_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      contents,
      settings: {
        resolution: params.resolution ?? "720p",
        duration: params.duration ?? 5,
      },
      options: {
        external_task_id: params.externalTaskId ?? crypto.randomUUID(),
        watermark_info: { enabled: params.watermarkEnabled ?? false },
        ...(params.callbackUrl ? { callback_url: params.callbackUrl } : {}),
      },
    }),
  });

  const json = await response.json();
  if (!response.ok || json.code !== 0) {
    throw new Error(`API 错误 ${json.code ?? response.status}：${json.message ?? "创建失败"}`);
  }
  if (!json.data?.id) throw new Error("创建响应缺少 data.id");

  return {
    taskId: String(json.data.id),
    externalTaskId: json.data.external_id,
    status: json.data.status,
  };
}
```

完整轮询调用：

```typescript
const created = await createTurboImageTask({
  firstFrame: "https://example.com/first-frame.png",
  prompt: "人物缓慢转头看向镜头",
  resolution: "1080p",
  duration: 5,
  externalTaskId: `image-${crypto.randomUUID()}`,
});

const result = await pollTurboVideoTask(created.taskId);
if (result.status === "failed") throw new Error(result.message || "视频生成失败");
console.log("视频 URL：", result.outputs?.[0]?.url);
```

`pollTurboVideoTask` 见 `task-query-api.md`。

---

## Edge Function 代码

```typescript
// supabase/functions/kling-3-turbo-image-create/index.ts
import { serve } from "https://deno.land/std/http/server.ts";

const ENDPOINT =
  "https://app-dvtmyuucfs3l-api-eLMlzO5Veyw9-gateway.appmiaoda.com/image-to-video/kling-3.0-turbo";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") return Response.json({ error: "Method Not Allowed" }, { status: 405 });

  try {
    const body = await req.json();
    const firstFrame = String(body.first_frame_url ?? "").trim();
    const prompt = String(body.prompt ?? "").trim();
    const duration = Number(body.duration ?? 5);
    const resolution = body.resolution ?? "720p";

    if (!firstFrame) return Response.json({ error: "请提供首帧图片" }, { status: 400 });
    if (prompt.length > 2500) return Response.json({ error: "视频描述不能超过 2500 字符" }, { status: 400 });
    if (!Number.isInteger(duration) || duration < 3 || duration > 15) {
      return Response.json({ error: "视频时长必须为 3-15 秒整数" }, { status: 400 });
    }
    if (!["720p", "1080p"].includes(resolution)) {
      return Response.json({ error: "分辨率必须为 720p 或 1080p" }, { status: 400 });
    }

    const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!apiKey) return Response.json({ error: "视频服务配置缺失" }, { status: 500 });
    const authorization = apiKey.startsWith("Bearer ") ? apiKey : `Bearer ${apiKey}`;

    const contents: Array<Record<string, string>> = [];
    if (prompt) contents.push({ type: "prompt", text: prompt });
    contents.push({ type: "first_frame", url: firstFrame });

    const upstream = await fetch(ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": authorization,
      },
      body: JSON.stringify({
        contents,
        settings: { resolution, duration },
        options: {
          external_task_id: body.external_task_id ?? crypto.randomUUID(),
          watermark_info: { enabled: Boolean(body.watermark_enabled) },
        },
      }),
    });

    const data = await upstream.json().catch(() => ({}));
    if (!upstream.ok || data.code !== 0) {
      return Response.json({
        error: data.message || "视频任务创建失败",
        type: upstream.status >= 500 ? "upstream_unavailable" : "upstream_error",
        code: data.code,
        message: data.message,
        request_id: data.request_id,
      }, { status: upstream.status || 502 });
    }
    if (!data.data?.id) return Response.json({ error: "创建响应缺少任务 ID" }, { status: 502 });

    return Response.json({
      task_id: String(data.data.id),
      external_task_id: data.data.external_id,
      status: data.data.status,
    });
  } catch (error) {
    console.error("[kling-3-turbo-image-create]", error);
    return Response.json({ error: "视频服务请求异常", type: "gateway_error" }, { status: 502 });
  }
});
```

---

## 前端调用代码

```typescript
async function submitTurboImageVideo(params: {
  first_frame_url: string;
  prompt?: string;
  resolution?: "720p" | "1080p";
  duration?: number;
}): Promise<string> {
  const { data, error } = await supabase.functions.invoke("kling-3-turbo-image-create", {
    body: { ...params, external_task_id: `image-${crypto.randomUUID()}` },
  });
  if (error) throw error;
  if (!data?.task_id) throw new Error("创建响应缺少任务 ID");
  return data.task_id;
}
```
