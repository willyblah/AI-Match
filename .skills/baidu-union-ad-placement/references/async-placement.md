# 异步投放集成详解

百度联盟推荐 PC / WAP 场景使用**异步投放**：整页只引入一次联盟脚本，投放代码放在 `<body>` 中需要展示广告的位置即可。异步投放对广告位置、加载时机、页面性能更友好。

## 一、投放代码基线

异步投放由三部分组成：

```html
<!-- 1. 广告容器：优先创建，class 值需与下方 container 一致 -->
<div class="_gpunkxjudct"></div>

<!-- 2. 投放代码：创建广告单元，传入 3 个属性 -->
<script type="text/javascript">
  (window.slotbydup = window.slotbydup || []).push({
    id: "u6341556",            // 广告位 id（来自 BAIDU_UNION_SLOT_ID）
    container: "_gpunkxjudct", // 广告容器 class 值
    async: true                // 异步投放默认为 true
  });
</script>

<!-- 3. 广告脚本：整页只需引入一次（多条广告下方脚本也只引入一次） -->
<script type="text/javascript"
        src="//cpro.baidustatic.com/cpro/ui/cm.js"
        async="async" defer="defer"></script>
```

代码解析：
- 页面优先创建广告容器，包含 `class` 属性。
- 创建广告单元，向 `window.slotbydup` push 一个对象，含 `id`（广告位 id）、`container`（容器 class 值）、`async`（异步固定 true）。
- 引入广告脚本文件 `cm.js`。

## 二、原生 HTML / JS 集成

```html
<!DOCTYPE html>
<html>
<head>
  <!-- cm.js 也可放在 head，整页只引一次 -->
</head>
<body>
  <!-- 广告位 -->
  <div class="ad_slot_home"></div>
  <script type="text/javascript">
    (window.slotbydup = window.slotbydup || []).push({
      id: "u6341556",
      container: "ad_slot_home",
      async: true
    });
  </script>

  <!-- 整页只引入一次 -->
  <script type="text/javascript"
          src="//cpro.baidustatic.com/cpro/ui/cm.js"
          async="async" defer="defer"></script>
</body>
</html>
```

## 三、React 投放组件

脚本只引入一次（放在应用入口或用单例守卫），组件挂载时 push 配置：

```tsx
import { useEffect, useRef } from "react";

// 全局只加载一次 cm.js
let scriptLoaded = false;
function ensureUnionScript() {
  if (scriptLoaded || typeof document === "undefined") return;
  scriptLoaded = true;
  const s = document.createElement("script");
  s.src = "//cpro.baidustatic.com/cpro/ui/cm.js";
  s.async = true;
  s.defer = true;
  document.body.appendChild(s);
}

interface UnionAdProps {
  slotId: string;   // 来自 BAIDU_UNION_SLOT_ID
  container: string; // 唯一 class
}

export function UnionAd({ slotId, container }: UnionAdProps) {
  const pushed = useRef(false);
  useEffect(() => {
    if (pushed.current) return;
    pushed.current = true;
    (window as any).slotbydup = (window as any).slotbydup || [];
    (window as any).slotbydup.push({ id: slotId, container, async: true });
    ensureUnionScript();
  }, [slotId, container]);

  return <div className={container} />;
}

// 使用：
// <UnionAd slotId={import.meta.env.VITE_BAIDU_UNION_SLOT_ID} container="ad_slot_home" />
```

## 四、Vue 投放组件

```vue
<!-- UnionAd.vue -->
<template>
  <div :class="container"></div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

const props = defineProps<{ slotId: string; container: string }>();

let scriptLoaded = (window as any).__unionScriptLoaded ?? false;
function ensureUnionScript() {
  if (scriptLoaded) return;
  (window as any).__unionScriptLoaded = true;
  scriptLoaded = true;
  const s = document.createElement("script");
  s.src = "//cpro.baidustatic.com/cpro/ui/cm.js";
  s.async = true;
  s.defer = true;
  document.body.appendChild(s);
}

onMounted(() => {
  (window as any).slotbydup = (window as any).slotbydup || [];
  (window as any).slotbydup.push({ id: props.slotId, container: props.container, async: true });
  ensureUnionScript();
});
</script>
```

## 五、多广告位处理

- 每个广告位对应一个**独立容器 div** 和一次 **push**，容器 class 值必须唯一且与 push 的 `container` 一致。
- 无论页面有多少广告位，`cm.js` 脚本**整页只引入一次**（重复引入可能导致绘制异常）。
- 示例：

```html
<div class="ad_slot_home"></div>
<script>
  (window.slotbydup = window.slotbydup || []).push({ id: "u6341556", container: "ad_slot_home", async: true });
</script>

<div class="ad_slot_article"></div>
<script>
  (window.slotbydup = window.slotbydup || []).push({ id: "u6341557", container: "ad_slot_article", async: true });
</script>

<!-- 脚本只引一次 -->
<script src="//cpro.baidustatic.com/cpro/ui/cm.js" async defer></script>
```
