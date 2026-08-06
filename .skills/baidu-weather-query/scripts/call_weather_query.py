#!/usr/bin/env python3
"""
Query domestic weather via Baidu Maps weather API, by district code or by lat/lng.

Usage:
    # By administrative district code
    python3 call_weather_query.py district --district-id 110100 [--data-type all]

    # By latitude/longitude
    python3 call_weather_query.py location --latitude 39.915 --longitude 116.404 [--data-type all]

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


DISTRICT_ENDPOINT = "https://app-dvtmyuucfs3l-api-oLpZbd8ed8wa-gateway.appmiaoda.com/weather/v1/"
LOCATION_ENDPOINT = "https://app-dvtmyuucfs3l-api-GYX1bnRz2Pxa-gateway.appmiaoda.com/weather/v1/"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)

    d = sub.add_parser("district", help="按行政区划代码查询天气")
    d.add_argument("--district-id", dest="district_id", required=True, help="行政区划代码，如 110100（北京市）")
    d.add_argument("--data-type", dest="data_type", default="all",
                    choices=["all", "now", "forecast"], help="数据类型，默认 all")

    l = sub.add_parser("location", help="按经纬度查询天气")
    l.add_argument("--latitude", required=True, type=float, help="纬度")
    l.add_argument("--longitude", required=True, type=float, help="经度")
    l.add_argument("--data-type", dest="data_type", default="all",
                    choices=["all", "now", "forecast", "hourly"], help="数据类型，默认 all")

    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main():
    """入口：按 mode 调用天气查询接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    if args.mode == "district":
        endpoint = DISTRICT_ENDPOINT
        params = {"district_id": args.district_id, "data_type": args.data_type}
    else:
        endpoint = LOCATION_ENDPOINT
        # 注意：百度地图 API location 参数格式为 纬度,经度
        params = {"location": f"{args.latitude},{args.longitude}", "data_type": args.data_type}

    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
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

    if body.get("status") != 0:
        fail(f"API error status: {body.get('status')}, message: {body.get('message', '')}")

    print(json.dumps({"status": "succeed", "result": body.get("result", body)}))


if __name__ == "__main__":
    main()
