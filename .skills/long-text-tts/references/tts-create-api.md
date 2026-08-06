# TTS Create API — 创建长文本语音合成任务

## API 基本信息

| 字段 | 值 |
|------|----|
| Plugin ID | `6c2d8399-c9ba-40d4-9f5f-96dfc9b71a68` |
| API ID | `api-nYWNozBb8X3L` |
| Endpoint | `POST https://app-dvtmyuucfs3l-api-nYWNozBb8X3L-gateway.appmiaoda.com/rpc/2.0/tts/v1/create` |
| 生成期 URL | `https://app-dvtmyuucfs3l-api-nYWNozBb8X3L-gateway.appmiaoda.com/rpc/2.0/tts/v1/create` |
| Auth 模式 | `platform_managed`（traefik: true） |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Content-Type | `application/json` |
| Third-party domain | `app-dvtmyuucfs3l-api-nYWNozBb8X3L-gateway.appmiaoda.com` |
| 计费 | 启用（按调用次数计费） |

---

## 请求参数表

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `text` | `array` | 是 | — | 待合成的文本数组，UTF-8 编码，总字数不超过 10 万字符 |
| `format` | `string` | 否 | `"mp3-16k"` | 音频格式：`mp3-16k` / `mp3-48k` / `wav` |
| `voice` | `integer` | 否 | `0` | 音库：度小宇=1，度小美=0，度逍遥=3，度丫丫=4 |
| `speed` | `integer` | 否 | `5` | 语速，范围 0–15 |
| `pitch` | `integer` | 否 | `5` | 音调，范围 0–15 |
| `volume` | `integer` | 否 | `5` | 音量，范围 0–15 |
| `break` | `integer` | 否 | `0` | 段落间隔时长，单位毫秒，范围 0–5000 |

---

## 响应字段表

### 成功响应（200）

| 字段 | 类型 | 说明 |
|------|------|------|
| `log_id` | `number` | 日志 ID，用于问题排查 |
| `task_id` | `string` | 合成任务 ID，用于后续查询（如 `"234acb234acb234acb234acb"`） |
| `task_status` | `string` | 任务初始状态，通常为 `"Running"` |

### 失败响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `error_code` | `number` | 错误码（18 = QPS 超限） |
| `error_msg` | `string` | 错误描述 |

---

## 生成期用法

生成期（Agent 直接调用）已改为脚本调用方式，不再使用本节 API 的内联调用代码。具体命令示例、参数拼接方式、以及提交/轮询/超时后续查询逻辑，见 `SKILL.md` 的"生成期用法（Agent 直接调用）"一节（对应脚本 `scripts/generate_tts.py` 和 `scripts/query_tts.py`）。

---

## Edge Function 代码

```typescript
// edge-functions/tts-create.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- 解析客户端请求 ---
  let text: string[];
  let format: string | undefined;
  let voice: number | undefined;
  let speed: number | undefined;
  let pitch: number | undefined;
  let volume: number | undefined;
  let breakMs: number | undefined;

  try {
    const body = await req.json();
    text = body.text;
    if (!Array.isArray(text) || text.length === 0) {
      throw new Error("Missing or empty text array");
    }
    format = body.format;
    voice = body.voice;
    speed = body.speed;
    pitch = body.pitch;
    volume = body.volume;
    breakMs = body.break;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- 注入平台密钥（禁止暴露至客户端） ---
  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- 构造上游请求体 ---
  const upstreamBody: Record<string, unknown> = { text };
  if (format !== undefined) upstreamBody.format = format;
  if (voice !== undefined) upstreamBody.voice = voice;
  if (speed !== undefined) upstreamBody.speed = speed;
  if (pitch !== undefined) upstreamBody.pitch = pitch;
  if (volume !== undefined) upstreamBody.volume = volume;
  if (breakMs !== undefined) upstreamBody.break = breakMs;

  // --- 调用上游 API ---
  const upstream = await fetch(
    "https://app-dvtmyuucfs3l-api-nYWNozBb8X3L-gateway.appmiaoda.com/rpc/2.0/tts/v1/create",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify(upstreamBody),
    }
  );

  // 透传配额/余额错误
  if (upstream.status === 429 || upstream.status === 402) {
    const errText = await upstream.text();
    return new Response(errText, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!upstream.ok) {
    return new Response(
      JSON.stringify({ error: `Upstream error: ${upstream.status}` }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }

  const data = await upstream.json();
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
```

---

## 前端调用代码

### Web & MiniProgram（通用，使用 supabase client）

```typescript
/**
 * 通过 Edge Function 创建 TTS 任务，返回 task_id。
 * @param text - 待合成的文本数组
 * @param options - 可选音频配置
 * @returns task_id 字符串
 */
async function createTTSTask(
  text: string[],
  options?: {
    format?: "mp3-16k" | "mp3-48k" | "wav";
    voice?: 0 | 1 | 3 | 4;
    speed?: number;
    pitch?: number;
    volume?: number;
    break?: number;
  }
): Promise<string> {
  const { data, error } = await supabase.functions.invoke("tts-create", {
    body: { text, ...options },
  });
  if (error) throw error;
  if (!data.task_id) throw new Error(`创建 TTS 任务失败: ${JSON.stringify(data)}`);
  return data.task_id as string;
}
```

---

## 注意事项

- **密钥安全**：`INTEGRATIONS_API_KEY` 仅在 Edge Function 服务端读取，严禁暴露到前端
- **计费**：调用 `tts-create` 会产生费用；避免重复提交相同任务
- **错误处理**：务必处理 429（配额超限）和 402（余额不足）；`error_code: 18` 表示 QPS 超限，需退避后重试
- **任务 ID 持久化**：获取 `task_id` 后应立即存入 Supabase DB，防止页面刷新后丢失轮询状态
- **文本长度限制**：总字数不超过 10 万字符，超出需分批提交
