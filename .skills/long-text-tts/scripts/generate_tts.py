#!/usr/bin/env python3
"""
Submit a long-text TTS task and poll until it finishes, then print the result.

Usage:
    python3 generate_tts.py --text "要合成的文本" [--format mp3-16k] \
        [--voice 0] [--speed 5] [--pitch 5] [--volume 5] [--break-ms 0]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "task_id": "...", "speech_url": "...", "expires": "72 hours"}
        or, if not finished within the safe time limit:
        {"status": "processing", "task_id": "..."}
    1 - API or argument error
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error


CREATE_URL = "https://app-dvtmyuucfs3l-api-nYWNozBb8X3L-gateway.appmiaoda.com/rpc/2.0/tts/v1/create"
QUERY_URL = "https://app-dvtmyuucfs3l-api-Q9KWZ2jy8W09-gateway.appmiaoda.com/rpc/2.0/tts/v1/query"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True, help="待合成文本，最长10万字符")
    p.add_argument("--format", default="mp3-16k", choices=["mp3-16k", "mp3-48k", "wav"])
    p.add_argument("--voice", type=int, default=0, choices=[0, 1, 3, 4])
    p.add_argument("--speed", type=int, default=5)
    p.add_argument("--pitch", type=int, default=5)
    p.add_argument("--volume", type=int, default=5)
    p.add_argument("--break-ms", type=int, default=0, dest="break_ms")
    return p.parse_args()


def request(url: str, api_key: str, payload: dict) -> dict:
    """向指定 URL 发起 JSON POST 请求，返回解析后的响应体。"""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
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


def submit(api_key: str, args) -> str:
    """提交长文本合成任务，返回 task_id。"""
    payload = {
        "text": [args.text],
        "format": args.format,
        "voice": args.voice,
        "speed": args.speed,
        "pitch": args.pitch,
        "volume": args.volume,
        "break": args.break_ms,
    }
    d = request(CREATE_URL, api_key, payload)
    if "error_code" in d:
        print(f"API error {d['error_code']}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)
    return d["task_id"]


def query(api_key: str, task_id: str) -> dict:
    """查询任务状态；QPS 限流（error_code 18）时视为仍在运行，不报错。"""
    d = request(QUERY_URL, api_key, {"task_ids": [task_id]})
    if d.get("error_code") == 18:
        return {"task_status": "Running"}
    if "error_code" in d:
        print(f"API error {d['error_code']}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)
    tasks = d.get("tasks_info", [])
    if not tasks:
        return {"task_status": "Running"}
    return tasks[0]


def main():
    """入口：提交任务后原地轮询，直到成功/失败或达到安全时限。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    task_id = submit(api_key, args)

    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        time.sleep(POLL_INTERVAL_S)
        info = query(api_key, task_id)
        status = info.get("task_status")

        if status == "Success":
            speech_url = info.get("task_result", {}).get("speech_url", "")
            print(json.dumps({
                "status": "succeed",
                "task_id": task_id,
                "speech_url": speech_url,
                "expires": "72 hours",
            }))
            return

        if status == "Failure":
            print(f"TTS task failed: {json.dumps(info)}", file=sys.stderr)
            sys.exit(1)

        # Running / Created -> keep polling

    print(json.dumps({"status": "processing", "task_id": task_id}))


if __name__ == "__main__":
    main()
