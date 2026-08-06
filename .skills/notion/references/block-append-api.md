# Notion Block Append API Action Reference

## API 基本信息

| 项目 | 内容 |
|------|------|
| Action | `appendBlockChildren` |
| 方法 | `PATCH` |
| 端点 | `/blocks/{block_id}/children` |
| 用途 | 向页面或块追加正文子块 |
| 读写类型 | 写操作，调用前必须确认 |

## 请求参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `block_id` | string | 是 | 目标页面 ID 或块 ID |
| `children` | array | 是 | 要追加的 Notion block 数组 |
| `position` | object | 否 | 追加位置，格式如 `{ "type": "after_block", "after_block": { "id": "..." } }`；不传时追加到目标块末尾 |

## 响应字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `object` | string | 通常为 `list` |
| `results` | array | 新追加的块列表 |
| `results[].id` | string | 新块 ID |
| `results[].type` | string | 新块类型 |
| `has_more` | boolean | 通常为 false |
| `next_cursor` | string/null | 下一页游标，通常为 null |

## 生成期代码（Agent 直接调用）

生成期由 Agent 直接调用 Notion REST API。执行前必须先向用户复述目标页面或块，以及将追加的正文内容，并获得明确确认。

```typescript
const token = process.env["NOTION_TOKEN"];
if (!token) {
  throw new Error("Notion 未授权或缺少 NOTION_TOKEN");
}

const confirmedByUser = true;
if (!confirmedByUser) {
  throw new Error("追加正文块前必须先获得用户确认");
}

const blockId = "<PAGE_OR_BLOCK_ID>";
const response = await fetch(`https://api.notion.com/v1/blocks/${blockId}/children`, {
  method: "PATCH",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    children: [
      {
        object: "block",
        type: "paragraph",
        paragraph: {
          rich_text: [
            { type: "text", text: { content: "追加的一段文字" } },
          ],
        },
      },
    ],
    position: {
      type: "after_block",
      after_block: { id: "<AFTER_BLOCK_ID>" },
    },
  }),
});

if (!response.ok) {
  throw new Error(`Notion block append failed: ${response.status}`);
}

const data = await response.json();
```

如果不需要指定插入位置，可以省略 `position`，默认追加到目标块末尾。

## Edge Function 代码

应用内运行时通过 Edge Function 追加块。确认交互应在前端完成，Edge Function 仍要校验 `confirmed` 标记。Edge Function 入口仍接收前端 POST 请求；只有转发到 Notion 的 upstream 请求使用 `PATCH`。

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
    return new Response(JSON.stringify({ error: "追加正文块前必须先确认目标和内容" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const blockId = String(body.block_id ?? body.page_id ?? "");
  if (!blockId) {
    return new Response(JSON.stringify({ error: "Missing block_id or page_id" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const response = await fetch(`https://api.notion.com/v1/blocks/${blockId}/children`, {
    method: "PATCH",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      children: body.children,
      position: body.position,
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

前端先展示确认信息，用户确认后只调用 Edge Function。`position` 是可选参数；不传时追加到目标块末尾。

```typescript
const confirmed = await showConfirmDialog({
  title: "确认追加 Notion 内容",
  message: "将在目标页面末尾追加：追加的一段文字。",
});

if (confirmed) {
  const { data, error } = await supabase.functions.invoke("notion-block-append", {
    body: {
      confirmed: true,
      block_id: pageId,
      children: [
        {
          object: "block",
          type: "paragraph",
          paragraph: {
            rich_text: [
              { type: "text", text: { content: "追加的一段文字" } },
            ],
          },
        },
      ],
      position: {
        type: "after_block",
        after_block: { id: afterBlockId },
      },
    },
  });

  if (error) {
    throw error;
  }
}
```

## 注意事项

- 这是写操作，调用前必须让用户确认目标页面或块，以及追加内容。
- 页面 ID 可以作为 `block_id` 使用。
- `PATCH /blocks/{block_id}/children` 用于追加子块。
- `PATCH /blocks/{block_id}` 用于更新已有 block 的内容，不能直接更新 block children。
- 支持追加 `paragraph`、`heading_1`、`heading_2`、`heading_3`、`bulleted_list_item`、`numbered_list_item`、`to_do`、`quote`、`code` 等块。
- Notion 对单次追加块数量有限制，内容较多时应拆分追加。
