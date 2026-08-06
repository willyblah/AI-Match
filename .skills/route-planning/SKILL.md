---
name: route-planning
description: 基于百度地图提供驾车、步行、骑行、公交路线规划及批量算路能力，返回路线距离、时间、路段详情等，适用于出行规划、路线对比、物流配送场景。
license: MIT
---

## 能力概述

基于百度地图 Direction API v2 和 RouteMatrix API v2，提供以下七个接口：

| 接口名称 | Endpoint | 方法 | 说明 |
|---------|---------|------|------|
| 驾车路线规划 | `GET https://app-dvtmyuucfs3l-api-GaDwZKpJxXOY-gateway.appmiaoda.com/direction/v2/driving` | GET | 单次驾车路线，支持多种策略 |
| 骑行路线规划 | `GET https://app-dvtmyuucfs3l-api-W9z3MpAdKeNL-gateway.appmiaoda.com/direction/v2/riding` | GET | 单次骑行路线 |
| 步行路线规划 | `GET https://app-dvtmyuucfs3l-api-wLNdomNRn42a-gateway.appmiaoda.com/direction/v2/walking` | GET | 单次步行路线 |
| 公交路线规划 | `GET https://app-dvtmyuucfs3l-api-m9xKXQkOKZXa-gateway.appmiaoda.com/direction/v2/transit` | GET | 公共交通路线，含换乘方案和票价 |
| 驾车批量算路 | `GET https://app-dvtmyuucfs3l-api-6LeBrqqMqKQY-gateway.appmiaoda.com/routematrix/v2/driving` | GET | 多起点多终点笛卡尔积算路 |
| 骑行批量算路 | `GET https://app-dvtmyuucfs3l-api-Aa2Pq88pDANL-gateway.appmiaoda.com/routematrix/v2/riding` | GET | 批量骑行距离耗时计算 |
| 步行批量算路 | `GET https://app-dvtmyuucfs3l-api-qYGW2zz1MklY-gateway.appmiaoda.com/routematrix/v2/walking` | GET | 批量步行距离耗时计算 |

**认证方式**：`platform_managed`，密钥由平台注入，通过 `INTEGRATIONS_API_KEY` 环境变量读取，
Header 统一使用 `X-Gateway-Authorization: Bearer ${apiKey}`。

**支持平台**：Web、MiniProgram（响应均为 JSON，两平台实现相同）。

**响应格式**：所有接口返回 JSON，`status=0` 表示成功，`result.routes[]` 包含路线方案。

## 生成期用法（Agent 直接调用）

生成期直接调用脚本 `scripts/call_route_planning.py`，脚本内完成密钥读取、请求、结果解析。**Bash 工具调用超时必须设置为 `600000ms`（600 秒）。**

`--endpoint` 取值：`driving` / `riding` / `walking` / `transit`（单线），`matrix-driving` / `matrix-riding` / `matrix-walking`（批量算路）。

```bash
# 驾车单线（origin/destination 为 "纬度,经度"）
python3 scripts/call_route_planning.py --endpoint driving \
  --origin "40.056878,116.30815" --destination "39.767892,116.527308"

# 公交路线
python3 scripts/call_route_planning.py --endpoint transit \
  --origin "40.056878,116.30815" --destination "39.767892,116.527308"

# 批量算路：origins/destinations 用 | 分隔多个 "纬度,经度"
python3 scripts/call_route_planning.py --endpoint matrix-driving \
  --origins "40.056878,116.30815|39.9,116.4" --destinations "39.767892,116.527308"
```

成功时 stdout 输出一行 JSON：`{"status":"succeed","result":{...上游原始响应...}}`（上游 `status=0` 表示成功）。

完整参数说明详见：

- [references/direction-api.md](references/direction-api.md) — 驾车 / 骑行 / 步行 / 公交路线规划接口
- [references/routematrix-api.md](references/routematrix-api.md) — 驾车 / 骑行 / 步行批量算路接口

生成期调用实现以 `scripts/call_route_planning.py` 为准。

## 生成后用法（应用内通过 Edge Function 调用）

在应用中，前端调用 Supabase Edge Function，Edge Function 在服务端注入 `INTEGRATIONS_API_KEY`
并转发请求到百度地图 API，避免密钥暴露到客户端。

Web 和 MiniProgram 均可使用 `supabase.functions.invoke` 调用，响应为标准 JSON。

完整 Edge Function 代码、前端调用代码及各接口注意事项详见：

- [references/direction-api.md](references/direction-api.md) — 驾车 / 骑行 / 步行 / 公交路线规划
- [references/routematrix-api.md](references/routematrix-api.md) — 驾车 / 骑行 / 步行批量算路
