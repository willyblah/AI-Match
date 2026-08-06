#!/usr/bin/env python3
"""Call the webpage summarizer component and print one JSON line."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-DY8MNXjBpKAa-gateway.appmiaoda.com/v2/components/c-wf-e1bc471f-1d33-4df1-ab42-87800e89c1ad"


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def load_json(resp):
    """读取响应内容并解析为 JSON。"""
    text = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fail("Response is not valid JSON: " + text[:500])


def call_api(args):
    """调用网页摘要组件接口并返回响应结果。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    payload = {
        "parameters": {
            "_sys_origin_query": args.query,
            "web_url": [args.url],
        }
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            body = load_json(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, detail[:1000]))
    except urllib.error.URLError as exc:
        fail("Network error: " + str(exc.reason))
    except TimeoutError:
        fail("Request timed out")

    content = body.get("content") if isinstance(body, dict) else None
    event = content[0].get("event") if content else None
    if isinstance(event, dict) and event.get("error_code_int") not in (0, None):
        fail("API error %s: %s" % (event.get("error_code_int"), event.get("error_message", "")))

    output = None
    try:
        output = content[0]["raw_data"]["origin_response"]["node_content"][0]["outputs"]["output"]
    except (KeyError, IndexError, TypeError):
        output = None

    return {"output": output, "raw": body}


def main():
    """入口：解析命令行参数，调用网页摘要接口并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="Summarize a webpage via the platform component.")
    parser.add_argument("--query", required=True, help="用户诉求描述，例如“请帮我分析下网页的内容”")
    parser.add_argument("--url", required=True, help="待分析的网页 URL（当前只支持一个地址）")
    parser.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    args = parser.parse_args()

    result = call_api(args)
    print(json.dumps({"status": "succeed", "result": result}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
