#!/usr/bin/env python3
"""Call the express tracking (kdi) API and print one JSON result."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-AalZz7v4QEGL-gateway.appmiaoda.com/kdi"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def main():
    """入口：查询快递物流轨迹并打印结果。"""
    parser = argparse.ArgumentParser(description="Query express tracking info and print one JSON result.")
    parser.add_argument("--no", required=True,
                         help='Express tracking number. For SF Express use "number:last4digits".')
    parser.add_argument(
        "--type",
        help="Express company short code (e.g. ZTO). Optional if it can be inferred from --no.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    params = {"no": args.no}
    if args.type:
        params["type"] = args.type
    endpoint = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"

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
