#!/usr/bin/env python3
"""
Query Baidu Baike (encyclopedia) lemma content.

Usage:
    python3 call_baike_lemma.py --search-type lemmaTitle --search-key "人工智能"
    python3 call_baike_lemma.py --search-type lemmaId --search-key "12345"

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


ENDPOINT = "https://app-dvtmyuucfs3l-api-wLNdo2j5eQWa-gateway.appmiaoda.com/v2/baike/lemma/get_content"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--search-type", dest="search_type", required=True,
                    choices=["lemmaTitle", "lemmaId"], help="检索类型")
    p.add_argument("--search-key", dest="search_key", required=True, help="检索关键字")
    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main():
    """入口：调用百度百科查询接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    params = urllib.parse.urlencode({
        "search_type": args.search_type,
        "search_key": args.search_key,
    })
    url = f"{ENDPOINT}?{params}"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
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

    print(json.dumps({"status": "succeed", "result": body.get("result", body)}))


if __name__ == "__main__":
    main()
