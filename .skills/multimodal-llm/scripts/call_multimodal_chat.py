#!/usr/bin/env python3
"""Call the multimodal (text + image) chat completion API and aggregate the SSE response."""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-k93RZBjPykEa-gateway.appmiaoda.com/v2/chat/completions"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def image_to_data_url(path):
    """读取本地图片并编码为 data URL。"""
    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type:
        mime_type = "image/jpeg"
    try:
        with open(path, "rb") as fh:
            encoded = base64.b64encode(fh.read()).decode("ascii")
    except OSError as exc:
        die(f"Failed to read image {path}: {exc}")
    return f"data:{mime_type};base64,{encoded}"


def iter_sse(response):
    """逐条解析 SSE 响应流，产出每个事件的数据内容。"""
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        yield data


def main():
    """入口：调用多模态对话接口并汇总流式响应。"""
    parser = argparse.ArgumentParser(description="Call the multimodal chat completion API and print one JSON result.")
    parser.add_argument("--text", help="Text prompt. Ignored when --messages is provided.")
    parser.add_argument(
        "--image", action="append", default=[],
        help="Local image path, can repeat. Encoded to base64 internally.",
    )
    parser.add_argument("--image-url", action="append", default=[], help="Public image URL, can repeat.")
    parser.add_argument("--messages", help="JSON array of chat messages, overrides --text/--image/--image-url.")
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
    else:
        if not args.text:
            die("--text is required when --messages is not provided")
        content = [{"type": "text", "text": args.text}]
        for path in args.image:
            content.append({"type": "image_url", "image_url": {"url": image_to_data_url(path)}})
        for url in args.image_url:
            content.append({"type": "image_url", "image_url": {"url": url}})
        messages = [{"role": "user", "content": content}]

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
                    piece = delta.get("content")
                    if piece:
                        content_parts.append(piece)
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
