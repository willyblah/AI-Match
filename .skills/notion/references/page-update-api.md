# Notion Page Update API Action Reference

## API 基本信息

| 项目 | 内容 |
|------|------|
| Action | `updatePageProperties` |
| 方法 | `PATCH` |
| 端点 | `/pages/{page_id}` |
| 用途 | 更新页面或数据库记录的属性字段 |
| 读写类型 | 写操作，调用前必须确认 |

## 请求参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page_id` | string | 是 | 要更新的页面 ID 或数据库记录 page ID |
| `properties` | object | 否 | 要更新的属性字段 |
| `archived` | boolean | 否 | 是否归档页面 |
| `icon` | object | 否 | 更新页面图标 |
| `cover` | object | 否 | 更新页面封面 |

## 响应字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 页面 ID |
| `object` | string | 通常为 `page` |
| `last_edited_time` | string | 最近编辑时间 |
| `properties` | object | 更新后的页面属性 |
| `archived` | boolean | 是否已归档 |
| `url` | string | 页面 URL |

## 生成期代码（Agent 直接调用）

生成期由 Agent 直接调用 Notion REST API。执行前必须先向用户复述目标页面、字段名和新值，并获得明确确认。

```typescript
const token = process.env["NOTION_TOKEN"];
if (!token) {
  throw new Error("Notion 未授权或缺少 NOTION_TOKEN");
}

const confirmedByUser = true;
if (!confirmedByUser) {
  throw new Error("更新页面属性前必须先获得用户确认");
}

const pageId = "<PAGE_ID>";
const response = await fetch(`https://api.notion.com/v1/pages/${pageId}`, {
  method: "PATCH",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    properties: {
      "状态": { select: { name: "已完成" } },
    },
  }),
});

if (!response.ok) {
  throw new Error(`Notion page update failed: ${response.status}`);
}

const page = await response.json();
```

## Edge Function 代码

应用内运行时通过 Edge Function 更新页面属性。确认交互应在前端完成，Edge Function 仍要校验 `confirmed` 标记。

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
    return new Response(JSON.stringify({ error: "更新页面属性前必须先确认目标字段和新值" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const pageId = String(body.page_id ?? "");
  if (!pageId) {
    return new Response(JSON.stringify({ error: "Missing page_id" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const response = await fetch(`https://api.notion.com/v1/pages/${pageId}`, {
    method: "PATCH",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      properties: body.properties,
      archived: body.archived,
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

前端先展示确认信息，用户确认后只调用 Edge Function。

```typescript
const confirmed = await showConfirmDialog({
  title: "确认更新 Notion 页面属性",
  message: "将把目标记录的状态更新为：已完成。",
});

if (confirmed) {
  const { data, error } = await supabase.functions.invoke("notion-page-update", {
    body: {
      confirmed: true,
      page_id: pageId,
      properties: {
        "状态": { select: { name: "已完成" } },
      },
    },
  });

  if (error) {
    throw error;
  }
}
```

## 注意事项

- 这是写操作，调用前必须让用户确认目标页面、字段名和新值。
- 更新数据库记录字段前，应先调用 `getDatabaseSchema` 对齐字段名和字段类型。
- 覆盖属性可能替换原值，确认文案必须明确说明会变更哪些字段。
- `validation_error` 通常表示字段名、字段类型或属性结构不匹配。
- 归档页面也属于写操作，必须确认后执行。
