#!/usr/bin/env python3
"""
Poll an already-submitted advanced image generation task by task_id (does NOT submit a new task).

Use this when generate_image_advanced.py returned {"status": "processing", "task_id": "..."}.

Usage:
    python3 query_image_advanced.py --task-id <task_id>

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "task_id": "...", "image_url": "...", "file": "<path or null>"}
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


QUERY_URL = "https://app-dvtmyuucfs3l-api-VaOwP2jDmAga-gateway.appmiaoda.com/image-generation/task"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True, dest="task_id")
    return p.parse_args()


def request_json(url: str, api_key: str, payload: dict) -> dict:
    """调用上游接口并返回响应 JSON。"""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
        method="POST",
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


def query(api_key: str, task_id: str) -> dict:
    """查询指定任务的当前状态和结果。"""
    return request_json(QUERY_URL, api_key, {"taskId": task_id}).get("data", {})


def main():
    """入口：轮询任务状态直到完成或超时，输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        data = query(api_key, args.task_id)
        status = data.get("status")
        if status == "SUCCESS":
            image_url = data.get("result", {}).get("imageUrl") or data.get("imageUrl")
            print(json.dumps({"status": "succeed", "task_id": args.task_id, "image_url": image_url, "file": None}))
            return
        if status == "FAILED":
            err = data.get("error") or {}
            print(f"任务失败: {err.get('message') or json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
            sys.exit(1)
        time.sleep(POLL_INTERVAL_S)

    print(json.dumps({"status": "processing", "task_id": args.task_id}))


if __name__ == "__main__":
    main()
