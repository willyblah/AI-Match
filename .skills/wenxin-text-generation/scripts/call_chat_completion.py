#!/usr/bin/env python3
"""Call Wenxin (ERNIE) text generation and aggregate the SSE response."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-zYkZz8qovQ1L-gateway.appmiaoda.com/v2/chat/completions"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


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
    """入口：解析命令行参数，调用文心对话接口并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="Call Wenxin text generation and print one JSON result.")
    parser.add_argument("--prompt", help="Single-turn user prompt. Ignored when --messages is provided.")
    parser.add_argument("--system", help="Optional system prompt (only used with --prompt).")
    parser.add_argument("--messages", help="JSON array of chat messages, overrides --prompt/--system.")
    parser.add_argument("--enable-thinking", action="store_true", help="Enable thinking mode.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    if args.messages:
        try:
            messages = json.loads(args.messages)
        except json.JSONDecodeError as exc:
            die(f"Invalid JSON for --messages: {exc}")
    elif args.prompt:
        messages = []
        if args.system:
            messages.append({"role": "system", "content": args.system})
        messages.append({"role": "user", "content": args.prompt})
    else:
        die("Either --prompt or --messages is required")

    body = {"messages": messages, "enable_thinking": args.enable_thinking}

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
    finish_reason = None

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            for data in iter_sse(response):
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                for choice in chunk.get("choices", []) or []:
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if content:
                        content_parts.append(content)
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        die(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        die(f"Request failed: {exc.reason}")

    print(json.dumps({
        "status": "succeed",
        "content": "".join(content_parts),
        "finish_reason": finish_reason,
    }, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
