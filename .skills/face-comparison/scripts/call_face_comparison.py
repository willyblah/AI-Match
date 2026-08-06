#!/usr/bin/env python3
"""
Compare two face images and print the Baidu face-match API response.
Base64 data never enters the LLM context.

Usage:
    python3 call_face_comparison.py --image1 /path/to/a.jpg --image2 /path/to/b.jpg
    python3 call_face_comparison.py --image1-token <face_token_a> --image2-token <face_token_b>

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one line of JSON with the API response
    1 - API or argument error
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error


ENDPOINT = "https://app-dvtmyuucfs3l-api-5YrZz81oerkY-gateway.appmiaoda.com/rest/2.0/face/v3/match"


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser()
    first = parser.add_mutually_exclusive_group(required=True)
    first.add_argument("--image1", help="First local image path")
    first.add_argument("--image1-token", dest="image1_token", help="First FACE_TOKEN")
    second = parser.add_mutually_exclusive_group(required=True)
    second.add_argument("--image2", help="Second local image path")
    second.add_argument("--image2-token", dest="image2_token", help="Second FACE_TOKEN")
    parser.add_argument("--face-type", dest="face_type", default="LIVE",
                         choices=["LIVE", "IDCARD", "WATERMARK", "CERT"])
    parser.add_argument("--quality-control", dest="quality_control", default="NONE",
                         choices=["NONE", "LOW", "NORMAL", "HIGH"])
    parser.add_argument("--liveness-control", dest="liveness_control", default="NONE",
                         choices=["NONE", "LOW", "NORMAL", "HIGH"])
    return parser.parse_args()


def face_payload(path: str = None, token: str = None, args=None) -> dict:
    """构造单张人脸的请求负载。"""
    if path:
        with open(path, "rb") as f:
            image = base64.b64encode(f.read()).decode()
        image_type = "BASE64"
    else:
        image = token
        image_type = "FACE_TOKEN"

    return {
        "image": image,
        "image_type": image_type,
        "face_type": args.face_type,
        "quality_control": args.quality_control,
        "liveness_control": args.liveness_control,
    }


def call_api(api_key: str, payload: list) -> dict:
    """调用上游接口并返回响应。"""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json",
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
    """入口：解析参数，调用人脸比对接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    payload = [
        face_payload(path=args.image1, token=args.image1_token, args=args),
        face_payload(path=args.image2, token=args.image2_token, args=args),
    ]
    d = call_api(api_key, payload)

    if d.get("error_code"):
        print(f"API error {d['error_code']}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
