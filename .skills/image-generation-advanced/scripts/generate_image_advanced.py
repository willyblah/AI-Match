#!/usr/bin/env python3
"""
Submit an advanced image generation/editing task and poll until done.

Usage:
    # Text to image
    python3 generate_image_advanced.py --prompt "..." [--output /path/to/output.png]

    # Image editing / multi-image input
    python3 generate_image_advanced.py --prompt "..." --image /path/a.png --image /path/b.jpg \
        [--output /path/to/output.png]

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
import base64
import mimetypes
import argparse
import urllib.request
import urllib.error


SUBMIT_URL = "https://app-dvtmyuucfs3l-api-ra5EZDjVKkXa-gateway.appmiaoda.com/image-generation/submit"
QUERY_URL = "https://app-dvtmyuucfs3l-api-VaOwP2jDmAga-gateway.appmiaoda.com/image-generation/task"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True, help="生成或编辑提示词")
    p.add_argument("--image", action="append", default=[], help="本地参考图片路径，可重复传入")
    p.add_argument("--output", help="下载生成图片到该本地路径（可选）")
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


def image_part(path: str) -> dict:
    """将本地图片读取并编码为请求所需的图片数据块。"""
    mime, _ = mimetypes.guess_type(path)
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return {"inline_data": {"mime_type": mime, "data": data}}


def submit(api_key: str, args) -> str:
    """提交图片生成/编辑任务并返回任务 ID。"""
    parts = [{"text": args.prompt}]
    parts.extend(image_part(path) for path in args.image)
    d = request_json(SUBMIT_URL, api_key, {"contents": [{"parts": parts}]})
    task_id = d.get("data", {}).get("taskId") or d.get("taskId")
    if not task_id:
        print(f"提交失败: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return task_id


def query(api_key: str, task_id: str) -> dict:
    """查询指定任务的当前状态和结果。"""
    return request_json(QUERY_URL, api_key, {"taskId": task_id}).get("data", {})


def download(url: str, output: str):
    """下载文件并保存到本地路径。"""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp, open(output, "wb") as f:
        f.write(resp.read())


def main():
    """入口：提交任务并轮询直到完成或超时，输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    task_id = submit(api_key, args)
    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        time.sleep(POLL_INTERVAL_S)
        data = query(api_key, task_id)
        status = data.get("status")
        if status == "SUCCESS":
            image_url = data.get("result", {}).get("imageUrl") or data.get("imageUrl")
            file_path = None
            if args.output and image_url:
                download(image_url, args.output)
                file_path = args.output
            print(json.dumps({"status": "succeed", "task_id": task_id, "image_url": image_url, "file": file_path}))
            return
        if status == "FAILED":
            err = data.get("error") or {}
            print(f"任务失败: {err.get('message') or json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps({"status": "processing", "task_id": task_id}))


if __name__ == "__main__":
    main()
