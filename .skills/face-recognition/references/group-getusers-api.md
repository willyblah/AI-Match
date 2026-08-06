# 获取用户列表接口（group-getusers）

## API 基本信息

| 字段 | 值 |
|------|----|
| Plugin ID | `faf0f771-1a33-47a4-a111-c128e647a25e` |
| API ID | `api-baBwZEjb7P19` |
| Endpoint | `POST https://app-dvtmyuucfs3l-api-baBwZEjb7P19-gateway.appmiaoda.com/rest/2.0/face/v3/faceset/group/getusers` |
| Auth 模式 | `platform_managed` |
| Auth Header | `X-Gateway-Authorization: Bearer <INTEGRATIONS_API_KEY>` |
| Content-Type | `application/json` |
| third_part_domain | `app-dvtmyuucfs3l-api-baBwZEjb7P19-gateway.appmiaoda.com` |
| 计费 | 否 |

## 请求参数表

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `start` | integer | 否 | 起始序号，默认值 0 |
| `length` | integer | 否 | 返回数量，默认值 100，最大值 1000 |

## 响应字段表

### 成功响应（error_code: 0）

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `result.user_id_list` | array | 用户 ID 列表数组 |
| `log_id` | number | 请求唯一标识码 |
| `error_code` | number | 错误码，0 表示成功 |
| `error_msg` | string | 错误描述，成功时为 "SUCCESS" |
| `cached` | number | 是否命中缓存（0：未命中，1：命中） |
| `timestamp` | number | 响应时间戳 |

### 失败响应

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `error_code` | number | 非 0 的错误码 |
| `error_msg` | string | 错误描述信息 |
| `log_id` | number | 请求唯一标识码 |

## 生成期代码

生成期调用已改为脚本方式，模型不再生成内联 TypeScript；只需拼命令并执行即可。脚本内部完成请求上游接口全部操作，模型只接收最终 JSON 结果。

```bash
python3 <skill-path>/scripts/call_group_getusers.py [--start 0] [--length 100]
```

脚本成功时 stdout 输出一行 JSON（即上游接口原始响应，含 `result.user_id_list` 等字段）。

## Edge Function 代码

```typescript
// edge-functions/face-group-getusers.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  let start: number | undefined;
  let length: number | undefined;

  try {
    const body = await req.json();
    start = body.start;
    length = body.length;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  const requestBody: Record<string, number> = {};
  if (start !== undefined) requestBody.start = start;
  if (length !== undefined) requestBody.length = length;

  const upstream = await fetch(
    "https://app-dvtmyuucfs3l-api-baBwZEjb7P19-gateway.appmiaoda.com/rest/2.0/face/v3/faceset/group/getusers",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify(requestBody),
    }
  );

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

## 前端调用代码

### Web / MiniProgram（通用）

```typescript
/**
 * 调用用户列表获取 Edge Function，查询指定用户组中的用户 ID 列表。
 * @param start - 起始序号，默认 0
 * @param length - 返回数量，默认 100
 * @returns 用户 ID 列表
 */
async function getGroupUsers(start = 0, length = 100) {
  const { data, error } = await supabase.functions.invoke("face-group-getusers", {
    body: { start, length },
  });
  if (error) throw error;
  if (data.error_code !== 0) throw new Error(`API 错误 ${data.error_code}：${data.error_msg}`);
  return data.result;
}
```

## 注意事项

- **密钥安全**：`INTEGRATIONS_API_KEY` 仅可在 Edge Function 服务端读取，严禁暴露到前端。
- **计费**：本接口不计费，可正常频率调用。
- **分页**：单次最多返回 1000 条记录，如需遍历大量用户请配合 `start` 参数进行分页。
- **错误处理**：务必处理 429（配额超限）和 402（余额不足）两类错误。
