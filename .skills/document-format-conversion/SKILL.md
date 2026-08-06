---
name: document-format-conversion
description: 将图片或 PDF 文档转换为 Word/Excel，保留原版式，支持表格/印章/水印/手写内容。需要 OCR 文档格式转换、PDF 转 Word/Excel 时使用。
license: MIT
---

## 能力概述

**文档格式转换**（百度 OCR）是一个**异步**接口，分两步完成：

1. **提交请求**（Submit）：上传图片或 PDF，获取 `task_id`
2. **轮询结果**（Poll）：用 `task_id` 查询进度，直到 `ret_code = 3` 时获取下载链接

| 维度 | 说明 |
|------|------|
| 提交接口 | `POST https://app-dvtmyuucfs3l-api-rY7JZ6jqrneL-gateway.appmiaoda.com/rest/2.0/ocr/v1/doc_convert/request` |
| 查询接口 | `POST https://app-dvtmyuucfs3l-api-oYA6ZGjReooa-gateway.appmiaoda.com/rest/2.0/ocr/v1/doc_convert/get_request_result` |
| Content-Type | `application/x-www-form-urlencoded` |
| 认证模式 | `platform_managed`（`traefik: true`） |
| 输入格式 | 图片 base64（jpg/jpeg/png/bmp，≤4M）、图片 URL，或 PDF base64（≤10M） |
| 输出格式 | Word 和 Excel 文件下载链接（有效期 30 天） |
| 计费 | 按提交请求计次，获取结果不计费 |

**关键约束：**
- `ret_code = 1`（未开始）、`ret_code = 2`（进行中）时**必须继续轮询**，不可停止
- 仅 `ret_code = 3` 时停止轮询，读取 `result_data.word` / `result_data.excel` 下载链接
- 提交接口 QPS 上限 2，查询接口 QPS 上限 10
- 建议提交后等待 5～10 秒再首次查询

---

## 生成期用法（Agent 直接调用）

生成期调用已改为脚本方式，模型不再生成内联 TypeScript；只需拼命令并执行即可。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认 120 秒会导致请求中断。

**提交并等待结果（本地图片或 PDF 文件）：**

```bash
python3 <skill-path>/scripts/generate_doc_convert.py --file /path/to/doc.pdf
```

**远程图片 URL：**

```bash
python3 <skill-path>/scripts/generate_doc_convert.py --url "https://example.com/scan.jpg"
```

脚本成功时 stdout 输出一行 JSON：
```json
{"status": "succeed", "task_id": "...", "word": "...", "excel": "...", "expires": "30 days"}
```

如果任务在脚本安全时限内仍未完成，脚本会正常退出（非报错）并输出：
```json
{"status": "processing", "task_id": "<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_doc_convert.py` 与 `query_doc_convert.py` 存在先后依赖，必须等 `generate_doc_convert.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_doc_convert.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时**不要重新提交任务**（会重复计费），改用只查询、不提交的脚本继续等待：

```bash
python3 <skill-path>/scripts/query_doc_convert.py --task-id <task_id>
```

`query_doc_convert.py` 输出格式与 `generate_doc_convert.py` 成功/处理中的输出完全一致。

详细参数说明与响应结构见：
- `references/doc-convert-submit-api.md`（提交请求接口）
- `references/doc-convert-query-api.md`（获取结果接口）

---

## 生成后用法（应用内通过 Edge Function 调用）

本插件为**异步**流程，需要两个 Edge Function（分别对应提交和查询），前端负责轮询。

| 平台 | Edge Function | 前端轮询方式 |
|------|--------------|-------------|
| Web / MiniProgram | `doc-convert-submit` + `doc-convert-query` | 调用两次 Edge Function，`ret_code ≠ 3` 时继续轮询 |

完整 Edge Function 代码、前端调用代码及注意事项详见：
- `references/doc-convert-submit-api.md`（提交 Edge Function + 前端调用）
- `references/doc-convert-query-api.md`（查询 Edge Function + 前端轮询循环）
