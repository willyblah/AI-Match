---
name: air-ticket-ocr
description: 识别飞机行程单图片，结构化提取24个字段（乘客、航班、票价、税费等）；适用于差旅报销、财务管理、行程记录场景。
license: MIT
---

## 能力概述

对飞机行程单进行结构化 OCR 识别，支持单张行程单上的多航班信息提取。返回最多 24 个字段，包括乘客姓名、始发站/目的站、航班号、日期时间、票价、税费、电子客票号等。

- **Endpoint**: `POST https://app-dvtmyuucfs3l-api-DLEO7Vjd8Qea-gateway.appmiaoda.com/rest/2.0/ocr/v1/air_ticket`
- **Content-Type**: `application/x-www-form-urlencoded`
- **认证模式**: `platform_managed`（密钥由平台注入，无需用户配置）
- Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。
- **输入格式**: 支持 Base64 图片（jpg/jpeg/png/bmp）、图片 URL、PDF 文件（Base64）、OFD 文件（Base64）
- **输出格式**: JSON，包含 `words_result`（结构化字段）和 `words_result_num`（识别字段数）

| 平台 | Edge Function | 前端调用方式 |
|------|--------------|-------------|
| Web | 返回 JSON | `supabase.functions.invoke` 或原生 fetch |
| MiniProgram | 返回 JSON | `supabase.functions.invoke` |

详见 [references/air-ticket-ocr-api.md](references/air-ticket-ocr-api.md)

---

## 生成期用法（Agent 直接调用）

生成期调用已收敛到脚本，模型只需要传本地文件路径或图片 URL，不再现场编写请求代码或把 Base64 放进上下文。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**。

识别本地图片：

```bash
python3 <skill-path>/scripts/call_air_ticket_ocr.py --image /path/to/air-ticket.jpg
```

也可以使用图片 URL、PDF 或 OFD：

```bash
python3 <skill-path>/scripts/call_air_ticket_ocr.py --url "https://example.com/air-ticket.jpg"
python3 <skill-path>/scripts/call_air_ticket_ocr.py --pdf-file /path/to/air-ticket.pdf --pdf-file-num 1
python3 <skill-path>/scripts/call_air_ticket_ocr.py --ofd-file /path/to/air-ticket.ofd --ofd-file-num 1
```

脚本会读取 `INTEGRATIONS_API_KEY`，完成 Base64/URL 编码并调用上游 OCR 接口，stdout 输出一行 JSON（即上游 `words_result` / `words_result_num` 等字段），失败时输出错误信息到 stderr 并以非 0 退出。

详见 [references/air-ticket-ocr-api.md](references/air-ticket-ocr-api.md) 的「生成期代码」章节。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内通过 Supabase Edge Function 代理调用，`INTEGRATIONS_API_KEY` 在服务端注入，不暴露到前端。Web 和 MiniProgram 均返回 JSON，前端用 `supabase.functions.invoke` 调用。

详见 [references/air-ticket-ocr-api.md](references/air-ticket-ocr-api.md) 的「Edge Function 代码」和「前端调用代码」章节。
