---
name: id-card-ocr
description: 识别二代居民身份证正反面信息（姓名、性别、民族、出生、住址、证件号等），适用于实名认证、用户注册、身份验证场景
license: MIT
---

## 能力概述

调用百度 OCR 接口对二代居民身份证正反面进行结构化识别，返回 JSON 格式的文字识别结果。

- **Endpoint**：`POST https://app-dvtmyuucfs3l-api-k93RZBjP0zqa-gateway.appmiaoda.com/rest/2.0/ocr/v1/idcard`
- **Content-Type**：`application/x-www-form-urlencoded`
- **认证模式**：`platform_managed`（密钥由平台注入，客户端无需关心）
- Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。
- **Plugin ID**：`feccaf6c-9221-4532-b7e0-f95086eec01d`
- **支持平台**：Web、MiniProgram

### 正面识别结果示例

```json
{
  "log_id": "1559208562721579319",
  "image_status": "normal",
  "words_result": {
    "姓名":       { "words": "伍云龙" },
    "性别":       { "words": "男" },
    "民族":       { "words": "汉" },
    "出生":       { "words": "19990417" },
    "住址":       { "words": "南京市江宁区弘景大道3889号" },
    "公民身份号码": { "words": "330881199904173914" }
  },
  "words_result_num": 6
}
```

### 反面识别结果示例

```json
{
  "words_result": {
    "签发机关": { "words": "陆丰市公安局" },
    "签发日期": { "words": "20190606" },
    "失效日期": { "words": "20390711" }
  }
}
```

---

## 生成期用法（Agent 直接调用）

生成期直接使用脚本调用 OCR 接口，避免把身份证图片 Base64 放入模型上下文。

```bash
python3 <skill-path>/scripts/recognize_idcard.py --image /path/to/idcard-front.jpg --side front
```

也可以传入图片 URL 或识别反面，并按需开启可选检测项：

```bash
python3 <skill-path>/scripts/recognize_idcard.py --url https://example.com/idcard-back.jpg --side back --detect-risk
```

脚本内部会读取本地图片并完成 Base64 编码，使用 `INTEGRATIONS_API_KEY` 通过 `X-Gateway-Authorization` 调用上游。成功时 stdout 输出一行 OCR JSON（`words_result` 等字段）；失败时输出错误信息到 stderr 并以非 0 退出。

完整参数表详见 [references/idcard-ocr-api.md](references/idcard-ocr-api.md)。

---

## 生成后用法（应用内通过 Edge Function 调用）

将 Edge Function 部署为 `id-card-ocr`，前端通过 `supabase.functions.invoke` 传入图片（base64 或 URL）和
`id_card_side`（正面 `front` / 反面 `back`），即可获得结构化 OCR 结果。

各平台的完整 Edge Function 代码和前端调用代码详见 [references/idcard-ocr-api.md](references/idcard-ocr-api.md)。

| 平台 | Edge Function 实现 | 前端调用方式 |
|------|--------------------|-------------|
| Web  | 返回 JSON，标准流程 | `supabase.functions.invoke` 或原生 `fetch` |
| MiniProgram | 返回 JSON，标准流程 | `supabase.functions.invoke` |
