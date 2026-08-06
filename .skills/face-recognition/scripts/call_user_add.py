#!/usr/bin/env python3
"""
Register a face to the Baidu face library and print the API response.
Base64 data never enters the LLM context.

Usage:
    python3 call_user_add.py --image /path/to/face.jpg --user-id user_001
    python3 call_user_add.py --face-token <face_token> --user-id user_001

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


ENDPOINT = "https://app-dvtmyuucfs3l-api-l9nZz8ro7Bl9-gateway.appmiaoda.com/rest/2.0/face/v3/faceset/user/add"


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Local image path")
    group.add_argument("--face-token", dest="face_token", help="Existing FACE_TOKEN")
    parser.add_argument("--user-id", dest="user_id", required=True)
    parser.add_argument("--user-info", dest="user_info")
    parser.add_argument("--quality-control", dest="quality_control", default="NONE",
                         choices=["NONE", "LOW", "NORMAL", "HIGH"])
    parser.add_argument("--liveness-control", dest="liveness_control", default="NONE",
                         choices=["NONE", "LOW", "NORMAL", "HIGH"])
    parser.add_argument("--action-type", dest="action_type", default="APPEND", choices=["APPEND", "REPLACE"])
    return parser.parse_args()


def build_payload(args) -> dict:
    """构造请求参数。"""
    if args.image:
        with open(args.image, "rb") as f:
            image = base64.b64encode(f.read()).decode()
        image_type = "BASE64"
    else:
        image = args.face_token
        image_type = "FACE_TOKEN"

    payload = {
        "image": image,
        "image_type": image_type,
        "user_id": args.user_id,
        "quality_control": args.quality_control,
        "liveness_control": args.liveness_control,
        "action_type": args.action_type,
    }
    if args.user_info is not None:
        payload["user_info"] = args.user_info
    return payload


def call_api(api_key: str, payload: dict) -> dict:
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
    """入口：解析参数，调用接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    d = call_api(api_key, build_payload(args))
    if d.get("error_code"):
        print(f"API error {d['error_code']}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
