---
name: long-text-tts
description: 将超长文本（最多10万字符）异步转换为语音音频，支持多音库/语速/语调设置，适用于有声内容、新闻播报等场景
license: MIT
---

## 能力概述

百度 AI 长文本语音合成服务，通过两步异步接口将超长文本转换为音频：

1. **创建任务**（`POST /rpc/2.0/tts/v1/create`）：提交文本数组，返回 `task_id`
2. **查询任务**（`POST /rpc/2.0/tts/v1/query`）：轮询任务状态，成功后返回 `speech_url` 音频链接

| 能力维度 | 说明 |
|----------|------|
| 文本上限 | 总字数不超过 10 万字符 |
| 音频格式 | mp3-16k（默认）、mp3-48k、wav |
| 音库选项 | 度小美(0)、度小宇(1)、度逍遥(3)、度丫丫(4) |
| 语速/音调/音量 | 均为 0–15，默认均为 5 |
| 任务状态 | Running / Success / Failure / Created |
| 结果有效期 | 音频下载链接储存 72 小时 |
| 平台支持 | Web、MiniProgram |

**平台差异关键说明：**

| 差异点 | Web | MiniProgram |
|--------|-----|-------------|
| 音频播放方式 | `<audio>` 标签或 `Audio` 对象，直接使用 Supabase Storage 公开 URL | Taro `InnerAudioContext`，使用 https 链接（须将 http 升级为 https） |
| 轮询计数器实现 | `useRef` 防止重复轮询链 | 同 Web，必须用 `useRef` 而非 `useState` |
| 缓存策略 | 优先读 Supabase DB 缓存的 `speech_url`，避免重复调用 | 同 Web |

---

## 生成期用法（Agent 直接调用）

完整异步工作流（提交任务 → 轮询直到成功/失败）已固化为脚本，模型无需现场生成调用代码，只需拼接命令执行：

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认 120 秒会导致请求中断。

**提交并等待结果：**

```bash
python3 <skill-path>/scripts/generate_tts.py \
  --text "今年上半年我国工业经济面临的内外部环境还是比较严峻复杂的" \
  --format mp3-16k --voice 3 --speed 5
```

成功时 stdout 输出一行 JSON：
```json
{"status": "succeed", "task_id": "...", "speech_url": "https://...", "expires": "72 hours"}
```

若任务在脚本安全时限内仍未完成（长文本合成可能超过 600 秒），脚本会正常退出（非报错）并输出：
```json
{"status": "processing", "task_id": "<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_tts.py` 与 `query_tts.py` 存在先后依赖，必须等 `generate_tts.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_tts.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时**不要重新提交任务**（会重复计费），改用只查询、不提交的脚本继续等待：

```bash
python3 <skill-path>/scripts/query_tts.py --task-id <task_id>
```

`query_tts.py` 输出格式与 `generate_tts.py` 成功/处理中的输出完全一致，可反复调用直到拿到 `speech_url`。

参数说明见 `references/tts-create-api.md`（提交接口）和 `references/tts-query-api.md`（查询接口）的参数表；两个脚本内部已处理 QPS 超限（`error_code: 18`）退避重试逻辑，模型无需关心。

---

## 生成后用法（应用内通过 Edge Function 调用）

需要两个 Edge Function：`tts-create`（提交任务）和 `tts-query`（查询结果）。
- `tts-create` 的完整代码及前端调用见 `references/tts-create-api.md`
- `tts-query` 的完整代码及前端调用（含轮询、缓存、错误处理）见 `references/tts-query-api.md`

**前端整体架构（Web & MiniProgram 通用）：**

1. 调用 `tts-create` Edge Function 提交任务，获取 `task_id`
2. 将 `task_id` 存入 Supabase DB（状态 `Running`）
3. 使用 `useRef` 计数器轮询 `tts-query`，避免双重轮询链
4. 任务成功后，Edge Function 将 `speech_url` 转存至 Supabase Storage，返回永久 `publicUrl`
5. 将 `publicUrl` 更新至 DB（状态 `Success`），前端展示播放控件

> 下次加载时优先从 DB 读取 `speech_url`；如已有完成记录，直接使用缓存 URL，跳过轮询。

---

## 注意事项

- **密钥安全**：`INTEGRATIONS_API_KEY` 仅在 Edge Function 服务端使用，严禁暴露到前端
- **计费**：每次调用 `tts-create` 计费；`tts-query` 不计费
- **错误处理**：务必处理 429（配额超限）和 402（余额不足）；Baidu TTS `error_code: 18` 表示 QPS 超限，需退避重试
- **音频链接有效期**：`speech_url` 仅保留 72 小时，应在 Edge Function 侧及时转存至 Supabase Storage
- **MiniProgram 特别说明**：原始 `speech_url` 使用 http，微信小程序会阻断非 https 资源，需升级协议或使用 Supabase Storage 的 https URL
