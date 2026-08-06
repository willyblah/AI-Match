---
name: train-ticket-query
description: 火车票查询：查询车次时刻表、站站余票及票价信息。适用于出行规划、车票信息展示、列车站点查询等场景。
license: MIT
---

## 能力概述

本 skill 基于极速数据火车票 API，提供三个核心查询能力：

| 能力 | 接口 | 方法 | API ID |
|------|------|------|--------|
| 车次查询 | `POST https://app-dvtmyuucfs3l-api-DLEO73l7Vjwa-gateway.appmiaoda.com/train/line` | POST | `api-DLEO73l7Vjwa` |
| 余票查询 | `POST https://app-dvtmyuucfs3l-api-DLEO73lBPZ2a-gateway.appmiaoda.com/train/ticket` | POST | `api-DLEO73lBPZ2a` |
| 站站查询 | `POST https://app-dvtmyuucfs3l-api-V9PworyO6gEa-gateway.appmiaoda.com/train/station2s` | POST | `api-V9PworyO6gEa` |

- **认证方式**：平台托管（`platform_managed`），密钥由平台注入
- **响应格式**：JSON，`status=0` 表示成功
- **适用平台**：Web、MiniProgram

### 三个接口简介

1. **车次查询**（`/train/line`）：根据车次号查询列车全程站点时刻表，包括各站到达/发车时间、停靠时长、运行里程及各席位价格。
2. **余票查询**（`/train/ticket`）：根据出发站、到达站和日期，查询当日所有车次的余票数量及发到时间。
3. **站站查询**（`/train/station2s`）：查询两站之间的所有车次列表，含运行时长、里程及票价，支持按高铁筛选。

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场编写请求代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**。

车次查询：

```bash
python3 scripts/query_train_line.py --trainno "G34" --date "2024-06-01"
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","result":{"trainno":"G34","type":"高铁","list":[{"sequenceno":"1","station":"杭州东","arrivaltime":"-","departuretime":"07:18"}]}}
```

余票查询：

```bash
python3 scripts/query_train_ticket.py --start "杭州东" --end "北京南" --date "2024-06-01"
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","result":[{"trainno":"G42","type":"高铁","departuretime":"09:26","arrivaltime":"16:06","numyd":"无","numed":"无"}]}
```

站站查询：

```bash
python3 scripts/query_train_station2s.py --start "杭州东" --end "北京南" --ishigh "1" --date "2024-06-01"
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","result":[{"trainno":"G34","type":"高铁","departuretime":"07:18","arrivaltime":"13:07","priceed":"538.5"}]}
```

三个脚本内部均负责读取 `INTEGRATIONS_API_KEY`、拼接 query string 参数、以 POST + 空 Body 发送请求并输出 `result` 字段。这里不再维护内联请求代码，避免生成期重复消耗 token。

---

## 生成后用法（应用内通过 Edge Function 调用）

每个接口对应一个独立的 Edge Function，前端通过 Supabase client 调用。平台密钥仅在服务端读取，不暴露至前端。

| 接口 | Edge Function 名称 | 前端调用示例 |
|------|-------------------|-------------|
| 车次查询 | `train-line` | `supabase.functions.invoke("train-line", { body: { trainno, date } })` |
| 余票查询 | `train-ticket` | `supabase.functions.invoke("train-ticket", { body: { start, end, date } })` |
| 站站查询 | `train-station2s` | `supabase.functions.invoke("train-station2s", { body: { start, end, ishigh, date } })` |

完整 Edge Function 及前端代码详见各 references 文件：
- 车次查询：[references/train-line-api.md](references/train-line-api.md)
- 余票查询：[references/train-ticket-api.md](references/train-ticket-api.md)
- 站站查询：[references/train-station2s-api.md](references/train-station2s-api.md)
