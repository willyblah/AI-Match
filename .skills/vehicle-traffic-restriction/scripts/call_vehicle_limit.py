#!/usr/bin/env python3
"""
Query vehicle traffic restriction (limit) rules by city, via jisuapivehiclelimit API.

Usage:
    # Query restriction rule for a city on a given date
    python3 call_vehicle_limit.py query --city hangzhou --date 2026-04-27

    # Get the list of supported cities
    python3 call_vehicle_limit.py cities

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


QUERY_ENDPOINT = "https://app-dvtmyuucfs3l-api-pLVzAxRQyMWL-gateway.appmiaoda.com/vehiclelimit/query"
CITY_ENDPOINT = "https://app-dvtmyuucfs3l-api-DYJwnJVBwb4a-gateway.appmiaoda.com/vehiclelimit/city"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)

    q = sub.add_parser("query", help="查询指定城市在特定日期的限行规则")
    q.add_argument("--city", required=True, help="城市代号，如 beijing、hangzhou")
    q.add_argument("--date", required=True, help="查询日期，格式 YYYY-MM-DD")

    sub.add_parser("cities", help="获取支持限行查询的城市列表")

    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def post(url: str, api_key: str, params: dict | None = None):
    """向上游发起 POST 请求并返回解析后的 JSON body。"""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        fail(f"HTTP {e.code}: {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        fail(f"Network error: {e}")


def main():
    """入口：按 mode 调用限行查询或城市列表接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    if args.mode == "query":
        body = post(QUERY_ENDPOINT, api_key, {"city": args.city, "date": args.date})
    else:
        body = post(CITY_ENDPOINT, api_key)

    if body.get("status") != 0:
        fail(f"API error status: {body.get('status')}, msg: {body.get('msg', '')}")

    print(json.dumps({"status": "succeed", "result": body.get("result")}))


if __name__ == "__main__":
    main()
