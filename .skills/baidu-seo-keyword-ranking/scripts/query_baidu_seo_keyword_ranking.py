#!/usr/bin/env python3
"""
Query Baidu PC keyword ranking data for a domain.

Usage:
    python3 query_baidu_seo_keyword_ranking.py --domain "www.jumdata.com" [--catalog "/"] [--page "1"]

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


ENDPOINT = "https://app-dvtmyuucfs3l-api-DLEO4zmpN5ja-gateway.appmiaoda.com/seo/baidu/pc/keyword"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True, help="查询的域名")
    p.add_argument("--catalog", help="可选，目录名称，默认选择全部数据")
    p.add_argument("--page", help="可选，分页页码，默认第 1 页")
    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main():
    """入口：调用百度PC关键词排名接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    params = {"domain": args.domain}
    if args.catalog:
        params["catalog"] = args.catalog
    if args.page:
        params["page"] = args.page

    payload = urllib.parse.urlencode(params).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
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
        fail(f"API error {body.get('code')}: {body.get('msg', '')}")

    print(json.dumps({"status": "succeed", "result": body.get("data", {})}))


if __name__ == "__main__":
    main()
