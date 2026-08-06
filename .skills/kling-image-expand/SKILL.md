---
name: kling-image-expand
description: 使用可灵 AI 对图片进行扩图编辑，支持上下左右自由扩展画布，适用于图片尺寸调整、构图优化、海报适配等场景
license: MIT
---

## 能力概述

本 skill 基于可灵 AI 的图像扩展能力，对原始图片在上、下、左、右四个方向按比例扩充画布，并自动填充生成新的图像内容。

| 项目 | 说明 |
|------|------|
| 服务商 | 可灵 AI（Kling AI） |
| 认证模式 | `platform_managed`（密钥由平台注入，读取 `INTEGRATIONS_API_KEY`） |
| 工作流 | 异步任务：提交任务 → 轮询状态 → 获取结果图片 |
| 图片转存 | 任务完成后须将图片 URL 转存至 Supabase Storage（原始 URL 30 天后失效） |
| 支持平台 | Web、MiniProgram |

Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。


### API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 创建扩图任务 | POST | `https://app-dvtmyuucfs3l-api-Q9KWnzwVQMk9-gateway.appmiaoda.com/v1/images/editing/expand` |
| 查询单个任务 | GET  | `https://app-dvtmyuucfs3l-api-rLobR6vwZJJ9-gateway.appmiaoda.com/v1/images/editing/expand/{task_id}` |
| 查询任务列表 | GET  | `https://app-dvtmyuucfs3l-api-AalZkPVdZX8L-gateway.appmiaoda.com/v1/images/editing/expand` |

### 关键约束

- 原图格式：.jpg / .jpeg / .png，文件大小 ≤ 10 MB，宽高 ≥ 300 px，宽高比在 1:2.5 ~ 2.5:1 之间
- 四个方向的扩充倍数均在 [0, 2] 范围内，且扩充后总面积不超过原图的 3 倍
- Base64 传参时，**不要添加 `data:image/png;base64,` 等前缀**，直接传裸 Base64 字符串
- 生成图片 URL 30 天后失效，务必及时转存至 Supabase Storage

---

## 生成期用法（Agent 直接调用）

生成期（Agent 直接调用场景）使用 Python 脚本完成"提交任务 → 脚本内轮询 → 下载结果"全流程，不再使用内联 TypeScript 调用代码。

> **重要**：调用以下脚本时，Bash 工具超时必须设置为 `600000`（毫秒），因为脚本内部会轮询最长 550 秒（安全余量，避免撞到 Bash 工具 600s 超时）。

**提交并等待结果：**

```bash
python3 managed/kling-image-expand/scripts/generate_image_expand.py \
  --image /path/to/input.png \
  --up-ratio 0.15 \
  --down-ratio 0.15 \
  --left-ratio 0.65 \
  --right-ratio 0.65 \
  --prompt "蓝天白云，自然延伸" \
  --num 1 \
  --output-dir /path/to/output_images
```

也支持 `--image-url` 直接传图片 URL。

- 成功时 stdout 输出一行 JSON，并已将图片下载到 `--output-dir`：
  ```json
  {"status":"succeed","task_id":"...","images":[{"url":"https://...","file":"/path/to/output_images/image_0.png"}]}
  ```
- 若达到脚本内部安全时限（550 秒）仍未完成，输出（退出码 0，不是失败）：
  ```json
  {"status":"processing","task_id":"..."}
  ```
  此时应使用下方查询脚本继续轮询。
- 失败时 stderr 输出错误信息，退出码 1。

**必须串行调用，禁止并行发起：** `generate_image_expand.py` 与 `query_image_expand.py` 存在先后依赖，必须等 `generate_image_expand.py` 的 Bash 工具调用返回并拿到 `task_id` 后，才能发起 `query_image_expand.py` 的调用；不要在同一条命令里用 `&&`/`;`/换行拼接两者，也不要在第一步结果未返回时就假设其已完成并提前发起第二步。

**继续查询未完成的任务：**

```bash
python3 managed/kling-image-expand/scripts/query_image_expand.py \
  --task-id <task_id> \
  --output-dir /path/to/output_images
```

输出格式与上面一致。

脚本参数、字段含义详见 [references/kling-image-expand-api.md](references/kling-image-expand-api.md)。

**脚本使用约束（生成图片时严格遵守）：**
- **禁止新增脚本**：只能执行 `scripts/` 目录中已有的脚本（`generate_image_expand.py`、`query_image_expand.py`），不得为本次任务创建任何新的 Python/Shell/Node 脚本或临时封装。
- **禁止改名**：脚本文件名是固定的，不得重命名，也不得复制成其他文件名后再调用。
- **非必要不修改**：除非用户明确要求修复脚本 Bug，否则不得修改脚本源码；所有行为差异通过命令行参数控制。

---

## 使用示例

将一张竖版图片向左右两侧各扩展约 65%，生成 16:9 横版图：

```bash
# 原图 100×100，目标宽高比 16:9，扩充后总面积约 3 倍
# 向上/下各扩 0.15，向左/右各扩 0.65
python3 managed/kling-image-expand/scripts/generate_image_expand.py \
  --image /path/to/photo.png \
  --up-ratio 0.15 \
  --down-ratio 0.15 \
  --left-ratio 0.65 \
  --right-ratio 0.65 \
  --prompt "蓝天白云，自然延伸" \
  --num 1 \
  --output-dir /path/to/output_images
```

详细参数约束（原图格式、面积上限等）见 [references/kling-image-expand-api.md](references/kling-image-expand-api.md)。

---

## 生成后用法（应用内通过 Edge Function 调用）

详见 [references/kling-image-expand-api.md](references/kling-image-expand-api.md) 的"Edge Function 代码"和"前端调用代码"章节。

### 平台差异对比

| 项目 | Web | MiniProgram |
|------|-----|-------------|
| 调用方式 | `supabase.functions.invoke` 或原生 `fetch` | `supabase.functions.invoke` |
| 图片结果 | 转存后返回 `publicUrl` | 转存后返回 `publicUrl` |
| 异步轮询 | Edge Function 内部循环，前端单次调用 | Edge Function 内部循环，前端单次调用 |

Edge Function 将在内部完成"提交 → 轮询 → 转存"全流程，前端只需发起一次请求并等待最终图片 URL。
