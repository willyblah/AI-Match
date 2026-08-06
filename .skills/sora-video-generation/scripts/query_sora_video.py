#!/usr/bin/env python3
"""
Poll an already-submitted Sora 2 video task by video_id (does NOT submit a new task).

Use this when generate_sora_video.py returned {"status": "processing", "video_id": "..."}.

Usage:
    python3 query_sora_video.py --video-id <video_id> [--output /path/to/output.mp4]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "video_id": "...", "url": "...", "file": "<path or null>"}
        or, if not finished within the safe time limit:
        {"status": "processing", "video_id": "..."}
    1 - API or argument error
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error


QUERY_URL = "https://app-dvtmyuucfs3l-api-M9v0w87KjxoY-gateway.appmiaoda.com/query"
POLL_INTERVAL_S = 8
SAFE_LIMIT_S = 550


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--video-id", required=True)
    p.add_argument("--output", help="下载生成视频到该本地路径（可选）")
    return p.parse_args()


def api_key():
    """读取环境变量中的 API Key，缺失则报错退出。"""
    key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return key


def post_json(url: str, api_key_value: str, payload: dict) -> dict:
    """调用上游接口并返回响应。"""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key_value}",
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


def download(url: str, output: str):
    """下载文件并保存到本地路径。"""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp, open(output, "wb") as f:
        f.write(resp.read())


def poll_until_done(key: str, video_id: str, output: str):
    """轮询任务直到完成或超时。"""
    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        time.sleep(POLL_INTERVAL_S)
        data = post_json(QUERY_URL, key, {"video_id": video_id})
        status = data.get("status")
        if status == "completed":
            video_url = data.get("video_url")
            if not video_url:
                print(f"任务已完成但缺少 video_url: {json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
                sys.exit(1)
            file_path = None
            if output:
                download(video_url, output)
                file_path = output
            print(json.dumps({
                "status": "succeed",
                "video_id": video_id,
                "url": video_url,
                "file": file_path,
            }))
            return
        if status == "failed":
            print(f"任务失败: {json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
            sys.exit(1)
        if status == "cancelled":
            print(f"任务已取消: {json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps({"status": "processing", "video_id": video_id}))


def main():
    """入口：查询已提交的 Sora 视频任务并输出结果 JSON。"""
    args = parse_args()
    poll_until_done(api_key(), args.video_id, args.output)


if __name__ == "__main__":
    main()
