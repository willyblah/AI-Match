#!/usr/bin/env python3
"""Call the short text-to-speech API and save the resulting audio to a file."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-e94GZ5j0ljja-gateway.appmiaoda.com/text2audio"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def report_error_body(raw_bytes):
    """解析错误响应体并打印错误信息后退出。"""
    text = raw_bytes.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except ValueError:
        die(f"API error: {text}")
        return
    die(f"API error {data.get('err_no')}: {data.get('err_msg')}")


def main():
    """入口：合成短文本语音并保存音频文件。"""
    parser = argparse.ArgumentParser(description="Synthesize short text to speech and save the audio file.")
    parser.add_argument("--text", required=True, help="Text to synthesize, up to 500 Chinese characters.")
    parser.add_argument("--output", required=True, help="Local file path to save the synthesized audio to.")
    parser.add_argument("--aue", default="3", help="Audio format: 3=MP3, 6=WAV. Default 3.")
    parser.add_argument("--per", default="0", help="Voice id: 0=度小美, 1=度小宇, 3=度逍遥, 4=度丫丫. Default 0.")
    parser.add_argument("--spd", default="5", help="Speech speed, 0-15. Default 5.")
    parser.add_argument("--pit", default="5", help="Pitch, 0-15. Default 5.")
    parser.add_argument("--vol", default="5", help="Volume, 0-9 (basic voices) or 0-15 (premium voices). Default 5.")
    parser.add_argument("--cuid", default="ducc", help="Client/user identifier, default ducc.")
    parser.add_argument("--ctp", default="1", help="Client type, default 1.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    body = {
        "tex": args.text,
        "cuid": args.cuid,
        "ctp": args.ctp,
        "aue": args.aue,
        "per": args.per,
        "spd": args.spd,
        "pit": args.pit,
        "vol": args.vol,
    }

    request = urllib.request.Request(
        ENDPOINT,
        data=urllib.parse.urlencode(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        if "json" in content_type or "text" in content_type:
            report_error_body(raw)
        else:
            die(f"HTTP {exc.code}: {raw.decode('utf-8', errors='replace')}")
        return
    except urllib.error.URLError as exc:
        die(f"Request failed: {exc.reason}")
        return

    if "json" in content_type or "text" in content_type:
        report_error_body(raw)
        return

    try:
        with open(args.output, "wb") as fh:
            fh.write(raw)
    except OSError as exc:
        die(f"Failed to write audio file {args.output}: {exc}")
        return

    print(json.dumps(
        {"status": "succeed", "file": args.output, "bytes": len(raw)},
        ensure_ascii=False,
        separators=(",", ":"),
    ))


if __name__ == "__main__":
    main()
