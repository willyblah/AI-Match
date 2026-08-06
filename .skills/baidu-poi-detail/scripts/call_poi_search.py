#!/usr/bin/env python3
"""百度地图 POI 地点信息搜索：行政区划检索 / 圆形区域检索 / 地点详情检索。

用法：
    python3 call_poi_search.py region --query "银行" --region "北京市海淀区" [--scope 2] [--page-size 10]
    python3 call_poi_search.py around --query "银行" --location "39.915,116.404" [--radius 1000]
    python3 call_poi_search.py detail --uid "435d7aea036e54355abbbcc8" [--scope 2]
    python3 call_poi_search.py detail --uids "uid1,uid2" [--scope 2]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REGION_ENDPOINT = "https://app-dvtmyuucfs3l-api-ra5EZvmRrG4a-gateway.appmiaoda.com/place/v3/region"
AROUND_ENDPOINT = "https://app-dvtmyuucfs3l-api-DLEO7eMnzMwa-gateway.appmiaoda.com/place/v3/around"
DETAIL_ENDPOINT = "https://app-dvtmyuucfs3l-api-GaDwZekp8WzY-gateway.appmiaoda.com/place/v3/detail"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser(description="百度地图 POI 地点信息搜索")
    sub = p.add_subparsers(dest="mode", required=True)

    region = sub.add_parser("region", help="行政区划区域检索")
    region.add_argument("--query", required=True, help="检索关键字，如「银行」")
    region.add_argument("--region", required=True, help="行政区划区域，如「北京市海淀区」")
    region.add_argument("--region-limit", dest="region_limit", choices=["true", "false"])
    region.add_argument("--type", help="二次筛选类型")
    region.add_argument("--scope", type=int, choices=[1, 2], default=1)
    region.add_argument("--page-num", dest="page_num", type=int)
    region.add_argument("--page-size", dest="page_size", type=int)

    around = sub.add_parser("around", help="圆形区域检索")
    around.add_argument("--query", required=True, help="检索关键字，支持 $ 分隔多关键字")
    around.add_argument("--location", required=True, help="圆心坐标，格式「纬度,经度」")
    around.add_argument("--radius", type=int, default=1000)
    around.add_argument("--radius-limit", dest="radius_limit", choices=["true", "false"])
    around.add_argument("--type", help="二次筛选类型")
    around.add_argument("--scope", type=int, choices=[1, 2], default=1)
    around.add_argument("--filter", help="排序条件")
    around.add_argument("--page-num", dest="page_num", type=int)
    around.add_argument("--page-size", dest="page_size", type=int)

    detail = sub.add_parser("detail", help="地点详情检索")
    detail.add_argument("--uid", help="单个 POI uid")
    detail.add_argument("--uids", help="多个 uid，逗号分隔，最多 10 个")
    detail.add_argument("--scope", type=int, choices=[1, 2], default=1)
    detail.add_argument("--photo-show", dest="photo_show", choices=["true", "false"])

    return p.parse_args()


def call(endpoint: str, params: dict) -> dict:
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        print("错误：环境变量 INTEGRATIONS_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{endpoint}?{query}"
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP 错误 {e.code}: {e.read().decode('utf-8', 'ignore')}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    if body.get("status") != 0:
        print(f"API 错误 {body.get('status')}: {body.get('message')}", file=sys.stderr)
        sys.exit(1)

    return body


def main():
    """入口：按 mode 调用相应的 POI 接口并输出结果 JSON。"""
    args = parse_args()

    if args.mode == "region":
        params = {
            "query": args.query,
            "region": args.region,
            "region_limit": args.region_limit,
            "type": args.type,
            "scope": args.scope,
            "page_num": args.page_num,
            "page_size": args.page_size,
        }
        body = call(REGION_ENDPOINT, params)
    elif args.mode == "around":
        params = {
            "query": args.query,
            "location": args.location,
            "radius": args.radius,
            "radius_limit": args.radius_limit,
            "type": args.type,
            "scope": args.scope,
            "filter": args.filter,
            "page_num": args.page_num,
            "page_size": args.page_size,
        }
        body = call(AROUND_ENDPOINT, params)
    else:  # detail
        if not args.uid and not args.uids:
            print("错误：detail 模式需要 --uid 或 --uids", file=sys.stderr)
            sys.exit(1)
        params = {
            "uid": args.uid,
            "uids": args.uids,
            "scope": args.scope,
            "photo_show": args.photo_show,
        }
        body = call(DETAIL_ENDPOINT, params)

    print(json.dumps({"status": "succeed", "results": body.get("results", [])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
