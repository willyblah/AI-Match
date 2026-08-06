---
name: kling-video-generation
description: 使用可灵 Omni 模型创建视频生成任务，支持文生视频、图生视频、视频编辑、多镜头等多种模式；轮询查询任务状态直到视频生成完成。
license: MIT
---

## 能力概述

基于可灵 Omni（`kling-video-o1` / `kling-v3-omni`）模型的视频生成能力，支持：

- **文生视频**：纯文本提示词生成视频
- **图生视频**：以参考图片为首帧/尾帧或主体参考生成视频
- **视频编辑（指令转换）**：对已有视频进行内容增删改、切换视角等编辑操作
- **视频参考**：参考视频内容生成下一/上一个镜头，或参考运镜方式生成新视频
- **主体参考**：基于主体库中的图片或视频主体生成视频
- **多镜头视频**：通过分镜提示词生成多个镜头连续的视频

| 属性 | 值 |
|------|----|
| 服务商 | KlingAI（快手可灵） |
| 模型 | `kling-video-o1`（默认）、`kling-v3-omni` |
| 响应方式 | 异步轮询（提交任务 → 轮询状态 → 获取结果） |
| 视频时长 | 3–15 秒（视频编辑时跟随输入视频时长） |
| 视频宽高比 | 16:9、9:16、1:1 |
| 生成模式 | `std`（标准）、`pro`（高品质，默认） |
| 视频返回 | 视频 URL（含水印版和无水印版），需转存至 Supabase Storage |
| 计费 | 创建任务接口按调用次数计费 |

**端点：**
- 创建任务：`POST https://app-dvtmyuucfs3l-api-oLpZb03wbNBa-gateway.appmiaoda.com/v1/videos/omni-video`
- 查询任务：`GET https://app-dvtmyuucfs3l-api-o9wN0pyVE2ea-gateway.appmiaoda.com/v1/videos/omni-video/{task_id}`

---

## 生成期用法（Agent 直接调用）

生成期（Agent 直接调用）已改为脚本调用方式，模型只需拼接命令并执行，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

文生视频：

```bash
python3 <skill-path>/scripts/generate_omni_video.py --prompt "一只橘猫在草地上慵懒地打滚" --mode pro --aspect-ratio 16:9 --duration 5 --output /path/to/output.mp4
```

图生视频（首帧/尾帧参考）：

```bash
python3 <skill-path>/scripts/generate_omni_video.py --prompt "让<<<image_1>>>中的人物向镜头挥手" --image /path/to/first.png --duration 5 --output /path/to/output.mp4
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4"}
```

如果脚本在安全时限内还没完成，会正常退出并输出：

```json
{"status":"processing","task_id":"<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_omni_video.py` 与 `query_omni_video.py` 存在先后依赖，必须等 `generate_omni_video.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_omni_video.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时不要重新提交任务，改用只查询脚本继续等待：

```bash
python3 <skill-path>/scripts/query_omni_video.py --task-id <task_id> --output /path/to/output.mp4
```

`query_omni_video.py` 不会重新提交任务，适合在任务已进入队列但生成未完成时继续查询。视频编辑、主体参考、多镜头等更复杂模式的参数详见 `references/omni-video-create-api.md`。返回的视频 URL 30 天后失效，如需长期保留请及时使用 `--output` 下载。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内需要两个 Edge Function：

| Edge Function | 文件 | 说明 |
|---------------|------|------|
| `kling-video-create` | `references/omni-video-create-api.md` | 提交视频生成任务，返回 `task_id` |
| `kling-video-query` | `references/omni-video-query-api.md` | 查询任务状态；任务成功时将视频转存至 Supabase Storage 并返回持久化 URL |

前端实现**提交 + 轮询**两步 UI：
1. 点击"生成"按钮 → 调用 `kling-video-create` Edge Function，获取 `task_id`
2. 前端定时轮询（每 7 秒）`kling-video-query` Edge Function，直到返回 `status: "succeed"` 并展示视频

详见 `references/omni-video-create-api.md` 和 `references/omni-video-query-api.md`。
