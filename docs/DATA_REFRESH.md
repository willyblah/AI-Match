# 基准数据自动更新 / Automatic benchmark data refresh

本站的 16 项基准指标可由脚本从 **Artificial Analysis Data API** 拉取。

> **当前状态：定时刷新已关闭。** 数据只在你主动运行时更新——本地 `npm run refresh:data`，
> 或在 GitHub Actions 页面手动点击 *Run workflow*。
> 如需恢复每周自动刷新，取消 `.github/workflows/refresh-model-data.yml` 里 `schedule:` 两行的注释即可。

---

## 1. 一次性设置（需要你本人操作）

有两步我无法代劳：注册账号、以及把代码推到 GitHub。

### 1.1 获取 Artificial Analysis API Key（免费）

1. 打开 <https://artificialanalysis.ai/data-api>
2. 注册账号并生成 API Key（免费档：**每 24 小时 100 次请求**，本脚本每次运行只用 1 次）
3. 妥善保存这串 Key，**不要提交到代码库**

### 1.2 让本地能跑

```bash
export AA_API_KEY=你的key
npm run refresh:data:dry
```

`:dry` 表示只报告、不写文件。确认输出正常后，去掉 `:dry` 即可真正写入。

### 1.3 启用手动触发的更新（需要 GitHub 仓库）

当前这份代码**还不是一个 git 仓库**（没有 `.git` 目录），所以定时任务还跑不起来。
GitHub Actions 只能在 GitHub 仓库里运行。启用步骤：

```bash
git init && git add -A && git commit -m "Initial commit"
git branch -M master
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin master
```

然后在仓库页面：**Settings → Secrets and variables → Actions → New repository secret**

| 字段 | 值 |
| --- | --- |
| Name | `AA_API_KEY` |
| Secret | 你在 1.1 拿到的 key |

完成后，即可在 **Actions** 标签页点 *Run workflow* 手动触发刷新。
定时任务当前是关闭的，不会自己跑。

---

## 2. 每次运行会发生什么

```
你在 Actions 页面点 Run workflow（或本地 npm run refresh:data）
   │
   ├─ 调用 AA API 拉取最新数据
   ├─ 更新 src/lib/model-data.json 中的指标数值
   ├─ 跑 typecheck + build（不过就不提交）
   │
   ├─ 数值有变化 ──────────→ 直接提交到 master，站点自动重新部署
   └─ 发现更强的新模型 ────→ 开一个 issue，等你决定，不自动替换
```

### 为什么新模型不自动替换？

三个原因：

1. **它会改变论文的模型集合。** 站内六款模型对应论文表 3.2。如果它悄悄变了，
   站点和论文就对不上了——而你很可能要到答辩现场才发现。
2. **自动选型容易选错。** AA 上同一家有多个变体（Claude Opus 5 的 max / xhigh / high，
   还有 Fable 5、Mythos 5）。"取该厂商分数最高的"未必是你想要的那个。
3. **新模型缺 LiveBench 分数。** AA API 不提供 LiveBench，必须人工去
   <https://livebench.ai> 查 CODING 列。自动换模型会得到一个缺指标的条目。

所以脚本只**报告**，不**替换**。

### 采用一个新模型

1. 改 `scripts/models.config.json` 里对应 slot 的 `id` 和 `aaSlug`
2. 在 `src/lib/data.ts` 的 `DESCRIPTIONS` 里给新 id 写一句简介
3. 去 <https://livebench.ai> 查该模型 **CODING** 列的分数，除以 100，
   填进 `src/lib/model-data.json` 对应模型的 `liveBench`
4. `npm run refresh:data` 拉取其余 15 项
5. 确认站点与论文的差异是你有意为之

---

## 3. 数据来源与出处

| 指标 | 来源 |
| --- | --- |
| Terminal-Bench v2.1、SciCode、GDPval-AA v2、τ³-Banking、MLCR-AA、AA-Omniscience Accuracy、Humanity's Last Exam、GPQA Diamond、CritPt | Artificial Analysis Data API |
| 输入/输出价格、单任务成本、Index token 量、生成速度 | Artificial Analysis Data API |
| **AA-Omniscience Non-Hallucination** | **推导**（见下） |
| **LiveBench** | **人工**，来自 <https://livebench.ai> CODING 列 |

### 关于推导的那一项

AA 只对部分模型公布 hallucination rate，但对所有模型公布 accuracy 和 Omniscience Index。
由此可反推：

```
hallucination = (accuracy − omniscienceIndex / 100) / (1 − accuracy)
nonHallucination = 1 − hallucination
```

该公式已用 AA 确实公布了 hallucination rate 的模型验证，误差约 1e-16（即精确）。
**若写进论文，这一项应标注为"推导值"而非"实测值"。**

### 脚本绝不编造数字

这是硬性设计原则。拿不到的值一律**保留上一次的数值并标记为 stale**，
在运行日志里明确列出，绝不用估计值或"看起来合理"的数字填充。

原因很实际：一个错误的基准数值不会报错，它只会安静地产出一个自信但错误的排名。

---

## 4. 归属要求

AA 的免费 API **要求所有使用方标注数据来源**。页脚的 Artificial Analysis 与
LiveBench 链接即用于满足此要求，位于 `src/components/layouts/MainLayout.tsx`，**请勿移除**。

---

## 5. 故障排查

| 现象 | 原因 / 处理 |
| --- | --- |
| `AA_API_KEY is not set` | 本地没 export；或 GitHub secret 名字拼错 |
| `401` | key 失效，去 AA 重新生成 |
| `403` | 该端点需要更高档位，免费档只能用 `/language/models/free` |
| `429` | 当天 100 次配额用完，等 `x-ratelimit-reset` 时间 |
| 日志里某项一直 stale | AA 改了字段名。在 `models.config.json` 的 `indicatorMap` 里加上新的候选路径即可（支持多个候选，按顺序尝试） |
| `Intelligence Index version changed` 警告 | AA 改了指数口径，分数可能不再与论文表格可比。合并前先人工确认 |

出错时脚本一律**不写任何文件**并以非零码退出，不会留下半成品数据。
