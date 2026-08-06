#!/usr/bin/env python3
"""Call precious metal price/kline/contract APIs and print one JSON line."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINTS = {
    "domestic-price": "https://app-dvtmyuucfs3l-api-ra5Err8G2Rla-gateway.appmiaoda.com/precious-metal/domestic/price",
    "domestic-kline": "https://app-dvtmyuucfs3l-api-rLobRR63mpd9-gateway.appmiaoda.com/precious-metal/domestic/kline",
    "domestic-contract": "https://app-dvtmyuucfs3l-api-DY8Mnnl0GGAa-gateway.appmiaoda.com/precious-metal/domestic/contract",
    "inter-price": "https://app-dvtmyuucfs3l-api-NLZ133Rnwr29-gateway.appmiaoda.com/precious-metal/inter/price",
    "inter-kline": "https://app-dvtmyuucfs3l-api-2Y00VV8Rkb2Y-gateway.appmiaoda.com/precious-metal/inter/kline",
    "inter-contract": "https://app-dvtmyuucfs3l-api-nYWNRRkexgKL-gateway.appmiaoda.com/precious-metal/inter/contract",
}


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def load_json(resp):
    """读取响应体并解析为 JSON。"""
    text = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fail("Response is not valid JSON: " + text[:500])


def post_form(endpoint, params, timeout):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    body = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return load_json(resp)
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, body_text[:1000]))
    except urllib.error.URLError as exc:
        fail("Network error: " + str(exc.reason))
    except TimeoutError:
        fail("Request timed out")


def main():
    """入口：查询贵金属行情、K 线或合约数据并打印结果。"""
    parser = argparse.ArgumentParser(description="Query precious metal market data.")
    parser.add_argument("--endpoint", choices=sorted(ENDPOINTS), required=True, help="API endpoint selector")
    parser.add_argument("--symbol", required=True, help="品种代码")
    parser.add_argument("--type", dest="kline_type", help="K 线类型，仅 *-kline 端点需要")
    parser.add_argument("--limit", default="10", help="K 线条数，默认 10")
    parser.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    args = parser.parse_args()

    params = {"symbol": args.symbol}
    if args.endpoint.endswith("-kline"):
        if not args.kline_type:
            fail("--type is required for kline endpoints")
        params["type"] = args.kline_type
        params["limit"] = args.limit
    elif args.kline_type:
        fail("--type is only valid for kline endpoints")

    result = post_form(ENDPOINTS[args.endpoint], params, args.timeout)
    print(json.dumps({"status": "succeed", "result": result}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
