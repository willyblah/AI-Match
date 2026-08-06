#!/usr/bin/env python3
"""Call the short speech recognition API and print one JSON result."""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-Aa2PZnjEw5NL-gateway.appmiaoda.com/server_api"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def read_audio(path):
    """读取本地音频文件并返回其 base64 编码及字节长度。"""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        die(f"Failed to read audio file {path}: {exc}")
    return base64.b64encode(data).decode("ascii"), len(data)


def main():
    """入口：识别短语音音频并打印识别结果。"""
    parser = argparse.ArgumentParser(description="Recognize short speech audio and print one JSON result.")
    parser.add_argument("--file", required=True, help="Local audio file path, 60 seconds or shorter.")
    parser.add_argument("--format", required=True, choices=["wav", "m4a"], help="Audio format.")
    parser.add_argument("--rate", required=True, type=int, choices=[8000, 16000], help="Audio sample rate.")
    parser.add_argument("--cuid", default="ducc", help="Client/user identifier, default ducc.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    speech, byte_len = read_audio(args.file)
    body = {
        "format": args.format,
        "rate": args.rate,
        "cuid": args.cuid,
        "speech": speech,
        "len": byte_len,
    }

    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
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

    if data.get("err_no") not in (None, 0):
        die(f"API error {data.get('err_no')}: {data.get('err_msg')}")

    print(json.dumps({"status": "succeed", "data": data}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
