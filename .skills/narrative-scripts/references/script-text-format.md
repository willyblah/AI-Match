# Script Text Format

Use this format for narrative game scripts meant to be read, edited, and QAed as text before any runtime conversion.

## Required Shape

```md
## 剧本文本（按节点顺序）

### start
**旁白：** 雨落在旧车站的铁皮檐上。

**林月：** 今晚若再错过这班车，证词就会消失。

**选项：**
- 直接进候车室。 → waiting_room
- 先问售票员。 → clerk

---

### waiting_room
**旁白：** 候车室里只亮着一盏灯。

**选项：**
- 查看长椅下的纸袋。 → clue_bag

---

### ending_truth（结局）
**旁白：** 天亮前，真相终于被排进铅字。

**结局类型：成功**

## 节点跳转关系一览

| 节点 | 选项文本 | 目标节点 |
|------|---------|---------|
| start | 直接进候车室 | waiting_room |
| start | 先问售票员 | clerk |
| waiting_room | 查看纸袋 | clue_bag |
```

## Node Rules

- Use `### node_id` for every playable node.
- Use `### node_id（结局）` for terminal nodes.
- Put nodes in intended play order; `start` should be first.
- Separate nodes with `---`.
- Non-ending nodes must have at least one `**选项：**` block and one or more arrow choices.
- Ending nodes must have `**结局类型：...**` and no outgoing choices.

## Text Rules

- Use `**角色：** 文本` for all narration and dialogue.
- Use `旁白` for narration.
- Keep scene, mood, music, emotion, portrait, and camera information inside prose only when it is story-relevant.
- Do not add production fields or per-line metadata.

## Choice Rules

Choices use this exact line shape:

```md
- 选择文本。 → target_node
```

The target must be an existing node ID. Keep choice text player-facing; avoid debug labels.

## Silent Jump Rules (复合节点链接)

For linear narrative segments without player choice, use a silent jump line:

```md
→ next_node
```

This line must appear in the node body and has no option marker. The QA script treats it as an implicit choice with empty text. It must still appear in the jump table with an empty or descriptive text cell.

## Jump Table Rules

Every body choice must appear in the final table, and every table row must correspond to a body choice.

The table choice text may be shortened, but it must still clearly match the body choice for the same source and target:

```md
| start | 直接进后台 | backstage_first |
```

## QA Scope

`scripts/qa_script_text.py` checks:

- duplicate or invalid node IDs
- missing `start`
- missing or unknown jump targets
- non-ending dead ends
- ending nodes with outgoing choices
- unreachable nodes
- whether at least one ending is reachable
- body choices and jump-table rows agree by source and target
- table text roughly matches the body choice text when `--strict-text` is used

It does not verify hidden inventory/state logic. If a route must require evidence, make that requirement visible in text or convert to a structured runtime format later.
