#!/usr/bin/env python3
"""
Query phone number location (province-city), original ISP, and virtual-ISP flag.

Usage:
    python3 call_phone_location.py --mobile-number 13800138000

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one-line JSON: {"status": "succeed", "result": {...}}
    1 - API or argument error, prints one-line JSON: {"status": "error", "message": "..."}
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error


ENDPOINT = "https://app-dvtmyuucfs3l-api-ELbWz8OmB58Y-gateway.appmiaoda.com/mobile/area"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--mobile-number", dest="mobile_number", required=True, help="手机号，例如：13800138000")
    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main():
    """入口：调用手机号归属地查询接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    # 注意：mobile_number 通过 URL Query 参数传递，请求体为空
    params = urllib.parse.urlencode({"mobile_number": args.mobile_number})
    url = f"{ENDPOINT}?{params}"

    req = urllib.request.Request(
        url,
        method="POST",
        data=b"",
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        fail(f"HTTP {e.code}: {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        fail(f"Network error: {e}")

    if body.get("code") != 200:
        fail(f"API error {body.get('code')}: {body.get('msg')}")

    print(json.dumps({"status": "succeed", "result": body.get("data", {})}))


if __name__ == "__main__":
    main()
