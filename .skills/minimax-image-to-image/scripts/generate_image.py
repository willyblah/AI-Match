#!/usr/bin/env python3
"""
Generate images via MiniMax image-to-image/text-to-image and download results to local files.
Reference image files are encoded inside this script.

Usage:
    python3 generate_image.py --prompt "a portrait" --reference-image /path/to/person.jpg --output /path/to/output.png
    python3 generate_image.py --prompt "..." --n 2 --output-dir /path/to/images

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON: {"files": [...], "urls": [...], "metadata": {...}}
    1 - API or argument error
"""

import os
import sys
import json
import base64
import argparse
import mimetypes
import urllib.request
import urllib.error


IMAGE_GENERATION_URL = "https://app-dvtmyuucfs3l-api-6LeBzWJjy3QY-gateway.appmiaoda.com/v1/image_generation"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True)
    p.add_argument("--output", help="单张输出文件路径")
    p.add_argument("--output-dir", help="多张图片输出目录")
    p.add_argument("--model", default="image-01", choices=["image-01", "image-01-live"])
    p.add_argument("--aspect-ratio", default="1:1")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--width", type=int, default=None)
    p.add_argument("--height", type=int, default=None)
    p.add_argument("--style", default=None, help="image-01-live 可用：漫画/元气/中世纪/水彩")
    p.add_argument("--reference-image", action="append", default=[], help="本地参考图路径，可重复传入")
    p.add_argument("--reference-url", action="append", default=[], help="参考图 URL，可重复传入")
    args = p.parse_args()
    if bool(args.output) == bool(args.output_dir):
        p.error("必须且只能指定 --output 或 --output-dir")
    if args.output and args.n != 1:
        p.error("--output 仅支持 --n 1，多图请使用 --output-dir")
    return args


def image_to_data_url(path: str) -> str:
    """读取本地图片并编码为 data URL。"""
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{data}"


def post_json(api_key: str, payload_obj: dict) -> dict:
    """调用上游接口并返回响应。"""
    payload = json.dumps(payload_obj).encode()
    req = urllib.request.Request(
        IMAGE_GENERATION_URL,
        data=payload,
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


def download(url: str, output: str):
    """下载文件并保存到本地路径。"""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp, open(output, "wb") as f:
        f.write(resp.read())


def save_b64(data: str, output: str):
    """将 base64 数据解码并保存为本地文件。"""
    with open(output, "wb") as f:
        f.write(base64.b64decode(data))


def build_output_paths(args, count: int) -> list:
    """根据参数生成输出图片的本地文件路径列表。"""
    if args.output:
        return [args.output]
    os.makedirs(args.output_dir, exist_ok=True)
    return [os.path.join(args.output_dir, f"minimax_image_{i + 1}.png") for i in range(count)]


def main():
    """入口：生成图片并下载到本地文件。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    references = [{"type": "character", "image_file": image_to_data_url(p)} for p in args.reference_image]
    references += [{"type": "character", "image_file": u} for u in args.reference_url]

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "response_format": "url",
        "n": args.n,
        "aspect_ratio": args.aspect_ratio,
    }
    if references:
        payload["subject_reference"] = references
    if args.width is not None:
        payload["width"] = args.width
    if args.height is not None:
        payload["height"] = args.height
    if args.style:
        payload["style"] = {"style_type": args.style, "style_weight": 0.8}

    d = post_json(api_key, payload)
    base_resp = d.get("base_resp", {})
    if base_resp.get("status_code") not in (None, 0):
        print(f"API error: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    data = d.get("data", {})
    urls = data.get("image_urls") or []
    b64_images = data.get("image_base64") or []
    count = len(urls) or len(b64_images)
    if count == 0:
        print(f"响应中未找到图片: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    files = build_output_paths(args, count)
    for i, path in enumerate(files):
        if i < len(urls):
            download(urls[i], path)
        else:
            save_b64(b64_images[i], path)

    print(json.dumps({
        "files": files,
        "urls": urls,
        "metadata": data.get("metadata", {}),
        "base_resp": base_resp,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
