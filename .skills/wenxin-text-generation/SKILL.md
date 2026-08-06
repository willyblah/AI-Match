---
name: wenxin-text-generation
description: 调用百度文心大模型（ERNIE 4.5 Turbo）进行流式文本生成；适用于内容创作、摘要提炼、翻译、润色等 AI 文本处理场景。
license: MIT
---

## 能力概述

使用百度文心大模型（ERNIE 4.5 Turbo）进行对话式文本生成，支持内容生成、语言润色、摘要提炼、信息提取、翻译等场景。

| 项目 | 值 |
|------|----|
| Endpoint | `POST https://app-dvtmyuucfs3l-api-zYkZz8qovQ1L-gateway.appmiaoda.com/v2/chat/completions` |
| 响应模式 | SSE 流式（Server-Sent Events） |
| 认证模式 | `platform_managed`（密钥由平台注入） |
| 上下文限制 | 32k token 总长度，27k token 单次输入 |
| 支持平台 | Web、MiniProgram、App、Task |

Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。


**多平台关键差异：**

| 平台 | 流式处理方式 | 核心依赖 |
|------|-------------|---------|
| Web | `ky` + `eventsource-parser` SSE Hook | `ky@^1.2.3`, `eventsource-parser@^3.0.3` |
| MiniProgram | `miaoda-taro-utils` 的 `sendChatStream` | `miaoda-taro-utils@^0.0.4` |
| App | `expo/fetch` + `eventsource-parser` 手动解析 SSE 流 | `expo/fetch`（内置）, `eventsource-parser@^3.0.3`, `react-native-marked` |

**响应数据格式（流式每帧）：**

```json
{
  "id": "as-9ki4hm6kkp",
  "choices": [
    {
      "index": 0,
      "delta": {
        "role": "assistant",
        "content": "您好！"
      },
      "finish_reason": null,
      "flag": 0
    }
  ]
}
```

内容提取：`choices[0].delta.content`

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场处理 SSE 协议。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断流式聚合。

```bash
python3 <skill-path>/scripts/call_chat_completion.py --prompt "请用 200 字总结大模型在教育场景的应用"
```

支持传入完整消息数组：

```bash
python3 <skill-path>/scripts/call_chat_completion.py --messages '[{"role":"user","content":"把下面这段话润色得更专业：..."}]'
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","content":"...","finish_reason":"stop"}
```

完整参数说明和返回字段见 [references/chat-completions-api.md](references/chat-completions-api.md)。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内通过 Supabase Edge Function 代理调用，Edge Function 负责持有 `INTEGRATIONS_API_KEY` 并将上游 SSE 流透传给前端。

**平台差异说明：**

| 平台 | Edge Function | 前端调用方式 |
|------|--------------|-------------|
| Web | 同一个 Edge Function（SSE proxy） | `ky` + `eventsource-parser` SSE Hook |
| MiniProgram | 同一个 Edge Function（SSE proxy） | `miaoda-taro-utils` 的 `sendChatStream`，`appId` 填空字符串 |
| App | 同一个 Edge Function（SSE proxy） | `expo/fetch` + `eventsource-parser` 手动解析 SSE，`react-native-marked` 渲染 |

详细 Edge Function 代码及各平台前端调用代码见 [references/chat-completions-api.md](references/chat-completions-api.md)。
