#!/usr/bin/env python3
"""Call the AI PPT generation API and print one JSON line."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-l9nZz8ro3my9-gateway.appmiaoda.com/v2/tools/ai_command_ppt/command_ppt"


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_inner_result(event):
    """解析事件中的内层结果数据。

    兼容两种响应格式：
    1. event.data.result (JSON string) -> 内含 result_type 字段
    2. event.data.content (string/dict) -> 最终结果直接在 content 里
    """
    data = event.get("data")
    if not isinstance(data, dict):
        return None

    # 优先尝试 data.result 格式
    raw = data.get("result")
    if isinstance(raw, str) and raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

    # 兼容 data.content 格式（generate_ppt 使用此路径）
    content = data.get("content")
    if isinstance(content, str) and content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_result": content}
    elif isinstance(content, dict):
        return content

    if isinstance(raw, str) and raw:
        return {"raw_result": raw}
    return None


def call_api(args):
    """调用 AI PPT 生成接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    body = json.dumps({"query": args.query}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )

    build_events = []
    final_result = None
    last_inner = None
    raw_events = []

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    fail("Stream line is not valid JSON: " + line[:500])
                raw_events.append(event)
                if event.get("errno") not in (None, 0):
                    fail("API error %s: %s" % (event.get("errno"), event.get("errMsg", "")))
                inner = parse_inner_result(event)
                if not isinstance(inner, dict):
                    continue
                data = inner.get("data") if isinstance(inner.get("data"), dict) else inner
                last_inner = data
                result_type = data.get("result_type") if isinstance(data, dict) else None
                if result_type == 1:
                    build_events.append(data)
                elif result_type == 0:
                    final_result = data
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, body[:1000]))
    except urllib.error.URLError as exc:
        fail("Network error: " + str(exc.reason))
    except TimeoutError:
        fail("Request timed out")

    # 部分响应不带 result_type==0 的终止事件，最终结果直接在最后一条数据中，
    # 此时用最后一条成功解析的内层数据兜底。
    if final_result is None:
        final_result = last_inner

    if final_result is None:
        fail("API stream ended without final result")

    return {
        "ppt_url": final_result.get("ppt_url") or final_result.get("pptUrl") or final_result.get("download_url"),
        "cover_urls": final_result.get("cover_urls") or final_result.get("cover_url") or final_result.get("coverUrl"),
        "title": final_result.get("title"),
        "final": final_result,
        "build_events": build_events,
        "raw_event_count": len(raw_events),
    }


def main():
    """入口：生成 AI PPT 并输出 JSON 结果。"""
    parser = argparse.ArgumentParser(description="Generate a PPT from a topic query.")
    parser.add_argument("--query", required=True, help="PPT 主题内容")
    parser.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    args = parser.parse_args()

    result = call_api(args)
    print(json.dumps({"status": "succeed", "result": result}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
