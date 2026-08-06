#!/usr/bin/env python3
"""查询企业工商信息。"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-e94GZ5j0Kxja-gateway.appmiaoda.com/business4/get"


def call_api(keyword):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        raise RuntimeError("INTEGRATIONS_API_KEY is required")

    query = urllib.parse.urlencode({"keyword": keyword})
    request = urllib.request.Request(
        ENDPOINT + "?" + query,
        method="GET",
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
    parser = argparse.ArgumentParser(description="Query company business information.")
    parser.add_argument(
        "--keyword", required=True,
        help="Company name, registration number, or unified social credit code",
    )
    args = parser.parse_args()

    try:
        result = call_api(args.keyword)
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
