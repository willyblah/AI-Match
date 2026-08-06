#!/usr/bin/env python3
"""
Edit an image via Gemini image editing API and save the result to disk.
Base64 data never enters the LLM context.

Usage:
    python3 generate_image_edit.py --input /path/to/source.png --instruction "将图片更换个背景" --output /path/to/output.png

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON: {"file": "...", "logText": "...", "usage": {...}}
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


GENERATE_URL = (
    "https://app-dvtmyuucfs3l-api-o9wN0AExZQ8a-gateway.appmiaoda.com/v1beta/models/"
    "gemini-3.1-flash-image-preview:generateContent"
)


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="待编辑图片的本地路径")
    p.add_argument("--instruction", required=True, help="中文编辑指令")
    p.add_argument("--output", required=True, help="编辑结果保存路径")
    p.add_argument("--mime-type", default=None, help="覆盖自动检测的 MIME 类型")
    p.add_argument("--temperature", type=float, default=None)
    return p.parse_args()


def guess_mime_type(path: str) -> str:
    """根据文件路径猜测图片的 MIME 类型。"""
    mime, _ = mimetypes.guess_type(path)
    return mime or "image/jpeg"


def save_image(b64: str, path: str):
    """将 Base64 编码的图片数据解码并保存到本地路径。"""
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))


def call_gemini_edit(api_key: str, image_path: str, instruction: str, mime_type: str, temperature):
    """调用 Gemini 图片编辑接口并返回响应结果。"""
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("ascii")

    body = {
        "contents": [
            {
                "parts": [
                    {"text": instruction},
                    {"inlineData": {"mimeType": mime_type, "data": image_b64}},
                ]
            }
        ]
    }
    if temperature is not None:
        body["temperature"] = temperature

    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        GENERATE_URL,
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
        body_text = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body_text}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """入口：编辑图片并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    mime_type = args.mime_type or guess_mime_type(args.input)
    d = call_gemini_edit(api_key, args.input, args.instruction, mime_type, args.temperature)

    parts = (d.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    image_b64 = None
    image_mime = "image/png"
    log_text = None
    for part in parts:
        inline = part.get("inlineData")
        if inline and inline.get("data"):
            image_b64 = inline["data"]
            image_mime = inline.get("mimeType", "image/png")
        elif part.get("text") and not part.get("thought"):
            log_text = part["text"]

    if not image_b64:
        print(f"响应中未找到图片数据: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    save_image(image_b64, args.output)

    usage = d.get("usageMetadata", {})
    print(json.dumps({
        "file": args.output,
        "mimeType": image_mime,
        "logText": log_text,
        "usage": {
            "promptTokenCount": usage.get("promptTokenCount", 0),
            "candidatesTokenCount": usage.get("candidatesTokenCount", 0),
            "totalTokenCount": usage.get("totalTokenCount", 0),
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
