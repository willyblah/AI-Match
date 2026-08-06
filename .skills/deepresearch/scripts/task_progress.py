#!/usr/bin/env python3
"""Shared 研究任务.json / conclusions 进度门，供 baidu_search.py、fetch_webpage.py、
save_conclusion.py 三个脚本共用。

核心概念：
- 「完成」只认磁盘上是否存在 <output_dir>/conclusions/task_N.md（不管是不是经由
  save_conclusion.py 写入——工程要的是 JSON 全 completed，这条比"是否走脚本"优先）。
- 「待写」= 指针 = 按编号顺序第一个还没有 task_N.md 的任务号；全部存在时指针为 None。
- search / fetch 的 --phase task-N 只允许在 N-1 已有过 search/fetch 记录或已有
  task_{N-1}.md 时才放行（不跳号）；--phase reflection 只允许在指针为 None（任务结论
  全部齐了）时放行。
- save_conclusion.py --type task 要求 --task-id 必须等于指针；--type reflection 要求
  指针为 None。
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


PLAN_FILENAME = "研究任务.json"
CONCLUSIONS_DIRNAME = "conclusions"

PHASE_TASK_RE = re.compile(r"^task-(\d+)$")


def die(message):
    """打印错误信息（可多行）并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def _plan_path(output_dir):
    return os.path.join(output_dir, PLAN_FILENAME)


def load_plan(output_dir):
    """读取 研究任务.json；不存在返回 None；存在但解析失败直接 die。"""
    path = _plan_path(output_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        die(f"ERROR: 读取 outputs/{PLAN_FILENAME} 失败：{exc}")


def plan_steps(plan_data):
    return plan_data.get("plan", {}).get("steps", []) if plan_data else []


def step_num(step):
    m = re.search(r"\d+", step.get("id", "0"))
    return int(m.group()) if m else 0


def _steps_by_num(steps):
    return {step_num(s): s for s in steps}


def step_title(steps, n):
    step = _steps_by_num(steps).get(n)
    return step.get("title", "") if step else ""


def max_step_num(steps):
    nums = [step_num(s) for s in steps]
    return max(nums) if nums else 0


def completed_ids_from_disk(output_dir):
    """按 conclusions/task_N.md 是否存在判定完成（手写也算数）。"""
    conclusions_dir = os.path.join(output_dir, CONCLUSIONS_DIRNAME)
    ids = set()
    if os.path.isdir(conclusions_dir):
        for fname in os.listdir(conclusions_dir):
            m = re.match(r"task_(\d+)\.md$", fname)
            if m:
                ids.add(int(m.group(1)))
    return ids


def first_missing_id(steps, completed_ids):
    """按编号顺序第一个还没有结论文件的任务号；全部完成返回 None。"""
    for n in sorted(step_num(s) for s in steps):
        if n not in completed_ids:
            return n
    return None


def missing_ids(steps, completed_ids):
    return sorted(step_num(s) for s in steps if step_num(s) not in completed_ids)


def sync_plan_status(output_dir, plan_data):
    """按磁盘上的 conclusions/task_N.md 同步 研究任务.json 的 status：

    - 有结论文件的 step → completed（无论是否经由 save_conclusion.py 写入）。
    - 指针（第一个没有结论文件的 step）→ in_progress。
    - 其余 → pending（超前搜索只写 log，不把 JSON 标 in_progress）。

    返回 (steps, completed_ids, pointer)；有修改才写回文件。
    """
    steps = plan_steps(plan_data)
    if not steps:
        return steps, set(), None

    completed_ids = completed_ids_from_disk(output_dir)
    pointer = first_missing_id(steps, completed_ids)

    modified = False
    for step in steps:
        n = step_num(step)
        if n in completed_ids:
            if step.get("status") != "completed":
                step["status"] = "completed"
                modified = True
        elif n == pointer:
            if step.get("status") != "in_progress":
                step["status"] = "in_progress"
                modified = True
        else:
            if step.get("status") != "pending":
                step["status"] = "pending"
                modified = True

    if modified:
        plan_data["last_updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(_plan_path(output_dir), "w", encoding="utf-8") as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=2)

    return steps, completed_ids, pointer


def log_touched_ids(log_data):
    """log 里出现过 phase=task-N 记录的所有 N（search + fetch 合并统计）。"""
    ids = set()
    for entry in log_data.get("search", []) + log_data.get("fetch", []):
        m = PHASE_TASK_RE.match(entry.get("phase", "") or "")
        if m:
            ids.add(int(m.group(1)))
    return ids


def has_prior_evidence(output_dir, log_data, n):
    """N 是否已有 search/fetch 记录，或已有 conclusions/task_N.md（跳号判定用）。"""
    if n in log_touched_ids(log_data):
        return True
    return os.path.isfile(os.path.join(output_dir, CONCLUSIONS_DIRNAME, f"task_{n}.md"))


def format_id_list(steps, ids):
    parts = [f"task-{n}「{step_title(steps, n)}」" for n in sorted(ids)]
    return "、".join(parts)


def validate_phase_for_research(output_dir, phase, log_data):
    """search / fetch 阶段 4/5 硬门：无 JSON / phase 非法 / 越界 / 跳号 / reflection 未齐。

    在真正发起网络请求前调用，避免违规调用浪费配额。
    返回 (steps, completed_ids) 供后续渲染进度块复用。
    """
    plan_data = load_plan(output_dir)
    if plan_data is None:
        die(f"ERROR: 未找到 outputs/{PLAN_FILENAME}，请回到阶段 3 生成研究任务。")

    steps, completed_ids, pointer = sync_plan_status(output_dir, plan_data)
    k = max_step_num(steps)

    if phase == "reflection":
        missing = missing_ids(steps, completed_ids)
        if missing:
            die(
                "ERROR: 不能进入反思：任务结论未齐（"
                f"{len(completed_ids)}/{k}）。缺 {format_id_list(steps, missing)}。"
            )
        return steps, completed_ids

    m = PHASE_TASK_RE.match(phase or "")
    if not m:
        die(f"ERROR: --phase 非法（只接受 task-N 或 reflection）：{phase}")

    n = int(m.group(1))
    if n < 1 or n > k:
        die(f"ERROR: --phase=task-{n} 超出计划（有效范围 task-1 ~ task-{k}）")

    if n > 1 and not has_prior_evidence(output_dir, log_data, n - 1):
        die(
            f"ERROR: 不能 --phase task-{n}：task-{n - 1} 既没有 search/fetch 记录，"
            f"也没有 {CONCLUSIONS_DIRNAME}/task_{n - 1}.md。\n"
            f"待写 task-{pointer}「{step_title(steps, pointer)}」。"
        )

    return steps, completed_ids


def validate_save_task(output_dir, task_id):
    """save_conclusion.py --type task 硬门：--task-id 必须等于指针。"""
    plan_data = load_plan(output_dir)
    if plan_data is None:
        die(f"ERROR: 未找到 outputs/{PLAN_FILENAME}，请回到阶段 3 生成研究任务。")

    steps, _completed_ids, pointer = sync_plan_status(output_dir, plan_data)
    valid_ids = {step_num(s) for s in steps}
    if task_id not in valid_ids:
        die(f"ERROR: --task-id={task_id} 超出计划（有效范围 1 ~ {max_step_num(steps)}）")

    if pointer is not None and task_id != pointer:
        die(f"ERROR: 不能 save task-{task_id}：待写 task-{pointer}「{step_title(steps, pointer)}」。")


def validate_save_reflection(output_dir):
    """save_conclusion.py --type reflection 硬门：任务结论必须已全部齐。"""
    plan_data = load_plan(output_dir)
    if plan_data is None:
        die(f"ERROR: 未找到 outputs/{PLAN_FILENAME}，请回到阶段 3 生成研究任务。")

    steps, completed_ids, _pointer = sync_plan_status(output_dir, plan_data)
    k = max_step_num(steps)
    missing = missing_ids(steps, completed_ids)
    if missing:
        die(
            "ERROR: 不能保存反思：任务结论未齐（"
            f"{len(completed_ids)}/{k}）。缺 {format_id_list(steps, missing)}。"
        )


def render_progress_block(steps, completed_ids, this_phase):
    """生成 search / fetch stdout 里的 progress 文本块。

    「研究进度」直接取本次 --phase 的任务号 N（task-N → N/k）；--phase reflection
    时只有在任务结论已全部齐（硬门已保证）才会调用到这里，所以直接记为 k/k。
    不再单独统计日志里出现过的任务号，避免和「研究中」的号错位。
    """
    k = max_step_num(steps)
    completed = len(completed_ids)
    pointer = first_missing_id(steps, completed_ids)

    m = PHASE_TASK_RE.match(this_phase or "")
    current_num = int(m.group(1)) if m else None
    current_label = (
        f"task-{current_num}「{step_title(steps, current_num)}」"
        if current_num is not None
        else "全局反思"
    )

    reached = current_num if current_num is not None else k

    lines = []
    header = f"研究进度：{reached}/{k}，完成进度：{completed}/{k}"
    if pointer is not None:
        header += f"，待写：task-{pointer}"
    lines.append(header)
    lines.append(f"研究中：{current_label}")

    if completed_ids:
        lines.append("已完成：")
        for n in sorted(completed_ids):
            lines.append(f"  task-{n}「{step_title(steps, n)}」")

    shown = set(completed_ids)
    if pointer is not None:
        shown.add(pointer)
    if current_num is not None:
        shown.add(current_num)
    not_started = sorted(step_num(s) for s in steps if step_num(s) not in shown)
    if not_started:
        lines.append("未开始：")
        for n in not_started:
            lines.append(f"  task-{n}「{step_title(steps, n)}」")

    lines.append("结论保存：save_conclusion.py")
    return "\n".join(lines)
