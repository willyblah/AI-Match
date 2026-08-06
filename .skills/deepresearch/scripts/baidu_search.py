#!/usr/bin/env python3
"""Call the Baidu AI search (Qianfan ai_search) API and print one JSON result.

Observe:
    {
        "progress", "status", "log_file", "log_schema",
        "this_call": {"phase", "query", "search_results": [{"url", "title", "date", "website", "rerank_score", "preview"}]}
    }
Log:
    <project_root>/outputs/research/research_log.json
        {
        "search": [{"phase", "query", "recency_filter", "results": [{"url", "title", "snippet", "date", "website", ...}]}],
        "fetch": [{"phase", "url", "status", "content_file"}]
    }

--phase 必须是 研究任务.json 里的 task-N 或 reflection：
- 无 JSON / phase 非法 / N 越界 / 跳号（N-1 既无 log 也无结论文件）→ die，不发起请求。
- --phase reflection 但任务结论未齐（按 conclusions/task_N.md 是否存在判定）→ die。
- 有结论文件的任务即视为 completed（不要求经由 save_conclusion.py 写入），只有指针
  （第一个没有结论文件的任务）才会被标 in_progress；超前的 --phase 只写 log，不改 JSON。
详见 task_progress.py。
"""

import argparse
import http.client
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import task_progress as tp


# ENDPOINT = "https://app-dbg3596z1ce9-api-ELbWqrZ1krJY-gateway-evaluation.appmiaoda.com/v2/ai_search/chat/completions"
ENDPOINT = "https://api-rY7JZ6jqr6dL@app-dvtmyuucfs3l-api-ELbWqrZ1krJY-gateway.appmiaoda.com/v2/ai_search/chat/completions"

# 脚本位置 → 项目根（向上 3 级）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
LOG_DIR = os.path.join(DEFAULT_PROJECT_ROOT, "outputs")
RESEARCH_DIR = os.path.join(LOG_DIR, "research")

FIXED_TOP_K = 20
SNIPPET_PREVIEW_LEN = 150


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def load_log():
    """读取 log 文件，返回 (path, {search: [...], fetch: [...]}) 结构。"""
    log_file = os.path.join(RESEARCH_DIR, "research_log.json")
    log_data = {"search": [], "fetch": []}
    if os.path.isfile(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                if isinstance(loaded.get("search"), list):
                    log_data["search"] = loaded["search"]
                if isinstance(loaded.get("fetch"), list):
                    log_data["fetch"] = loaded["fetch"]
        except (json.JSONDecodeError, OSError) as exc:
            print(f"WARNING: 读取 log 文件失败，使用新文件: {exc}", file=sys.stderr)
    return log_file, log_data


def save_log(log_file, log_data):
    """将 log 数据写回文件。"""
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def build_search_results(references):
    """保留 API 全部字段，snippet 存完整，剔除 content 字段。"""
    results = []
    for ref in references:
        entry = {k: v for k, v in ref.items() if k != "content"}
        entry["snippet"] = ref.get("snippet") or ref.get("content", "")
        results.append(entry)
    return results


def main():
    """入口：解析参数，调用搜索接口并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="Call Baidu AI search and print one JSON result.")
    parser.add_argument("--query", help="Single user query. Ignored when --messages is provided.")
    parser.add_argument("--messages", help="JSON array of {role, content} messages, overrides --query.")
    parser.add_argument("--resource-type", action="append", choices=["web", "video"], default=[],
                         help="Resource type to include, can repeat (web/video).")
    parser.add_argument("--search-recency-filter", choices=["week", "month", "semiyear", "year"],
                         help="Time filter for search recency.")
    parser.add_argument("--phase", required=True,
                         help="研究任务.json 里的 task-N 或 reflection（不是全局 todo 序号）")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    if args.messages:
        try:
            messages = json.loads(args.messages)
        except json.JSONDecodeError as exc:
            die(f"Invalid JSON for --messages: {exc}")
    elif args.query:
        messages = [{"role": "user", "content": args.query}]
    else:
        die("Either --query or --messages is required")

    # 阶段 4/5 进度硬门（无 JSON / phase 非法 / 越界 / 跳号 / reflection 未齐）：
    # 在发起网络请求前校验，避免违规调用浪费配额。
    log_file, log_data = load_log()
    steps, completed_ids = tp.validate_phase_for_research(LOG_DIR, args.phase, log_data)

    body = {"messages": messages}
    body["resource_type_filter"] = [
        {"type": t, "top_k": FIXED_TOP_K}
        for t in (args.resource_type or ["web"])
    ]
    if args.search_recency_filter:
        body["search_recency_filter"] = args.search_recency_filter

    # Strip userinfo from ENDPOINT to avoid IDNA label-too-long errors
    _parsed_ep = urllib.parse.urlsplit(ENDPOINT)
    _netloc = _parsed_ep.hostname + (f":{_parsed_ep.port}" if _parsed_ep.port else "")
    _clean_endpoint = urllib.parse.urlunsplit((
        _parsed_ep.scheme, _netloc, _parsed_ep.path, _parsed_ep.query, ""
    ))

    request = urllib.request.Request(
        _clean_endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 402:
            die(f"HTTP 402: 账户余额不足 - {detail}")
        if exc.code == 429:
            die(f"HTTP 429: 调用配额超限 - {detail}")
        die(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        die(f"Search request failed: {exc.reason}")
    except http.client.HTTPException as exc:
        # IncompleteRead / ChunkedEncodingError 等协议层异常，兜底避免 traceback
        die(f"HTTP protocol error: {type(exc).__name__}: {exc}")

    references = data.get("references", [])
    search_results = build_search_results(references)

    # 追加到 log 文件
    log_data["search"].append({
        "phase": args.phase,
        "query": args.query or json.dumps(messages, ensure_ascii=False),
        "recency_filter": args.search_recency_filter,
        "results": search_results,
    })
    try:
        save_log(log_file, log_data)
    except Exception as exc:
        print(f"WARNING: 写入 log 文件失败: {exc}", file=sys.stderr)

    # 组装进度块（放在 this_call 前）
    progress = tp.render_progress_block(steps, completed_ids, args.phase)

    # 返回给 LLM
    output = {
        "progress": progress,
        "status": "succeed",
        "log_file": os.path.abspath(log_file),
        "log_schema": "{search: [{phase, query, recency_filter, results: [{url, title, snippet, date, website, ...}]}], fetch: [{phase, url, status, content_file}]}",
        "this_call": {
            "phase": args.phase,
            "query": args.query or json.dumps(messages, ensure_ascii=False),
            "search_results": [
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "date": r.get("date", ""),
                    "website": r.get("website", ""),
                    "rerank_score": r.get("rerank_score"),
                    "preview": (r.get("snippet", "") or "")[:SNIPPET_PREVIEW_LEN],
                }
                for r in search_results
            ],
        },
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()