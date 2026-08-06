#!/usr/bin/env python3
"""
Recognize objects and scenes in an image via Baidu advanced_general API.
Base64 data never enters the LLM context.

Usage:
    python3 recognize_scene.py --image /path/to/image.jpg
    python3 recognize_scene.py --url https://example.com/image.jpg

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints the recognition JSON result on one line
    1 - API or argument error
"""

import os
import sys
import json
import base64
import argparse
import urllib.parse
import urllib.request
import urllib.error


ADVANCED_GENERAL_URL = "https://app-dvtmyuucfs3l-api-zYm4zKQoePjL-gateway.appmiaoda.com/rest/2.0/image-classify/v2/advanced_general"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--image", help="本地图片路径")
    src.add_argument("--url", help="图片 URL")
    p.add_argument("--baike-num", default=None, help="返回百科信息数量，0-5")
    return p.parse_args()


def post_form(api_key: str, params: dict) -> dict:
    """调用上游接口并返回响应。"""
    payload = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        ADVANCED_GENERAL_URL,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """入口：识别图片中的物体和场景并打印结果。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    params = {}
    if args.image:
        with open(args.image, "rb") as f:
            params["image"] = base64.b64encode(f.read()).decode("ascii")
    else:
        params["url"] = args.url
    if args.baike_num is not None:
        params["baike_num"] = args.baike_num

    d = post_form(api_key, params)
    if d.get("error_code"):
        print(f"API error {d.get('error_code')}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
