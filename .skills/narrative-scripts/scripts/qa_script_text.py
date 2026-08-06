#!/usr/bin/env python3
"""QA Markdown node-by-node narrative script text."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
TABLE_HEADING_RE = re.compile(r"^##\s+.*(?:\u8282\u70b9.*\u8df3\u8f6c|jump)", re.I)
ENDING_TYPE_RE = re.compile(r"\*\*[^*]*(?:\u7ed3\u5c40\u7c7b\u578b|ending\s*type)\s*[:\uff1a]\s*([^*]+?)\s*\*\*", re.I)
OPTION_MARKER_RE = re.compile(r"^\s*\*\*[^*]*(?:\u9009\u9879|choices?)\s*[:\uff1a]\s*\*\*\s*$", re.I)
ARROWS = ("\u2192", "->")
ENDING_MARKERS = ("\uff08\u7ed3\u5c40\uff09", "(\u7ed3\u5c40)", "(ending)")
JUMP_RE = re.compile(r"^\s*(?:\u2192|->)\s*([a-z][a-z0-9_]*)\s*$")


@dataclass
class Choice:
    source: str
    text: str
    target: str
    line: int


@dataclass
class Node:
    id: str
    line: int
    raw_heading: str
    is_ending: bool = False
    ending_type: str | None = None
    body: list[tuple[int, str]] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def split_body_and_table(lines: list[str]) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    table_start = None
    for idx, line in enumerate(lines):
        if TABLE_HEADING_RE.match(line.strip()):
            table_start = idx
            break
    numbered = [(idx + 1, line.rstrip("\n")) for idx, line in enumerate(lines)]
    if table_start is None:
        return numbered, []
    return numbered[:table_start], numbered[table_start:]


def parse_heading(raw: str) -> tuple[str, bool]:
    heading = raw.strip()
    lower = heading.lower()
    is_ending = False
    for marker in ENDING_MARKERS:
        if marker.lower() in lower:
            is_ending = True
            heading = heading.replace(marker, "").replace(marker.upper(), "")
            lower = heading.lower()
    node_id = heading.strip()
    return node_id, is_ending


def parse_nodes(body_lines: list[tuple[int, str]], rep: Reporter) -> list[Node]:
    nodes: list[Node] = []
    current: Node | None = None

    for line_no, line in body_lines:
        match = HEADING_RE.match(line.strip())
        if match:
            node_id, is_ending = parse_heading(match.group(1))
            current = Node(id=node_id, line=line_no, raw_heading=match.group(1), is_ending=is_ending)
            nodes.append(current)
            continue
        if current is not None:
            current.body.append((line_no, line))

    for node in nodes:
        if not ID_RE.fullmatch(node.id):
            rep.error(f"line {node.line}: invalid node ID '{node.raw_heading}'")
        parse_node_body(node, rep)
    return nodes


def parse_node_body(node: Node, rep: Reporter) -> None:
    in_options = False
    for line_no, raw in node.body:
        line = raw.strip()
        if not line:
            continue
        if OPTION_MARKER_RE.match(line):
            in_options = True
            continue
        ending_match = ENDING_TYPE_RE.search(line)
        if ending_match:
            node.is_ending = True
            node.ending_type = ending_match.group(1).strip()
            continue
        choice = parse_choice_line(line, node.id, line_no)
        if choice:
            if not in_options:
                rep.warn(f"line {line_no}: choice appears before an options marker in node '{node.id}'")
            node.choices.append(choice)
            continue
        jump_match = JUMP_RE.match(line)
        if jump_match:
            node.choices.append(Choice(source=node.id, text="", target=jump_match.group(1), line=line_no))
            continue


def parse_choice_line(line: str, source: str, line_no: int) -> Choice | None:
    stripped = line.strip()
    if not stripped.startswith(("-", "*")):
        return None
    content = stripped[1:].strip()
    arrow = next((item for item in ARROWS if item in content), None)
    if not arrow:
        return None
    text, target_part = content.split(arrow, 1)
    target_match = re.search(r"([a-z][a-z0-9_]*)", target_part)
    if not target_match:
        return Choice(source=source, text=text.strip(), target="", line=line_no)
    return Choice(source=source, text=text.strip(), target=target_match.group(1), line=line_no)


def parse_jump_table(table_lines: list[tuple[int, str]], rep: Reporter) -> list[Choice]:
    rows: list[Choice] = []
    if not table_lines:
        rep.error("missing '节点跳转关系一览' jump table")
        return rows

    for line_no, raw in table_lines:
        line = raw.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        source, text, target_cell = cells[:3]
        if not ID_RE.fullmatch(source):
            continue
        target_match = re.search(r"([a-z][a-z0-9_]*)", target_cell)
        target = target_match.group(1) if target_match else ""
        rows.append(Choice(source=source, text=text, target=target, line=line_no))

    if not rows:
        rep.error("jump table has no valid rows")
    return rows


def validate(nodes: list[Node], table_rows: list[Choice], rep: Reporter, strict_text: bool = False) -> dict[str, Any]:
    node_ids: set[str] = set()
    duplicates: set[str] = set()
    graph: dict[str, set[str]] = defaultdict(set)
    endings: set[str] = set()
    all_choices: list[Choice] = []

    if not nodes:
        rep.error("no script nodes found; expected headings like '### start'")
        return stats(nodes, table_rows, set(), {})

    for node in nodes:
        if node.id in node_ids:
            duplicates.add(node.id)
        node_ids.add(node.id)
    for node_id in sorted(duplicates):
        rep.error(f"duplicate node ID '{node_id}'")

    if nodes[0].id != "start":
        rep.warn(f"first node is '{nodes[0].id}', but 'start' should be first")
    if "start" not in node_ids:
        rep.error("missing required start node 'start'")

    for node in nodes:
        if node.is_ending:
            endings.add(node.id)
            if node.choices:
                rep.error(f"node '{node.id}' is an ending but has outgoing choices")
            if not node.ending_type:
                rep.warn(f"ending node '{node.id}' is missing an ending type line")
        elif not node.choices:
            rep.error(f"non-ending node '{node.id}' has no outgoing choices")

        for choice in node.choices:
            all_choices.append(choice)
            if not choice.target:
                rep.error(f"line {choice.line}: choice in node '{node.id}' has no target")
                continue
            graph[node.id].add(choice.target)
            if choice.target not in node_ids:
                rep.error(f"line {choice.line}: node '{node.id}' points to missing node '{choice.target}'")

        if not has_story_text(node):
            rep.warn(f"node '{node.id}' has no narration or dialogue text")

    validate_table_rows(table_rows, all_choices, node_ids, rep, strict_text)
    validate_reachability(node_ids, graph, endings, rep)
    return stats(nodes, table_rows, endings, graph)


def validate_table_rows(
    table_rows: list[Choice],
    body_choices: list[Choice],
    node_ids: set[str],
    rep: Reporter,
    strict_text: bool,
) -> None:
    body_counter = Counter((c.source, c.target) for c in body_choices)
    table_counter = Counter((r.source, r.target) for r in table_rows)

    for row in table_rows:
        if row.source not in node_ids:
            rep.error(f"line {row.line}: jump table source node '{row.source}' does not exist")
        if not row.target:
            rep.error(f"line {row.line}: jump table row has no target")
        elif row.target not in node_ids:
            rep.error(f"line {row.line}: jump table target node '{row.target}' does not exist")

    for edge, count in sorted(body_counter.items()):
        table_count = table_counter.get(edge, 0)
        if table_count != count:
            rep.error(
                f"jump table mismatch for {edge[0]} -> {edge[1]}: body has {count}, table has {table_count}"
            )

    for edge, count in sorted(table_counter.items()):
        body_count = body_counter.get(edge, 0)
        if body_count != count:
            rep.error(
                f"jump table mismatch for {edge[0]} -> {edge[1]}: table has {count}, body has {body_count}"
            )

    if strict_text:
        choices_by_edge: dict[tuple[str, str], list[Choice]] = defaultdict(list)
        for choice in body_choices:
            choices_by_edge[(choice.source, choice.target)].append(choice)
        for row in table_rows:
            options = choices_by_edge.get((row.source, row.target), [])
            if options and not any(text_compatible(row.text, choice.text) for choice in options):
                rep.warn(
                    f"line {row.line}: table text '{row.text}' is hard to match to body choices for {row.source} -> {row.target}"
                )


def validate_reachability(
    node_ids: set[str],
    graph: dict[str, set[str]],
    endings: set[str],
    rep: Reporter,
) -> None:
    if "start" not in node_ids:
        return
    reachable = reachable_nodes("start", graph)
    for node_id in sorted(node_ids - reachable):
        rep.warn(f"node '{node_id}' is unreachable from start")
    if not (reachable & endings):
        rep.error("no ending node is reachable from start")


def reachable_nodes(start: str, graph: dict[str, set[str]]) -> set[str]:
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for target in graph.get(node, set()):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def has_story_text(node: Node) -> bool:
    for _, raw in node.body:
        line = raw.strip()
        if not line or line == "---":
            continue
        if OPTION_MARKER_RE.match(line) or parse_choice_line(line, node.id, 0):
            continue
        if line.startswith("|"):
            continue
        return True
    return False


def normalized_chars(text: str) -> set[str]:
    chars = set()
    for ch in text.lower():
        if ch.isspace():
            continue
        if unicodedata.category(ch).startswith("P"):
            continue
        chars.add(ch)
    return chars


def text_compatible(short: str, long: str) -> bool:
    short_norm = "".join(sorted(normalized_chars(short)))
    long_norm = "".join(sorted(normalized_chars(long)))
    if not short_norm or not long_norm:
        return False
    short_set = set(short_norm)
    long_set = set(long_norm)
    if short_set <= long_set or long_set <= short_set:
        return True
    overlap = len(short_set & long_set)
    return overlap / max(1, min(len(short_set), len(long_set))) >= 0.55


def stats(
    nodes: list[Node],
    table_rows: list[Choice],
    endings: set[str],
    graph: dict[str, set[str]],
) -> dict[str, Any]:
    body_choices = sum(len(node.choices) for node in nodes)
    return {
        "nodes": len(nodes),
        "body_choices": body_choices,
        "table_rows": len(table_rows),
        "endings": len(endings),
        "edges": sum(len(targets) for targets in graph.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="QA a Markdown node-by-node narrative script.")
    parser.add_argument("script", type=Path)
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    parser.add_argument("--strict-text", action="store_true", help="warn when table text does not resemble body choice text")
    args = parser.parse_args()

    rep = Reporter()
    try:
        lines = args.script.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        print(f"ERROR: failed to read script: {exc}", file=sys.stderr)
        return 2

    body_lines, table_lines = split_body_and_table(lines)
    nodes = parse_nodes(body_lines, rep)
    table_rows = parse_jump_table(table_lines, rep)
    report_stats = validate(nodes, table_rows, rep, strict_text=args.strict_text)

    if args.json:
        print(
            json.dumps(
                {"errors": rep.errors, "warnings": rep.warnings, "stats": report_stats},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for error in rep.errors:
            print(f"ERROR: {error}")
        for warning in rep.warnings:
            print(f"WARNING: {warning}")
        if not rep.errors and not rep.warnings:
            print("OK: script text passed QA")
        elif not rep.errors:
            print(f"OK: script text passed with {len(rep.warnings)} warning(s)")
        print(
            "STATS: "
            f"{report_stats['nodes']} nodes, "
            f"{report_stats['body_choices']} body choices, "
            f"{report_stats['table_rows']} table rows, "
            f"{report_stats['endings']} endings"
        )

    return 1 if rep.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
