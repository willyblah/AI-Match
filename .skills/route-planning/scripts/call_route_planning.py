#!/usr/bin/env python3
"""
Call Baidu route planning / route matrix APIs.

Endpoints:
    - driving | riding | walking | transit          (single-route)
    - matrix-driving | matrix-riding | matrix-walking (batch route matrix)

Usage:
    # 驾车单线
    python3 call_route_planning.py --endpoint driving \
        --origin "40.056878,116.30815" --destination "39.767892,116.527308"

    # 步行/骑行/公交单线（参数同 driving）
    python3 call_route_planning.py --endpoint transit \
        --origin "40.056878,116.30815" --destination "39.767892,116.527308"

    # 批量算路：origins 与 destinations 用 | 分隔多个 "lat,lng"
    python3 call_route_planning.py --endpoint matrix-driving \
        --origins "40.056878,116.30815|39.9,116.4" \
        --destinations "39.767892,116.527308"

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one-line JSON: {"status":"succeed","result":{...}}
    1 - API or argument error, prints error line on stderr
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINTS = {
    "driving": "https://app-dvtmyuucfs3l-api-GaDwZKpJxXOY-gateway.appmiaoda.com/direction/v2/driving",
    "riding": "https://app-dvtmyuucfs3l-api-W9z3MpAdKeNL-gateway.appmiaoda.com/direction/v2/riding",
    "walking": "https://app-dvtmyuucfs3l-api-wLNdomNRn42a-gateway.appmiaoda.com/direction/v2/walking",
    "transit": "https://app-dvtmyuucfs3l-api-m9xKXQkOKZXa-gateway.appmiaoda.com/direction/v2/transit",
    "matrix-driving": "https://app-dvtmyuucfs3l-api-6LeBrqqMqKQY-gateway.appmiaoda.com/routematrix/v2/driving",
    "matrix-riding": "https://app-dvtmyuucfs3l-api-Aa2Pq88pDANL-gateway.appmiaoda.com/routematrix/v2/riding",
    "matrix-walking": "https://app-dvtmyuucfs3l-api-qYGW2zz1MklY-gateway.appmiaoda.com/routematrix/v2/walking",
}

MATRIX_ENDPOINTS = {"matrix-driving", "matrix-riding", "matrix-walking"}


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser(description="Baidu route planning")
    p.add_argument("--endpoint", required=True, choices=sorted(ENDPOINTS), help="接口选择")
    # single-route
    p.add_argument("--origin", help='起点 "lat,lng"')
    p.add_argument("--destination", help='终点 "lat,lng"')
    p.add_argument("--waypoints", help='途经点 "lat,lng|lat,lng"（driving 支持）')
    p.add_argument("--tactics", help="路线策略（driving/riding/walking/transit）")
    # matrix
    p.add_argument("--origins", help='批量起点 "lat,lng|lat,lng"')
    p.add_argument("--destinations", help='批量终点 "lat,lng|lat,lng"')
    p.add_argument("--riding-type", help="骑行类型（matrix-riding）")
    p.add_argument("--road-prefer", help="道路偏好")
    # common
    p.add_argument("--coord-type", help="传入坐标类型，默认 bd09ll")
    p.add_argument("--ret-coordtype", help="返回坐标类型")
    p.add_argument("--output", default="json", help="json/xml，默认 json")
    p.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    return p.parse_args()


def build_params(args):
    """构造 query 参数。"""
    params = {"output": args.output}
    if args.endpoint in MATRIX_ENDPOINTS:
        if not args.origins or not args.destinations:
            fail("--origins and --destinations are required for %s" % args.endpoint)
        params["origins"] = args.origins
        params["destinations"] = args.destinations
        if args.tactics:
            params["tactics"] = args.tactics
        if args.riding_type:
            params["riding_type"] = args.riding_type
        if args.road_prefer:
            params["road_prefer"] = args.road_prefer
    else:
        if not args.origin or not args.destination:
            fail("--origin and --destination are required for %s" % args.endpoint)
        params["origin"] = args.origin
        params["destination"] = args.destination
        if args.waypoints:
            params["waypoints"] = args.waypoints
        if args.tactics:
            params["tactics"] = args.tactics
    if args.coord_type:
        params["coord_type"] = args.coord_type
    if args.ret_coordtype:
        params["ret_coordtype"] = args.ret_coordtype
    return params


def call_api(args):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    url = ENDPOINTS[args.endpoint] + "?" + urllib.parse.urlencode(build_params(args))
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, detail[:1000]))
    except urllib.error.URLError as exc:
        fail("Network error: " + str(exc.reason))

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        fail("Response is not valid JSON: " + body[:500])


def main():
    """入口：路线规划并输出结果 JSON。"""
    args = parse_args()
    result = call_api(args)
    if result.get("status") not in (0, None):
        fail("API error %s: %s" % (result.get("status"), result.get("message", "")))
    print(json.dumps({"status": "succeed", "result": result}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
