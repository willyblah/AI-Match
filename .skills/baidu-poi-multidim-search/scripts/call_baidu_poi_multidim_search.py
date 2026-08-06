#!/usr/bin/env python3
"""
Query Baidu Map multidim POI search.

Usage:
    python3 call_baidu_poi_multidim_search.py --query "宠物友好餐厅" --region "北京市" \
        [--region-limit true] [--scope 2] [--page-num 0] [--page-size 10] \
        [--filter "industry_type:cater sort_name:overall_rating sort_rule:1"] \
        [--center "39.9,116.4"] [--coord-type 3] [--ret-coordtype "bd09ll"] \
        [--extensions-adcode true] [--output json]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one-line JSON: {"status":"succeed","result":{...}}
    1 - API or argument error, prints one-line JSON on stderr
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-zYkZXBBNPe8L-gateway.appmiaoda.com/api_place_pro/v1/region"


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser(description="Baidu multidim POI search")
    p.add_argument("--query", required=True, help="检索关键字")
    p.add_argument("--region", required=True, help="限定搜索区域")
    p.add_argument("--region-limit", help="是否仅召回 region 内数据: true/false")
    p.add_argument("--scope", help="1 基本信息 / 2 详细信息")
    p.add_argument("--page-num", help="分页页码，默认 0")
    p.add_argument("--page-size", help="单页条数，最大 20")
    p.add_argument("--filter", help='排序筛选，例如 "industry_type:cater sort_name:overall_rating sort_rule:1"')
    p.add_argument("--center", help='参考坐标 "lat,lng"')
    p.add_argument("--coord-type", help="传入坐标类型 1-4")
    p.add_argument("--ret-coordtype", help="返回坐标类型")
    p.add_argument("--extensions-adcode", help="是否召回国标行政区划编码 true/false")
    p.add_argument("--output", default="json", help="json/xml，默认 json")
    p.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    return p.parse_args()


def call_api(args):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    params = {"query": args.query, "region": args.region, "output": args.output}
    if args.region_limit is not None:
        params["region_limit"] = args.region_limit
    if args.scope is not None:
        params["scope"] = args.scope
    if args.page_num is not None:
        params["page_num"] = args.page_num
    if args.page_size is not None:
        params["page_size"] = args.page_size
    if args.filter:
        params["filter"] = args.filter
    if args.center:
        params["center"] = args.center
    if args.coord_type is not None:
        params["coord_type"] = args.coord_type
    if args.ret_coordtype:
        params["ret_coordtype"] = args.ret_coordtype
    if args.extensions_adcode is not None:
        params["extensions_adcode"] = args.extensions_adcode

    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
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
    """入口：POI 检索并输出结果 JSON。"""
    args = parse_args()
    result = call_api(args)
    if result.get("status") not in (0, None):
        fail("API error %s: %s" % (result.get("status"), result.get("message", "")))
    print(json.dumps({"status": "succeed", "result": result}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
