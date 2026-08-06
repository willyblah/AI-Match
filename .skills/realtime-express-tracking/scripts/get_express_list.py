#!/usr/bin/env python3
"""Call the express company list API and print one JSON result."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-V9gDz8wo0V5L-gateway.appmiaoda.com/getExpressList"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def main():
    """入口：获取快递公司列表并打印结果。"""
    parser = argparse.ArgumentParser(description="Get the express company list and print one JSON result.")
    parser.add_argument("--type", help='Express company short code (e.g. "ZTO"), or "ALL"/omit for all companies.')
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    endpoint = ENDPOINT
    if args.type:
        endpoint = f"{ENDPOINT}?{urllib.parse.urlencode({'type': args.type})}"

    request = urllib.request.Request(
        endpoint,
        method="GET",
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
        die(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        die(f"Request failed: {exc.reason}")

    if data.get("status") != "200":
        die(f"API error {data.get('status')}: {data.get('msg')}")

    print(json.dumps(
        {"status": "succeed", "result": data.get("result", {})},
        ensure_ascii=False,
        separators=(",", ":"),
    ))


if __name__ == "__main__":
    main()
