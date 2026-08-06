# 动作控制 3.0：创建任务

## 接口

```http
POST https://app-dvtmyuucfs3l-api-n9QVBZkleO2L-gateway.appmiaoda.com/motion-control/kling-3.0
X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}
Content-Type: application/json
```

| 属性 | 值 |
|---|---|
| API ID | `api-n9QVBZkleO2L` |
| 上游方法与路径 | `POST /motion-control/kling-3.0` |
| 网关模式 | `platform_managed` |

## 请求 Schema

```json
{
  "contents": [
    { "type": "prompt", "text": "人物穿灰色宽松 T 恤和牛仔短裤" },
    { "type": "image", "url": "https://example.com/character.png" },
    { "type": "video", "url": "https://example.com/motion.mp4" }
  ],
  "settings": {
    "character_orientation": "video",
    "audio": "original",
    "resolution": "1080p"
  },
  "options": {
    "callback_url": "https://example.com/callback",
    "external_task_id": "motion-unique-id",
    "watermark_info": { "enabled": false }
  }
}
```

## 字段

| 字段 | 类型 | 必填 | 约束 |
|---|---|---:|---|
| `contents` | array | 是 | 素材集合 |
| `contents[].type` | string | 是 | `prompt`、`image`、`video`、`element` |
| `prompt.text` | string | 条件 | 最多 2500 字符 |
| `image.url` | string | 条件 | URL 或接口接受的 Base64 |
| `video.url` | string | 条件 | URL |
| `element.element_id` | string | 条件 | 查询主体 API 返回的主体 ID |
| `element.id` | string | 条件 | Prompt 引用索引，同任务不得重复 |
| `settings.character_orientation` | string | 是 | `image` 或 `video` |
| `settings.audio` | string | 否 | `original`（默认）或 `off` |
| `settings.resolution` | string | 否 | `720p`（默认）或 `1080p` |
| `options.callback_url` | string | 否 | 状态变更回调地址 |
| `options.external_task_id` | string | 否 | 账号内唯一 |
| `options.watermark_info.enabled` | boolean | 否 | 默认 `false` |

## 响应

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "id": "string",
    "status": "submitted",
    "create_time": 1781080778802,
    "update_time": 1781080794151,
    "external_id": "string"
  }
}
```

创建成功后必须保存 `data.id`。只有 HTTP 成功且 `code=0` 才进入轮询。
