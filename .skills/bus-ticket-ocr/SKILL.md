---
name: bus-ticket-ocr
description: 识别全国范围不同版式汽车票的关键字段（发票代码、票号、日期、金额、出发/到达站等）；适用于财务报销、票据管理、出行记录等需要结构化提取汽车票信息的场景。
license: MIT
---

## 能力概述

调用百度 OCR 汽车票识别接口，对全国范围内不同版式的汽车票进行结构化识别，最多返回 10 个关键字段。

| 属性 | 值 |
|------|-----|
| Endpoint | `POST https://app-dvtmyuucfs3l-api-Xa6JZxjyqrGa-gateway.appmiaoda.com/rest/2.0/ocr/v1/bus_ticket` |
| Content-Type | `application/x-www-form-urlencoded` |
| 认证模式 | platform_managed（密钥由平台注入） |
| 响应格式 | JSON |
| 支持平台 | Web、MiniProgram |

Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。


支持 4 种输入方式（优先级：image > url > pdf_file > ofd_file）：base64 图片、图片 URL、PDF 文件（base64）、OFD 文件（base64）。

识别字段：发票代码（InvoiceCode）、发票号码（InvoiceNum）、日期（Date）、时间（Time）、出发站（StartingStation）、到达站（DestinationStation）、金额（Fare）、身份证号（IdNum）、姓名（Name）。

## 生成期用法（Agent 直接调用）

生成期调用已收敛到脚本，模型只需要传本地文件路径或图片 URL，不再现场编写请求代码或把 Base64 放进上下文。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**。

识别本地图片：

```bash
python3 <skill-path>/scripts/call_bus_ticket_ocr.py --image /path/to/bus-ticket.jpg
```

也可以使用图片 URL、PDF 或 OFD：

```bash
python3 <skill-path>/scripts/call_bus_ticket_ocr.py --url "https://example.com/bus-ticket.jpg"
python3 <skill-path>/scripts/call_bus_ticket_ocr.py --pdf-file /path/to/bus-ticket.pdf --pdf-file-num 1
python3 <skill-path>/scripts/call_bus_ticket_ocr.py --ofd-file /path/to/bus-ticket.ofd --ofd-file-num 1
```

脚本会读取 `INTEGRATIONS_API_KEY`，按 `image > url > pdf_file > ofd_file` 优先级完成编码并调用上游接口，stdout 输出一行 JSON（含 `words_result` 等字段），失败时输出错误信息到 stderr 并以非 0 退出。

完整参数表详见 `references/bus-ticket-api.md`。

## 生成后用法（应用内通过 Edge Function 调用）

通过 Supabase Edge Function 代理调用，确保 `INTEGRATIONS_API_KEY` 不暴露到前端。Web 和 MiniProgram 均使用相同的 Edge Function，前端通过 `supabase.functions.invoke` 传入图片数据（base64 / URL）并获取 JSON 结果。

完整 Edge Function 代码、前端调用示例及注意事项详见 `references/bus-ticket-api.md`。
