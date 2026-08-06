#!/usr/bin/env python3
"""
Query real-time traffic condition via Baidu Maps traffic API.

Usage:
    # By road name
    python3 call_traffic_condition.py road --road-name "东二环" [--city "北京市"]

    # By rectangle bounds
    python3 call_traffic_condition.py bound --bounds "39.912078,116.464303;39.918276,116.475442" \
        [--coord-type-input gcj02] [--coord-type-output gcj02]

    # By polygon
    python3 call_traffic_condition.py polygon \
        --polygon "39.910528,116.472926;39.918276,116.475442;39.916671,116.459056" \
        [--coord-type-input gcj02] [--coord-type-output gcj02]

    # By center point + radius
    python3 call_traffic_condition.py around --center "39.912078,116.464303" --radius 200 \
        [--coord-type-input gcj02] [--coord-type-output gcj02]

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


ROAD_ENDPOINT = "https://app-dvtmyuucfs3l-api-rLobR3D3dbg9-gateway.appmiaoda.com/traffic/v1/road"
BOUND_ENDPOINT = "https://app-dvtmyuucfs3l-api-ra5ErGpGM8wa-gateway.appmiaoda.com/traffic/v1/bound"
POLYGON_ENDPOINT = "https://app-dvtmyuucfs3l-api-BYdwQ5e51blL-gateway.appmiaoda.com/traffic/v1/polygon"
AROUND_ENDPOINT = "https://app-dvtmyuucfs3l-api-Xa6JeEnEb2na-gateway.appmiaoda.com/traffic/v1/around"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)

    road = sub.add_parser("road", help="道路实时路况查询")
    road.add_argument("--road-name", dest="road_name", required=True, help="道路名称，如东二环")
    road.add_argument("--city", help="可选，城市名称，如北京市")

    bound = sub.add_parser("bound", help="矩形区域实时路况查询")
    bound.add_argument("--bounds", required=True, help="左下角纬度,经度;右上角纬度,经度")
    bound.add_argument("--coord-type-input", dest="coord_type_input", help="输入坐标系，如 gcj02")
    bound.add_argument("--coord-type-output", dest="coord_type_output", help="输出坐标系，如 gcj02")

    polygon = sub.add_parser("polygon", help="多边形区域实时路况查询")
    polygon.add_argument("--polygon", required=True, help="多边形顶点坐标序列（至少3个点）")
    polygon.add_argument("--coord-type-input", dest="coord_type_input", help="输入坐标系，如 gcj02")
    polygon.add_argument("--coord-type-output", dest="coord_type_output", help="输出坐标系，如 gcj02")

    around = sub.add_parser("around", help="周边实时路况查询")
    around.add_argument("--center", required=True, help="中心点坐标，格式：纬度,经度")
    around.add_argument("--radius", required=True, type=int, help="查询半径，单位米")
    around.add_argument("--coord-type-input", dest="coord_type_input", help="输入坐标系，如 gcj02")
    around.add_argument("--coord-type-output", dest="coord_type_output", help="输出坐标系，如 gcj02")

    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main():
    """入口：按 mode 调用对应路况接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    if args.mode == "road":
        endpoint = ROAD_ENDPOINT
        params = {"road_name": args.road_name}
        if args.city:
            params["city"] = args.city
    elif args.mode == "bound":
        endpoint = BOUND_ENDPOINT
        params = {"bounds": args.bounds}
        if args.coord_type_input:
            params["coord_type_input"] = args.coord_type_input
        if args.coord_type_output:
            params["coord_type_output"] = args.coord_type_output
    elif args.mode == "polygon":
        endpoint = POLYGON_ENDPOINT
        params = {"polygon": args.polygon}
        if args.coord_type_input:
            params["coord_type_input"] = args.coord_type_input
        if args.coord_type_output:
            params["coord_type_output"] = args.coord_type_output
    else:  # around
        endpoint = AROUND_ENDPOINT
        params = {"center": args.center, "radius": str(args.radius)}
        if args.coord_type_input:
            params["coord_type_input"] = args.coord_type_input
        if args.coord_type_output:
            params["coord_type_output"] = args.coord_type_output

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
