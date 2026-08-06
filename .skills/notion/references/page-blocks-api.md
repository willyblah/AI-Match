# Notion Page Blocks API Action Reference

## API 基本信息

| 项目 | 内容 |
|------|------|
| Action | `getPageBlocks` |
| 方法 | `GET` |
| 端点 | `/blocks/{block_id}/children` |
| 用途 | 读取页面或块的子块内容，必要时递归读取嵌套块 |
| 读写类型 | 读操作 |

## 请求参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `block_id` | string | 是 | 页面 ID 或块 ID；页面 ID 可直接作为 block ID 使用 |
| `page_size` | number | 否 | 单页数量，最大 100，默认 100 |
| `start_cursor` | string | 否 | 下一页游标 |
| `recursive` | boolean | 否 | 是否递归读取 `has_children=true` 的子块 |

## 响应字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `object` | string | 通常为 `list` |
| `results` | array | 子块列表 |
| `results[].id` | string | 块 ID |
| `results[].type` | string | 块类型，如 `paragraph`、`heading_1`、`to_do`、`code` |
| `results[].has_children` | boolean | 是否存在嵌套子块 |
| `results[][{type}].rich_text` | array | 文本内容数组，字段名随块类型变化 |
| `has_more` | boolean | 是否还有下一页 |
| `next_cursor` | string/null | 下一页游标 |

## 生成期代码（Agent 直接调用）

生成期由 Agent 直接调用 Notion REST API；如果用户要“全文”，需要处理分页和递归。

```typescript
const token = process.env["NOTION_TOKEN"];
if (!token) {
  throw new Error("Notion 未授权或缺少 NOTION_TOKEN");
}

async function getBlockChildren(blockId: string, startCursor?: string) {
  const url = new URL(`https://api.notion.com/v1/blocks/${blockId}/children`);
  url.searchParams.set("page_size", "100");
  if (startCursor) {
    url.searchParams.set("start_cursor", startCursor);
  }

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
    },
  });

  if (!response.ok) {
    throw new Error(`Notion blocks read failed: ${response.status}`);
  }

  return response.json();
}

const firstPage = await getBlockChildren("<PAGE_OR_BLOCK_ID>");
```

## Edge Function 代码

应用内通过 Edge Function 读取块列表，递归整理可放在 Edge Function 或前端展示层，但 token 只能在 Edge Function 中使用。

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
  const blockId = String(body.block_id ?? body.page_id ?? "");
  if (!blockId) {
    return new Response(JSON.stringify({ error: "Missing block_id or page_id" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const url = new URL(`https://api.notion.com/v1/blocks/${blockId}/children`);
  url.searchParams.set("page_size", String(body.page_size ?? 100));
  if (body.start_cursor) {
    url.searchParams.set("start_cursor", String(body.start_cursor));
  }

  const response = await fetch(url, {
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

前端只传页面或块 ID 与分页参数。

```typescript
const { data, error } = await supabase.functions.invoke("notion-page-blocks", {
  body: {
    block_id: pageId,
    page_size: 100,
  },
});

if (error) {
  throw error;
}
```

## 注意事项

- `/pages/{page_id}` 只返回页面属性，不返回正文。
- 页面正文必须读取 `/blocks/{block_id}/children`。
- `has_children=true` 的块需要递归读取才能得到完整正文。
- 常见文本块包括 `paragraph`、`heading_1`、`heading_2`、`heading_3`、`bulleted_list_item`、`numbered_list_item`、`to_do`、`quote`、`code`。
- 输出给用户时优先整理为 Markdown。
