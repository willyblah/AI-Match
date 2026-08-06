#!/usr/bin/env python3
"""
Poll an already-submitted image-understanding task by task_id (does NOT submit a new task).

Use this when generate_image_understanding.py returned {"status": "processing", "task_id": "..."}.

Usage:
    python3 query_image_understanding.py --task-id <task_id>

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "task_id": "...", "description": "..."}
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
import urllib.parse
import urllib.error


QUERY_URL = "https://app-dvtmyuucfs3l-api-zYkZz8qoKDdL-gateway.appmiaoda.com/rest/2.0/image-classify/v1/image-understanding/get-result"

POLL_INTERVAL_S = 5
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True, dest="task_id")
    return p.parse_args()


def post_json(url: str, api_key: str, params: dict) -> dict:
    """提交 JSON 请求并返回解析后的 JSON 响应。"""
    data = json.dumps(params).encode("utf-8")
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


def query(api_key: str, task_id: str) -> dict:
    """查询图像理解任务并返回结果数据。"""
    return post_json(QUERY_URL, api_key, {"task_id": task_id}).get("result", {})


def main():
    """入口：查询图像理解任务并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        result = query(api_key, args.task_id)
        ret_code = result.get("ret_code")
        if ret_code == 0:
            print(json.dumps({
                "status": "succeed",
                "task_id": args.task_id,
                "description": result.get("description", ""),
            }))
            return
        if ret_code != 1:
            print(f"任务失败: {result.get('ret_msg', 'unknown error')} (ret_code={ret_code})", file=sys.stderr)
            sys.exit(1)
        time.sleep(POLL_INTERVAL_S)

    print(json.dumps({"status": "processing", "task_id": args.task_id}))


if __name__ == "__main__":
    main()
