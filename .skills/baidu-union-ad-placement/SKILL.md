---
name: baidu-union-ad-placement
description: 在 PC/WAP 网页中接入百度联盟广告投放（异步投放）。当用户需要为网站/H5 接入百度联盟广告位、生成投放代码与容器、处理广告关闭、无广告返回、有广告返回回调，或做网站流量变现、广告位接入时触发。基于用户自己的广告位 ID，生成符合官方规范的纯前端异步投放代码。
license: MIT
packageType: instruction-skill
instructionOnly: true
---

## 能力概述

本 skill 帮助在 **PC / WAP 网页**中接入**百度联盟广告投放**，采用官方推荐的**异步投放**方式。

- **类型**：用户配置类（user-config）。用户在 [union.baidu.com](https://union.baidu.com/) 后台创建广告位后，把**广告位 ID** 配置给本 skill 即可。
- **纯前端集成**：不调用任何后端 API，不需要部署 Edge Function，只向页面注入投放脚本与容器。
- **无平台密钥**：不使用 `INTEGRATIONS_API_KEY`。用户唯一需要提供的是广告位 ID（公开值，会出现在页面 HTML 中，非机密信息）。
- **支持平台**：`Web`（PC / WAP 浏览器，http/https 网页）。

核心流程：

| 步骤 | 说明 |
|------|------|
| 1. 引入脚本 | 整页**只引入一次**联盟脚本 `//cpro.baidustatic.com/cpro/ui/cm.js` |
| 2. 创建容器 | 每个广告位创建一个带指定 `class` 的容器 `div` |
| 3. 推送配置 | 向 `window.slotbydup` push 广告单元配置（`id` / `container` / `async`） |
| 4. 定义回调 | （可选）页面内**只定义一次** `closeAd` / `noAd` / `haveAd` 回调 |

---

## 用户配置

| 配置项 | 环境变量 | 必填 | 说明 |
|--------|----------|------|------|
| 广告位 ID | `BAIDU_UNION_SLOT_ID` | 是 | 从 union.baidu.com 后台获取，形如 `u6341556` |

> 广告位 ID 为**公开值**，会出现在页面 HTML 中，属于非机密信息。配置与获取步骤详见 `references/setup-guide.md`。
>
> 广告容器的 class 名**无需用户配置**：生成代码时由模型自动生成唯一 class（或直接写死一个唯一 class），只要保证容器 `<div>` 的 class 与 push 的 `container` 一致、且页面内唯一即可。

---

## 生成期用法（生成投放代码）

生成期从环境变量读取广告位 ID，将其写入异步投放代码基线：

```html
<!-- 1. 广告容器：每个广告位一个，class 值需与 container 一致 -->
<div class="_gpunkxjudct"></div>

<!-- 2. 投放代码：push 广告单元配置 -->
<script type="text/javascript">
  (window.slotbydup = window.slotbydup || []).push({
    id: "u6341556",            // 广告位 id（来自 BAIDU_UNION_SLOT_ID）
    container: "_gpunkxjudct", // 广告容器 class 值
    async: true                // 异步投放固定为 true
  });
</script>

<!-- 3. 联盟脚本：整页只需引入一次（多条广告也只引一次） -->
<script type="text/javascript"
        src="//cpro.baidustatic.com/cpro/ui/cm.js"
        async="async" defer="defer"></script>
```

读取环境变量示例：

```javascript
const slotId = process.env["BAIDU_UNION_SLOT_ID"];  // 如 "u6341556"
if (!slotId) {
  throw new Error("未配置 BAIDU_UNION_SLOT_ID，请先在 union.baidu.com 创建广告位并配置广告位 ID");
}
// 容器 class 无需配置：生成期直接写死或生成一个页面内唯一的 class
const container = "ad_slot_1"; // 或 "_" + Math.random().toString(36).slice(2)
```

---

## 前端集成（异步投放）

支持原生 HTML/JS、React、Vue 三种集成方式，脚本整页只引入一次，多广告位可多次 push。完整组件代码见 `references/async-placement.md`。

---

## 对外回调接口

对外回调与广告投放是**平行逻辑**，必须**独立 push**，且每个页面**只定义一次**：

| 回调 | 触发时机 | 限制 |
|------|----------|------|
| `closeAd` | 用户点击"广告关闭" | 无 |
| `noAd` | 无广告返回 | 无 |
| `haveAd` | 有广告返回 | **仅屏保代码位开放** |

完整定义方式、参数说明与注意事项见 `references/callbacks.md`。

---

## 环境与注意事项

- 运行环境需为 **http/https 协议 + 正常域名**；`localhost`、IP（如 `127.0.0.1`）、`file://` 下广告不绘制。
- `cm.js` 脚本整页**只引入一次**；`closeAd` / `noAd` / `haveAd` 每页也**只定义一次**。
- 无广告时除 `noAd` 回调外，可用平台"自定义链接""自动收起"作为兜底，避免页面空白。
- 广告白屏、公益广告、请求报错（400/404）等常见问题自查见 `references/environment-notes.md`。
