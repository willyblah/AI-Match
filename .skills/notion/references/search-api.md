# Notion Search API Action Reference

## API 基本信息

| 项目 | 内容 |
|------|------|
| Action | `search` |
| 方法 | `POST` |
| 端点 | `/search` |
| 用途 | 按标题关键词搜索当前授权用户可访问的 Notion 页面或数据库 |
| 读写类型 | 读操作 |

## 请求参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 否 | 搜索关键词；不传时按 Notion 默认搜索授权内容 |
| `filter` | object | 否 | 限定搜索对象，格式如 `{ "property": "object", "value": "page" }`，`value` 可为 `page` 或 `database` |
| `sort` | object | 否 | 排序条件，如按 `last_edited_time` 排序 |
| `start_cursor` | string | 否 | 下一页游标 |
| `page_size` | number | 否 | 单页数量，最大 100 |

## 响应字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `object` | string | 通常为 `list` |
| `results` | array | 搜索结果，元素可能是 page 或 database |
| `results[].object` | string | `page` 或 `database` |
| `results[].id` | string | 页面或数据库 ID |
| `results[].url` | string | Notion 页面 URL |
| `has_more` | boolean | 是否还有下一页 |
| `next_cursor` | string/null | 下一页游标 |

## 生成期代码（Agent 直接调用）

生成期由 Agent 直接调用 Notion REST API，不创建、不调用 Edge Function。

```typescript
const token = process.env["NOTION_TOKEN"];
if (!token) {
  throw new Error("Notion 未授权或缺少 NOTION_TOKEN");
}

const response = await fetch("https://api.notion.com/v1/search", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    query: "周报",
    filter: { property: "object", value: "page" },
    page_size: 10,
  }),
});

if (!response.ok) {
  throw new Error(`Notion search failed: ${response.status}`);
}

const data = await response.json();
```

## Edge Function 代码

应用内运行时通过 Edge Function 转发，token 只在服务端读取。

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
  const response = await fetch("https://api.notion.com/v1/search", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: body.query,
      filter: body.filter,
      sort: body.sort,
      start_cursor: body.start_cursor,
      page_size: body.page_size ?? 10,
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

前端只调用 Edge Function，不接触 Notion token 或 Notion 认证头。

```typescript
const { data, error } = await supabase.functions.invoke("notion-search", {
  body: {
    query: "周报",
    filter: { property: "object", value: "page" },
    page_size: 10,
  },
});

if (error) {
  throw error;
}
```

## 注意事项

- 只能搜索用户已授权给集成的页面和数据库。
- `404 object_not_found` 不一定代表对象不存在，也可能是未授权。
- 需要获取全部结果时，循环使用 `has_more` 和 `next_cursor`。
- 搜索结果只包含页面或数据库元数据；读取页面正文需调用 `getPageBlocks`。
