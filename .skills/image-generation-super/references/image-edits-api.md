# 编辑图片接口 — 完整规格与实现

## API 基本信息

| 字段 | 值                                                                   |
|------|---------------------------------------------------------------------|
| Plugin ID | `e480d4b6-835c-45f8-a494-d38da962b394`                              |
| API ID | `api-baBw3XMNVmv9`                                                  |
| Endpoint | `POST https://app-dvtmyuucfs3l-api-baBw3XMNVmv9-gateway.appmiaoda.com/image2`       |
| Content-Type | `application/json` (images are Base64 encoded)                     |
| 认证模式 | `platform_managed`                                                  |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`           |
| 支持平台 | Web、MiniProgram                                                     |

> CFC 请求使用 JSON。原始 multipart 图片上传经过 CFC 事件转换可能损坏二进制，调用方应将图片编码到 `images[].b64_json`，由 CFC 重新构造 multipart 请求。

### CFC 请求示例

```json
{
  "model": "gpt-image-2",
  "prompt": "Keep the original product and change the background to a pale blue studio background",
  "size": "1024x1024",
  "images": [
    {
      "filename": "product.png",
      "content_type": "image/png",
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ]
}
```

---

## 请求参数表

### 顶层参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `model` | `string` | 是 | 固定值：`gpt-image-2` |
| `prompt` | `string` | 是 | 图片编辑描述词，控制最终生成效果 |
| `size` | `string` | 否 | 输出图片尺寸，如 `2848x1152` |
| `n` | `integer` | 否 | 输出图片数量，默认 1 |
| `images[0].b64_json` | `string` | 是 | 主图片 Base64 数据 |
| `images[1].b64_json` | `string` | 否 | 附加图片 Base64 数据 |
| `images[2].b64_json` | `string` | 否 | 附加图片 Base64 数据 |
| `images[].filename` | `string` | 否 | 文件名，默认 `image-N.png` |
| `images[].content_type` | `string` | 否 | MIME 类型，默认 `image/png` |

---

## 响应字段表

### 成功响应（HTTP 200）

```json
{
  "created": 1778148759,
  "data": [
    {
      "b64_json": "iVBORw0KGgoAAAANSUhEUgAA...",
      "revised_prompt": "Edit the provided images into a cinematic movie poster with dramatic lighting and unified composition"
    }
  ],
  "background": "auto",
  "output_format": "png",
  "quality": "auto",
  "size": "2848x1152",
  "model": "gpt-image-2",
  "usage": {
    "input_tokens": 842,
    "input_tokens_details": {
      "image_tokens": 782,
      "text_tokens": 60
    },
    "output_tokens": 1756,
    "output_tokens_details": {
      "image_tokens": 1756,
      "text_tokens": 0
    },
    "total_tokens": 2598
  }
}
```

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `created` | `number` | 创建时间戳 |
| `data` | `array` | 生成结果列表 |
| `data[].b64_json` | `string` | Base64 编码后的图片内容，需解码后保存为 png/jpg 文件 |
| `data[].revised_prompt` | `string` | 模型自动优化后的提示词 |
| `background` | `string` | 背景设置（如 `auto`） |
| `output_format` | `string` | 输出格式（如 `png`） |
| `quality` | `string` | 图片质量（如 `auto`） |
| `size` | `string` | 输出尺寸 |
| `model` | `string` | 使用的模型 |
| `usage` | `object` | 本次图片生成的 token 消耗统计 |
| `usage.input_tokens` | `number` | 输入 token 数 |
| `usage.input_tokens_details.image_tokens` | `number` | 图片输入 token 数 |
| `usage.input_tokens_details.text_tokens` | `number` | 文本输入 token 数 |
| `usage.output_tokens` | `number` | 输出 token 数 |
| `usage.output_tokens_details.image_tokens` | `number` | 图片输出 token 数 |
| `usage.output_tokens_details.text_tokens` | `number` | 文本输出 token 数 |
| `usage.total_tokens` | `number` | 总 token 数 |

---

## 生成期代码（TypeScript）

生成期由 Agent 直接调用上游 API。认证使用 `platform_managed` 模式，密钥由平台注入。

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

interface EditImageParams {
  model: "gpt-image-2";
  prompt: string;
  size?: string;
  n?: number;
  images: File[]; // 1–3 张图片文件，调用前编码为 Base64
}

interface EditImageResult {
  created: number;
  data: Array<{
    b64_json: string;
    revised_prompt: string;
  }>;
  background: string;
  output_format: string;
  quality: string;
  size: string;
  model: string;
  usage?: {
    input_tokens: number;
    input_tokens_details: { image_tokens: number; text_tokens: number };
    output_tokens: number;
    output_tokens_details: { image_tokens: number; text_tokens: number };
    total_tokens: number;
  };
}

async function editImage(params: EditImageParams): Promise<EditImageResult> {
  const images = await Promise.all(params.images.slice(0, 3).map(async (file) => {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return {
      filename: file.name,
      content_type: file.type || "image/png",
      b64_json: btoa(binary),
    };
  }));
  const body = {
    model: params.model,
    prompt: params.prompt,
    ...(params.size ? { size: params.size } : {}),
    ...(params.n ? { n: params.n } : {}),
    images,
  };

  const response = await fetch(
    "https://app-dvtmyuucfs3l-api-baBw3XMNVmv9-gateway.appmiaoda.com/image2",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    }
  );

  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

  const json = await response.json();
  if (json.error) throw new Error(`API error: ${JSON.stringify(json.error)}`);

  return json;
}
```

### 生成期文件保存（必须执行）

本接口直接返回 **Base64 编码的媒体数据**（不含 URL），在生成期获得 Base64 数据后，**必须立即使用 Bash 工具将其解码并保存到本地**，以便用户查看结果。

```bash
echo "<base64_data>" | base64 -d > <本地路径>.png
```

**完整生成期工作流（含保存步骤）：**

1. 准备图片文件（1–3 张）
2. 调用 `editImage(params)` 获取响应
3. 从 `json.data[0].b64_json` 提取 Base64 数据
4. 使用 Bash 工具将 Base64 解码并保存：`echo "<b64_json>" | base64 -d > <本地路径>.png`
5. 告知用户文件已保存到对应路径，同时展示 `revised_prompt`

> **注意**：Base64 数据仅存在于当次响应中，必须及时保存，否则数据丢失。

---

## Edge Function 代码

### Web 平台

CFC 编辑接口接收 JSON，图片放在 `images[].b64_json` 中。Edge Function 可直接转发 JSON。

```typescript
// edge-functions/image-edits.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- Parse client request (JSON with Base64 images) ---
  const contentType = req.headers.get("content-type");
  if (!contentType || !contentType.includes("application/json")) {
    return new Response(JSON.stringify({ error: "Expected application/json" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- Inject platform key (never expose to client) ---
  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  const bodyBytes = new Uint8Array(await req.arrayBuffer());

  // --- Call upstream ---
  const upstream = await fetch(
    "https://app-dvtmyuucfs3l-api-baBw3XMNVmv9-gateway.appmiaoda.com/image2",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: bodyBytes,
    }
  );

  // Forward quota/balance errors verbatim
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

### MiniProgram 平台

MiniProgram 的 Edge Function 逻辑与 Web 平台相同（JSON Base64 直接转发），前端处理图片的方式略有不同（需写入临时文件后用 `<image>` 组件展示，weapp 真机不支持 `data:` URI 直接渲染）。

---

## 前端调用代码

### Web 平台（React / Vue / 原生 TypeScript）

**推荐方式（supabase client）：**

```typescript
async function editImage(params: { prompt: string; size?: string; n?: number; images: File[] }) {
  const images = await Promise.all(params.images.slice(0, 3).map(async (file) => {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return {
      filename: file.name,
      content_type: file.type || "image/png",
      b64_json: btoa(binary),
    };
  }));
  const body = {
    model: "gpt-image-2",
    prompt: params.prompt,
    ...(params.size ? { size: params.size } : {}),
    ...(params.n ? { n: params.n } : {}),
    images,
  };

  const { data, error } = await supabase.functions.invoke("image-edits", {
    body: JSON.stringify(body),
  });
  if (error) throw error;
  return data;
}
```

**备用方式（fetch）：**

```typescript
async function editImage(params: { prompt: string; size?: string; n?: number; images: File[] }) {
  const images = await Promise.all(params.images.slice(0, 3).map(async (file) => {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return {
      filename: file.name,
      content_type: file.type || "image/png",
      b64_json: btoa(binary),
    };
  }));

  const res = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/image-edits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "gpt-image-2",
      prompt: params.prompt,
      ...(params.size ? { size: params.size } : {}),
      ...(params.n ? { n: params.n } : {}),
      images,
    }),
  });

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
  return json;
}
```

**前端解码 Base64：**

```typescript
const base64 = json.data[0].b64_json;
const byteCharacters = atob(base64);
const byteNumbers = new Array(byteCharacters.length);
for (let i = 0; i < byteCharacters.length; i++) {
  byteNumbers[i] = byteCharacters.charCodeAt(i);
}
const byteArray = new Uint8Array(byteNumbers);
const blob = new Blob([byteArray], { type: "image/png" });
const imageUrl = URL.createObjectURL(blob);
// 使用 imageUrl 在 <img> 中展示
```

### MiniProgram 平台（Taro / 原生小程序）

```typescript
import Taro from "@tarojs/taro";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.TARO_APP_SUPABASE_URL!,
  process.env.TARO_APP_SUPABASE_ANON_KEY!
);

async function readFileBase64(filePath: string): Promise<string> {
  const fs = Taro.getFileSystemManager();
  return new Promise((resolve, reject) => {
    fs.readFile({
      filePath,
      encoding: "base64",
      success: (res) => resolve(res.data as string),
      fail: reject,
    });
  });
}

async function editImage(params: { prompt: string; size?: string; n?: number; images: string[] }) {
  const images = await Promise.all(params.images.slice(0, 3).map(async (filePath, index) => ({
    filename: `image-${index}.png`,
    content_type: "image/png",
    b64_json: await readFileBase64(filePath),
  })));

  const { data, error } = await supabase.functions.invoke("image-edits", {
    body: JSON.stringify({
      model: "gpt-image-2",
      prompt: params.prompt,
      ...(params.size ? { size: params.size } : {}),
      ...(params.n ? { n: params.n } : {}),
      images,
    }),
  });
  if (error) throw error;
  return data;
}

// 获取 Base64 后写入临时文件并展示
async function saveAndPreviewBase64(base64: string): Promise<string> {
  const fs = Taro.getFileSystemManager();
  const filePath = `${Taro.env.USER_DATA_PATH}/edited_${Date.now()}.png`;
  const buffer = Taro.base64ToArrayBuffer(base64);

  return new Promise((resolve, reject) => {
    fs.writeFile({
      filePath,
      data: buffer,
      encoding: "binary",
      success: () => resolve(filePath),
      fail: reject,
    });
  });
}

// 使用示例
const result = await editImage({
  prompt: "帮我把多张图片整合成一张电影海报",
  size: "2848x1152",
  images: [file1, file2],
});
const imagePath = await saveAndPreviewBase64(result.data[0].b64_json);
// <Image src={imagePath} mode="aspectFit" />
```

---

## 注意事项

1. **密钥安全**：`INTEGRATIONS_API_KEY` 仅可在 Edge Function 服务端读取，严禁暴露到前端。

2. **文件上传限制**：编辑接口最多支持 3 张图片（`images[0].b64_json` 必填，`images[1]`、`images[2]` 可选），需确保图片格式和大小符合上游要求。

3. **错误处理**：务必处理 429（配额超限）和 402（余额不足）两种错误状态码，这两种错误会从上游直接转发。

4. **Base64 格式**：返回的 `b64_json` 是纯 Base64 字符串，不含 `data:image/xxx;base64,` 前缀，前端需自行拼接或转为 Blob。

5. **支持的图片格式**：输出固定为 PNG 格式。输入支持常见图片格式（jpg、png、webp 等），具体以上游限制为准。
