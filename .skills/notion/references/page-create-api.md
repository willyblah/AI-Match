# Notion Page Create API Action Reference

## API 基本信息

| 项目 | 内容 |
|------|------|
| Action | `createPage` |
| 方法 | `POST` |
| 端点 | `/pages` |
| 用途 | 创建普通子页面或数据库记录 |
| 读写类型 | 写操作，调用前必须确认 |

## 请求参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `parent` | object | 是 | 父级对象，普通页面用 `{ "page_id": "..." }`，数据库记录用 `{ "database_id": "..." }` |
| `properties` | object | 是 | 页面或数据库记录属性；数据库记录必须匹配 schema |
| `children` | array | 否 | 创建页面时一并写入的正文块 |
| `icon` | object | 否 | 页面图标 |
| `cover` | object | 否 | 页面封面 |

## 响应字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 新建页面 ID |
| `object` | string | 通常为 `page` |
| `created_time` | string | 创建时间 |
| `last_edited_time` | string | 最近编辑时间 |
| `properties` | object | 页面属性 |
| `url` | string | 新建页面 URL |

## 生成期代码（Agent 直接调用）

生成期由 Agent 直接调用 Notion REST API。执行前必须先向用户复述目标父页面或数据库、将写入的属性和正文内容，并获得明确确认。

```typescript
const token = process.env["NOTION_TOKEN"];
if (!token) {
  throw new Error("Notion 未授权或缺少 NOTION_TOKEN");
}

const confirmedByUser = true;
if (!confirmedByUser) {
  throw new Error("创建页面前必须先获得用户确认");
}

const response = await fetch("https://api.notion.com/v1/pages", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    parent: { database_id: "<DATABASE_ID>" },
    properties: {
      "名称": { title: [{ text: { content: "新任务" } }] },
      "状态": { select: { name: "待办" } },
    },
    children: [
      {
        object: "block",
        type: "paragraph",
        paragraph: {
          rich_text: [{ type: "text", text: { content: "任务说明" } }],
        },
      },
    ],
  }),
});

if (!response.ok) {
  throw new Error(`Notion page create failed: ${response.status}`);
}

const page = await response.json();
```

## Edge Function 代码

应用内运行时通过 Edge Function 创建页面。确认交互应在前端完成，Edge Function 仍要校验 `confirmed` 标记，避免绕过确认。

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
  if (body.confirmed !== true) {
    return new Response(JSON.stringify({ error: "创建页面前必须先确认目标和内容" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const response = await fetch("https://api.notion.com/v1/pages", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      parent: body.parent,
      properties: body.properties,
      children: body.children,
      icon: body.icon,
      cover: body.cover,
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

前端先展示确认信息，用户确认后只调用 Edge Function，不接触 Notion token 或 Notion 认证头。

```typescript
const confirmed = await showConfirmDialog({
  title: "确认创建 Notion 页面",
  message: "将在目标数据库中创建记录：新任务，状态：待办。",
});

if (confirmed) {
  const { data, error } = await supabase.functions.invoke("notion-page-create", {
    body: {
      confirmed: true,
      parent: { database_id: databaseId },
      properties: {
        "名称": { title: [{ text: { content: "新任务" } }] },
        "状态": { select: { name: "待办" } },
      },
    },
  });

  if (error) {
    throw error;
  }
}
```

## 注意事项

- 这是写操作，调用前必须让用户确认目标和写入内容。
- 普通子页面使用 `parent.page_id`。
- 数据库记录使用 `parent.database_id`，并按 schema 填写 `properties`。
- 不确定字段名或字段类型时，先调用 `getDatabaseSchema`。
- `validation_error` 通常表示字段名、字段类型或属性结构不匹配。
