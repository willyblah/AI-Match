---
name: kling-omni-image-generation
description: 基于可灵 Kling Omni 模型文生图或参考图生图，支持多种分辨率和画面比例，生成结果需轮询获取；适用于创意设计、宣传海报制作、日常作图等场景
license: MIT
---

## 能力概述

该 Skill 调用可灵 Omni 图像生成接口，支持 kling-image-o1 和 kling-v3-omni 两种模型，
通过文本提示词、参考图片或主体库 ID 生成 1K/2K 高清图像，支持单图（single）和组图（series）两种结果模式。

**工作流：异步任务 — 提交 → 轮询 → 获取结果**

| 步骤 | API | Endpoint |
|------|-----|----------|
| 1. 创建图像生成任务 | 创建图像生成任务 | POST `https://app-dvtmyuucfs3l-api-DLEO4zbkvoea-gateway.appmiaoda.com/v1/images/omni-image` |
| 2. 查询图像生成任务 | 查询单个图像生成任务 | GET `https://app-dvtmyuucfs3l-api-79jK6nw4zxDL-gateway.appmiaoda.com/v1/images/omni-image/{id}` |
| 3. 创建图像生成任务（图像编辑入口） | 创建图像生成任务（图像编辑） | POST `https://app-dvtmyuucfs3l-api-eLMlPzV7qWJ9-gateway.appmiaoda.com/v1/images/omni-image` |

**核心能力：**
- 支持模型：kling-image-o1（默认）、kling-v3-omni
- 分辨率：1k（默认）、2k
- 生成类型：single（单图，n 张，1~9）/ series（组图，series_amount 张，2~9）
- 画面比例：16:9、9:16、1:1、4:3、3:4、3:2、2:3、21:9、auto（默认 9:16）
- 可附加参考图（image_list，支持 Base64 或 URL）和主体库引用（element_list）
- 返回图像 URL（有效期 30 天，需及时转存）

**重要约束：**
- `result_type = single` 时：**不得传 `series_amount`**
- `result_type = series` 时：**必须传 `series_amount`（范围 [2, 9]）**
- `image_list` 格式必须为对象数组：`[{"image": "base64 or URL"}]`，禁止直接传字符串数组
- Base64 编码不得含 `data:image/jpeg;base64,` 等前缀

**多平台差异：**

| 项目 | Web | MiniProgram |
|------|-----|-------------|
| Edge Function 图片转存 | Appendix A（Supabase Storage 转存） | 同 Web |
| 前端调用方式 | `supabase.functions.invoke` | `supabase.functions.invoke` |
| 图片展示 | `<img src={publicUrl} />` | `<Image src={publicUrl} />` |

**计费：** 按调用次数计费，具体以平台计费页面为准。

---

## 生成期用法（Agent 直接调用）

生成期（Agent 直接调用）已改为脚本调用方式，模型只需拼接命令并执行，不再现场生成提交/轮询代码。

**必须将 Bash 工具的超时时间设置为 600000ms（600 秒）**，否则默认超时会打断生成任务的轮询流程。

单图模式：

```bash
python3 <skill-path>/scripts/generate_omni_image.py --prompt "一只在雪地里奔跑的金毛犬，阳光照射，摄影风格" --resolution 2k --aspect-ratio 3:2 -n 1 --output-dir /path/to/dir
```

组图模式：

```bash
python3 <skill-path>/scripts/generate_omni_image.py --prompt "..." --result-type series --series-amount 4 --output-dir /path/to/dir
```

带参考图：

```bash
python3 <skill-path>/scripts/generate_omni_image.py --prompt "将所有图片中的人物融合到<<<image_1>>>图中" --image /path/to/target.png --image /path/to/person1.jpg --output-dir /path/to/dir
```

成功时 stdout 输出一行 JSON：

```json
{"status":"succeed","task_id":"...","images":[{"url":"https://...","file":"/path/to/dir/xxx_0.jpg"}]}
```

如果脚本在安全时限内还没完成，会正常退出并输出：

```json
{"status":"processing","task_id":"<task_id>"}
```

**必须串行调用，禁止并行发起：** `generate_omni_image.py` 与 `query_omni_image.py` 存在先后依赖，必须等 `generate_omni_image.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_omni_image.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

此时不要重新提交任务，改用只查询脚本继续等待：

```bash
python3 <skill-path>/scripts/query_omni_image.py --task-id <task_id> --output-dir /path/to/dir
```

`query_omni_image.py` 不会重新提交任务，适合在任务已进入队列但生成未完成时继续查询。脚本内部已处理 `result_type=single/series` 的字段依赖及下载逻辑；返回的图片 URL 30 天后失效，如需长期保留请及时使用 `--output-dir` 下载。

**单条命令限制：每次 Bash 工具执行的 `command` 中只能包含 1 个 `generate_omni_image.py` 调用。** 如果用户需要多批次/多组不同 prompt 的图片，必须拆成多次 Bash 工具调用，每次单独执行一条 `generate_omni_image.py ... --output-dir <不同目录>` 命令；禁止在同一条命令里用 `&&`、`;` 或换行串联多个 `generate_omni_image.py`，避免单次执行耗时过长导致 Bash 工具超时。

**脚本使用约束（生成图片时严格遵守）：**
- **禁止新增脚本**：只能执行 `scripts/` 目录中已有的脚本（`generate_omni_image.py`、`query_omni_image.py`），不得为本次任务创建任何新的 Python/Shell/Node 脚本或临时封装。
- **禁止改名**：脚本文件名是固定的，不得重命名，也不得复制成其他文件名后再调用。
- **非必要不修改**：除非用户明确要求修复脚本 Bug，否则不得修改脚本源码；所有行为差异通过命令行参数控制。

---

## 生成后用法（应用内通过 Edge Function 调用）

应用内分两个 Edge Function：

1. **`kling-omni-image-submit`** — 接收前端请求，调用创建任务接口，返回 `task_id`
2. **`kling-omni-image-query`** — 接收 `task_id`，查询任务状态和结果，成功时将图片 URL 转存至
   Supabase Storage 并返回 `publicUrl` 列表

前端轮询逻辑在应用层实现（提交后每 7 秒轮询一次，超时 10 分钟）。

**Web 和 MiniProgram 平台共用相同的 Edge Function，前端均通过 `supabase.functions.invoke` 调用。**

详见 `references/omni-image-api.md` 中的完整 Edge Function 和前端代码。
