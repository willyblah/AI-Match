#!/usr/bin/env python3
"""继续查询 Seedance 2.0 视频生成任务（不会重新提交任务）。

当 generate_seedance_video.py 在 550s 内未完成时，用此脚本接力轮询。

用法：
    python3 query_seedance_video.py --task-id "doubao.p1.cgt-xxxx"
    python3 query_seedance_video.py --task-id "..." --output /tmp/video.mp4

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

QUERY_URL_TPL = "https://app-dvtmyuucfs3l-api-Q9KWPzO1Eg69-gateway.appmiaoda.com/doubao/v3/contents/generations/tasks/{task_id}"

POLL_INTERVAL_S = 5
SAFE_LIMIT_S = 550

# 上游任务状态：queued（排队）→ running（生成中）→ succeeded（完成）；失败为 failed/error 等。
SUCCESS_STATES = {"succeeded", "success", "completed", "done"}
FAILED_STATES = {"failed", "error", "cancelled", "canceled"}


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def get_api_key():
    """读取环境变量中的 API Key，缺失则报错退出。"""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        fail("INTEGRATIONS_API_KEY is required")
    return key


def query_task(api_key, task_id):
    """调用上游查询任务接口并返回响应。"""
    url = QUERY_URL_TPL.format(task_id=task_id)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, detail[:1000]))
    except urllib.error.URLError as exc:
        fail("Network error: " + str(exc.reason))

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fail("Response is not valid JSON: " + text[:500])


def download(url, output_path):
    """下载文件并保存到本地路径。"""
    try:
        urllib.request.urlretrieve(url, output_path)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        fail("Failed to download result: %s" % e)


def main():
    """入口：轮询已提交的视频任务直到完成并打印结果。"""
    parser = argparse.ArgumentParser(description="继续查询 Seedance 视频任务，不会重新提交任务")
    parser.add_argument("--task-id", required=True, help="已有任务 ID")
    parser.add_argument("--output", help="下载视频到本地路径（可选）")
    args = parser.parse_args()

    api_key = get_api_key()
    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        data = query_task(api_key, args.task_id)
        status = (data.get("status") or "").lower()
        if status in SUCCESS_STATES:
            video_url = (data.get("content") or {}).get("video_url", "")
            result = {"status": "succeed", "task_id": args.task_id, "url": video_url}
            if args.output and video_url:
                download(video_url, args.output)
                result["file"] = args.output
            print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
            return
        if status in FAILED_STATES:
            fail("Task failed: " + json.dumps(data, ensure_ascii=False))
        # queued / running / processing / pending → keep polling
        time.sleep(POLL_INTERVAL_S)

    print(json.dumps({"status": "processing", "task_id": args.task_id},
                     ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
