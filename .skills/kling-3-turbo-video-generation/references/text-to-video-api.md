# Kling 3.0 Turbo 文生视频 API

## API 基本信息

| 属性 | 值 |
|------|----|
| Plugin ID | `56017df0-1c14-4bdb-8ead-d1bfbd65db08` |
| API ID | `api-zYm4DV8yrj8L` |
| Endpoint | `POST https://app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com/text-to-video/kling-3.0-turbo` |
| Auth 模式 | `platform_managed`（`traefik: true`） |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Content-Type | `application/json` |
| third_part_domain | `app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com` |
| 返回 | 异步任务；读取 `data.id` |

上游密钥只保存在 API Plugin 后端；前端和 Skill 不保存真实密钥。秒哒生成应用时必须使用此完整 Endpoint，不得自行猜测或拼接其他网关基址。

## 请求体

```json
{
  "prompt": "雨夜的城市街道，霓虹灯倒映在路面",
  "settings": {
    "resolution": "1080p",
    "aspect_ratio": "16:9",
    "duration": 5
  },
  "options": {
    "external_task_id": "video-20260807-001",
    "watermark_info": { "enabled": false }
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | 是 | 文本提示词；最大 3072 字符，建议不超过 2500 |
| `settings.resolution` | string | 否 | `720p` 或 `1080p`；默认 `720p` |
| `settings.aspect_ratio` | string | 否 | `16:9`、`9:16`、`1:1`；默认 `16:9` |
| `settings.duration` | integer | 否 | 3–15 秒；默认 5 |
| `options.callback_url` | string | 否 | 服务端 HTTPS Callback 地址 |
| `options.external_task_id` | string | 否 | 单用户内唯一，用于查询与创建查重 |
| `options.watermark_info.enabled` | boolean | 否 | 是否生成含水印结果；默认 `false` |

模型版本由路径确定，**不得传入** `model` 字段。

秒哒生成应用时，Edge Function 必须按 HTTP 状态和 JSON `code` 检查结果；失败时保留安全的 `error`、`code`、`message` 和 `request_id`，不得统一返回“未知错误”。

Turbo 支持通过 Prompt 固定格式生成多镜头视频，但不提供独立的多镜头 API 参数或 Omni 式多镜头控制字段。格式为：`镜头 n, m, words; 镜头 n, m, words;`。

- `n`：分镜序号，最多 6 个分镜，最少 1 个分镜；
- `m`：分镜时长，每个分镜不小于 1 秒，所有分镜时长之和必须等于当前视频总时长；
- `words`：分镜提示词，每段最大 512 字符；
- 使用半角分号分隔各个分镜；
- 只能将该格式作为普通 `prompt` 字符串提交，不得添加 `multi_shot`、`shot_type`、`multi_prompt` 等请求字段。

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
    "external_id": "video-20260807-001"
  }
}
```

`data.id` 是后续查询使用的系统任务 ID。

---

## 生成期代码（Agent 直接调用）

```typescript
const TEXT_ENDPOINT =
  "https://app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com/text-to-video/kling-3.0-turbo";
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

interface CreateTurboTextParams {
  prompt: string;
  resolution?: "720p" | "1080p";
  aspectRatio?: "16:9" | "9:16" | "1:1";
  duration?: number;
  callbackUrl?: string;
  externalTaskId?: string;
  watermarkEnabled?: boolean;
}

interface CreateTurboTaskResult {
  taskId: string;
  externalTaskId?: string;
  status: "submitted" | "processing";
  createdAt?: number;
  updatedAt?: number;
}

async function createTurboTextTask(
  params: CreateTurboTextParams,
): Promise<CreateTurboTaskResult> {
  if (!params.prompt.trim()) throw new Error("prompt 不能为空");
  if (params.prompt.length > 3072) throw new Error("prompt 不能超过 3072 字符");

  const response = await fetch(TEXT_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      prompt: params.prompt.trim(),
      settings: {
        resolution: params.resolution ?? "720p",
        aspect_ratio: params.aspectRatio ?? "16:9",
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
    createdAt: json.data.create_time,
    updatedAt: json.data.update_time,
  };
}
```

完整轮询调用：

```typescript
const created = await createTurboTextTask({
  prompt: "雨夜的城市街道，霓虹灯倒映在路面",
  resolution: "1080p",
  aspectRatio: "16:9",
  duration: 5,
  externalTaskId: `text-${crypto.randomUUID()}`,
});

const result = await pollTurboVideoTask(created.taskId);
if (result.status === "failed") throw new Error(result.message || "视频生成失败");
console.log("视频 URL：", result.outputs?.[0]?.url);
```

`pollTurboVideoTask` 见 `task-query-api.md`。

---

## Edge Function 代码

```typescript
// supabase/functions/kling-3-turbo-text-create/index.ts
import { serve } from "https://deno.land/std/http/server.ts";

const ENDPOINT =
  "https://app-dvtmyuucfs3l-api-zYm4DV8yrj8L-gateway.appmiaoda.com/text-to-video/kling-3.0-turbo";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") return Response.json({ error: "Method Not Allowed" }, { status: 405 });

  try {
    const body = await req.json();
    const prompt = String(body.prompt ?? "").trim();
    const duration = Number(body.duration ?? 5);
    const resolution = body.resolution ?? "720p";
    const aspectRatio = body.aspect_ratio ?? "16:9";

    if (!prompt) return Response.json({ error: "请输入视频描述" }, { status: 400 });
    if (prompt.length > 3072) return Response.json({ error: "视频描述不能超过 3072 字符" }, { status: 400 });
    if (!Number.isInteger(duration) || duration < 3 || duration > 15) {
      return Response.json({ error: "视频时长必须为 3-15 秒整数" }, { status: 400 });
    }
    if (!["720p", "1080p"].includes(resolution)) {
      return Response.json({ error: "分辨率必须为 720p 或 1080p" }, { status: 400 });
    }
    if (!["16:9", "9:16", "1:1"].includes(aspectRatio)) {
      return Response.json({ error: "画面比例必须为 16:9、9:16 或 1:1" }, { status: 400 });
    }

    const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!apiKey) return Response.json({ error: "视频服务配置缺失" }, { status: 500 });
    const authorization = apiKey.startsWith("Bearer ") ? apiKey : `Bearer ${apiKey}`;

    const upstream = await fetch(ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": authorization,
      },
      body: JSON.stringify({
        prompt,
        settings: { resolution, aspect_ratio: aspectRatio, duration },
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
    console.error("[kling-3-turbo-text-create]", error);
    return Response.json({ error: "视频服务请求异常", type: "gateway_error" }, { status: 502 });
  }
});
```

---

## 前端调用代码

```typescript
async function submitTurboTextVideo(params: {
  prompt: string;
  resolution?: "720p" | "1080p";
  aspect_ratio?: "16:9" | "9:16" | "1:1";
  duration?: number;
}): Promise<string> {
  const { data, error } = await supabase.functions.invoke("kling-3-turbo-text-create", {
    body: { ...params, external_task_id: `text-${crypto.randomUUID()}` },
  });
  if (error) throw error;
  if (!data?.task_id) throw new Error("创建响应缺少任务 ID");
  return data.task_id;
}
```
