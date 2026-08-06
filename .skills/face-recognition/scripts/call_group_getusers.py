#!/usr/bin/env python3
"""
List users in the Baidu face library and print the API response.

Usage:
    python3 call_group_getusers.py [--start 0] [--length 100]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one line of JSON with the API response
    1 - API or argument error
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error


ENDPOINT = "https://app-dvtmyuucfs3l-api-baBwZEjb7P19-gateway.appmiaoda.com/rest/2.0/face/v3/faceset/group/getusers"


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--length", type=int, default=100)
    return parser.parse_args()


def call_api(api_key: str, payload: dict) -> dict:
    """调用上游接口并返回响应。"""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """入口：解析参数，调用接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    d = call_api(api_key, {"start": args.start, "length": args.length})
    if d.get("error_code"):
        print(f"API error {d['error_code']}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
