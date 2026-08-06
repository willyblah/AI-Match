#!/usr/bin/env python3
"""
Generate or edit an image via GPT-Image-2 and save the result to disk.
Base64 data never enters the LLM context.

Usage:
    # Text-to-image
    python3 generate_image.py --prompt "a cat" --output image.png [--size 1024x1024]

    # Image editing (1-3 input images)
    python3 generate_image.py --prompt "make it anime" --output image_v2.png \
        --images /path/to/img1.png [/path/to/img2.png]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON: {"file": "...", "revised_prompt": "...", "size": "..."}
    1 - API or argument error
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error


GENERATIONS_URL = os.environ.get(
    "IMAGE_GENERATIONS_URL",
    "https://app-dvtmyuucfs3l-api-wLNdpny6ZpVa-gateway.appmiaoda.com/image2",
)
EDITS_URL = os.environ.get(
    "IMAGE_EDITS_URL",
    "https://app-dvtmyuucfs3l-api-wLNdpny6ZpVa-gateway.appmiaoda.com/image2",
)


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--size", default="1024x1024")
    p.add_argument("--images", nargs="+", default=[])
    return p.parse_args()


def save_image(b64: str, path: str):
    """将 Base64 字符串解码并写入文件。"""
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))


def create_image(api_key: str, prompt: str, size: str, output: str):
    """调用文生图接口，生成图片并保存到 output。"""
    payload = json.dumps({"model": "gpt-image-2", "prompt": prompt, "size": size}).encode()
    req = urllib.request.Request(
        GENERATIONS_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in d:
        print(f"API error: {d['error']}", file=sys.stderr)
        sys.exit(1)

    save_image(d["data"][0]["b64_json"], output)
    return d


def edit_image(api_key: str, prompt: str, size: str, images: list, output: str):
    """调用 CFC JSON Base64 图生图接口（最多 3 张输入图）。"""
    image_payload = []
    for p in images[:3]:
        with open(p, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        ext = os.path.splitext(p)[1].lower()
        content_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(ext, "image/png")
        image_payload.append({
            "filename": os.path.basename(p),
            "content_type": content_type,
            "b64_json": encoded,
        })

    payload = json.dumps({
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": size,
        "images": image_payload,
    }).encode("utf-8")
    req = urllib.request.Request(
        EDITS_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in d:
        print(f"API error: {d['error']}", file=sys.stderr)
        sys.exit(1)

    save_image(d["data"][0]["b64_json"], output)
    return d


def main():
    """入口：根据是否传入 --images 分别走文生图或图生图流程，输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if args.images:
        d = edit_image(api_key, args.prompt, args.size, args.images, args.output)
    else:
        d = create_image(api_key, args.prompt, args.size, args.output)

    print(json.dumps({
        "file": args.output,
        "revised_prompt": d["data"][0].get("revised_prompt", ""),
        "size": d.get("size", args.size),
    }))


if __name__ == "__main__":
    main()
