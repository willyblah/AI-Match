#!/usr/bin/env python3
"""继续查询可灵 Omni-Video 视频生成任务，不会重新提交任务。"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

QUERY_URL = "https://app-dvtmyuucfs3l-api-o9wN0pyVE2ea-gateway.appmiaoda.com/v1/videos/omni-video"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def get_api_key():
    """从环境变量读取 API Key，未设置则报错退出。"""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        print("Error: INTEGRATIONS_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    return key


def request_json(url, api_key):
    """发送 GET 请求并返回解析后的 JSON 响应。"""
    req = urllib.request.Request(url, method="GET")
    req.add_header("X-Gateway-Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"Error: HTTP {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: request failed: {e}", file=sys.stderr)
        sys.exit(1)


def query(api_key, task_id):
    """查询任务状态并返回结果数据。"""
    url = f"{QUERY_URL}/{task_id}"
    json_resp = request_json(url, api_key)
    if json_resp.get("code") != 0:
        print(f"Error: API error {json_resp.get('code')}: {json_resp.get('message')}", file=sys.stderr)
        sys.exit(1)
    return json_resp["data"]


def download(url, output_path):
    """下载视频文件并保存到本地路径。"""
    try:
        urllib.request.urlretrieve(url, output_path)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"Error: failed to download result: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """入口：轮询查询视频生成任务并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="继续查询可灵 Omni-Video 任务，不会重新提交任务")
    parser.add_argument("--task-id", required=True, help="已有任务 ID")
    parser.add_argument("--output", help="下载视频到本地路径（可选）")
    args = parser.parse_args()

    api_key = get_api_key()
    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        data = query(api_key, args.task_id)
        status = data.get("task_status")
        if status == "succeed":
            videos = (data.get("task_result") or {}).get("videos") or []
            if not videos:
                print("Error: task succeeded but no video returned", file=sys.stderr)
                sys.exit(1)
            video_url = videos[0]["url"]
            result = {"status": "succeed", "task_id": args.task_id, "url": video_url}
            if args.output:
                download(video_url, args.output)
                result["file"] = args.output
            print(json.dumps(result, ensure_ascii=False))
            return
        if status == "failed":
            msg = data.get("task_status_msg", "unknown reason")
            print(f"Error: task failed: {msg}", file=sys.stderr)
            sys.exit(1)
        time.sleep(POLL_INTERVAL_S)

    print(json.dumps({"status": "processing", "task_id": args.task_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
