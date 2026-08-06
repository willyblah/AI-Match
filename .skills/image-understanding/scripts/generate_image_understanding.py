#!/usr/bin/env python3
"""
Submit an image-understanding request and poll until a description is ready.

Usage:
    python3 generate_image_understanding.py --question "..." --image /path/to/image.jpg
    python3 generate_image_understanding.py --question "..." --url "https://example.com/image.jpg"

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
import base64
import argparse
import urllib.request
import urllib.parse
import urllib.error


SUBMIT_URL = "https://app-dvtmyuucfs3l-api-DYJwo27V85oa-gateway.appmiaoda.com/rest/2.0/image-classify/v1/image-understanding/request"
QUERY_URL = "https://app-dvtmyuucfs3l-api-zYkZz8qoKDdL-gateway.appmiaoda.com/rest/2.0/image-classify/v1/image-understanding/get-result"

POLL_INTERVAL_S = 5
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--question", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--image", help="本地图片路径")
    g.add_argument("--url", help="图片 URL")
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


def submit(api_key: str, args) -> str:
    """提交图像理解任务并返回任务 ID。"""
    params = {"question": args.question}
    if args.image:
        with open(args.image, "rb") as f:
            params["image"] = base64.b64encode(f.read()).decode()
    else:
        params["url"] = args.url

    d = post_json(SUBMIT_URL, api_key, params)
    task_id = d.get("result", {}).get("task_id")
    if not task_id:
        print(f"提交失败: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return task_id


def query(api_key: str, task_id: str) -> dict:
    """查询图像理解任务并返回结果数据。"""
    return post_json(QUERY_URL, api_key, {"task_id": task_id}).get("result", {})


def main():
    """入口：提交图像理解任务并输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    task_id = submit(api_key, args)
    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        time.sleep(POLL_INTERVAL_S)
        result = query(api_key, task_id)
        ret_code = result.get("ret_code")
        if ret_code == 0:
            print(json.dumps({"status": "succeed", "task_id": task_id, "description": result.get("description", "")}))
            return
        if ret_code != 1:
            print(f"任务失败: {result.get('ret_msg', 'unknown error')} (ret_code={ret_code})", file=sys.stderr)
            sys.exit(1)

    print(json.dumps({"status": "processing", "task_id": task_id}))


if __name__ == "__main__":
    main()
