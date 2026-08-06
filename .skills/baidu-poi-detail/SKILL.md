---
name: baidu-poi-detail
description: 百度地图 POI 地点信息搜索，支持行政区划检索、周边圆形区域搜索、地点详情查询。适合商圈查询、周边设施搜索、地点详情展示等场景。
license: MIT
---

## 能力概述

本 Skill 封装百度地图地点信息搜索（Place API v3），提供三个互补接口：

| 接口 | 作用 | Endpoint |
|------|------|----------|
| **行政区划区域检索** | 在指定行政区划（省/市/区县）内按关键词检索 POI | `GET https://app-dvtmyuucfs3l-api-ra5EZvmRrG4a-gateway.appmiaoda.com/place/v3/region` |
| **圆形区域检索** | 以经纬度为圆心、指定半径范围内检索周边 POI | `GET https://app-dvtmyuucfs3l-api-DLEO7eMnzMwa-gateway.appmiaoda.com/place/v3/around` |
| **地点详情检索** | 根据 POI uid 获取详细信息（评分/营业时间/价格等） | `GET https://app-dvtmyuucfs3l-api-GaDwZekp8WzY-gateway.appmiaoda.com/place/v3/detail` |

**认证方式**：platform_managed，密钥由平台注入（`INTEGRATIONS_API_KEY`），请求头统一使用 `X-Gateway-Authorization: Bearer <key>`。

**典型使用流程**：
1. 使用「行政区划检索」或「圆形区域检索」按关键词查找 POI，获取 `uid`
2. 使用「地点详情检索」传入 `uid`（支持批量，最多 10 个），获取评分、营业时间、价格等详细信息

**计费**：三个接口均按次计费。

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 `INTEGRATIONS_API_KEY`。

使用 Bash 工具执行时，`timeout` 必须设置为 `600000`（600 秒）。

```bash
python3 <skill-path>/scripts/call_poi_search.py region --query "银行" --region "北京市海淀区" --scope 2 --page-size 10
python3 <skill-path>/scripts/call_poi_search.py around --query "银行" --location "39.915,116.404" --radius 1000
python3 <skill-path>/scripts/call_poi_search.py detail --uid "435d7aea036e54355abbbcc8" --scope 2
```

成功时输出一行 JSON：

```json
{"status":"succeed","results":[{"name":"中国银行ATM","location":{"lng":116.315,"lat":40.043},"address":"上地信息路15号"}]}
```

各接口完整参数表、响应结构，详见：

- `references/region-search-api.md` — 行政区划区域检索
- `references/around-search-api.md` — 圆形区域检索
- `references/detail-search-api.md` — 地点详情检索

---

## 生成后用法（应用内通过 Edge Function 调用）

生成的应用中，前端**不得直接持有 `INTEGRATIONS_API_KEY`**，必须通过 Deno Edge Function 代理调用。

| 平台 | Edge Function 文件 | 前端调用方式 |
|------|-------------------|------------|
| Web | `edge-functions/baidu-poi-region.ts` | `supabase.functions.invoke` 或原生 `fetch` |
| Web | `edge-functions/baidu-poi-around.ts` | `supabase.functions.invoke` 或原生 `fetch` |
| Web | `edge-functions/baidu-poi-detail.ts` | `supabase.functions.invoke` 或原生 `fetch` |
| MiniProgram | 同上三个 Edge Function（实现相同） | `supabase.functions.invoke` |

各接口完整 Edge Function 代码与前端调用示例，详见：

- `references/region-search-api.md` — 行政区划区域检索
- `references/around-search-api.md` — 圆形区域检索
- `references/detail-search-api.md` — 地点详情检索
