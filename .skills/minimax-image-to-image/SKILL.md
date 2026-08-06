---
name: minimax-image-to-image
description: 调用 MiniMax 图像生成 API，根据文本描述和可选的人物参考图生成图片；适用于图像风格转换、人物场景拓展、创意设计迭代、素材二次创作等场景
license: MIT
---

## 能力概述

基于 MiniMax `image-01` 和 `image-01-live` 模型的图像生成能力，支持纯文本生图和图生图（人物主体参考）两种模式。`image-01-live` 模型在 `image-01` 的基础上额外支持画风设置（漫画、元气、中世纪、水彩等风格），适合需要特定艺术风格的图像生成场景。

| 项目 | 详情 |
|------|------|
| Endpoint | `POST https://app-dvtmyuucfs3l-api-6LeBzWJjy3QY-gateway.appmiaoda.com/v1/image_generation` |
| 认证方式 | `platform_managed`，密钥由平台注入 |
| Content-Type | `application/json` |
| 返回格式 | 图片 URL 数组（有效期 24 小时），需转存至 Supabase Storage |
| 最大批量 | 单次最多生成 9 张图片 |
| 文本描述长度 | 最长 1500 字符 |

Auth Header 为 `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`（注意不是标准的 `Authorization`）。


**平台差异：**

| 平台 | Edge Function 特点 | 前端调用方式 |
|------|--------------------|--------------|
| Web | 转存媒体 URL 后返回永久链接 | `supabase.functions.invoke` |
| MiniProgram | 同 Web，接口一致 | `supabase.functions.invoke` |

> 完整参数表、响应结构、生成期代码及各平台 Edge Function 详见
> `references/image-generation-api.md`

---

## 生成期用法（Agent 直接调用）

生成期调用请使用内置脚本，脚本会从环境变量读取 INTEGRATIONS_API_KEY，不再现场生成请求/下载代码。

纯文本生图：

```bash
python3 <skill-path>/scripts/generate_image.py --prompt "A girl looking into the distance from a library window" --aspect-ratio 16:9 --output /path/to/output.png
```

图生图（人物主体参考，本地图片会在脚本内编码为 Base64 Data URL）：

```bash
python3 <skill-path>/scripts/generate_image.py --prompt "..." --reference-image /path/to/person.jpg --output /path/to/output.png
```

生成多张图片时改用 `--output-dir`（`--reference-url` 可传公网参考图 URL）：

```bash
python3 <skill-path>/scripts/generate_image.py --prompt "..." --n 3 --output-dir /path/to/images
```

脚本内部会调用上游接口获取图片 URL（有效期 24 小时）并立即下载到本地，成功时 stdout 输出一行 JSON：

```json
{"files":["/path/to/output.png"],"urls":["https://..."],"metadata":{"success_count":1,"failed_count":0},"base_resp":{"status_code":0,"status_msg":"success"}}
```

**脚本使用约束（生成图片时严格遵守）：**
- **禁止新增脚本**：只能执行 `scripts/` 目录中已有的脚本（`generate_image.py`），不得为本次任务创建任何新的 Python/Shell/Node 脚本或临时封装。
- **禁止改名**：脚本文件名是固定的，不得重命名，也不得复制成其他文件名后再调用。
- **非必要不修改**：除非用户明确要求修复脚本 Bug，否则不得修改脚本源码；所有行为差异通过命令行参数控制。

---

## 生成后用法（应用内通过 Edge Function 调用）

在应用中部署 Edge Function，由 Edge Function 负责持有密钥、调用上游、将返回的临时图片 URL 转存至 Supabase Storage，最终向前端返回永久可访问的公开链接。

- Web 与 MiniProgram 共用同一个 Edge Function，前端均使用 `supabase.functions.invoke` 调用。
- 图片 URL 有效期 24 小时，**必须经过 Supabase Storage 转存**，否则链接在生成后很快失效。

详见 `references/image-generation-api.md` → **Edge Function 代码** 和 **前端调用代码** 小节。
