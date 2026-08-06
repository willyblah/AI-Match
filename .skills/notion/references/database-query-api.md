# Notion Database Query API Action Reference

## API 基本信息

| 项目 | 内容 |
|------|------|
| Action | `queryDatabase` |
| 方法 | `POST` |
| 端点 | `/databases/{database_id}/query` |
| 用途 | 查询 Notion 数据库记录，支持 filter、sorts 和分页 |
| 读写类型 | 读操作 |

## 请求参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `database_id` | string | 是 | 数据库 ID |
| `filter` | object | 否 | Notion 数据库过滤条件 |
| `sorts` | array | 否 | 排序条件数组 |
| `start_cursor` | string | 否 | 下一页游标 |
| `page_size` | number | 否 | 单页数量，最大 100 |

## 响应字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `object` | string | 通常为 `list` |
| `results` | array | 查询到的数据库记录，每条记录本质是 page |
| `results[].id` | string | 记录 page ID |
| `results[].properties` | object | 字段值集合 |
| `results[].url` | string | 记录页面 URL |
| `has_more` | boolean | 是否还有下一页 |
| `next_cursor` | string/null | 下一页游标 |

## 生成期代码（Agent 直接调用）

生成期由 Agent 直接调用 Notion REST API。字段名或字段类型不确定时，先调用 `getDatabaseSchema`。

```typescript
const token = process.env["NOTION_TOKEN"];
if (!token) {
  throw new Error("Notion 未授权或缺少 NOTION_TOKEN");
}

const databaseId = "<DATABASE_ID>";
const response = await fetch(`https://api.notion.com/v1/databases/${databaseId}/query`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    filter: { property: "状态", select: { equals: "进行中" } },
    sorts: [{ property: "创建时间", direction: "descending" }],
    page_size: 20,
  }),
});

if (!response.ok) {
  throw new Error(`Notion database query failed: ${response.status}`);
}

const data = await response.json();
```

## Edge Function 代码

应用内通过 Edge Function 查询数据库，前端只传数据库 ID、过滤、排序和分页条件。

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

  const response = await fetch(`https://api.notion.com/v1/databases/${databaseId}/query`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filter: body.filter,
      sorts: body.sorts,
      start_cursor: body.start_cursor,
      page_size: body.page_size ?? 20,
    }),
  });

  const data = await response.json();
  return new Response(JSON.stringify(data), {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
});
```

## 前端调用代码

前端只传查询条件，不接触 Notion token 或 Notion 认证头。

```typescript
const { data, error } = await supabase.functions.invoke("notion-database-query", {
  body: {
    database_id: databaseId,
    filter: { property: "状态", select: { equals: "进行中" } },
    sorts: [{ property: "创建时间", direction: "descending" }],
    page_size: 20,
  },
});

if (error) {
  throw error;
}
```

## 注意事项

- 数据库记录本质是 page，字段值在 `results[].properties`。
- 字段结构随类型变化，常见类型包括 `title`、`rich_text`、`select`、`multi_select`、`date`、`number`、`checkbox`、`url`、`email`、`phone_number`、`relation`、`rollup`。
- 不确定字段名或字段类型时，先读取数据库 schema。
- 需要读取全部记录时，循环使用 `has_more` 和 `next_cursor`。
