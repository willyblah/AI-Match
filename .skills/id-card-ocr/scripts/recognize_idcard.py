#!/usr/bin/env python3
"""
Recognize a Chinese ID card via Baidu OCR using a local file path or URL.
Base64 data never enters the LLM context.

Usage:
    python3 recognize_idcard.py --image /path/to/idcard.jpg --side front
    python3 recognize_idcard.py --url https://example.com/idcard.jpg --side back

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints the OCR JSON result on one line
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


IDCARD_URL = "https://app-dvtmyuucfs3l-api-k93RZBjP0zqa-gateway.appmiaoda.com/rest/2.0/ocr/v1/idcard"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--image", help="身份证图片本地路径")
    src.add_argument("--url", help="身份证图片 URL")
    p.add_argument("--side", required=True, choices=["front", "back"], help="front=正面，back=反面")
    p.add_argument("--detect-ps", action="store_true")
    p.add_argument("--detect-risk", action="store_true")
    p.add_argument("--detect-quality", action="store_true")
    p.add_argument("--detect-direction", action="store_true")
    return p.parse_args()


def post_form(api_key: str, params: dict) -> dict:
    """将参数编码为表单并调用 OCR 接口，返回解析后的响应。"""
    payload = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        IDCARD_URL,
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
    """入口：解析参数，调用身份证 OCR 接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    params = {"id_card_side": args.side}
    if args.image:
        with open(args.image, "rb") as f:
            params["image"] = base64.b64encode(f.read()).decode("ascii")
    else:
        params["url"] = args.url

    if args.detect_ps:
        params["detect_ps"] = "true"
    if args.detect_risk:
        params["detect_risk"] = "true"
    if args.detect_quality:
        params["detect_quality"] = "true"
    if args.detect_direction:
        params["detect_direction"] = "true"

    d = post_form(api_key, params)
    if d.get("error_code"):
        print(f"OCR API error {d.get('error_code')}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
