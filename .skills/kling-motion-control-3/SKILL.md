---
name: kling-motion-control-3
description: 使用可灵动作控制 3.0，根据人物参考图与动作参考视频生成动作一致的视频；支持提示词、参考主体、人物朝向、原声、720p/1080p、异步任务查询、回调与结果转存。当用户提到可灵动作控制、动作迁移、参考视频驱动人物、让图片人物模仿视频动作或 Motion Control 3.0 时使用。
license: MIT
---

# 可灵动作控制 3.0

## 能力概述

基于可灵 Kling Motion Control 3.0，将参考视频中的动作迁移到参考图片或参考主体中的角色：

- 参考图确定人物、服饰、背景等视觉内容；
- 参考视频提供动作与可选原声；
- 提示词补充服饰、环境、元素和运镜要求；
- 可选参考主体提升角色一致性；
- 创建后通过统一任务接口查询结果；
- 成功视频链接 30 天后清理，应立即下载或转存。

| 属性 | 值 |
|---|---|
| 创建任务 | `POST https://app-dvtmyuucfs3l-api-n9QVBZkleO2L-gateway.appmiaoda.com/motion-control/kling-3.0` |
| 精确查询 | `GET https://app-dvtmyuucfs3l-api-Aa2P8o0BV1RL-gateway.appmiaoda.com/tasks` |
| 鉴权 | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| 状态 | `submitted`、`processing`、`succeeded`、`failed` |
| 输出 | 视频 URL、可选水印 URL、时长与计费信息 |

本 Skill 只使用上述动作控制 3.0 创建接口和统一任务查询接口，不引入文生视频、图生视频、Omni、Turbo 或未在接口文档中声明的字段。

## 前置条件

- 使用飞轮后台生成的 API ID 访问秒哒网关；创建接口为 `api-n9QVBZkleO2L`，查询接口为 `api-Aa2P8o0BV1RL`。
- 平台密钥只从服务端环境变量 `INTEGRATIONS_API_KEY` 读取。
- 浏览器和客户端不得持有或输出 Key。
- 输入图片与视频需要是可灵服务可访问的 URL；图片也支持接口允许的 Base64 内容。
- 直接调用时优先执行 `scripts/kling_motion_control.py`，不要临时重写请求代码。

## 执行优先级（严格约束）

1. 校验参考图、动作视频、人物朝向与时长约束。
2. 创建任务一次，保存系统 `data.id` 与可选 `external_id`。
3. 使用系统任务 ID 精确轮询；不得把创建请求当作重试查询。
4. 查询数组时按 `id` 或 `external_id` 精确匹配，不直接取第一项。
5. 成功后立即下载或转存视频；转存失败只重试转存，不重新生成。
6. 同时检查 HTTP 状态和业务 `code`；仅 HTTP 成功且 `code=0` 视为成功。
7. 不记录 Authorization、Key、图片 Base64、完整原始响应中的敏感内容。

## 输入规则

### contents

`contents` 必须包含：

- 一个 `{ "type": "image", "url": "..." }`；
- 一个 `{ "type": "video", "url": "..." }`。

可选包含：

- 一个 `{ "type": "prompt", "text": "..." }`，最多 2500 字符；
- 最多一个 `{ "type": "element", "element_id": "...", "id": "..." }`。

同一任务内 `element.id` 不得重复。使用主体时，`settings.character_orientation` 只能为 `video`。

### settings

- `character_orientation` 必填：
  - `image`：人物朝向跟随图片，动作视频最长 10 秒；
  - `video`：人物朝向跟随视频，动作视频最长 30 秒。
- `audio` 可选：`original`（默认，保留原声）或 `off`。
- `resolution` 可选：`720p`（默认）或 `1080p`。

### 素材约束

- 图片：jpg/jpeg/png；不超过 50MB；宽高均不小于 300px；宽高比在 1:2.5 至 2.5:1。
- 视频：mp4/mov；3–30 秒；不超过 100MB；宽高均在 340–3850px。
- 建议单人、一镜到底、全身或清晰上半身、无遮挡、动作相对平稳。
- 图片人物比例应尽量与动作视频人物比例一致。

## 生成期用法

```bash
export INTEGRATIONS_API_KEY='<平台服务端密钥>'

python3 scripts/kling_motion_control.py create \
  --image-url 'https://example.com/character.png' \
  --video-url 'https://example.com/motion.mp4' \
  --prompt '人物穿灰色宽松 T 恤和牛仔短裤' \
  --character-orientation video \
  --resolution 1080p \
  --audio original \
  --external-task-id 'motion-unique-id'
```

命令以 JSON 输出创建结果。取得 `task_id` 后轮询：

```bash
python3 scripts/kling_motion_control.py wait \
  --task-id '<TASK_ID>' \
  --interval 7 \
  --timeout 600 \
  --download '/absolute/path/result.mp4'
```

也可查询单个或多个任务：

```bash
python3 scripts/kling_motion_control.py query --task-ids '<TASK_ID_1>,<TASK_ID_2>'
python3 scripts/kling_motion_control.py query --external-task-ids '<EXTERNAL_ID>'
```

## 应用内集成（必须形成完整闭环）

**禁止把创建接口返回任务 ID 当作生成成功。** 生成应用必须自动完成“创建任务 → 轮询查询 → 取得视频 URL → 视频预览 → 下载视频”的完整链路。仅展示成功状态和任务 ID 属于未完成实现。

应用内使用两个服务端 Edge Function：

1. `kling-motion-control-create`：校验素材与参数，调用创建接口并返回 `task_id`；
2. `kling-motion-control-query`：接收 `task_id` 或 `external_task_id`，转换为上游 GET 查询；成功后转存视频并返回持久化 URL。

前端流程：提交一次 → 保存任务 ID → 前 30 秒每 3 秒查询 → 之后每 7 秒查询 → `succeeded` 时提取 `outputs[type=video].url` → 自动渲染带 controls 的视频播放器 → 显示“下载视频”按钮 → 失败时展示任务 `message` → 10 分钟后停止自动轮询并保留继续查询入口。

页面只有在 `status=succeeded` 且至少取得一个视频 URL 后才能显示“生成成功”。任务 ID 只能作为进度信息，不能作为最终结果。Web 与小程序都必须实现预览；Web 必须提供下载链接，小程序必须提供保存到相册或复制下载地址的入口。完整 Edge Function、React 轮询与结果 UI 代码见 `references/app-complete-workflow.md`，生成应用时必须读取并实现，不得只生成任务状态卡片。

不要只依赖 Callback。配置 Callback 时仍保留轮询兜底，并校验回调来源、任务 ID、状态顺序和幂等键。以服务端查询结果为权威状态。

## 状态与幂等

- `external_task_id` 在账号内必须唯一，建议服务端生成 UUID。
- 创建按钮提交后立即禁用，避免重复扣费。
- 转存幂等键使用 `task.id + output.id`。
- 状态只允许 `submitted → processing → succeeded|failed`；忽略迟到的倒退状态。
- 下载失败不等于生成失败，保留原 URL 并单独重试下载。

## 错误处理

返回给前端的安全结构：

```json
{
  "error": "动作控制任务创建失败",
  "type": "upstream_error",
  "code": 1200,
  "message": "上游错误信息",
  "request_id": "request-id"
}
```

参数错误返回 400；鉴权或权限错误不自动重试；429 与服务端临时错误仅对查询进行退避；创建请求响应不确定时，先按唯一 `external_task_id` 查询，不盲目重提。

## 参考资料

- `references/motion-control-create-api.md`：创建接口、Schema 与示例。
- `references/task-query-api.md`：按任务 ID 精确查询与状态处理。
- `references/integration-guide.md`：产品体验、持久化与验收。
- `references/app-complete-workflow.md`：应用内自动轮询、视频转存、预览与下载的强制完整实现。
- `scripts/kling_motion_control.py`：可复用的创建、精确查询、轮询、下载 CLI。

## 沟通规则

- 默认使用中文解释结果。
- 对用户展示业务状态、失败原因和结果链接，不展示内部鉴权材料。
- 未知值使用明确字段名标记；API ID 以飞轮后台生成信息为准，不猜测计费单价或文档未提供的错误码。

## 常见坑

- `character_orientation=image` 却上传超过 10 秒的视频；
- 使用主体时仍选择 `image` 朝向；
- 同时传 `task_ids` 与 `external_task_ids`；
- 查询时直接读取 `data[0]`，拿到错误任务；
- 只接 Callback，事件丢失后任务永久卡住；
- 成功后未转存，30 天后结果链接失效；
- 把第三方 Key 放进前端、日志或 Skill 文档。
