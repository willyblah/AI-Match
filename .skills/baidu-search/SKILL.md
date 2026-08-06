---
name: baidu-search
description: 百度千帆 AI 搜索，根据用户 query 检索全网实时信息，返回网页/视频来源引用列表。需要搜索网页、获取实时信息时使用。
license: MIT
---

## 能力概述

百度千帆 AI 搜索接口，通过 POST 请求向 `https://app-dvtmyuucfs3l-api-rY7JZ6jqr6dL-gateway.appmiaoda.com/v2/ai_search/chat/completions`
发送对话消息，实时检索全网内容，返回结构化的引用来源列表（网页 / 视频）。

**Endpoint：** `POST https://app-dvtmyuucfs3l-api-rY7JZ6jqr6dL-gateway.appmiaoda.com/v2/ai_search/chat/completions`

**核心参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `messages` | array | 是 | 搜索输入，以 user 角色开始和结束 |
| `resource_type_filter` | array | 否 | 搜索资源类型配置（web / video） |
| `search_recency_filter` | string | 否 | 时间筛选：week / month / semiyear / year |

**响应格式（200）：** 返回 `references` 数组，每条含 `id`、`title`、`type`、`url`、`content`、`date`、`web_anchor`。

**认证模式：** `platform_managed` — 密钥由平台注入，无需用户配置。
- Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。

**计费：** 计费信息以平台实际配置为准。

**支持平台：** Web、MiniProgram、App

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场编写请求代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**。

```bash
python3 <skill-path>/scripts/call_search.py --query "河北各个城市最近的天气"
```

可按需限定资源类型和时间范围：

```bash
python3 <skill-path>/scripts/call_search.py --query "最新 AI 新闻" --resource-type web --top-k 10 --search-recency-filter week
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","references":[{"id":1,"title":"...","type":"web","url":"...","content":"...","date":"..."}]}
```

---

## 生成后用法（应用内通过 Edge Function 调用）

在应用内需通过 Supabase Edge Function 代理调用，将 `INTEGRATIONS_API_KEY` 保存在服务端，
避免密钥暴露到前端。Web、MiniProgram 和 App 共用同一套 Edge Function，前端调用方式相同。

详见 [`references/ai-search-api.md`](references/ai-search-api.md) — **Edge Function 代码** 和 **前端调用代码** 章节。
