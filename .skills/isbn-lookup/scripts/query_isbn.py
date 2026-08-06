#!/usr/bin/env python3
"""查询 ISBN 图书信息。"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-ra5EZDjVKbza-gateway.appmiaoda.com/isbn/query"


def call_api(isbn):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        raise RuntimeError("INTEGRATIONS_API_KEY is required")

    query = urllib.parse.urlencode({"isbn": isbn})
    request = urllib.request.Request(
        ENDPOINT + "?" + query,
        data=b"",
        method="POST",
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def main():
    """入口：解析参数，调用接口并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="Query book information by ISBN.")
    parser.add_argument("--isbn", required=True, help="10-digit or 13-digit ISBN")
    args = parser.parse_args()

    try:
        result = call_api(args.isbn)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print("HTTP error {}: {}".format(exc.code, detail), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
