---
name: baidu-traffic-condition
description: 基于百度地图查询实时交通路况，支持道路名称、矩形/多边形/圆形区域四种查询方式，适用于出行导航、路线规划和拥堵预警场景
license: MIT
---

## 能力概述

基于百度地图交通路况 API，提供分钟级实时道路拥堵数据，支持四种查询维度：

| 接口 | 方法 | Endpoint | 核心参数 |
|------|------|----------|---------|
| 道路实时路况查询 | GET | `https://app-dvtmyuucfs3l-api-rLobR3D3dbg9-gateway.appmiaoda.com/traffic/v1/road` | `road_name`（必填）、`city`（可选） |
| 矩形区域实时路况查询 | GET | `https://app-dvtmyuucfs3l-api-ra5ErGpGM8wa-gateway.appmiaoda.com/traffic/v1/bound` | `bounds`（必填，左下角;右上角坐标） |
| 多边形区域实时路况查询 | GET | `https://app-dvtmyuucfs3l-api-BYdwQ5e51blL-gateway.appmiaoda.com/traffic/v1/polygon` | `polygon`（必填，多边形坐标点序列） |
| 周边实时路况查询 | GET | `https://app-dvtmyuucfs3l-api-Xa6JeEnEb2na-gateway.appmiaoda.com/traffic/v1/around` | `center`（必填，中心坐标）、`radius`（必填，单位米） |

所有接口均返回 JSON，包含整体拥堵评价（`evaluation`）和各拥堵路段详情（`congestion_sections` / `roads`）。

**认证模式**：`platform_managed`（密钥由平台注入，前端无需关心）

**支持平台**：Web、MiniProgram

## 生成期用法（Agent 直接调用）

生成期请直接调用脚本，不再在提示词里拼 TypeScript 请求代码。Bash 工具超时必须设为 `600000` ms。

```bash
# 道路实时路况查询
python3 scripts/call_traffic_condition.py road --road-name "长安街" --city "北京"

# 矩形区域实时路况查询
python3 scripts/call_traffic_condition.py bound --bounds "39.912078,116.464303;39.918276,116.475442" --coord-type-input gcj02 --coord-type-output gcj02

# 多边形区域实时路况查询
python3 scripts/call_traffic_condition.py polygon --polygon "39.910528,116.472926;39.918276,116.475442;39.916671,116.459056" --coord-type-input gcj02 --coord-type-output gcj02

# 周边实时路况查询
python3 scripts/call_traffic_condition.py around --center "39.912078,116.464303" --radius 200 --coord-type-input gcj02 --coord-type-output gcj02
```

脚本会读取 `INTEGRATIONS_API_KEY`，并输出一行 JSON。参数细节见各 references/ 文件。

成功示例：

```json
{
  "status": "succeed",
  "result": {
    "evaluation": "畅通",
    "congestion_sections": []
  }
}
```

## 生成后用法（应用内通过 Edge Function 调用）

每个接口对应一个独立的 Edge Function，前端通过 `supabase.functions.invoke` 调用，
平台密钥仅在 Edge Function 服务端注入，不暴露到前端。

| 接口 | Edge Function 名称 | 参考文件 |
|------|-------------------|---------|
| 道路路况 | `traffic-road` | `references/traffic-road-api.md` |
| 矩形区域 | `traffic-bound` | `references/traffic-bound-api.md` |
| 多边形区域 | `traffic-polygon` | `references/traffic-polygon-api.md` |
| 周边路况 | `traffic-around` | `references/traffic-around-api.md` |

Web 和 MiniProgram 均使用标准 `supabase.functions.invoke` 调用方式，响应均为 JSON，
无二进制流，两个平台实现无差异。完整 Edge Function 和前端代码详见各 references/ 文件。
