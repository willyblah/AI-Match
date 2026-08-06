#!/usr/bin/env python3
"""Verify an SMS verification code and print one JSON result."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-Xa6JZxjyqK0a-gateway.appmiaoda.com/v1/code/verify_message_code"


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
    """入口：校验短信验证码并打印结果。"""
    parser = argparse.ArgumentParser(description="Verify an SMS verification code and print one JSON result.")
    parser.add_argument("--session-id", required=True, help="sessionId returned by send_sms_code.py.")
    parser.add_argument("--code", required=True, help="Verification code entered by the user.")
    parser.add_argument("--mobile", required=True, help="Mobile phone number the code was sent to.")
    args = parser.parse_args()

    payload = {"sessionId": args.session_id, "code": args.code, "mobile": args.mobile}

    data = post_json(payload)
    if data.get("status") != 0:
        die(f"Verification failed {data.get('status')}: {data.get('msg') or data.get('message')}")

    print(json.dumps({"status": "succeed", "msg": data.get("msg")}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
