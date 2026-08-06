#!/usr/bin/env python3
"""
Poll an already-submitted MiniMax text-to-video task by task_id (does NOT submit a new task).

Use this when generate_text_to_video.py returned {"status": "processing", "task_id": "..."}.

Usage:
    python3 query_text_to_video.py --task-id <task_id> [--output /path/to/output.mp4]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "task_id": "...", "url": "...", "file": "<path or null>"}
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


QUERY_URL = "https://app-dvtmyuucfs3l-api-zYkZz2eDWvPL-gateway.appmiaoda.com/v1/query/video_generation"
RETRIEVE_URL = "https://app-dvtmyuucfs3l-api-GYX1ld3ExkQa-gateway.appmiaoda.com/v1/files/retrieve"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True, dest="task_id")
    p.add_argument("--output", help="下载生成视频到该本地路径（可选）")
    return p.parse_args()


def get_json(url: str, api_key: str, params: dict) -> dict:
    """调用上游接口并返回响应。"""
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        full_url,
        headers={"X-Gateway-Authorization": f"Bearer {api_key}"},
        method="GET",
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
    """查询任务状态并返回结果。"""
    return get_json(QUERY_URL, api_key, {"task_id": task_id})


def retrieve(api_key: str, file_id: str) -> dict:
    """根据文件 ID 获取下载链接信息。"""
    d = get_json(RETRIEVE_URL, api_key, {"file_id": file_id})
    if d.get("base_resp", {}).get("status_code") != 0:
        print(f"获取下载链接失败: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return d["file"]


def download(url: str, output: str):
    """下载文件并保存到本地路径。"""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp, open(output, "wb") as f:
        f.write(resp.read())


def main():
    """入口：轮询视频生成任务状态，成功后下载视频。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        data = query(api_key, args.task_id)
        status = data.get("status")
        if status == "Success":
            file_id = data.get("file_id")
            file_info = retrieve(api_key, file_id) if file_id else {}
            download_url = file_info.get("download_url")
            file_path = None
            if args.output and download_url:
                download(download_url, args.output)
                file_path = args.output
            print(json.dumps({
                "status": "succeed",
                "task_id": args.task_id,
                "url": download_url,
                "file": file_path,
                "filename": file_info.get("filename"),
            }))
            return
        if status == "Fail":
            print(f"任务失败: {json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
            sys.exit(1)
        time.sleep(POLL_INTERVAL_S)

    print(json.dumps({"status": "processing", "task_id": args.task_id}))


if __name__ == "__main__":
    main()
