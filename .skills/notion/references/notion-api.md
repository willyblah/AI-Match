# Notion API 通用规则与 Action 索引

本文是 Notion Skill 的总索引，只放通用规则、使用边界和 action reference 映射。具体接口参数、生成期代码、Edge Function 代码和前端调用代码分别放在独立 action reference 文件中。

## 使用边界

### 生成期用法（Agent 直接调用）

生成期指 Agent 在需求澄清、信息读取、内容生成、生成前校验或生成中辅助决策时调用 Notion。

- 必须由 Agent 直接调用 Notion REST API：`https://api.notion.com/v1`。
- 使用服务端环境变量读取 token，例如 `process.env["NOTION_TOKEN"]`。
- 不创建、不调用、不依赖 Edge Function。
- 不使用 `supabase.functions.invoke` 作为生成期 Notion 调用方式。
- 不展示、不保存、不复述真实 token 或 Authorization header。

### 生成后用法（应用内通过 Edge Function 调用）

生成后指已经生成出的应用在运行时访问 Notion。

- 前端只能调用 Edge Function 或等价服务端接口。
- Edge Function 通过 `Deno.env.get("NOTION_TOKEN")` 读取密钥。
- 前端不能出现 `NOTION_TOKEN`，不能设置 Notion `Authorization` header。
- Edge Function 不向前端返回 token、Authorization header 或其他敏感上下文。
- 写操作需要应用侧确认交互，确认后再调用 Edge Function。

## API 基本信息

Base URL：`https://api.notion.com/v1`

| Action | 方法与端点 | Reference | 用途 |
|--------|------------|-----------|------|
| `search` | `POST /search` | `search-api.md` | 搜索页面或数据库 |
| `getPageBlocks` | `GET /blocks/{block_id}/children` | `page-blocks-api.md` | 读取页面或块的正文子块 |
| `queryDatabase` | `POST /databases/{database_id}/query` | `database-query-api.md` | 查询数据库记录 |
| `getDatabaseSchema` | `GET /databases/{database_id}` | `database-schema-api.md` | 读取数据库 schema |
| `createPage` | `POST /pages` | `page-create-api.md` | 创建页面或数据库记录 |
| `appendBlockChildren` | `PATCH /blocks/{block_id}/children` | `block-append-api.md` | 追加正文块 |
| `updatePageProperties` | `PATCH /pages/{page_id}` | `page-update-api.md` | 更新页面属性 |

ID 可以从 Notion URL 中提取：`https://www.notion.so/<name>-<32位十六进制>`，末尾 32 位十六进制字符串就是 page/database id，可按 Notion API 习惯加连字符。

## 认证头

所有 Notion API 请求都需要带：

```http
Authorization: Bearer ${NOTION_TOKEN}
Notion-Version: 2022-06-28
Content-Type: application/json
```

说明：

- `NOTION_TOKEN` 由平台注入，示例只能使用环境变量占位。
- 生成期代码读取 `process.env["NOTION_TOKEN"]` 或等价安全注入方式。
- Edge Function 代码读取 `Deno.env.get("NOTION_TOKEN")`。
- 前端调用代码不得包含 token 或 Authorization header。

## 分页处理

Notion 常见分页响应字段：

```json
{
  "has_more": true,
  "next_cursor": "..."
}
```

下一页请求：

- 搜索：body 中加入 `start_cursor`。
- 数据库查询：body 中加入 `start_cursor`。
- 块 children：query string 加 `start_cursor`。

如果用户要求“全部内容”，应持续请求直到 `has_more=false`。为避免单次响应过大，读取块内容时可先按页获取，再整理为 Markdown。

## 写操作确认规则

以下 action 属于写操作，调用前必须让用户确认目标和写入内容：

- `createPage`
- `appendBlockChildren`
- `updatePageProperties`

确认内容至少包括：

- 目标页面、父页面或数据库
- 将要创建、追加或更新的字段与内容
- 覆盖属性时的字段名和新值

未获得明确确认前，不执行写操作。

## 常见错误码

| 现象 | 原因 | 处理 |
|------|------|------|
| 401 unauthorized | token 过期或无效 | 提示用户重新授权 |
| 400 missing/invalid `Notion-Version` | 未带版本头或版本错误 | 加 `Notion-Version: 2022-06-28` |
| 404 object_not_found | 页面或数据库未授权，或 ID 错误 | 核对 ID；提示重新授权时勾选对应页面 |
| 400 validation_error | properties 字段名或类型不匹配 schema | 先 `GET /databases/{id}` 对齐字段名和类型 |
| 429 rate_limited | 触发限流 | 按 `Retry-After` 退避重试，降低并发 |

## 安全检查清单

- 不在文件中写入真实 token。
- 不把 `Authorization` header 返回给前端。
- 不让前端直接调用 Notion API 并携带 token。
- 不在生成期代码中使用 `supabase.functions.invoke` 调 Notion。
- 不在前端示例中出现 `NOTION_TOKEN` 或 Notion `Authorization` header。
- 写操作前确认目标页面 / 数据库、字段和值。
- 404 时优先检查授权范围和 ID。

## Action Reference 索引

- `search-api.md`：搜索页面或数据库。
- `page-blocks-api.md`：读取页面或块的子块、分页和递归读取。
- `database-query-api.md`：查询数据库记录、filter、sorts、分页和字段读取。
- `database-schema-api.md`：读取数据库 schema 和字段类型。
- `page-create-api.md`：创建普通页面或数据库记录。
- `block-append-api.md`：追加正文块。
- `page-update-api.md`：更新页面属性。
