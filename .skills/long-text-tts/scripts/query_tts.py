#!/usr/bin/env python3
"""
Poll an already-submitted long-text TTS task by task_id (does NOT submit a new task).

Use this when generate_tts.py returned {"status": "processing", "task_id": "..."}.

Usage:
    python3 query_tts.py --task-id <task_id>

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


QUERY_URL = "https://app-dvtmyuucfs3l-api-Q9KWZ2jy8W09-gateway.appmiaoda.com/rpc/2.0/tts/v1/query"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True, dest="task_id")
    return p.parse_args()


def query(api_key: str, task_id: str) -> dict:
    """查询任务状态；QPS 限流（error_code 18）时视为仍在运行，不报错。"""
    payload = json.dumps({"task_ids": [task_id]}).encode()
    req = urllib.request.Request(
        QUERY_URL,
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
    """入口：只查询、不提交，原地轮询直到成功/失败或达到安全时限。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    start = time.time()
    while True:
        info = query(api_key, args.task_id)
        status = info.get("task_status")

        if status == "Success":
            speech_url = info.get("task_result", {}).get("speech_url", "")
            print(json.dumps({
                "status": "succeed",
                "task_id": args.task_id,
                "speech_url": speech_url,
                "expires": "72 hours",
            }))
            return

        if status == "Failure":
            print(f"TTS task failed: {json.dumps(info)}", file=sys.stderr)
            sys.exit(1)

        if time.time() - start >= SAFE_LIMIT_S:
            print(json.dumps({"status": "processing", "task_id": args.task_id}))
            return

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
