#!/usr/bin/env python3
"""
Submit a MiniMax subject-reference video generation task and poll until done.

Usage:
    python3 generate_subject_video.py --image /path/to/face.jpg \
        --prompt "A girl runs toward the camera and winks with a smile." \
        [--output /path/to/output.mp4]
    python3 generate_subject_video.py --image-url "https://example.com/face.jpg" --prompt "..."

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
import base64
import argparse
import urllib.request
import urllib.parse
import urllib.error


SUBMIT_URL = "https://app-dvtmyuucfs3l-api-oLpZbv47qvea-gateway.appmiaoda.com/v1/video_generation"
QUERY_URL = "https://app-dvtmyuucfs3l-api-GYX1bq2l5vWa-gateway.appmiaoda.com/v1/query/video_generation"
RETRIEVE_URL = "https://app-dvtmyuucfs3l-api-VaOw5V2Pbqoa-gateway.appmiaoda.com/v1/files/retrieve"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", help="视频文本描述，最大 2000 字符")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--image", help="人物主体参考图片本地路径")
    g.add_argument("--image-url", dest="image_url", help="人物主体参考图片 URL")
    p.add_argument("--output", help="下载生成视频到该本地路径（可选）")
    return p.parse_args()


def request_json(url: str, api_key: str, payload: dict) -> dict:
    """调用上游接口并返回响应。"""
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


def image_ref(args) -> str:
    """返回图片引用：本地路径转 base64，否则返回 URL。"""
    if args.image:
        with open(args.image, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return args.image_url


def submit(api_key: str, args) -> str:
    """提交任务并返回任务标识。"""
    payload = {
        "model": "S2V-01",
        "prompt_optimizer": True,
        "subject_reference": [{"type": "character", "image": [image_ref(args)]}],
    }
    if args.prompt:
        payload["prompt"] = args.prompt
    d = request_json(SUBMIT_URL, api_key, payload)
    if d.get("base_resp", {}).get("status_code") != 0:
        print(f"提交失败: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return d["task_id"]


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
    """入口：提交视频生成任务并轮询直到完成或超时。"""
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
        if status == "Success":
            file_info = retrieve(api_key, data["file_id"])
            download_url = file_info.get("download_url")
            file_path = None
            if args.output and download_url:
                download(download_url, args.output)
                file_path = args.output
            print(json.dumps({
                "status": "succeed",
                "task_id": task_id,
                "url": download_url,
                "file": file_path,
                "filename": file_info.get("filename"),
            }))
            return
        if status == "Fail":
            print(f"任务失败: {json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
            sys.exit(1)
        # Preparing / Queueing / Processing → keep polling

    print(json.dumps({"status": "processing", "task_id": task_id}))


if __name__ == "__main__":
    main()
