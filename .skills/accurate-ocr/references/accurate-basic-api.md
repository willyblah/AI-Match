# 通用文字识别（高精度版）API 参考

## API 基本信息

| 字段 | 值 |
|------|----|
| Plugin ID | `c2f50034-60cb-4f6d-b6ad-1fcbb11d65bf` |
| API ID | `api-eLMlJ2jB44g9` |
| Endpoint | `POST https://app-dvtmyuucfs3l-api-eLMlJ2jB44g9-gateway.appmiaoda.com/rest/2.0/ocr/v1/accurate_basic` |
| 认证模式 | `platform_managed` |
| Auth Header | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Content-Type | `application/x-www-form-urlencoded` |
| third_part_domain | `app-dvtmyuucfs3l-api-eLMlJ2jB44g9-gateway.appmiaoda.com` |
| 流式响应 | 否 |

---

## 请求参数表

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `image` | string | 与 url/pdf_file/ofd_file 四选一 | — | 图像数据，base64编码后进行urlencode，大小不超过10M，最短边至少15px，最长边最大8192px，支持jpg/jpeg/png/bmp格式。**优先级最高**，存在时其他输入字段失效 |
| `url` | string | 与 image/pdf_file/ofd_file 四选一 | — | 图片完整URL，URL长度不超过1024字节，对应图片大小不超过10M，支持jpg/jpeg/png/bmp格式。请注意关闭URL防盗链 |
| `pdf_file` | string | 与 image/url/ofd_file 四选一 | — | PDF文件，base64编码后进行urlencode，大小不超过10M |
| `pdf_file_num` | string | 否 | `1`（第1页） | 需要识别的PDF文件对应页码，当 pdf_file 参数有效时生效 |
| `ofd_file` | string | 与 image/url/pdf_file 四选一 | — | OFD文件，base64编码后进行urlencode，大小不超过10M |
| `ofd_file_num` | string | 否 | `1`（第1页） | 需要识别的OFD文件对应页码，当 ofd_file 参数有效时生效 |
| `language_type` | string | 否 | `CHN_ENG` | 识别语言类型，支持 `auto_detect`、`CHN_ENG`、`ENG`、`JAP`、`KOR`、`FRE`、`SPA`、`POR`、`GER`、`ITA`、`RUS`、`DAN`、`DUT`、`MAL`、`SWE`、`IND`、`POL`、`ROM`、`TUR`、`GRE`、`HUN`、`THA`、`VIE`、`ARA`、`HIN` |
| `detect_direction` | string | 否 | `false` | 是否检测图像朝向，可选值 `true`/`false` |
| `paragraph` | string | 否 | `false` | 是否输出段落信息，可选值 `true`/`false` |
| `probability` | string | 否 | `false` | 是否返回识别结果中每一行的置信度，可选值 `true`/`false` |
| `multidirectional_recognize` | string | 否 | `false` | 是否开启行级别的多方向文字识别，可选值 `true`/`false` |

---

## 响应字段表

### 成功响应（HTTP 200，error_code=0）

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `log_id` | number | 唯一日志 ID，用于问题定位 |
| `direction` | number | 图像方向（-1:未定义, 0:正向, 1:逆时针90°, 2:逆时针180°, 3:逆时针270°），`detect_direction=true` 时返回 |
| `words_result_num` | number | 识别结果总数 |
| `words_result` | array | 识别结果数组 |
| `words_result[].words` | string | 识别出的文字内容 |
| `words_result[].probability?` | object | 置信度信息，`probability=true` 时返回 |
| `words_result[].probability.average` | number | 平均置信度（0~1） |
| `words_result[].probability.variance` | number | 置信度方差 |
| `words_result[].probability.min` | number | 最低置信度 |
| `paragraphs_result?` | array | 段落检测结果，`paragraph=true` 时返回 |
| `paragraphs_result[].words_result_idx` | array | 段落包含的 words_result 下标列表 |
| `paragraphs_result_num?` | number | 段落总数，`paragraph=true` 时返回 |
| `pdf_file_size?` | string | 传入PDF文件的总页数，`pdf_file` 参数有效时返回 |
| `ofd_file_size?` | string | 传入OFD文件的总页数，`ofd_file` 参数有效时返回 |

### 错误响应

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `error_code` | number | 错误码 |
| `error_msg` | string | 错误描述信息 |

---

## 生成期代码

生成期调用已改为脚本方式，模型不再生成内联 TypeScript；只需拼命令并执行即可。脚本内部完成本地文件读取、Base64 编码、请求上游接口全部操作，模型只接收最终 JSON 结果。

```bash
# 本地图片
python3 <skill-path>/scripts/call_accurate_ocr.py --image /path/to/photo.jpg [--language-type CHN_ENG] [--detect-direction] [--paragraph] [--probability]

# 图片 URL
python3 <skill-path>/scripts/call_accurate_ocr.py --url "https://example.com/photo.jpg"

# PDF / OFD 文件
python3 <skill-path>/scripts/call_accurate_ocr.py --pdf-file /path/to/doc.pdf [--pdf-file-num 1]
python3 <skill-path>/scripts/call_accurate_ocr.py --ofd-file /path/to/doc.ofd [--ofd-file-num 1]
```

脚本成功时 stdout 输出一行 JSON（即上游接口原始响应，含 `words_result` 等字段）。

---

## Edge Function 代码

### Web 平台（及通用版本）

适用于 Web 和 MiniProgram 平台——两平台响应均为 JSON，实现相同。

```typescript
// edge-functions/accurate-ocr.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- 解析客户端请求 ---
  let image: string;
  let languageType: string | undefined;
  let detectDirection: boolean | undefined;
  let paragraph: boolean | undefined;
  let probability: boolean | undefined;
  let multidirectionalRecognize: boolean | undefined;
  let ofdFileNum: string | undefined;

  try {
    const body = await req.json();
    image = body.image;
    if (!image) throw new Error("Missing image");
    languageType = body.language_type;
    detectDirection = body.detect_direction;
    paragraph = body.paragraph;
    probability = body.probability;
    multidirectionalRecognize = body.multidirectional_recognize;
    ofdFileNum = body.ofd_file_num;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- 注入平台密钥（禁止暴露给客户端） ---
  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- 构造上游请求参数 ---
  const params: Record<string, string> = { image };
  if (languageType) params.language_type = languageType;
  if (detectDirection !== undefined) params.detect_direction = String(detectDirection);
  if (paragraph !== undefined) params.paragraph = String(paragraph);
  if (probability !== undefined) params.probability = String(probability);
  if (multidirectionalRecognize !== undefined) {
    params.multidirectional_recognize = String(multidirectionalRecognize);
  }
  if (ofdFileNum) params.ofd_file_num = ofdFileNum;

  // --- 调用上游 ---
  const upstream = await fetch(
    "https://app-dvtmyuucfs3l-api-eLMlJ2jB44g9-gateway.appmiaoda.com/rest/2.0/ocr/v1/accurate_basic",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: new URLSearchParams(params).toString(),
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

### Web 平台

**推荐方式（supabase client 可用时）：**

```typescript
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

interface OcrWord {
  words: string;
  probability?: { average: number; variance: number; min: number };
}

interface OcrResult {
  log_id: number;
  direction?: number;
  words_result_num: number;
  words_result: OcrWord[];
  error_code: number;
  error_msg: string;
}

/**
 * 通过 Edge Function 调用通用文字识别（高精度版）。
 * @param imageBase64 - 图片的 Base64 编码字符串
 * @param languageType - 识别语言类型，默认 CHN_ENG
 * @returns OcrResult 识别结果
 */
async function fetchOcrAccurateBasic(
  imageBase64: string,
  languageType = "CHN_ENG"
): Promise<OcrResult> {
  const { data, error } = await supabase.functions.invoke("accurate-ocr", {
    body: { image: imageBase64, language_type: languageType },
  });
  if (error) throw error;
  if (data.error_code !== 0) {
    throw new Error(`OCR API error ${data.error_code}: ${data.error_msg}`);
  }
  return data as OcrResult;
}

// 用法示例：从 <input type="file"> 读取图片并识别
async function handleFileInput(file: File): Promise<void> {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 8192;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  const imageBase64 = btoa(binary);

  const result = await fetchOcrAccurateBasic(imageBase64);
  console.log("识别结果：", result.words_result.map((w) => w.words).join("\n"));
}
```

**备用方式（无法使用 supabase client 时）：**

```typescript
/**
 * 通过原生 fetch 调用通用文字识别 Edge Function。
 * @param imageBase64 - 图片的 Base64 编码字符串
 * @param languageType - 识别语言类型，默认 CHN_ENG
 * @returns OcrResult 识别结果
 */
async function fetchOcrAccurateBasicRaw(
  imageBase64: string,
  languageType = "CHN_ENG"
): Promise<OcrResult> {
  const res = await fetch(
    `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/accurate-ocr`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: imageBase64, language_type: languageType }),
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
  if (json.error_code !== 0) {
    throw new Error(`OCR API error ${json.error_code}: ${json.error_msg}`);
  }
  return json as OcrResult;
}
```

### MiniProgram 平台（Taro）

```typescript
import Taro from "@tarojs/taro";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.TARO_APP_SUPABASE_URL!,
  process.env.TARO_APP_SUPABASE_ANON_KEY!
);

/**
 * MiniProgram 中将本地图片文件转为 Base64 字符串。
 * @param filePath - 本地临时文件路径（如相机或相册选择的图片）
 * @returns Base64 编码字符串
 */
async function fileToBase64(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const fs = Taro.getFileSystemManager();
    fs.readFile({
      filePath,
      encoding: "base64",
      success: (res) => resolve(res.data as string),
      fail: (err) => reject(new Error(JSON.stringify(err))),
    });
  });
}

/**
 * MiniProgram 中通过 Edge Function 调用通用文字识别（高精度版）。
 * @param imageBase64 - 图片的 Base64 编码字符串
 * @param languageType - 识别语言类型，默认 CHN_ENG
 * @returns OcrResult 识别结果
 */
async function fetchOcrMiniProgram(
  imageBase64: string,
  languageType = "CHN_ENG"
): Promise<OcrResult> {
  const { data, error } = await supabase.functions.invoke("accurate-ocr", {
    body: { image: imageBase64, language_type: languageType },
  });
  if (error) throw error;
  if (data.error_code !== 0) {
    throw new Error(`OCR API error ${data.error_code}: ${data.error_msg}`);
  }
  return data as OcrResult;
}

// 用法示例：从相册选取图片并识别
const handleChooseImage = async () => {
  const res = await Taro.chooseImage({ count: 1, sourceType: ["album", "camera"] });
  const filePath = res.tempFilePaths[0];
  const imageBase64 = await fileToBase64(filePath);
  const result = await fetchOcrMiniProgram(imageBase64);
  console.log("识别结果：", result.words_result.map((w) => w.words).join("\n"));
};
```

---

## 注意事项

1. **密钥安全**：`INTEGRATIONS_API_KEY` 仅可在 Edge Function 服务端读取，严禁暴露到前端或客户端代码。

2. **计费**：
   - 每次调用均计费，避免在循环或高频场景中不必要地重复调用。

3. **错误处理**：务必处理以下情况：
   - HTTP 429（配额超限）：已在 Edge Function 中透传，前端需提示用户稍后重试。
   - HTTP 402（余额不足）：已在 Edge Function 中透传，前端需提示充值。
   - `error_code !== 0`：OCR 服务自身错误，参考 `error_msg` 排查。

4. **图片格式**：仅支持 jpg、jpeg、png、bmp 格式，上传前需客户端校验。

5. **Base64 编码**：对于大图片，使用分块编码（chunkSize=8192）避免 `RangeError: Maximum call stack size exceeded`，禁止使用 `String.fromCharCode(...largeArray)` 展开写法。

6. **MiniProgram 注意**：微信小程序中 `Taro.getFileSystemManager().readFile` 的 `encoding: "base64"` 返回的已是纯 Base64 字符串，无需再做 btoa 处理。

7. **响应有效性判断**：不要用 `words_result_num > 0` 来判断是否有识别结果，应改为检查 `words_result` 数组本身（如 `words_result && words_result.length > 0`）。原因是当仅有段落结果（`paragraphs_result` 有值）而无逐行文字结果时，`words_result_num` 可能为 0，但 `words_result` 数组实际上可能并不为空。
