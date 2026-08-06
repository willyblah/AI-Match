#!/usr/bin/env python3
"""Call Baidu AI Search and aggregate the SSE response."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-DYJwo27V8Qya-gateway.appmiaoda.com/v2/ai_search/chat/completions"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_json(value, name):
    """解析 JSON 字符串参数，失败时报错退出。"""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        die(f"Invalid JSON for {name}: {exc}")


def iter_sse(response):
    """迭代解析 SSE 响应流，逐条返回 data 字段内容。"""
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        yield data


def main():
    """入口：解析参数，调用 AI 搜索接口并聚合流式结果输出 JSON。"""
    parser = argparse.ArgumentParser(description="Call Baidu AI Search and print one JSON result.")
    parser.add_argument("--query", help="User search question. Ignored when --messages is provided.")
    parser.add_argument("--messages", help="JSON array of chat messages.")
    parser.add_argument("--instruction", help="Search instruction.")
    parser.add_argument("--enable-deep-search", action="store_true", help="Enable deep search.")
    parser.add_argument("--enable-reasoning", action="store_true",
                         help="Enable reasoning content when supported.")
    parser.add_argument("--enable-followup-queries", action="store_true",
                         help="Return follow-up query suggestions when supported.")
    parser.add_argument("--search-recency-filter", choices=["week", "month", "semiyear", "year"],
                         help="Limit search recency.")
    parser.add_argument("--response-format", choices=["auto", "text", "rich_text"], help="Response format.")
    parser.add_argument("--max-completion-tokens", type=int, help="Maximum completion tokens.")
    parser.add_argument("--resource-type-filter", help="JSON array such as [{\"type\":\"web\",\"top_k\":5}].")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    if args.messages:
        messages = parse_json(args.messages, "--messages")
    elif args.query:
        messages = [{"role": "user", "content": args.query}]
    else:
        die("Either --query or --messages is required")

    body = {"messages": messages}
    optional = {
        "instruction": args.instruction,
        "enable_deep_search": args.enable_deep_search or None,
        "enable_reasoning": args.enable_reasoning or None,
        "enable_followup_queries": args.enable_followup_queries or None,
        "search_recency_filter": args.search_recency_filter,
        "response_format": args.response_format,
        "max_completion_tokens": args.max_completion_tokens,
    }
    body.update({key: value for key, value in optional.items() if value is not None})
    if args.resource_type_filter:
        body["resource_type_filter"] = parse_json(args.resource_type_filter, "--resource-type-filter")

    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )

    content_parts = []
    reasoning_parts = []
    references = []
    followup_queries = []
    chunks = []

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            for data in iter_sse(response):
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    chunks.append({"raw": data})
                    continue
                chunks.append(chunk)
                for choice in chunk.get("choices", []) or []:
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if content:
                        content_parts.append(content)
                    reasoning = delta.get("reasoning_content")
                    if reasoning:
                        reasoning_parts.append(reasoning)
                refs = chunk.get("references")
                if isinstance(refs, list):
                    references = refs
                followups = chunk.get("followup_queries")
                if isinstance(followups, list):
                    followup_queries = followups
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        die(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        die(f"Request failed: {exc.reason}")

    print(json.dumps({
        "status": "succeed",
        "content": "".join(content_parts),
        "reasoning_content": "".join(reasoning_parts),
        "references": references,
        "followup_queries": followup_queries,
        "chunks": chunks,
    }, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
