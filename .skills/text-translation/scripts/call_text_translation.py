#!/usr/bin/env python3
"""
Translate text via Baidu Translation API (200+ languages, auto-detect source).

Usage:
    python3 call_text_translation.py --q "hello world" --from auto --to zh

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one-line JSON: {"status": "succeed", "result": {...}}
    1 - API or argument error, prints one-line JSON: {"status": "error", "message": "..."}
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error


ENDPOINT = "https://app-dvtmyuucfs3l-api-e94GZ5j0PWpa-gateway.appmiaoda.com/rpc/2.0/mt/texttrans/v1"


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--q", required=True, help="待翻译文本，最大 6000 字符")
    p.add_argument("--from", dest="from_lang", required=True, help="源语言代码，可设置为 auto 自动检测")
    p.add_argument("--to", dest="to_lang", required=True, help="目标语言代码，不可设置为 auto")
    return p.parse_args()


def fail(message: str):
    """打印错误 JSON 并以非零状态退出。"""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main():
    """入口：调用百度翻译接口并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    payload = json.dumps({"q": args.q, "from": args.from_lang, "to": args.to_lang}).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json;charset=utf-8",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        fail(f"HTTP {e.code}: {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        fail(f"Network error: {e}")

    if body.get("error_code"):
        fail(f"API error {body.get('error_code')}: {body.get('error_msg')}")

    print(json.dumps({"status": "succeed", "result": body.get("result", body)}))


if __name__ == "__main__":
    main()
