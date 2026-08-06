#!/usr/bin/env python3
"""
Query location info by IPv4 address via Baidu Maps IP geolocation API.

Usage:
    python3 call_ip_geolocation.py --ip 1.2.3.4 [--coor bd09ll]
    python3 call_ip_geolocation.py   # auto-detect requesting IP

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


ENDPOINT = "https://app-dvtmyuucfs3l-api-79jK62Ze2pQL-gateway.appmiaoda.com/location/ip"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--ip", help="待查询的 IPv4 地址；不传则自动定位请求来源 IP")
    p.add_argument("--coor", choices=["bd09ll", "gcj02"], help="坐标系类型；不填返回百度墨卡托坐标")
    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main():
    """入口：调用百度 IP 定位接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    params = {}
    if args.ip:
        params["ip"] = args.ip
    if args.coor:
        params["coor"] = args.coor

    url = ENDPOINT
    if params:
        url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"

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
        fail(f"API error status {body.get('status')}")

    print(json.dumps({"status": "succeed", "result": body}))


if __name__ == "__main__":
    main()
