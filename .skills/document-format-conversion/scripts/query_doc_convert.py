#!/usr/bin/env python3
"""
Poll an already-submitted document-format-conversion task by task_id (does NOT submit a new task).

Use this when generate_doc_convert.py returned {"status": "processing", "task_id": "..."}.

Usage:
    python3 query_doc_convert.py --task-id <task_id>

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "task_id": "...", "word": "...", "excel": "...", "expires": "30 days"}
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


QUERY_URL = "https://app-dvtmyuucfs3l-api-oYA6ZGjReooa-gateway.appmiaoda.com/rest/2.0/ocr/v1/doc_convert/get_request_result"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True, dest="task_id")
    return p.parse_args()


def query(api_key: str, task_id: str) -> dict:
    """查询任务结果。"""
    data = urllib.parse.urlencode({"task_id": task_id}).encode()
    req = urllib.request.Request(
        QUERY_URL,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
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

    if not d.get("success"):
        print(f"查询失败: {d.get('message')} (code: {d.get('code')})", file=sys.stderr)
        sys.exit(1)
    return d.get("result", {})


def main():
    """入口：只查询、不提交，原地轮询直到完成或达到安全时限。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    start = time.time()
    while True:
        result = query(api_key, args.task_id)

        if result.get("ret_code") == 3:
            data = result.get("result_data", {})
            print(json.dumps({
                "status": "succeed",
                "task_id": args.task_id,
                "word": data.get("word", ""),
                "excel": data.get("excel", ""),
                "expires": "30 days",
            }))
            return

        if time.time() - start >= SAFE_LIMIT_S:
            print(json.dumps({"status": "processing", "task_id": args.task_id}))
            return

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
