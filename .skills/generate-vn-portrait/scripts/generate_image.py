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
import subprocess
import tempfile
import urllib.request
import urllib.error


GENERATIONS_URL = "http://app-dvtmyuucfs3l-api-Aa2P8AGZg2RL-gateway.appmiaoda.com/v1/images/generations"
EDITS_URL = "http://app-dvtmyuucfs3l-api-rY7JzDpZVBQL-gateway.appmiaoda.com/v1/images/edits"


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
    """调用图生图接口（最多 3 张输入图），编辑合成后保存到 output。"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmppath = tmp.name
    try:
        cmd = [
            "curl", "-sf",
            "-X", "POST", EDITS_URL,
            "-H", f"X-Gateway-Authorization: Bearer {api_key}",
            "-F", "model=gpt-image-2",
            "-F", f"prompt={prompt}",
            "-F", f"size={size}",
            "-o", tmppath,
        ]
        for i, p in enumerate(images[:3]):
            cmd += ["-F", f"image[{i}]=@{p}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"curl error: {r.stderr}", file=sys.stderr)
            sys.exit(1)
        with open(tmppath) as f:
            d = json.load(f)
    finally:
        os.unlink(tmppath)

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