#!/usr/bin/env python3
"""Call the train ticket OCR API and print one JSON result."""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-Xa6JZxjyqZna-gateway.appmiaoda.com/rest/2.0/ocr/v1/train_ticket"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def encode_file(path):
    """读取本地文件并编码为 base64 字符串。"""
    try:
        with open(path, "rb") as fh:
            return base64.b64encode(fh.read()).decode("ascii")
    except OSError as exc:
        die(f"Failed to read file {path}: {exc}")


def main():
    """入口：识别火车票信息并打印结果。"""
    parser = argparse.ArgumentParser(description="Recognize train ticket information and print one JSON result.")
    parser.add_argument("--image", help="Local image path. Highest priority when multiple input types are provided.")
    parser.add_argument("--url", help="Image URL.")
    parser.add_argument("--pdf-file", help="Local PDF file path.")
    parser.add_argument("--pdf-file-num", type=int, default=1, help="PDF page number, default 1.")
    parser.add_argument("--ofd-file", help="Local OFD file path.")
    parser.add_argument("--ofd-file-num", type=int, default=1, help="OFD page number, default 1.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    fields = {}
    if args.image:
        fields["image"] = encode_file(args.image)
    elif args.url:
        fields["url"] = args.url
    elif args.pdf_file:
        fields["pdf_file"] = encode_file(args.pdf_file)
        fields["pdf_file_num"] = str(args.pdf_file_num)
    elif args.ofd_file:
        fields["ofd_file"] = encode_file(args.ofd_file)
        fields["ofd_file_num"] = str(args.ofd_file_num)
    else:
        die("One of --image, --url, --pdf-file, or --ofd-file is required")

    request = urllib.request.Request(
        ENDPOINT,
        data=urllib.parse.urlencode(fields).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        die(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        die(f"Request failed: {exc.reason}")

    if "error_code" in data:
        die(f"API error {data.get('error_code')}: {data.get('error_msg')}")

    print(json.dumps({"status": "succeed", "data": data}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
