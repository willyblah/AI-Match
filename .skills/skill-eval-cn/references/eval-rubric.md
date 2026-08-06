# Skill-Eval 中文评分规则与报告模板

## 使用方式

在评估本地技能时，先读取目标文件，再按本文件的检查项给出证据化结论。除非有真实运行日志，否则只输出分档和原因，不输出伪造的精确 token 或 benchmark 结果。

## 一、技能评估检查项

| 维度 | 检查项 | 风险信号 | 建议严重度 |
|------|--------|----------|------------|
| frontmatter | 是否包含 `name`、`description`、`license`，需要时包含 `packageType: instruction-skill` 与 `instructionOnly: true` | 字段缺失、名称不一致、类型声明与正文能力不匹配 | high / medium |
| 触发描述 | 是否说明“何时触发”和“能做什么” | 只写用途不写触发语；关键词过少；描述过长导致触发成本高 | high / medium |
| 命名一致性 | 目录名、frontmatter `name`、引用名称是否一致 | 用户按名称调用时找不到或触发错目标 | medium |
| 正文结构 | 是否包含前置条件、核心能力、执行优先级、参考模板、沟通规则、常见坑 | 结构缺失导致执行不稳定 | medium |
| progressive disclosure | 主文件是否聚焦工作流，细节是否放入 `references/` | `SKILL.md` 过重，调用后上下文成本高 | medium |
| 证据与引用 | 是否要求引用文件路径和行号 | 评估结论不可追溯 | medium |
| 链接与路径 | references、assets、scripts 路径是否存在 | 运行时读取失败、模板不可用 | high / medium |
| 类型适配 | 纯指令型、API 集成型、MCP/CLI 型是否按各自约束编写 | 纯指令型要求不可用运行环境；API 型缺少密钥规则 | high |
| 安全与边界 | 是否避免泄露密钥、伪造执行、误导用户 | 把未执行结果写成已执行；建议保存敏感数据但无确认 | high |

## 二、技能包评估检查项

| 维度 | 检查项 | 风险信号 | 建议严重度 |
|------|--------|----------|------------|
| 包结构 | 是否能识别根目录、多个技能目录和共享资料 | 多入口混乱、目标不清 | medium |
| 多技能职责 | 每个技能是否有清晰边界 | 多个技能 description 高度重叠，容易误触发 | high / medium |
| 路由入口 | 是否有总入口或清晰的选择规则 | 用户不知道该调用哪个技能 | medium |
| 共享 references | 公共资料是否共享，专属资料是否隔离 | 资料互相污染、路径引用不稳定 | medium |
| 命名规则 | 目录名、frontmatter 名、用户可见名是否一致 | 安装、调用、上架时出现错配 | high / medium |
| 体积控制 | 主文件是否轻量，长模板是否后置 | 调用成本上升，响应变慢 | medium |

## 三、Token / 上下文预算三桶

| 桶 | 含义 | good | moderate | heavy |
|----|------|------|----------|-------|
| trigger | 触发前可能进入上下文的名称、描述、少量元信息 | ≤48 | ≤92 | ≤150 |
| invoke | Skill 被调用后加载的主指令内容 | ≤220 | ≤480 | ≤900 |
| deferred | 按需读取的 references、scripts、assets、长模板 | ≤180 | ≤520 | ≤1200 |

解释规则：
- 没有可靠 tokenizer 时，不给精确 token 数，按内容长度和结构估算分档。
- description 太长优先影响 trigger 桶。
- `SKILL.md` 正文太长优先影响 invoke 桶。
- 大型参考资料只在需要时读取，归入 deferred 桶，不应塞进主文件。

## 四、评分档位

| 档位 | 含义 | 典型状态 |
|------|------|----------|
| A | 低风险，可直接使用 | frontmatter 完整、触发清晰、结构合理、预算轻、路径有效 |
| B | 小问题，建议优化 | 有少量可维护性或触发描述问题，不影响主流程 |
| C | 中等风险，需要修 | 结构缺口、触发不清、预算偏重或 references 有问题 |
| D | 高风险，使用前应修 | 关键字段缺失、入口混乱、路径断裂或边界错误 |
| F | 不建议使用 | 无法识别入口、严重误导、缺失核心文件或安全边界错误 |

## 五、riskLevel 判定

| riskLevel | 判定标准 |
|-----------|----------|
| low | 问题主要是优化项，不影响用户正确调用 |
| medium | 存在触发、结构、路径或预算问题，可能影响稳定使用 |
| high | 存在入口不可用、关键信息缺失、严重误导、敏感信息或不可执行承诺 |

## 六、默认报告模板

```markdown
## At a Glance
| 项目 | 分档/结论 | 证据 |
|------|-----------|------|
| 整体档位 | A/B/C/D/F | path:line |
| 风险等级 | low/medium/high | path:line |
| 先修项 | 一句话说明 | path:line |
| 预算压力 | good/moderate/heavy | path:line |

## Why It Matters
- 说明问题会如何影响触发准确性、上下文成本、可维护性、用户结果或上架质量。

## Fix First
| 优先级 | 严重度 | 问题 | 证据 | 最小修复动作 |
|--------|--------|------|------|--------------|
| 1 | high/medium/low | ... | path:line | ... |

## Recommended Next Step
- 给一个最小、可执行的下一步。
```

## 七、改进 brief 模板

```markdown
# 技能改进 Brief

## 目标
- 这次改写要解决的核心问题。

## 必改项
1. 问题：...
   - 证据：path:line
   - 修改动作：...
   - 验收标准：...

## 建议项
1. 问题：...
   - 证据：path:line
   - 修改动作：...

## 保持不变
- 列出已有且应保留的设计。

## 复评清单
- [ ] frontmatter 完整
- [ ] description 触发清晰
- [ ] `SKILL.md` 主体不臃肿
- [ ] references 路径有效
- [ ] 估算与实测边界写清楚
```

## 八、自定义评分维度模板

| 字段 | 说明 |
|------|------|
| id | 稳定、可复评的规则 ID |
| category | 规则类别，如 trigger、budget、structure、security |
| severity | high / medium / low |
| status | pass / warn / fail / unknown |
| evidence | 文件路径、行号、观察到的事实 |
| remediation | 最小修复动作 |

示例：

```json
{
  "id": "trigger.description.too-broad",
  "category": "trigger",
  "severity": "medium",
  "status": "warn",
  "evidence": ["SKILL.md:3 description 同时覆盖多个无关场景"],
  "remediation": ["把触发语收窄到技能真实能处理的任务"]
}
```

## 九、本地真实测量指引

当用户要求实测时，按下面流程给计划，不在纯指令环境中伪造结果：

1. 收集 3-5 个代表性真实任务作为场景。
2. 记录每个场景的输入、期望输出、使用的技能版本。
3. 在本地可执行环境中 dry run，确认不会写错路径、联网或执行破坏性操作。
4. 正式运行并保存 usage 日志、耗时、输出文件和错误。
5. 把实测结果与静态估算并排展示，标注样本数和限制。
6. 根据差异更新触发描述、主指令体积、references 拆分和示例场景。

报告真实测量时必须写清：
- 样本数量
- 是否冷启动
- 是否有缓存
- 是否包含 reasoning token 或输出 token
- 估算值与实测值的差异是否稳定
