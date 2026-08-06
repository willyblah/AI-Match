---
name: narrative-scripts
description: "Create, revise, and QA narrative game scripts as Markdown script text in the user's node-by-node format. Use when the desired output is a readable script with '剧本文本（按节点顺序）', per-node dialogue, arrow choices, ending nodes, and a final '节点跳转关系一览' table instead of JSON, YAML, or TypeScript data."
---

# Narrative Scripts2

Use this skill to write a human-readable interactive script first. The default deliverable is Markdown text like the user's pasted example: nodes in order, dialogue/narration, choices with arrows, ending nodes, and a final jump table.

## Workflow

1. Ask only for missing essentials: premise, genre, length, audience, tone, and branch depth.
2. Read `references/script-text-format.md` for exact formatting and QA rules.
3. Draft or revise the script as Markdown script text.
4. Run `python3 scripts/qa_script_text.py <script.md|txt>` when the script is saved as a file.
5. Fix hard QA errors first: missing nodes, bad targets, dead ends, unreachable endings, or jump-table mismatches.

## Output Contract

- Start with `## 剧本文本（按节点顺序）`.
- Write each node as `### node_id`; use lowercase IDs with underscores.
- Write ending nodes as `### node_id（结局）`.
- Write narration/dialogue as `**角色：** 文本`; use `旁白` for narration.
- Use an options block exactly like:

```md
**选项：**
- 选择文本。 → target_node
```

- End terminal nodes with `**结局类型：失败**`, `**结局类型：苦涩**`, `**结局类型：成功**`, or another short ending type.
- Finish with `## 节点跳转关系一览` and a Markdown table: `节点 | 选项文本 | 目标节点`.

## Compression Rules

- Do not output JSON, YAML, TS, asset catalogs, variables, line-level emotion, music, portraits, camera, or production metadata unless explicitly requested.
- Keep all game logic visible in the node choices and jump table.
- If evidence or prerequisites matter, phrase them in the choice text or node prose; this Markdown QA checks route logic, not hidden state.
- Preserve stable node IDs during revision unless the user asks for a structural rewrite.

## 剧情结构与体验控制 (Design Rules)

### 1. 交互节奏控制 (Pacing & Chunking)

- **单节点体量：** 严禁“一句话一选择”。每个节点应包含 [3-5 句] 的剧情铺垫或细节描写，允许加入环境描写、内心独白、细节互动（如微表情、天气、动作、环境描写等）。
- **复合节点链接（静默推进）：** 引入“无选择直接跳转”节点。在用户体验核心剧情、情感高潮或连续发生的事件时，使用 `→ next_node`（无选项）进行线性叙事，确保用户有连续阅读剧情的体验，只在**面临命运转折、策略抉择、人际表态**的关键时刻才提供选项。

### 2. 情绪曲线设计 (Emotional Arc & Feedback)

- **正负反馈交替 (3:2 原则)：** 剧本整体基调应“有张有弛”。必须设计至少 30% 以上的正向高光节点（如角色被嘉奖、角色在关系冲突的关系中被友好对待、角色通过努力有所收获等等）。
- **多维度结局与命名 (Diverse Endings&Title)：**

  成功结局不能全是“惨胜”。应该有“完美通关（既拿 Offer 又收割友情与健康）”的爽点结局，苦涩结局中也要留有成长的温情，避免全盘否定玩家的努力。

  拒绝对结局进行简单粗暴的“好坏对错”评判。所有结局都是玩家一连串行为的“因果合力”，要让每种结局都具备独特的戏剧张力和回味价值：

  - **成功-圆满成功：** 玩家在剧情冲突需要权衡的价值点（如KPI、身体健康、个人高光、友情关系、爱情、成就等）上，得到比较综合的圆满结局，形成爽点。
  - **成功-有代价的成功：** 属于“遗憾的艺术”。可能世俗意义上不完美（如未能成功转正，或与重要伙伴告别，有所遗憾），但笔触上留有成长、重要收获等成功、教训、觉醒、收获等。有失有得，传递开放式结局和释怀感。
  - **失败：** 拒绝随机的飞来横祸或剧情杀，是主角在重要选择下失误的后果。失败必须是玩家在关键节点（如选择谎言、持续逃避、极限硬撑或彻底放弃）选择或者连续累积失误的结果。结局因果完整。
  
  **【命名要求】** 严禁直接输出“成功”、“失败”等分类标签。必须根据该结局的具体剧情、核心意象或情感基调，提炼出一个【具有故事感、文艺感或象征意义的4-8字结局名称】（例如：`永恒的等待`、`赴一场未来的约定`、`公路的告别诗`）。

- **数值计算逻辑：** 游戏结局由玩家做出不同价值倾向的选择综合决定，可以对每个选项赋予通往不同结局的分数，最后得到剧情结果。
