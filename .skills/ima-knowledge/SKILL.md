---
name: ima-knowledge
description: 腾讯 ima 知识库与笔记 API 集成。当用户需要上传文件到知识库、添加网页到知识库、搜索知识库、创建笔记、查询笔记、追加笔记内容时触发。需要自行在 https://ima.qq.com/agent-interface 申请 Client ID 和 API Key。支持知识库文件管理、网页导入、笔记读写、内容搜索。
license: MIT
---

# 腾讯 ima 知识库与笔记 API 集成

## 概述

在秒哒应用中集成腾讯 ima 知识库和笔记能力，通过 Edge Function 调用 ima OpenAPI，实现文件上传到知识库、网页导入、笔记读写、内容搜索等功能。

ima 提供两类核心能力：
- **知识库（Knowledge Base）**：存储和管理文件、网页、笔记等媒体内容
- **笔记（Notes）**：创建、读取、追加和搜索个人笔记

## 适用场景

- 上传文件（PDF/Word/Excel/图片/音频等）到知识库
- 添加网页链接或微信文章到知识库
- 搜索知识库中的内容
- 浏览知识库文件和文件夹
- 查看/分析/导出知识库中媒体的原文
- 查询用户有权限添加内容的知识库
- 创建新笔记并记录内容
- 追加内容到已有笔记
- 读取、搜索笔记，浏览笔记本

## 前置条件

**必填配置**：Client ID + API Key

获取方式：
1. 访问 https://ima.qq.com/agent-interface
2. 申请并获取 Client ID 和 API Key

**秒哒平台配置**：

在秒哒 Edge Function 的环境变量中配置：

```
IMA_CLIENT_ID=<your_client_id>
IMA_API_KEY=<your_api_key>
```

**其他配置**：文件上传到知识库需要腾讯云 COS，由 `create_media` 接口自动返回临时上传凭证，无需预配置。

## 关键工作流：知识库 ID 自动解析

**用户不需要手动填写知识库 ID。** Agent 的工作流如下：

```
用户说"把文件上传到我的知识库"
    │
    ▼
Agent 调用 search_knowledge_base(query="") 获取所有知识库
    │
    ▼
展示知识库列表给用户（显示名称，隐藏ID）
用户选择"XX知识库"
    │
    ▼
Agent 用 KB ID 执行后续操作（上传/搜索/添加等）
```

**任何时候都不要让用户提供知识库 ID 字符串**。用户提供知识库名称后，Agent 先用 `search_knowledge_base` 搜索获取 ID，再用 ID 操作。

## API 接入说明

- **Base URL**: `https://ima.qq.com`
- **协议**: HTTP POST，JSON Body
- **认证方式**: Header 鉴权

```typescript
const headers = {
  'Content-Type': 'application/json',
  'ima-openapi-clientid': Deno.env.get('IMA_CLIENT_ID')!,
  'ima-openapi-apikey': Deno.env.get('IMA_API_KEY')!,
};
```

### 统一响应格式

```json
{
  "code": 0,
  "msg": "success",
  "data": { ... }
}
```

- `code=0`：成功，从 `data` 提取业务字段
- `code≠0`：失败，直接将 `msg` 展示给用户

### 分页规范

所有列表/搜索接口使用游标分页：
1. 首次请求 `cursor` 传空字符串 `""`
2. `is_end=true` 时表示已到末尾
3. `is_end=false` 时用返回的 `next_cursor` 翻页

---

## 能力域

### 0. 知识库搜索（查询 KB ID 的入口）

所有知识库操作的第一步——通过知识库名称搜索获取其 ID。

```typescript
// POST https://ima.qq.com/openapi/wiki/v1/search_knowledge_base
// query 传知识库名称；query="" 返回所有知识库
async function searchKnowledgeBase(query: string, cursor = '', limit = 20) {
  const res = await fetch('https://ima.qq.com/openapi/wiki/v1/search_knowledge_base', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ query, cursor, limit }),
  });
  return res.json(); // data.info_list[].kb_id, data.info_list[].kb_name, data.info_list[].cover_url
}
```

> ⚠️ **字段名注意（重要，各接口不一致）**：
> - `search_knowledge_base` 返回的 `info_list` 元素字段是 **`kb_id`、`kb_name`**、`cover_url`（另有 member_count、content_count、description、creator、role_type、base_type）。取 ID 用 `info_list[0].kb_id`。
> - `get_addable_knowledge_base_list` 和 `get_knowledge_base` 返回的字段是 **`id`、`name`**（不是 kb_id）。
> - 三个接口字段名不统一，务必按接口区分，不要混用。

**展示格式**：
```
📚 你的知识库：
1. 产品文档库 — 存放产品相关文档
2. 技术方案库 — 技术方案汇总
```

#### 获取可添加的知识库列表（上传场景专用）

上传文件/添加内容时，应优先用此接口列出**用户有权限添加内容**的知识库（`search_knowledge_base` 返回的是所有可见知识库，不一定都有写入权限）。

```typescript
// POST https://ima.qq.com/openapi/wiki/v1/get_addable_knowledge_base_list
async function getAddableKnowledgeBaseList(cursor = '', limit = 50) {
  const res = await fetch('https://ima.qq.com/openapi/wiki/v1/get_addable_knowledge_base_list', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ cursor, limit }), // limit 1-50
  });
  return res.json(); // data.addable_knowledge_base_list[].id / .name, data.next_cursor, data.is_end
}
```

#### 获取知识库信息（按 ID 批量查询）

```typescript
// POST https://ima.qq.com/openapi/wiki/v1/get_knowledge_base
async function getKnowledgeBase(ids: string[]) {
  const res = await fetch('https://ima.qq.com/openapi/wiki/v1/get_knowledge_base', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ ids }), // 1-20 个，不重复
  });
  return res.json(); // data.infos: map<id, {id, name, cover_url, description, recommended_questions}>
}
```

### 1. 知识库文件管理

#### 上传文件到知识库

完整流程：`查知识库 ID` → `check_repeated_names` → `create_media` → `COS 上传` → `add_knowledge`

```typescript
// step1: 搜索知识库获取 KB ID（用户说名称，Agent 自动查）
// step2: 检查文件名重复
async function checkFileRepeat(kbId: string, fileName: string, mediaType: number) {
  // POST https://ima.qq.com/openapi/wiki/v1/check_repeated_names
}

// step3: 创建媒体，获取 COS 上传凭证
async function createMedia(kbId: string, fileName: string, fileSize: number, contentType: string, fileExt: string) {
  // POST https://ima.qq.com/openapi/wiki/v1/create_media
  // 返回 media_id + cos_credential（临时 COS 凭证）
}

// step4: 上传文件到腾讯云 COS
// 使用 create_media 返回的临时凭证上传

// step5: 添加知识
async function addKnowledge(kbId: string, mediaId: string, title: string, mediaType: number, fileInfo: object) {
  // POST https://ima.qq.com/openapi/wiki/v1/add_knowledge
}
```

**流程约束**：必须依次执行，不可跳步。文件已存在时必须询问用户是否保留两者。

#### 添加网页到知识库

```typescript
// POST https://ima.qq.com/openapi/wiki/v1/import_urls
async function importUrls(kbId: string, urls: string[], folderId?: string) {
  const res = await fetch('https://ima.qq.com/openapi/wiki/v1/import_urls', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      knowledge_base_id: kbId,
      folder_id: folderId, // 省略=根目录
      urls, // 1-10 个
    }),
  });
  return res.json();
}
```

#### 搜索知识库内容

```typescript
// POST https://ima.qq.com/openapi/wiki/v1/search_knowledge
async function searchKnowledge(kbId: string, query: string, cursor = '') {
  const res = await fetch('https://ima.qq.com/openapi/wiki/v1/search_knowledge', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ query, cursor, knowledge_base_id: kbId }),
  });
  return res.json();
}
```

**Agent 必须做的**：用 `search_knowledge_base` 先查出知识库 ID（用户只需告诉名称），再用 ID 调 `search_knowledge`。

#### 浏览知识库内容

```typescript
// POST https://ima.qq.com/openapi/wiki/v1/get_knowledge_list
async function listKnowledge(kbId: string, folderId?: string, cursor = '', limit = 20) {
  const res = await fetch('https://ima.qq.com/openapi/wiki/v1/get_knowledge_list', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      cursor, limit,
      knowledge_base_id: kbId,
      ...(folderId ? { folder_id: folderId } : {}),
    }),
  });
  return res.json();
}
```

> ⚠️ **返回字段是 `knowledge_list`（不是 `info_list`）**：`get_knowledge_list` 返回 `data.knowledge_list[]`（含 `media_id`、`title`、`parent_folder_id`、`media_type`、`tags`），另有 `is_end`、`next_cursor`、`current_path`。注意区别于 `search_knowledge` 的 `info_list`。

#### 获取媒体信息（查看/分析/导出原文）

用户想查看原文、分析原文、导出原文时，通过 `media_id` 获取访问信息。

```typescript
// POST https://ima.qq.com/openapi/wiki/v1/get_media_info
async function getMediaInfo(mediaId: string) {
  const res = await fetch('https://ima.qq.com/openapi/wiki/v1/get_media_info', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ media_id: mediaId }),
  });
  return res.json();
}
```

**返回分支处理：**

| 场景 | 响应特征 | 处理方式 |
|:---|:---|:---|
| 可 URL 访问 | `data.url_info.url` 非空 | 用 `url` + `headers`（如有）请求原文 |
| 笔记类型 | `data.media_type=11`，有 `notebook_ext_info.notebook_id` | 用 `notebook_id` 当 `note_id` 调 notes 的 `get_doc_content` |
| 不可访问 | `data.url_info` 为空 | 提示用户"请使用 ima 客户端查看原文" |
| 调用失败 | `code≠0` | 将 `msg` 展示给用户 |

#### 知识库文件类型与大小限制

| 类型 | media_type | 最大大小 |
|:---|:---:|:---:|
| PDF | 1 | 200 MB |
| 网页 | 2 | 无（直接 add_knowledge，web_info.content_id=url） |
| Word | 3 | 200 MB |
| PPT | 4 | 200 MB |
| Excel / CSV | 5 | 10 MB |
| 微信公众号文章 | 6 | 无（URL 匹配 mp.weixin.qq.com/s） |
| Markdown | 7 | 10 MB |
| 图片（png/jpg/webp） | 9 | 30 MB |
| 笔记 | 11 | 无（note_info.content_id=doc_id） |
| AI会话 | 12 | 无（session_info.content_id=session_id） |
| TXT | 13 | 10 MB |
| Xmind | 14 | 10 MB |
| 录音（mp3/m4a/wav/aac） | 15 | 200 MB（≤2小时） |
| 视频解析 | 16 | ❌ 不支持通过 skill 添加，仅 ima 桌面端 |

> **文件夹说明**：根目录的 `folder_id` 等于 `knowledge_base_id`。`import_urls` 要求 `folder_id` 必填时传 `knowledge_base_id` 即表示根目录。定位文件夹用 `search_knowledge` 按名称搜索或 `get_knowledge_list` 逐级浏览。

> **URL 类型识别**：`mp.weixin.qq.com/s/` → media_type=6；Bilibili/YouTube/`file://` → 不支持（media_type=16，告知只能在桌面端添加）；其他 text/html → media_type=2。均用 `import_urls`。

### 2. 笔记

#### 搜索笔记

```typescript
// POST https://ima.qq.com/openapi/note/v1/search_note
// search_type: 0=标题检索, 1=正文检索
async function searchNote(query: string, searchType = 0, start = 0, end = 20) {
  const res = await fetch('https://ima.qq.com/openapi/note/v1/search_note', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      search_type: searchType,
      query_info: searchType === 0 ? { title: query } : { content: query },
      start, end,
    }),
  });
  return res.json();
}
```

#### 读取笔记内容

```typescript
// POST https://ima.qq.com/openapi/note/v1/get_doc_content
async function getNoteContent(noteId: string) {
  const res = await fetch('https://ima.qq.com/openapi/note/v1/get_doc_content', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      note_id: noteId,
      target_content_format: 0, // 0=纯文本
    }),
  });
  return res.json();
}
```

#### 创建笔记

```typescript
// POST https://ima.qq.com/openapi/note/v1/import_doc
// content_format 固定为 1（Markdown）
async function createNote(content: string, title?: string, folderId?: string) {
  const markdown = title ? `# ${title}\n\n${content}` : content;
  const res = await fetch('https://ima.qq.com/openapi/note/v1/import_doc', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      content_format: 1,
      content: markdown,
      ...(folderId ? { folder_id: folderId } : {}),
    }),
  });
  return res.json(); // 返回 note_id
}
```

#### 追加笔记内容

```typescript
// POST https://ima.qq.com/openapi/note/v1/append_doc
async function appendToNote(noteId: string, content: string) {
  const res = await fetch('https://ima.qq.com/openapi/note/v1/append_doc', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      note_id: noteId,
      content_format: 1,
      content: `\n${content}`,
    }),
  });
  return res.json();
}
```

#### 列出笔记

```typescript
// POST https://ima.qq.com/openapi/note/v1/list_note
// folder_id 为空则拉取全部笔记；根目录为 user_list_{userid}
async function listNote(folderId = '', cursor = '', limit = 20) {
  const res = await fetch('https://ima.qq.com/openapi/note/v1/list_note', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ folder_id: folderId, cursor, limit }), // limit 1-20
  });
  return res.json(); // data.note_book_list[].note_id / .title / .summary, data.is_end
}
```

#### 列出笔记本

```typescript
// POST https://ima.qq.com/openapi/note/v1/list_notebook
// 注意：cursor 首次传 "0"（不是空字符串）
async function listNotebook(cursor = '0', limit = 20) {
  const res = await fetch('https://ima.qq.com/openapi/note/v1/list_notebook', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ cursor, limit }), // limit 1-20
  });
  return res.json(); // data.note_folder_infos[].folder_id / .name, data.next_cursor, data.is_end
}
```

> **笔记模块字段/翻页注意：**
> - `search_note` 返回字段是 `search_note_infos`（含 `note_book_info`、`highlightInfo`），翻页用 `start`/`end`（相差 ≤ 20），返回 `is_end` + `total_hit_num`。
> - `list_note` 翻页 `cursor` 首次传 `""`；`list_notebook` 翻页 `cursor` 首次传 `"0"`。
> - `get_doc_content` 的 `target_content_format` 用 `0`（纯文本），`1`（Markdown）不支持。
> - 笔记属于隐私，不要在群聊中主动展示笔记内容。

**笔记写入规则**：
- **新建 vs 追加**：用户说"新建/创建笔记"走 `import_doc`；说"追加到XX笔记"走 `append_doc`；模糊表述（"帮我记一下"）必须先问用户是新建还是追加
- **不支持本地图片**：写入前检查并移除 `file://` 等本地图片路径，告知用户
- **UTF-8 编码**：写入前确保内容是合法 UTF-8

---

## 秒哒平台 Edge Function 集成示例

### ⚠️ Edge Function 常见陷阱（必读）

#### 1. `req.json()` 只能调用一次

请求体是 ReadableStream，`req.json()` 消费后流就关闭了。**绝不能多次调用：**

```typescript
// ❌ 错误：第二次 req.json() 会挂起或抛异常
const { action } = await req.json();
const { kbName } = await req.json(); // 流已关闭，永远等不到数据

// ✅ 正确：一次解析，解构所有字段
const body = await req.json();
const { action, kbName, query, cursor } = body;
// 或直接在解构时取完
const { action, kbName, query, cursor } = await req.json();
```

#### 2. IMA API 参数校验严格

IMA OpenAPI 对参数范围和空值敏感：

| 参数 | 接口 | 限制 | 越界表现 |
|------|------|------|---------|
| `limit` | `search_knowledge_base` | 1-20 | 返回非 0 错误码 |
| `limit` | `get_knowledge_list` | 1-50 | 返回非 0 错误码 |
| `query` | `search_knowledge_base` | 可为空字符串 `""` | — |
| `query` | `search_knowledge` | **不可为空** | 参数错误 |

**解决方案：**
- `search_knowledge_base` 传 `limit` 不超过 20
- `get_knowledge_list` 传 `limit` 不超过 50
- `search_knowledge` 在前端层就校验 `query` 不能为空，空时不发起请求

#### 3. 请求体路由方式

推荐用单一 Edge Function + `action` 字段路由，不要拆多个 Function：

```typescript
// ✅ 正确：一个 Edge Function，通过 action 分发
Deno.serve(async (req) => {
  const { action, ...params } = await req.json();
  
  switch (action) {
    case 'search_kb':
      return handleSearchKB(params);
    case 'list_content':
      return handleListContent(params);
    // ...
  }
});

// ❌ 错误：拆成多个 Function 导致请求体重复解析和跨 Function 代码重复
```

### Edge Function：搜索知识库并返回内容

用户只需提供知识库名称，Edge Function 自动搜索 ID 再查询内容。

```typescript
// supabase/functions/ima-search/index.ts

Deno.serve(async (req) => {
  try {
    const { kbName, query, cursor } = await req.json();
    
    const headers = {
      'Content-Type': 'application/json',
      'ima-openapi-clientid': Deno.env.get('IMA_CLIENT_ID')!,
      'ima-openapi-apikey': Deno.env.get('IMA_API_KEY')!,
    };
    
    // 1. 先按名称搜索知识库获取 ID
    const kbRes = await fetch('https://ima.qq.com/openapi/wiki/v1/search_knowledge_base', {
      method: 'POST',
      headers,
      body: JSON.stringify({ query: kbName, cursor: '', limit: 5 }),
    });
    const kbData = await kbRes.json();
    
    if (!kbData.data?.info_list?.length) {
      return new Response(JSON.stringify({ error: `未找到知识库「${kbName}」` }), { status: 404 });
    }
    
    const kbId = kbData.data.info_list[0].kb_id;
    
    // 2. 用 ID 搜索内容
    const searchRes = await fetch('https://ima.qq.com/openapi/wiki/v1/search_knowledge', {
      method: 'POST',
      headers,
      body: JSON.stringify({ query, cursor, knowledge_base_id: kbId }),
    });
    
    const searchData = await searchRes.json();
    return new Response(JSON.stringify({
      kbName: kbData.data.info_list[0].kb_name,
      results: searchData.data,
    }), { headers: { 'Content-Type': 'application/json' } });
    
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
});
```

### Edge Function：上传文件到知识库

```typescript
// supabase/functions/ima-upload/index.ts

Deno.serve(async (req) => {
  try {
    const { kbName, fileName, fileSize, contentType, fileExt, fileBase64 } = await req.json();
    const fileBytes = Uint8Array.from(atob(fileBase64), c => c.charCodeAt(0));
    
    const clientId = Deno.env.get('IMA_CLIENT_ID')!;
    const apiKey = Deno.env.get('IMA_API_KEY')!;
    const headers = {
      'Content-Type': 'application/json',
      'ima-openapi-clientid': clientId,
      'ima-openapi-apikey': apiKey,
    };
    
    // 1. 按名称搜索知识库获取 ID
    const kbRes = await fetch('https://ima.qq.com/openapi/wiki/v1/search_knowledge_base', {
      method: 'POST',
      headers,
      body: JSON.stringify({ query: kbName, cursor: '', limit: 5 }),
    });
    const kbData = await kbRes.json();
    if (!kbData.data?.info_list?.length) {
      return new Response(JSON.stringify({ error: `未找到知识库「${kbName}」` }), { status: 404 });
    }
    const kbId = kbData.data.info_list[0].kb_id;
    
    // 2. 检查重名
    const checkRes = await fetch('https://ima.qq.com/openapi/wiki/v1/check_repeated_names', {
      method: 'POST', headers,
      body: JSON.stringify({
        params: [{ name: fileName, media_type: getMediaType(fileExt) }],
        knowledge_base_id: kbId,
      }),
    });
    const checkData = await checkRes.json();
    if (checkData.data?.results?.[0]?.is_repeated) {
      return new Response(JSON.stringify({ repeated: true, msg: '文件已存在' }));
    }
    
    // 3. 创建媒体获取 COS 凭证
    const mediaRes = await fetch('https://ima.qq.com/openapi/wiki/v1/create_media', {
      method: 'POST', headers,
      body: JSON.stringify({
        file_name: fileName, file_size: fileSize,
        content_type: contentType, knowledge_base_id: kbId,
        file_ext: fileExt,
      }),
    });
    const mediaData = await mediaRes.json();
    if (mediaData.code !== 0) throw new Error(mediaData.msg);
    const { media_id, cos_credential } = mediaData.data;
    
    // 4. 上传到 COS（必须使用 hex 签名，header 键必须小写标准化）
    const cosUrl = `https://${cos_credential.bucket_name}.cos.${cos_credential.region}.myqcloud.com/${cos_credential.cos_key}`;
    const cosHeaders = {
      'x-cos-security-token': cos_credential.token,
      'Content-Type': contentType,
    };
    const authorization = await signCOS(cos_credential, 'PUT', cosUrl, cosHeaders);
    const cosRes = await fetch(cosUrl, {
      method: 'PUT',
      headers: { ...cosHeaders, 'Authorization': authorization },
      body: fileBytes,
    });
    if (!cosRes.ok) throw new Error('COS upload failed');
    
    // 5. 添加知识
    const addRes = await fetch('https://ima.qq.com/openapi/wiki/v1/add_knowledge', {
      method: 'POST', headers,
      body: JSON.stringify({
        media_type: getMediaType(fileExt), media_id,
        title: fileName, knowledge_base_id: kbId,
        file_info: { cos_key: cos_credential.cos_key, file_size: fileSize, file_name: fileName },
      }),
    });
    const addData = await addRes.json();
    
    return new Response(JSON.stringify({ success: addData.code === 0 }), {
      headers: { 'Content-Type': 'application/json' },
    });
    
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500, headers: { 'Content-Type': 'application/json' },
    });
  }
});

function getMediaType(ext: string): number {
  const map: Record<string, number> = {
    pdf: 1, doc: 3, docx: 3, ppt: 4, pptx: 4,
    xls: 5, xlsx: 5, csv: 5, md: 7,
    png: 9, jpg: 9, jpeg: 9, webp: 9,
    txt: 13, xmind: 14, mp3: 15, m4a: 15, wav: 15, aac: 15,
  };
  return map[ext.toLowerCase()] || 1;
}

// COS 签名：必须使用 hex 编码 + header 小写标准化
// 与 cos-python-sdk-v5 保持一致，否则 COS 返回 403
function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function hmacSha1Hex(key: string, message: string): Promise<string> {
  const enc = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    'raw', enc.encode(key), { name: 'HMAC', hash: 'SHA-1' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', cryptoKey, enc.encode(message));
  return bytesToHex(new Uint8Array(sig));
}

async function sha1Hex(message: string): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(message));
  return bytesToHex(new Uint8Array(hash));
}

async function signCOS(
  credential: { secret_id: string; secret_key: string; start_time: string | number; expired_time: string | number },
  method: string, url: string, headers: Record<string, string>
): Promise<string> {
  const urlObj = new URL(url);
  const path = encodeURIComponent(urlObj.pathname).replace(/%2F/g, '/');
  const keyTime = `${credential.start_time};${credential.expired_time}`;

  // header 键必须小写标准化，否则签名不匹配
  const normalized: Record<string, string> = {};
  Object.keys(headers).forEach(k => { normalized[k.toLowerCase()] = headers[k] || ''; });
  const headerKeys = Object.keys(normalized).sort();
  const signedHeaders = headerKeys.map(k => `${k}=${encodeURIComponent(normalized[k].trim())}`).join('&');
  const signedHeaderList = headerKeys.join(';');

  const httpString = `${method.toLowerCase()}\n${path}\n\n${signedHeaders}\n`;
  const stringToSign = `sha1\n${keyTime}\n${await sha1Hex(httpString)}\n`;
  const signKey = await hmacSha1Hex(credential.secret_key, keyTime);
  const signature = await hmacSha1Hex(signKey, stringToSign);

  return `q-sign-algorithm=sha1&q-ak=${credential.secret_id}&q-sign-time=${keyTime}&q-key-time=${keyTime}&q-header-list=${signedHeaderList}&q-url-param-list=&q-signature=${signature}`;
}
```

---

## API 能力边界（已知限制）

IMA OpenAPI **不支持以下操作**，AI 生成应用时不能提供对应的 UI 或功能入口：

### 知识库不支持
- ❌ 删除文件/知识条目
- ❌ 修改/重命名文件标题
- ❌ 删除文件夹
- ❌ 移动文件到其他知识库

### 笔记不支持
- ❌ 更新/编辑已有笔记内容（没有 `update_doc`）
- ❌ 删除笔记
- ❌ 删除笔记本

### 变通方案

当用户要求"编辑笔记"时：

```typescript
// 笔记没有 update 接口，只能通过 append 追加修订内容
// Step 1: 读取当前内容
const content = await getNoteContent(noteId);
// Step 2: 追加修订说明 + 更新内容
await appendToNote(noteId, `\n---\n**修订于 ${new Date().toLocaleString()}**\n${revisedContent}`);
```

当用户要求"删除知识库条目"时：
- 告知用户当前 IMA API 不支持删除操作
- 引导用户在 ima 桌面端或 App 中删除

### 前端实现注意事项

AI 生成页面时，**不能为不支持的操作生成按钮、表单或路由**。例如：
- 笔记详情页不能有"编辑"或"删除"按钮
- 知识库内容列表不能有"删除"或"重命名"操作项

## Agent 执行流程规范

### 知识库操作流程

```
用户说"把XX文件上传到YY知识库"
    │
    ├─ Agent 调 search_knowledge_base("YY") 获取 KB ID
    ├─ Agent 调 check_repeated_names 检查重名
    ├─ 如有重复 → 问用户"保留两者还是取消？"
    ├─ Agent 调 create_media
    ├─ Agent 上传文件到 COS
    └─ Agent 调 add_knowledge
    │
    返回结果："已上传到「YY知识库」✓"
```

```
用户说"搜索知识库里关于XX的内容"
    │
    ├─ 用户没指定知识库 → Agent 调 search_knowledge_base("") 列出所有
    ├─ 用户选择 → Agent 用 kbId 调 search_knowledge
    └─ 展示结果（标题+摘要+高亮）
```

### 笔记操作流程

```
用户说"帮我记一下..."
    │
    ├─ 模糊表述 → Agent 先问"新建笔记还是追加到已有笔记？"
    ├─ 新建 → Agent 调 import_doc
    └─ 追加 → Agent 先搜索笔记获取 note_id，再调 append_doc
```

## 常见问题

| 问题 | 处理方式 |
|:---|:---|
| 用户说"把XX上传到知识库"但没指定知识库 | Agent 调 `search_knowledge_base("")` 列出所有，让用户选 |
| 用户说"搜索知识库"但没指定搜索哪个 | Agent 先列出全部知识库让用户确认 |
| 文件名已存在 | 问用户"保留两者（自动加时间戳后缀）还是取消？" |
| 用户没提供知识库名称 | 不要猜测或用默认值，用 `search_knowledge_base("")` 列出可选 |
| 笔记意图模糊（"帮我记一下"） | 先问新建还是追加，不要自行假设 |

---

## 前端集成核心约束（生成应用时必须遵守）

> ⚠️ **重要**：以下约束直接影响秒哒生成应用的用户体验。AI 在任何场景下生成前端代码时都必须遵守，不限制具体页面结构或组件选型。

### 必做

- **隐藏内部 ID**：用户界面绝不能出现 `kb_id`、`folder_id`、`cursor`、`media_id`、`note_id` 等内部标识。知识库通过名称选择，ID 在状态/上下文中传递，对用户透明。
- **自然语言标签**：输入框和按钮的文案用用户能理解的自然语言（"选择知识库" / "加载更多"），不用 API 参数名（`knowledge_base_id` / `cursor`）。
- **自动分页**：分页逻辑封装在服务层或 hooks 中，用户只需点击"加载更多"或滚动加载，`cursor` 对用户完全透明。

### 避免

- 不要让用户手动输入内部 ID
- 不要在 UI 中展示任何 API 层面的标识符
- 不要用接口或参数名作为 UI 文案

### 自检清单

生成前端代码前，AI 必须逐一检查：

- [ ] 所有输入框的 label 用的是自然语言还是 API 参数名？
- [ ] 有没有在 UI 中展示内部 ID（`kb_id`、`media_id`、`note_id` 等）？
- [ ] 分页是否对用户透明（用户只点"加载更多"，不填 cursor）？

## 注意事项

- **任何时候不要让用户填写 KB ID**：用户只需提供知识库名称，Agent 自动搜索获取 ID
- **搜索知识库用 `search_knowledge_base`**，搜索知识库内容用 `search_knowledge`，不要混用
- **知识库根目录 ID 等于 knowledge_base_id**：`import_urls` 要求 `folder_id` 必填时传 kbId
- **文件上传流程**：必须依次执行 check_repeated_names → create_media → COS → add_knowledge
- **COS 上传凭证有时效性**：create_media 返回后尽快上传
- **文件名保持原样**：add_knowledge 的 title 必须等于原始文件名（含扩展名）
- **笔记内容必须 UTF-8**：写入前确保编码正确
- **笔记内容不支持本地图片**：写入前过滤 file:// 路径并告知用户

## 常见错误

**知识库模块（wiki）：**

| 错误码 | 原因 | 处理建议 |
|:---:|:---|:---|
| 110001 | 参数非法 | 检查请求参数格式 |
| 110002 | 配置非法 | 检查服务配置 |
| 110010 | 下游网络错误 | 可重试 |
| 110011 | 下游逻辑错误 | 不可重试，详见 msg |
| 110012 | 接口无效 | 检查接口路径 |
| 110013 | 客户端取消 | 检查请求是否超时 |
| 110020 | 安全打击/内容违规 | 检查内容是否合规 |
| 110021 | 请求频控 | 降低请求频率 |
| 110030 | 无权限 | 确认 API Key 权限 |

**笔记模块（note）：**

| 错误码 | 原因 | 处理建议 |
|:---:|:---|:---|
| 210001 | 参数错误 | 检查请求参数 |
| 210004 | 用户空间不够 | 提示用户清理空间 |
| 210005 | 不是笔记作者 | 仅本人笔记可操作 |
| 210006 | 笔记已删除 | 笔记不存在 |
| 210009 | 单篇笔记超限 | 拆分为多次 append_doc |
| 210035 | 笔记本不存在 | 检查 folder_id |

**通用鉴权：**

| 错误码 | 原因 | 处理建议 |
|:---:|:---|:---|
| 20002 | API Key 超过限频 | 降低请求频率 |
| 20004 | API Key 鉴权失败 | 检查 Client ID 和 API Key |