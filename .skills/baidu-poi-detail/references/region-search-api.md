# 行政区划区域检索 API

## API 基本信息

| 项目 | 值 |
|------|-----|
| Plugin ID | `d5c0b7d3-bc6a-4d3a-b8a2-e37246fac4df` |
| API ID | `api-ra5EZvmRrG4a` |
| Endpoint | `GET https://app-dvtmyuucfs3l-api-ra5EZvmRrG4a-gateway.appmiaoda.com/place/v3/region` |
| Auth | `X-Gateway-Authorization: Bearer <INTEGRATIONS_API_KEY>`（platform_managed） |
| Content-Type | 无请求体（GET 参数通过 URL 查询串传递） |
| Third-party domain | `app-dvtmyuucfs3l-api-ra5EZvmRrG4a-gateway.appmiaoda.com` |
| 计费 | 按次计费 |

---

## 请求参数表

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `query` | string | 是 | — | 检索关键字，如「天安门」「美食」 |
| `region` | string | 是 | — | 检索行政区划区域，支持到区县级，如「北京市海淀区」 |
| `region_limit` | boolean | 否 | — | 是否严格限制在区域内召回，true/false |
| `type` | string | 否 | — | 对 query 结果进行二次筛选，参考 POI 分类 |
| `scope` | integer | 否 | 1 | 结果详细程度，1 为基本信息，2 为详细信息 |
| `page_num` | integer | 否 | 0 | 分页页码 |
| `page_size` | integer | 否 | — | 单次召回数量，10-20 条 |

---

## 响应字段表

### 成功响应（status=0）

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `status` | integer | 状态码，0 表示成功 |
| `message` | string | 状态信息，成功时为 "ok" |
| `result_type` | string | 结果类型，如 "poi_type" |
| `results` | array | POI 信息数组 |
| `results[].name` | string | POI 名称 |
| `results[].location` | object | 经纬度坐标 |
| `results[].location.lng` | number | 经度 |
| `results[].location.lat` | number | 纬度 |
| `results[].address` | string | 详细地址 |
| `results[].province` | string | 所属省份 |
| `results[].city` | string | 所属城市 |
| `results[].area` | string | 所属区域 |
| `results[].uid` | string | POI 唯一标识 |
| `results[].detail_info` | object? | 详细信息（scope=2 时返回） |

### 失败响应（status≠0）

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `status` | integer | 错误状态码（非 0） |
| `message` | string | 错误说明 |

---

## 响应示例

```json
{
  "status": 0,
  "message": "ok",
  "result_type": "poi_type",
  "results": [
    {
      "name": "中国银行ATM",
      "location": {"lng": 116.315, "lat": 40.043},
      "address": "上地信息路15号",
      "province": "北京市",
      "city": "北京市",
      "area": "海淀区",
      "uid": "05478f385d3729eef4eafc16"
    }
  ]
}
```

---

## 生成期代码

生成期调用请使用 `SKILL.md` 中的脚本方式：

```bash
python3 <skill-path>/scripts/call_poi_search.py region --query "银行" --region "北京市海淀区" --scope 2 --page-size 10
```

脚本内部负责读取 `INTEGRATIONS_API_KEY`、发送请求并输出行政区划检索结果。这里不再维护内联请求代码，避免生成期重复消耗 token。

---

## Edge Function 代码

```typescript
// edge-functions/baidu-poi-region.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- 解析客户端请求 ---
  let query: string;
  let region: string;
  let regionLimit: boolean | undefined;
  let type: string | undefined;
  let scope: number | undefined;
  let pageNum: number | undefined;
  let pageSize: number | undefined;

  try {
    const body = await req.json();
    query = body.query;
    region = body.region;
    if (!query) throw new Error("Missing query");
    if (!region) throw new Error("Missing region");
    regionLimit = body.region_limit;
    type = body.type;
    scope = body.scope;
    pageNum = body.page_num;
    pageSize = body.page_size;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- 注入平台密钥（不暴露给客户端）---
  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- 构建查询参数 ---
  const params = new URLSearchParams({ query, region });
  if (regionLimit !== undefined) params.set("region_limit", String(regionLimit));
  if (type) params.set("type", type);
  if (scope !== undefined) params.set("scope", String(scope));
  if (pageNum !== undefined) params.set("page_num", String(pageNum));
  if (pageSize !== undefined) params.set("page_size", String(pageSize));

  // --- 调用上游接口 ---
  const upstream = await fetch(
    `https://app-dvtmyuucfs3l-api-ra5EZvmRrG4a-gateway.appmiaoda.com/place/v3/region?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
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

### 推荐方式（supabase client 可用时）

```typescript
interface RegionSearchParams {
  query: string;
  region: string;
  region_limit?: boolean;
  type?: string;
  scope?: 1 | 2;
  page_num?: number;
  page_size?: number;
}

/**
 * 通过 Edge Function 调用行政区划 POI 检索。
 * @param params - 检索参数
 * @returns POI 列表
 */
async function searchPoiByRegion(params: RegionSearchParams) {
  const { data, error } = await supabase.functions.invoke("baidu-poi-region", {
    body: params,
  });
  if (error) throw error;
  if (data.status !== 0) throw new Error(`API 错误 ${data.status}：${data.message}`);
  return data.results;
}
```

### 备用方式（无法使用 supabase client 时）

```typescript
/**
 * 通过原生 fetch 调用行政区划 POI 检索 Edge Function。
 * @param params - 检索参数
 * @returns POI 列表
 */
async function searchPoiByRegion(params: RegionSearchParams) {
  const res = await fetch(
    `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/baidu-poi-region`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }
  );

  if (res.status === 429) {
    const err = await res.json();
    throw new Error(`配额已用尽：${err.message ?? res.statusText}`);
  }
  if (res.status === 402) {
    const err = await res.json();
    throw new Error(`余额不足：${err.message ?? res.statusText}`);
  }
  if (!res.ok) throw new Error(`请求失败：${res.status}`);

  const json = await res.json();
  if (json.status !== 0) throw new Error(`API 错误 ${json.status}：${json.message}`);
  return json.results;
}
```

---

## 注意事项

- **密钥安全**：`INTEGRATIONS_API_KEY` 仅可在 Edge Function 服务端读取，严禁暴露到前端。
- **错误处理**：务必处理 429（配额超限）和 402（余额不足）。
- **计费**：按次计费，避免不必要的重复调用。
- **region 参数**：支持到区县级，如「北京市」「海淀区」均可，过于宽泛可能导致结果过多。
- **scope=2**：返回详细信息，但会增加响应数据量，按需使用。
- **page_size**：范围 10-20 条，超出范围可能被截断。
