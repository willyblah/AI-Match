# Notion Database Schema API Action Reference

## API 基本信息

| 项目 | 内容 |
|------|------|
| Action | `getDatabaseSchema` |
| 方法 | `GET` |
| 端点 | `/databases/{database_id}` |
| 用途 | 读取数据库 schema，确认字段名、字段类型和可选项 |
| 读写类型 | 读操作 |

## 请求参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `database_id` | string | 是 | 数据库 ID |

## 响应字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 数据库 ID |
| `title` | array | 数据库标题 rich text |
| `properties` | object | 数据库字段定义 |
| `properties.{name}.id` | string | 字段 ID |
| `properties.{name}.type` | string | 字段类型 |
| `properties.{name}.{type}` | object | 字段类型对应的配置，例如 select options |
| `url` | string | 数据库 URL |

## 生成期代码（Agent 直接调用）

生成期由 Agent 直接调用 Notion REST API。写数据库记录或更新字段前优先读取 schema。

```typescript
const token = process.env["NOTION_TOKEN"];
if (!token) {
  throw new Error("Notion 未授权或缺少 NOTION_TOKEN");
}

const databaseId = "<DATABASE_ID>";
const response = await fetch(`https://api.notion.com/v1/databases/${databaseId}`, {
  method: "GET",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Notion-Version": "2022-06-28",
  },
});

if (!response.ok) {
  throw new Error(`Notion database schema read failed: ${response.status}`);
}

const schema = await response.json();
const properties = schema.properties;
```

## Edge Function 代码

应用内通过 Edge Function 读取 schema，前端只传数据库 ID。

```typescript
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const token = Deno.env.get("NOTION_TOKEN");
  if (!token) {
    return new Response(JSON.stringify({ error: "Notion 未授权或缺少 NOTION_TOKEN" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  const body = await req.json();
  const databaseId = String(body.database_id ?? "");
  if (!databaseId) {
    return new Response(JSON.stringify({ error: "Missing database_id" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const response = await fetch(`https://api.notion.com/v1/databases/${databaseId}`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
    },
  });

  const data = await response.json();
  return new Response(JSON.stringify(data), {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
});
```

## 前端调用代码

前端只传数据库 ID，不接触 Notion token 或 Notion 认证头。

```typescript
const { data, error } = await supabase.functions.invoke("notion-database-schema", {
  body: {
    database_id: databaseId,
  },
});

if (error) {
  throw error;
}
```

## 注意事项

- 写数据库记录或更新属性前，应先确认 schema。
- `properties` 的 key 是字段显示名，字段值中包含 `type` 和类型专属配置。
- select、multi_select、status 等字段需要确认可选项名称。
- Notion 返回 `404 object_not_found` 时，优先检查数据库是否授权给当前集成。
