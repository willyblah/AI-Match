#!/usr/bin/env python3
"""
Baidu Maps geocoding (address <-> coordinates), forward and reverse.

Usage:
    # Forward geocoding: address -> coordinates
    python3 call_geocoding.py forward --address "百度大厦" [--city "北京市"] [--ret-coordtype bd09ll]

    # Reverse geocoding: coordinates -> address
    python3 call_geocoding.py reverse --location "31.225696563611,121.49884033194" \
        [--coordtype bd09ll] [--ret-coordtype bd09ll] [--extensions-poi 0] [--extensions-road false]

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


FORWARD_ENDPOINT = "https://app-dvtmyuucfs3l-api-GaDwZ0j3erOY-gateway.appmiaoda.com/geocoding/v3/"
REVERSE_ENDPOINT = "https://app-dvtmyuucfs3l-api-baBwZEjbe1X9-gateway.appmiaoda.com/reverse_geocoding/v3"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)

    fwd = sub.add_parser("forward", help="地理编码：地址 -> 坐标")
    fwd.add_argument("--address", required=True, help="待解析的地址")
    fwd.add_argument("--city", help="地址所在城市，用于消歧")
    fwd.add_argument("--ret-coordtype", dest="ret_coordtype", default="bd09ll",
                      help="返回坐标类型，默认 bd09ll")

    rev = sub.add_parser("reverse", help="逆地理编码：坐标 -> 地址")
    rev.add_argument("--location", required=True, help="经纬度坐标，格式：纬度,经度")
    rev.add_argument("--coordtype", default="bd09ll", help="传入坐标类型，默认 bd09ll")
    rev.add_argument("--ret-coordtype", dest="ret_coordtype", default="bd09ll",
                      help="返回坐标类型，默认 bd09ll")
    rev.add_argument("--extensions-poi", dest="extensions_poi", default="0",
                      help="是否召回 POI 数据：0 不召回，1 召回，默认 0")
    rev.add_argument("--extensions-road", dest="extensions_road",
                      help="是否召回周边道路数据：true/false")

    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def call(endpoint: str, params: dict, api_key: str) -> dict:
    """发起 GET 请求并返回解析后的 JSON 响应。"""
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"X-Gateway-Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        fail(f"HTTP {e.code}: {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        fail(f"Network error: {e}")


def main():
    """入口：按 mode 调用地理编码或逆地理编码接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    if args.mode == "forward":
        params = {"address": args.address, "output": "json", "ret_coordtype": args.ret_coordtype}
        if args.city:
            params["city"] = args.city
        body = call(FORWARD_ENDPOINT, params, api_key)
    else:
        params = {
            "location": args.location,
            "coordtype": args.coordtype,
            "ret_coordtype": args.ret_coordtype,
            "extensions_poi": args.extensions_poi,
            "output": "json",
            "language": "zh-CN",
        }
        if args.extensions_road:
            params["extensions_road"] = args.extensions_road
        body = call(REVERSE_ENDPOINT, params, api_key)

    if body.get("status") != 0:
        fail(f"API error status {body.get('status')}: {body.get('message', '')}")

    print(json.dumps({"status": "succeed", "result": body.get("result", body)}))


if __name__ == "__main__":
    main()
