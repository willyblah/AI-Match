#!/usr/bin/env python3
"""查询驾考题库试题。"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-o9wN0mk1DAPa-gateway.appmiaoda.com/driverexam/query"


def call_api(params):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        raise RuntimeError("INTEGRATIONS_API_KEY is required")

    query = urllib.parse.urlencode(params)
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
    parser = argparse.ArgumentParser(description="Query driving exam questions.")
    parser.add_argument("--type", required=True, help="Vehicle type, for example C1, C2, B2")
    parser.add_argument("--subject", default="1", help="Subject: 1 or 4")
    parser.add_argument("--pagesize", default="1", help="Page size")
    parser.add_argument("--pagenum", help="Page number")
    parser.add_argument("--sort", default="normal", help="Sort mode: normal or rand")
    parser.add_argument("--chapter", help="Chapter number")
    args = parser.parse_args()

    params = {
        "type": args.type,
        "subject": args.subject,
        "pagesize": args.pagesize,
        "sort": args.sort,
    }
    if args.pagenum:
        params["pagenum"] = args.pagenum
    if args.chapter:
        params["chapter"] = args.chapter

    try:
        result = call_api(params)
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
