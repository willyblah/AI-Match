#!/usr/bin/env python3
"""
Query Baidu Map administrative region info.

Usage:
    python3 call_baidu_region_search.py --keyword "山东省" \
        [--sub-admin 0] [--extensions-code 0] [--boundary 0] [--boundarycode "370000"]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one-line JSON: {"status":"succeed","result":{...}}
    1 - API or argument error, prints one-line JSON on stderr
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-DYJwn2VZXvEa-gateway.appmiaoda.com/api_region_search/v1/"


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser(description="Baidu region search")
    p.add_argument("--keyword", required=True, help="行政区名称或 adcode")
    p.add_argument("--sub-admin", default="0", help="0-3 返回下级层级数")
    p.add_argument("--extensions-code", default="0", help="是否返回国标行政区划编码 0/1")
    p.add_argument("--boundary", default="0", help="是否返回边界数据 0/1")
    p.add_argument("--boundarycode", help="需要返回边界的行政区划编码")
    p.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    return p.parse_args()


def call_api(args):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    params = {
        "keyword": args.keyword,
        "sub_admin": args.sub_admin,
        "extensions_code": args.extensions_code,
        "boundary": args.boundary,
    }
    if args.boundarycode:
        params["boundarycode"] = args.boundarycode

    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, detail[:1000]))
    except urllib.error.URLError as exc:
        fail("Network error: " + str(exc.reason))

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        fail("Response is not valid JSON: " + body[:500])


def main():
    """入口：查询行政区划信息。"""
    args = parse_args()
    result = call_api(args)
    if result.get("status") not in (0, None):
        fail("API error %s" % result.get("status"))
    print(json.dumps({"status": "succeed", "result": result}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
