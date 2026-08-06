#!/usr/bin/env python3
"""Call the train station2s API and print one JSON result."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-V9PworyO6gEa-gateway.appmiaoda.com/train/station2s"


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def main():
    """入口：查询两站车次并输出 JSON 结果。"""
    parser = argparse.ArgumentParser(description="Query train station2s info and print one JSON result.")
    parser.add_argument("--start", required=True, help="Departure station, for example 杭州东.")
    parser.add_argument("--end", required=True, help="Arrival station, for example 北京南.")
    parser.add_argument("--ishigh", help='Pass "1" to only return high-speed/EMU trains.')
    parser.add_argument("--date", help="Travel date, for example 2024-01-01.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    params = {
        "start": args.start,
        "end": args.end,
    }
    if args.ishigh:
        params["ishigh"] = args.ishigh
    if args.date:
        params["date"] = args.date
    endpoint = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"

    request = urllib.request.Request(
        endpoint,
        data=b"",
        headers={
            "X-Gateway-Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json;charset=UTF-8",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        die(f"HTTP {exc.code}: {body}")
    except urllib.error.URLError as exc:
        die(f"Request failed: {exc.reason}")
    except json.JSONDecodeError as exc:
        die(f"Invalid JSON response: {exc}")

    if payload.get("status") != 0:
        die(str(payload.get("msg", "API error")))

    print(json.dumps({"status": "succeed", "result": payload.get("result", {})}, ensure_ascii=False))


if __name__ == "__main__":
    main()
