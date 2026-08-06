#!/usr/bin/env python3
"""查询货币汇率信息。"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-ELbWz8OmBW5Y-gateway.appmiaoda.com/exchange-rate-v2/single"


def call_api(from_code):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        raise RuntimeError("INTEGRATIONS_API_KEY is required")

    data = urllib.parse.urlencode({"fromCode": from_code}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def main():
    """入口：解析参数，调用接口并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="Query exchange rates for one source currency.")
    parser.add_argument("--from-code", required=True, help="Source currency code, for example CNY, USD, EUR")
    args = parser.parse_args()

    try:
        result = call_api(args.from_code)
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
