# 统一任务查询

## 按 ID 精确查询

```http
GET https://app-dvtmyuucfs3l-api-Aa2P8o0BV1RL-gateway.appmiaoda.com/tasks?task_ids=TASK_ID
GET https://app-dvtmyuucfs3l-api-Aa2P8o0BV1RL-gateway.appmiaoda.com/tasks?external_task_ids=EXTERNAL_ID
```

API ID：`api-Aa2P8o0BV1RL`。鉴权头为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`。

`task_ids` 与 `external_task_ids` 至少且只能选择一种，均支持英文逗号分隔的批量值。

成功响应的 `data` 是数组。必须按目标 `id` 或 `external_id` 精确匹配。

## 视频输出

```json
{
  "type": "video",
  "id": "string",
  "url": "string",
  "watermark_url": "string",
  "duration": "string"
}
```

媒体 URL 30 天后清理。成功后立即下载或持久化。`billing` 仅用于服务端审计，不默认展示给终端用户。

## 应用消费要求

- `submitted` / `processing`：继续自动轮询，页面不得显示“生成成功”；
- `failed`：展示任务 `message`，停止轮询；
- `succeeded`：筛选 `outputs[].type === "video"`，至少取得一个 `url`；
- 取得 URL 后立即渲染视频预览并提供下载按钮，同时发起持久化转存；
- 查询响应为数组时按目标 `id` 或 `external_id` 精确匹配，不直接读取 `data[0]`。

完整 Edge Function、前端轮询、播放器和下载实现见 `app-complete-workflow.md`。
