---
name: performance-optimization-cn
description: 优化应用性能。当存在性能需求、怀疑性能退化、Core Web Vitals 或加载时间需要改进时触发。使用前提：必须先测量再优化，无测量数据的优化是猜测。适用于前端加载优化、交互响应优化、后端查询优化、Supabase Edge Function 性能、视频生成轮询性能、大数据量处理等场景。
license: MIT
---

# 性能优化

## 概述

先测量，再优化。没有测量数据的性能优化只是猜测——猜测会导致过早优化，增加复杂度却不改善真正重要的指标。先分析，找到真实瓶颈，修复，再次测量。只优化测量数据证明有问题的地方。

## 适用场景

- 规格中存在性能需求（加载时间预算、响应时间 SLA）
- 用户或监控反映响应慢
- Core Web Vitals 分数低于阈值
- 怀疑某次变更引入了性能退化
- 构建处理大数据量或高流量的功能
- Supabase Edge Function 响应超时
- 视频生成/AI 任务轮询导致前端卡顿

**不适用场景：** 没有性能问题的证据时，不要优化。过早优化增加的复杂度代价高于收益。

## Core Web Vitals 目标

| 指标 | 良好 | 需改进 | 较差 |
|------|------|--------|------|
| **LCP**（最大内容绘制） | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| **INP**（交互到下一帧） | ≤ 200ms | ≤ 500ms | > 500ms |
| **CLS**（累积布局偏移） | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## 优化工作流

```
1. 测量 → 用真实数据建立基线
2. 定位 → 找到真实瓶颈（不是假设）
3. 修复 → 针对具体瓶颈
4. 验证 → 再次测量，确认改善
5. 守护 → 添加监控或测试防止退化
```

### 第一步：测量

两种互补方式——都要用：

- **合成测试（Lighthouse、DevTools Performance）：** 受控环境，可复现。适合 CI 回归检测和隔离问题。
- **真实用户监控（web-vitals 库、CrUX）：** 真实用户数据。验证修复是否真的改善了用户体验时必须用。

**前端：**

```typescript
// 合成测试：Chrome DevTools → Performance → 录制，或 Lighthouse CI

// 真实用户监控：代码中集成 web-vitals
import { onLCP, onINP, onCLS } from 'web-vitals';
onLCP(console.log);
onINP(console.log);
onCLS(console.log);
```

**后端（含 Supabase Edge Function）：**

```typescript
// 简单计时
console.time('db-query');
const result = await db.query(...);
console.timeEnd('db-query');

// Edge Function 中计时
const t0 = Date.now();
const data = await fetch(upstreamUrl);
console.log(`upstream took ${Date.now() - t0}ms`);
```

### 从哪里开始测量

```
什么慢？
├── 首屏加载
│   ├── bundle 过大？ --> 测量 bundle 大小，检查代码分割
│   ├── 服务端响应慢？ --> DevTools Network waterfall 看 TTFB
│   │   ├── DNS 解析长？ --> 添加 dns-prefetch / preconnect
│   │   ├── TCP/TLS 长？ --> 开启 HTTP/2，检查边缘部署
│   │   └── 等待服务端长？ --> 分析后端，检查查询和缓存
│   └── 阻塞渲染资源？ --> 检查 CSS/JS 阻塞
├── 交互卡顿
│   ├── 点击后 UI 冻结？ --> 分析主线程，找长任务（>50ms）
│   ├── 表单输入延迟？ --> 检查重渲染、受控组件开销
│   └── 动画抖动？ --> 检查布局抖动、强制回流
├── 页面跳转后
│   ├── 数据加载慢？ --> 测量 API 响应时间，检查瀑布流
│   └── 客户端渲染慢？ --> 分析组件渲染时间，检查 N+1 请求
├── 后端 / API
│   ├── 单个接口慢？ --> 分析数据库查询，检查索引
│   ├── 所有接口慢？ --> 检查连接池、内存、CPU
│   └── 偶发慢？ --> 检查锁竞争、GC 停顿、外部依赖
└── 秒哒平台专项
    ├── Edge Function 超时？ --> 检查是否同步下载大文件（应使用签名 URL 直接播放）
    ├── 视频生成轮询卡顿？ --> 检查轮询频率和 React 闭包捕获旧值问题
    └── Supabase 查询慢？ --> 检查 N+1 查询，添加必要索引
```

### 第二步：定位瓶颈

**前端：**

| 症状 | 可能原因 | 排查方式 |
|------|---------|---------|
| LCP 慢 | 大图片、阻塞渲染资源、服务端慢 | 检查 Network waterfall、图片大小 |
| CLS 高 | 图片无尺寸、晚加载内容、字体偏移 | 检查布局偏移归因 |
| INP 差 | 主线程 JS 过重、大量 DOM 更新 | Performance trace 中的长任务 |
| 首屏加载慢 | bundle 过大、网络请求过多 | 检查 bundle 大小、代码分割 |

**后端（含 Supabase）：**

| 症状 | 可能原因 | 排查方式 |
|------|---------|---------|
| API 响应慢 | N+1 查询、缺少索引、查询未优化 | Supabase Dashboard 查询日志 |
| 内存增长 | 引用泄漏、无界缓存、大载荷 | 堆快照分析 |
| CPU 突增 | 同步重计算、正则回溯 | CPU 性能分析 |
| 高延迟 | 缺少缓存、重复计算、网络跳数 | 全链路追踪 |
| Edge Function 超时 | 同步下载大文件、上游 API 慢 | 添加分段计时日志 |

### 第三步：修复常见反模式

#### N+1 查询（后端）

```typescript
// 错误：N+1——每个任务单独查一次 owner
const tasks = await db.tasks.findMany();
for (const task of tasks) {
  task.owner = await db.users.findUnique({ where: { id: task.ownerId } });
}

// 正确：单次查询 join/include
const tasks = await db.tasks.findMany({ include: { owner: true } });
```

#### 无限制数据拉取

```typescript
// 错误：拉取全量数据
const allTasks = await db.tasks.findMany();

// 正确：分页限制
const tasks = await db.tasks.findMany({
  take: 20,
  skip: (page - 1) * 20,
  orderBy: { createdAt: 'desc' },
});
```

#### 图片未优化（前端）

```html
<!-- 错误：无尺寸、无懒加载、无响应式 -->
<img src="/hero.jpg" />

<!-- 正确：尺寸防 CLS，懒加载，响应式 srcset -->
<img
  src="/hero.jpg"
  width="800" height="400"
  loading="lazy" decoding="async"
  alt="首屏图片描述"
  srcset="/hero-400.jpg 400w, /hero-800.jpg 800w"
  sizes="(max-width: 600px) 400px, 800px"
/>
<picture>
  <source srcset="/hero.avif" type="image/avif" />
  <source srcset="/hero.webp" type="image/webp" />
  <img src="/hero.jpg" alt="首屏图片描述" width="800" height="400" />
</picture>
```

#### 不必要的重渲染（React）

```tsx
// 错误：每次渲染都创建新对象，导致子组件重渲染
function TaskList() {
  return <TaskFilters options={{ sortBy: 'date', order: 'desc' }} />;
}

// 正确：稳定引用
const DEFAULT_OPTIONS = { sortBy: 'date', order: 'desc' } as const;
function TaskList() {
  return <TaskFilters options={DEFAULT_OPTIONS} />;
}

const TaskItem = React.memo(function TaskItem({ task }: Props) {
  return <div>{/* 复杂渲染 */}</div>;
});

function TaskStats({ tasks }: Props) {
  const stats = useMemo(() => calculateStats(tasks), [tasks]);
  return <div>{stats.completed} / {stats.total}</div>;
}
```

#### bundle 过大

```typescript
// 正确：路由级代码分割 + Suspense
const SettingsPage = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Suspense>
  );
}
```

#### 秒哒平台专项：Edge Function 下载大文件

```typescript
// 错误：Edge Function 同步下载几十MB视频，导致超时或内存溢出
const videoBuffer = await fetch(videoUrl).then(r => r.arrayBuffer());
return new Response(videoBuffer);

// 正确：返回上游签名 URL，让客户端直接播放
return new Response(JSON.stringify({ playUrl: signedUrl }), {
  headers: { 'Content-Type': 'application/json' },
});
```

#### 秒哒平台专项：视频生成轮询闭包问题

```typescript
// 错误：闭包捕获旧 taskId
const [taskId, setTaskId] = useState('');
useEffect(() => {
  const timer = setInterval(async () => {
    const status = await pollStatus(taskId); // 始终是初始值 ''
  }, 3000);
  return () => clearInterval(timer);
}, []);

// 正确：用 ref 存储最新值
const taskIdRef = useRef('');
const updateTaskId = (id: string) => {
  taskIdRef.current = id;
  setTaskId(id);
};
useEffect(() => {
  const timer = setInterval(async () => {
    if (!taskIdRef.current) return;
    const status = await pollStatus(taskIdRef.current); // 始终最新
  }, 3000);
  return () => clearInterval(timer);
}, []);
```

## 性能预算

```
JavaScript bundle：< 200KB gzipped（初始加载）
CSS：< 50KB gzipped
图片：< 200KB/张（首屏）
字体：< 100KB 合计
API 响应时间：< 200ms（p95）
可交互时间（TTI）：< 3.5s（4G 网络）
Lighthouse 性能评分：≥ 90
Edge Function 响应：< 2s（p95）
```

**CI 中强制执行：**

```bash
npx bundlesize --config bundlesize.config.json
npx lhci autorun
```

## 另请参阅

详细性能清单、优化命令和反模式参考，见 `references/performance-checklist.md`。

## 常见借口与现实

| 借口 | 现实 |
|------|------|
| "我们以后再优化" | 性能债务会复利累积。现在修复明显的反模式，推迟微优化。 |
| "在我机器上很快" | 你的机器不是用户的机器。在有代表性的硬件和网络上测试。 |
| "这个优化很显然" | 没测量就不知道。先分析。 |
| "用户感受不到 100ms 的差距" | 研究表明 100ms 延迟会影响转化率。用户比你想象的更敏感。 |
| "框架会处理性能" | 框架防止部分问题，但无法修复 N+1 查询或过大的 bundle。 |
| "Edge Function 不需要优化" | Edge Function 有执行时间限制，同步下载大文件会超时。 |

## 红色警报

- 没有性能分析数据就做优化
- 数据拉取中存在 N+1 查询模式
- 列表接口没有分页
- 图片缺少尺寸、懒加载或响应式设置
- bundle 大小持续增长但没有审查
- 生产环境没有性能监控
- `React.memo` 和 `useMemo` 滥用（过度使用和不使用一样有害）
- Edge Function 中同步下载大文件
- React 轮询中用 state 代替 ref 存储 taskId（闭包陷阱）

## 上线前验证

- [ ] 有优化前后的测量数据（具体数字）
- [ ] 已定位并解决具体瓶颈
- [ ] Core Web Vitals 在"良好"阈值内
- [ ] bundle 大小未显著增加
- [ ] 新数据拉取代码中无 N+1 查询
- [ ] CI 中性能预算通过（如已配置）
- [ ] 现有测试仍然通过（优化未破坏行为）
- [ ] Edge Function 无同步大文件下载
- [ ] 轮询逻辑使用 ref 存储最新 taskId
