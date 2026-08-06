#!/usr/bin/env python3
"""
Poll an already-submitted Kling image-to-video task by task_id (does NOT submit a new task).

Use this when generate_image_to_video.py returned {"status": "processing", "task_id": "..."}.

Exit codes:
    0 - success, prints JSON:
        {"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4"}
        or, if not finished within the safe time limit:
        {"status":"processing","task_id":"..."}
    1 - API or argument error
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


QUERY_URL_BASE = "https://app-dvtmyuucfs3l-api-zYkZzgKook1L-gateway.appmiaoda.com/v1/videos/image2video"
POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True, dest="task_id")
    p.add_argument("--output", help="下载生成视频到该本地路径（可选）")
    return p.parse_args()


def api_key():
    """从环境变量读取 API Key，未设置则报错退出。"""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        print("INTEGRATIONS_API_KEY is required", file=sys.stderr)
        sys.exit(1)
    return key


def get_json(url, key):
    """发送 GET 请求并返回解析后的 JSON 响应。"""
    req = urllib.request.Request(
        url,
        headers={"X-Gateway-Authorization": "Bearer " + key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP %s: %s" % (e.code, body))


def unwrap_response(data):
    """校验响应状态码并提取数据字段。"""
    if data.get("code") not in (None, 0):
        raise RuntimeError("API error %s: %s" % (data.get("code"), data.get("message")))
    return data.get("data", data)


def extract_video_url(data):
    """从任务结果中提取生成视频的 URL。"""
    result = data.get("task_result") or data.get("taskResult") or {}
    videos = result.get("videos") or data.get("videos") or []
    if videos:
        first = videos[0]
        if isinstance(first, dict):
            return first.get("url") or first.get("video_url") or first.get("videoUrl")
        if isinstance(first, str):
            return first
    return result.get("url") or data.get("url")


def download(url, output):
    """下载视频文件并保存到本地路径。"""
    if not output:
        return None
    parent = os.path.dirname(os.path.abspath(output))
    if parent:
        os.makedirs(parent, exist_ok=True)
    urllib.request.urlretrieve(url, output)
    return output


def poll_task(task_id, key, output):
    """轮询任务状态直到完成、失败或达到安全时限。"""
    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        data = unwrap_response(get_json(QUERY_URL_BASE + "/" + urllib.parse.quote(task_id), key))
        status = data.get("task_status") or data.get("status")
        if status == "succeed":
            url = extract_video_url(data)
            if not url:
                raise RuntimeError("succeed response missing video url: %s" % json.dumps(data, ensure_ascii=False))
            print(json.dumps(
                {"status": "succeed", "task_id": task_id, "url": url, "file": download(url, output)},
                ensure_ascii=False,
            ))
            return
        if status in ("failed", "failure"):
            msg = data.get("task_status_msg") or data.get("message") or "unknown error"
            raise RuntimeError("Task %s failed: %s" % (task_id, msg))
        time.sleep(POLL_INTERVAL_S)
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


def main():
    """入口：查询任务状态并输出结果 JSON。"""
    args = parse_args()
    key = api_key()
    try:
        poll_task(args.task_id, key, args.output)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
