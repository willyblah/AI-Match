#!/usr/bin/env python3
"""Send an SMS verification code and print one JSON result."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-W9z3M74x6ZNL-gateway.appmiaoda.com/v1/code/send_message"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def post_json(payload):
    """发送 JSON 请求并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        die(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        die(f"Request failed: {exc.reason}")


def main():
    """入口：发送短信验证码并打印结果。"""
    parser = argparse.ArgumentParser(description="Send an SMS verification code and print one JSON result.")
    parser.add_argument("--mobile", required=True, help="Mobile phone number receiving the SMS code.")
    parser.add_argument("--session-id", help="Optional existing sessionId.")
    args = parser.parse_args()

    payload = {"mobile": args.mobile}
    if args.session_id:
        payload["sessionId"] = args.session_id

    data = post_json(payload)
    if data.get("status") != 0:
        die(f"API error {data.get('status')}: {data.get('msg') or data.get('message')}")

    print(json.dumps({"status": "succeed", "data": data.get("data", {})}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
