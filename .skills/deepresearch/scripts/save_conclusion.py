#!/usr/bin/env python3
"""Save a task/reflection conclusion with structural field validation (no word limit).

进度门（详见 task_progress.py）：
- --type task 时，--task-id 必须等于指针（第一个还没有 conclusions/task_N.md 的任务号），
  否则 die，不要求本号刚 search/fetch 过。
- --type reflection 时，要求任务结论已经全部齐（每个任务号都有 task_N.md），否则 die。
- 保存成功后按磁盘上的 conclusions/task_N.md 重新同步 研究任务.json（有文件即
  completed，不要求经由本脚本写入），并在 stdout 追加完成进度 / 待写编号。
"""

import argparse
import os
import re
import shutil
import sys

import task_progress as tp


# --- 自动推断项目根路径（不依赖 cwd）---
# 本脚本位置：<project_root>/.skills/deepresearch/scripts/save_conclusion.py
# 项目根：向上 3 级
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
DEFAULT_OUTPUT_DIR = os.path.join(DEFAULT_PROJECT_ROOT, "outputs")


# --- Required sections per conclusion type ---
TASK_REQUIRED = [
    "对应研究问题或主题",
    "结论摘要",
    "关键结论",
    "信息缺口与写作提醒",
]

REFLECTION_REQUIRED = [
    "检查结果",
    "修正与补充",
    "报告写作提醒",
]


# --- 依据行识别 ---
# 只保留最小语义：识别以「依据」开头（可带括号标注）的行；
# 无括号 或 括号内容含「网页」→ 视为网页型，要求含 http(s) URL；
# 括号内容为其他文字（文件、计算、综合判断、原始数据…）→ 只要求内容非空。
EVIDENCE_LINE_RE = re.compile(
    r"^\s*[-*+]?\s*"                    # 可选 markdown 列表前缀
    r"(?:\*\*)?"                        # 可选粗体开
    r"依据"                              # 必须以「依据」开头
    r"(?:[（(]\s*([^）)]*)\s*[)）])?"   # 可选 (类别) / （类别）
    r"(?:\*\*)?"                        # 可选粗体闭
    r"\s*[:：]\s*"                      # 半角或全角冒号
    r"(.*)$"                            # 依据正文
)

URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    print("请修正上述问题后重新调用 save_conclusion.py。", file=sys.stderr)
    sys.exit(1)


def count_words(content):
    """Rough word count: Chinese chars + English words."""
    zh = len(re.findall(r"[\u4e00-\u9fff]", content))
    en = len(re.findall(r"[a-zA-Z]+", content))
    return zh + en


def extract_section(content, section_name, all_sections):
    """Extract a non-empty section delimited by the required bold headings."""
    names = "|".join(re.escape(name) for name in all_sections)
    pattern = re.compile(
        rf"(?ms)"
        rf"^\*\*{re.escape(section_name)}\*\*\s*$"
        rf"(.*?)"
        rf"(?=^\*\*(?:{names})\*\*\s*$|\Z)"
    )
    match = pattern.search(content)
    if not match:
        die(f"缺少字段：**{section_name}**")

    body = match.group(1).strip()
    if not body:
        die(f"字段内容为空：**{section_name}**")
    return body


def reject_placeholders(content):
    placeholders = re.search(
        r"TODO|TBD|待填写|\[\s*请填写\s*\]",
        content,
        re.IGNORECASE,
    )
    if placeholders:
        die(f"存在未完成的占位内容：{placeholders.group(0)}")


def split_numbered_items(body):
    """把「关键结论」正文按行首编号（1. / 1、）拆成若干条目。

    返回 [(index_str, item_text), ...]；未识别到编号时返回空列表。
    """
    # 用 (?m) 让 ^ 匹配行首；行首允许若干空白后紧跟数字 + . 或 、
    marker_re = re.compile(r"(?m)^\s*(\d+)\s*[\.、]\s+")
    matches = list(marker_re.finditer(body))
    if not matches:
        return []
    items = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()
        items.append((m.group(1), text))
    return items


def iter_evidence_lines(text):
    """扫描文本，yield (category, remainder) 依据行。

    category:
      - None    → 无括号，视为网页型（需要 URL）
      - str     → 括号里的标注内容（如「网页」「文件」「计算」「综合判断」…）
    remainder: 依据正文。
    """
    for raw_line in text.splitlines():
        m = EVIDENCE_LINE_RE.match(raw_line)
        if m:
            category = m.group(1)
            if category is not None:
                category = category.strip()
            yield category, m.group(2).strip()


def is_web_evidence(category):
    """无括号 或 括号内容含「网页」→ 视为网页型，要求 URL。"""
    if category is None:
        return True
    return "网页" in category


def validate_task_key_conclusions(content):
    """对「关键结论」段落做编号列表与依据完整性校验。"""
    body = extract_section(content, "关键结论", TASK_REQUIRED)
    items = split_numbered_items(body)
    if not items:
        die(
            "「关键结论」必须使用编号列表（形如 `1. ...` 或 `1、...`），"
            "只用粗体小标题的段落式写法会被拒绝。"
        )
    for idx, text in items:
        evidences = list(iter_evidence_lines(text))
        if not evidences:
            die(f"关键结论第 {idx} 条缺少依据行（`- 依据：...`）。")
        for category, remainder in evidences:
            if not remainder:
                label = "依据" if category is None else f"依据（{category}）"
                die(f"关键结论第 {idx} 条的「{label}」内容为空。")
            if is_web_evidence(category) and not URL_PATTERN.search(remainder):
                label = "依据" if category is None else f"依据（{category}）"
                die(
                    f"关键结论第 {idx} 条的「{label}」缺少具体 URL（需包含 http:// 或 https://）；"
                    "如属本地文件、计算或综合判断，请改用「依据（文件）」「依据（计算）」"
                    "或「依据（综合判断）」等带括号的依据标签。"
                )


def validate_reflection_evidence(content):
    """反思结论中若出现网页依据，必须包含 URL。"""
    for section in ("检查结果", "修正与补充"):
        body = extract_section(content, section, REFLECTION_REQUIRED)
        for category, remainder in iter_evidence_lines(body):
            if not remainder:
                label = "依据" if category is None else f"依据（{category}）"
                die(f"反思「{section}」中「{label}」内容为空。")
            if is_web_evidence(category) and not URL_PATTERN.search(remainder):
                label = "依据" if category is None else f"依据（{category}）"
                die(
                    f"反思「{section}」中「{label}」缺少具体 URL（需包含 http:// 或 https://）；"
                    "如属本地文件、计算或综合判断，请使用带括号的依据标签。"
                )


def validate_task(content, task_id):
    title_pattern = rf"(?m)^###\s*任务\s*{task_id}\s*[：:]\s*\S.*$"
    if not re.search(title_pattern, content):
        die(f"标题必须是：### 任务 {task_id}：任务标题")

    for section in TASK_REQUIRED:
        extract_section(content, section, TASK_REQUIRED)
    reject_placeholders(content)
    validate_task_key_conclusions(content)


def validate_reflection(content, round_id):
    title_pattern = rf"(?m)^###\s*反思第\s*{round_id}\s*轮\s*$"
    if not re.search(title_pattern, content):
        die(f"标题必须是：### 反思第 {round_id} 轮")

    for section in REFLECTION_REQUIRED:
        extract_section(content, section, REFLECTION_REQUIRED)
    reject_placeholders(content)
    validate_reflection_evidence(content)


def validate(content, conclusion_type, task_id=None, round_id=None):
    if conclusion_type == "task":
        validate_task(content, task_id)
    else:
        validate_reflection(content, round_id)


def resolve_target(args):
    if args.type == "task":
        target_dir = os.path.join(args.output_dir, "conclusions")
        target = os.path.join(target_dir, f"task_{args.task_id}.md")
        label = f"task_{args.task_id}.md"
    else:
        target_dir = os.path.join(args.output_dir, "reflection")
        target = os.path.join(target_dir, f"round_{args.round}.md")
        label = f"reflection/round_{args.round}.md"
    return target_dir, target, label


def resolve_output_dir(raw_output_dir):
    """把 --output-dir 参数解析为绝对路径，并对可疑相对路径发出警告。"""
    if os.path.isabs(raw_output_dir):
        return raw_output_dir
    abs_path = os.path.abspath(raw_output_dir)
    print(
        f"WARNING: --output-dir 是相对路径 ({raw_output_dir!r}), "
        f"已按当前 cwd 拼接为绝对路径 {abs_path!r}。"
        f"若结果与预期项目根不符，请显式传入绝对路径。",
        file=sys.stderr,
    )
    return abs_path


def main():
    parser = argparse.ArgumentParser(description="Save task or reflection conclusion with validation.")
    parser.add_argument("--type", choices=["task", "reflection"], required=True,
                        help="task = 任务结论, reflection = 阶段 5 反思结论")
    parser.add_argument("--task-id", type=int, help="任务编号（--type task 时必填）")
    parser.add_argument("--round", type=int, help="反思轮次（--type reflection 时必填）")
    parser.add_argument("--force", action="store_true", help="覆盖已有文件（自动备份到 .bak）")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出根目录（默认基于脚本位置自动推断：{DEFAULT_OUTPUT_DIR}）",
    )
    args = parser.parse_args()

    if args.type == "task" and args.task_id is None:
        die("--type=task 时必须指定 --task-id")
    if args.type == "reflection" and args.round is None:
        die("--type=reflection 时必须指定 --round")

    # 解析 output-dir 为绝对路径（进度门也依赖它，提前解析）
    args.output_dir = resolve_output_dir(args.output_dir)

    # 结论内容只从 stdin 读取
    content = sys.stdin.read().strip()
    if not content:
        die("内容为空（结论内容需通过 stdin 传入，例如 << 'EOF' ... EOF）")

    validate(
        content=content,
        conclusion_type=args.type,
        task_id=args.task_id,
        round_id=args.round,
    )

    # 进度硬门：task 必须等于指针；reflection 必须任务结论已全部齐
    if args.type == "task":
        tp.validate_save_task(args.output_dir, args.task_id)
    else:
        tp.validate_save_reflection(args.output_dir)

    target_dir, target, label = resolve_target(args)
    os.makedirs(target_dir, exist_ok=True)

    if os.path.exists(target):
        if not args.force:
            die(f"文件已存在: {target}（如需覆盖，加 --force）")
        shutil.copy2(target, target + ".bak")

    with open(target, "w", encoding="utf-8") as f:
        f.write(content + "\n")

    wc = count_words(content)
    print(f"OK: 已保存 {label}（约 {wc} 字，绝对路径 {target}）")

    # 按磁盘上的 conclusions/task_N.md 重新同步 研究任务.json，并报告完成/待写进度
    if args.type == "task":
        plan_data = tp.load_plan(args.output_dir)
        if plan_data is not None:
            steps, completed_ids, pointer = tp.sync_plan_status(args.output_dir, plan_data)
            k = tp.max_step_num(steps)
            print(f"OK: 研究任务.json 已更新（task-{args.task_id} → completed，{len(completed_ids)}/{k}）")
            if pointer is None:
                print(
                    "NEXT: 任务已齐。下一步反思 baidu_search.py --phase reflection，"
                    "然后 save_conclusion --type reflection --round 1。"
                )
            else:
                print(f"完成进度：{len(completed_ids)}/{k}，待写：task-{pointer}")


if __name__ == "__main__":
    main()
