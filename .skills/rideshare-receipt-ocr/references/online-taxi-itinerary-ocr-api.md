# 网约车行程单识别 API

## API 基本信息

| 字段 | 值 |
|------|-----|
| Plugin ID | `ee3a6608-c49a-4361-b6fb-fdd5aa131cfa` |
| API ID | `api-zYkZz8qoKp1L` |
| Endpoint | `POST https://app-dvtmyuucfs3l-api-zYkZz8qoKp1L-gateway.appmiaoda.com/rest/2.0/ocr/v1/online_taxi_itinerary` |
| Content-Type | `application/x-www-form-urlencoded` |
| 认证模式 | `platform_managed` |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| third_part_domain | `app-dvtmyuucfs3l-api-zYkZz8qoKp1L-gateway.appmiaoda.com` |
| 支持平台 | Web、MiniProgram |

---

## 请求参数表

> 四个输入参数互斥，优先级为：image > url > pdf_file > ofd_file，提供其一即可。

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `image` | string | 否 | — | 图片 base64 编码，最大 4 MB，支持 jpg/jpeg/png/bmp |
| `url` | string | 否 | — | 图片完整 HTTP/HTTPS URL 地址 |
| `pdf_file` | string | 否 | — | PDF 文件 base64 编码 |
| `pdf_file_num` | string | 否 | `"1"` | PDF 页码，默认第 1 页 |
| `ofd_file` | string | 否 | — | OFD 文件 base64 编码 |
| `ofd_file_num` | string | 否 | `"1"` | OFD 页码，默认第 1 页 |

---

## 响应字段表

### 成功响应（HTTP 200）

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `log_id` | `string` | 请求唯一标识 |
| `words_result_num` | `number` | 识别到的字段数量 |
| `words_result.ServiceProvider` | `string` | 服务商名称（如"滴滴企业版"） |
| `words_result.StartTime` | `string` | 行程起始时间 |
| `words_result.EndTime` | `string` | 行程结束时间 |
| `words_result.Phone` | `string` | 联系电话 |
| `words_result.TotalFare` | `string` | 总金额（字符串，单位元） |
| `words_result.ItemNum` | `string` | 行程数量 |
| `words_result.items` | `array` | 行程明细数组 |
| `words_result.items[].ItemId` | `string` | 行程序号 |
| `words_result.items[].PickupDate` | `string` | 上车日期（格式 yy-MM-dd） |
| `words_result.items[].PickupTime` | `string` | 上车时间（格式 HH:mm） |
| `words_result.items[].StartPlace` | `string` | 出发地 |
| `words_result.items[].DestinationPlace` | `string` | 目的地 |
| `words_result.items[].CarType` | `string` | 车型（如"快车"） |
| `words_result.items[].Distance` | `string` | 行驶里程（km） |
| `words_result.items[].City` | `string` | 城市 |
| `words_result.items[].Fare` | `string` | 本次行程费用（元） |

### 失败响应

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `error_code` | `number` | 错误码 |
| `error_msg` | `string` | 错误描述 |

---

## 生成期代码

生成期调用请使用 `SKILL.md` 中的脚本方式：

```bash
python3 <skill-path>/scripts/call_online_taxi_itinerary_ocr.py --image /path/to/rideshare-receipt.jpg
```

脚本内部负责读取 `INTEGRATIONS_API_KEY`、按 `image > url > pdf_file > ofd_file` 优先级读取本地文件并编码、发送请求并输出识别结果。这里不再维护内联请求代码，避免生成期重复消耗 token。

---

## Edge Function

Web 和 MiniProgram 响应均为 JSON，**共用一个 Edge Function**。

```typescript
// edge-functions/rideshare-receipt-ocr.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- 解析客户端请求 ---
  let image: string | undefined;
  let url: string | undefined;
  let pdf_file: string | undefined;
  let pdf_file_num: string | undefined;
  let ofd_file: string | undefined;
  let ofd_file_num: string | undefined;

  try {
    const body = await req.json();
    image = body.image;
    url = body.url;
    pdf_file = body.pdf_file;
    pdf_file_num = body.pdf_file_num;
    ofd_file = body.ofd_file;
    ofd_file_num = body.ofd_file_num;

    // 四个输入参数至少需要一个
    if (!image && !url && !pdf_file && !ofd_file) {
      throw new Error("Missing input: image, url, pdf_file, or ofd_file required");
    }
  } catch (e) {
    return new Response(
      JSON.stringify({ error: (e as Error).message || "Invalid request body" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  // --- 注入平台密钥（禁止暴露到前端）---
  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(
      JSON.stringify({ error: "Server configuration error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  // --- 构建表单参数，优先级：image > url > pdf_file > ofd_file ---
  const formParams: Record<string, string> = {};
  if (image) {
    formParams.image = image;
  } else if (url) {
    formParams.url = url;
  } else if (pdf_file) {
    formParams.pdf_file = pdf_file;
    if (pdf_file_num) formParams.pdf_file_num = pdf_file_num;
  } else if (ofd_file) {
    formParams.ofd_file = ofd_file;
    if (ofd_file_num) formParams.ofd_file_num = ofd_file_num;
  }

  // --- 调用上游 API ---
  const upstream = await fetch(
    "https://app-dvtmyuucfs3l-api-zYkZz8qoKp1L-gateway.appmiaoda.com/rest/2.0/ocr/v1/online_taxi_itinerary",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: new URLSearchParams(formParams).toString(),
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

Web 与 MiniProgram 响应均为 JSON，调用方式相同。

### 推荐方式（supabase client 可用时）

```typescript
interface TaxiOcrInput {
  image?: string;
  url?: string;
  pdf_file?: string;
  pdf_file_num?: string;
  ofd_file?: string;
  ofd_file_num?: string;
}

/**
 * 调用网约车行程单识别 Edge Function。
 * @param input - 识别输入，提供 image/url/pdf_file/ofd_file 之一。
 * @returns 结构化行程单数据。
 */
async function recognizeTaxiItinerary(input: TaxiOcrInput) {
  const { data, error } = await supabase.functions.invoke(
    "rideshare-receipt-ocr",
    { body: input }
  );
  if (error) throw error;
  if (data.error_code) {
    throw new Error(`API 错误 ${data.error_code}: ${data.error_msg}`);
  }
  return data;
}

// 用法示例（使用图片 base64）
const result = await recognizeTaxiItinerary({ image: "<base64_string>" });
console.log(result.words_result.TotalFare);

// 用法示例（使用图片 URL）
const result2 = await recognizeTaxiItinerary({ url: "https://example.com/receipt.jpg" });
```

### 备用方式（无 supabase client 时）

```typescript
/**
 * 通过原生 fetch 调用网约车行程单识别 Edge Function。
 * @param input - 识别输入，提供 image/url/pdf_file/ofd_file 之一。
 * @returns 结构化行程单数据。
 */
async function recognizeTaxiItinerary(input: TaxiOcrInput) {
  const res = await fetch(
    `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/rideshare-receipt-ocr`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }
  );

  if (res.status === 429) {
    const err = await res.json();
    throw new Error(`配额已用尽: ${err.message ?? res.statusText}`);
  }
  if (res.status === 402) {
    const err = await res.json();
    throw new Error(`余额不足: ${err.message ?? res.statusText}`);
  }
  if (!res.ok) throw new Error(`请求失败: ${res.status}`);

  const json = await res.json();
  if (json.error_code) {
    throw new Error(`API 错误 ${json.error_code}: ${json.error_msg}`);
  }
  return json;
}
```

---

## 注意事项

- **密钥安全**: `INTEGRATIONS_API_KEY` 仅可在 Edge Function 服务端通过 `Deno.env.get` 读取，严禁将密钥暴露到前端代码或版本库。
- **错误处理**: 务必处理 429（配额超限）和 402（余额不足）两种错误，并向用户给出友好提示。
- **调用注意**: 请在业务层做好防重复提交，避免同一张行程单多次识别。
- **图片大小**: `image` 参数（base64）最大 4 MB，超出需压缩或改用 `url` 方式。
- **输入优先级**: 同时传入多个输入参数时，优先级为 `image > url > pdf_file > ofd_file`，Edge Function 已按此顺序处理，客户端无需担心。
- **PDF/OFD 页码**: `pdf_file_num` 和 `ofd_file_num` 不填时默认识别第 1 页，若行程单跨页需按需传入。
- **响应字段不稳定**: `words_result` 中的字段数量取决于识别结果，部分字段（如 `Phone`）可能不存在，前端须做可选处理。
