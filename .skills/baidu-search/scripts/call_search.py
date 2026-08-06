#!/usr/bin/env python3
"""Call the Baidu AI search (Qianfan ai_search) API and print one JSON result."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-rY7JZ6jqr6dL-gateway.appmiaoda.com/v2/ai_search/chat/completions"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def main():
    """入口：解析参数，调用搜索接口并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="Call Baidu AI search and print one JSON result.")
    parser.add_argument("--query", help="Single user query. Ignored when --messages is provided.")
    parser.add_argument("--messages", help="JSON array of {role, content} messages, overrides --query.")
    parser.add_argument("--resource-type", action="append", choices=["web", "video"], default=[],
                         help="Resource type to include, can repeat (web/video).")
    parser.add_argument("--top-k", type=int, help="Max results per resource type (web<=50, video<=10).")
    parser.add_argument("--search-recency-filter", choices=["week", "month", "semiyear", "year"],
                         help="Time filter for search recency.")
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

    body = {"messages": messages}
    if args.resource_type:
        body["resource_type_filter"] = [
            {"type": t, **({"top_k": args.top_k} if args.top_k is not None else {})}
            for t in args.resource_type
        ]
    if args.search_recency_filter:
        body["search_recency_filter"] = args.search_recency_filter

    request = urllib.request.Request(
        ENDPOINT,
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
        die(f"Request failed: {exc.reason}")

    references = data.get("references", [])
    print(json.dumps({"status": "succeed", "references": references}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
