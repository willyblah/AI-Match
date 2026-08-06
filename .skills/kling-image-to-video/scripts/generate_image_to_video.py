#!/usr/bin/env python3
"""
Submit a Kling image-to-video task and poll until done.

Exit codes:
    0 - success, prints JSON:
        {"status":"succeed","task_id":"...","url":"https://...","file":"/path/to/output.mp4"}
        or, if not finished within the safe time limit:
        {"status":"processing","task_id":"..."}
    1 - API, argument, or download error
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


SUBMIT_URL = "https://app-dvtmyuucfs3l-api-DY8MN3QBydBa-gateway.appmiaoda.com/v1/videos/image2video"
QUERY_URL_BASE = "https://app-dvtmyuucfs3l-api-zYkZzgKook1L-gateway.appmiaoda.com/v1/videos/image2video"
POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


MODEL_NAMES = [
    "kling-v1",
    "kling-v1-5",
    "kling-v1-6",
    "kling-v2-master",
    "kling-v2-1",
    "kling-v2-1-master",
    "kling-v2-5-turbo",
    "kling-v2-6",
]


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    input_group = p.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", help="首帧图片本地路径")
    input_group.add_argument("--image-url", help="首帧图片 URL")
    tail_group = p.add_mutually_exclusive_group()
    tail_group.add_argument("--image-tail", help="尾帧图片本地路径（可选）")
    tail_group.add_argument("--image-tail-url", help="尾帧图片 URL（可选）")
    p.add_argument("--prompt", default="", help="正向提示词")
    p.add_argument("--model-name", default="kling-v1", choices=MODEL_NAMES)
    p.add_argument("--duration", default="5", choices=["5", "10"])
    p.add_argument("--mode", default="std", choices=["std", "pro"])
    p.add_argument("--output", help="下载生成视频到该本地路径（可选）")
    return p.parse_args()


def api_key():
    """从环境变量读取 API Key，未设置则报错退出。"""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        print("INTEGRATIONS_API_KEY is required", file=sys.stderr)
        sys.exit(1)
    return key


def file_to_base64(path):
    """读取本地文件并编码为 Base64 字符串。"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def post_json(url, key, payload):
    """发送 POST JSON 请求并返回解析后的响应。"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": "Bearer " + key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP %s: %s" % (e.code, body))


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


def submit_task(args, key):
    """提交图生视频任务并返回任务 ID。"""
    payload = {
        "model_name": args.model_name,
        "image": args.image_url if args.image_url else file_to_base64(args.image),
        "mode": args.mode,
        "duration": args.duration,
    }
    if args.image_tail_url:
        payload["image_tail"] = args.image_tail_url
    elif args.image_tail:
        payload["image_tail"] = file_to_base64(args.image_tail)
    if args.prompt:
        payload["prompt"] = args.prompt

    data = unwrap_response(post_json(SUBMIT_URL, key, payload))
    task_id = data.get("task_id") or data.get("taskId") or data.get("id")
    if not task_id:
        raise RuntimeError("submit response missing task_id: %s" % json.dumps(data, ensure_ascii=False))
    return task_id


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
        time.sleep(POLL_INTERVAL_S)
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
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


def main():
    """入口：解析参数、提交并轮询图生视频任务，输出结果 JSON。"""
    args = parse_args()
    key = api_key()
    try:
        task_id = submit_task(args, key)
        poll_task(task_id, key, args.output)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
