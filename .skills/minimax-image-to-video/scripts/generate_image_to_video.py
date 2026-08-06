#!/usr/bin/env python3
"""
Submit a MiniMax image-to-video generation task (single-frame or first/last-frame) and poll until done.

Usage:
    # Single-frame (first_frame_image + prompt)
    python3 generate_image_to_video.py --first-frame /path/to/first.jpg --prompt "..." \
        [--duration 6] [--resolution 768P] [--output /path/to/output.mp4]

    # First+last frame transition
    python3 generate_image_to_video.py --first-frame /path/to/first.jpg --last-frame /path/to/last.jpg \
        --prompt "..." [--output /path/to/output.mp4]

    # URL inputs also supported
    python3 generate_image_to_video.py --first-frame-url "https://..." --prompt "..."

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


SUBMIT_URL_SINGLE = "https://app-dvtmyuucfs3l-api-VaOw5VAJdQBa-gateway.appmiaoda.com/v1/video_generation"
SUBMIT_URL_FIRST_LAST = "https://app-dvtmyuucfs3l-api-nYWNRQr5pV1L-gateway.appmiaoda.com/v1/video_generation"
QUERY_URL = "https://app-dvtmyuucfs3l-api-eLMlPNkelVj9-gateway.appmiaoda.com/v1/query/video_generation"
RETRIEVE_URL = "https://app-dvtmyuucfs3l-api-rLyOyznAK2Ba-gateway.appmiaoda.com/v1/files/retrieve"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--first-frame", dest="first_frame", help="首帧图片本地路径")
    p.add_argument("--first-frame-url", dest="first_frame_url", help="首帧图片 URL")
    p.add_argument("--last-frame", dest="last_frame", help="尾帧图片本地路径（提供后走首尾帧模式）")
    p.add_argument("--last-frame-url", dest="last_frame_url", help="尾帧图片 URL")
    p.add_argument("--prompt", default="", help="视频文本描述，最大 2000 字符，支持 [运镜指令] 语法")
    p.add_argument("--model", default="MiniMax-Hailuo-02")
    p.add_argument("--duration", type=int, default=6, choices=[6, 10])
    p.add_argument("--resolution", default="768P", choices=["768P", "1080P"])
    p.add_argument("--output", help="下载生成视频到该本地路径（可选）")
    args = p.parse_args()
    if not (args.first_frame or args.first_frame_url or args.last_frame or args.last_frame_url):
        p.error("必须提供 --first-frame/--first-frame-url 或 --last-frame/--last-frame-url 之一")
    return args


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


def image_ref(path, url):
    """返回图片引用：本地路径转 base64，否则返回 URL。"""
    if path:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return url


def submit(api_key: str, args) -> str:
    """提交任务并返回任务标识。"""
    if args.resolution == "1080P" and args.duration != 6:
        print("1080P 分辨率仅支持 duration=6", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "duration": args.duration,
        "resolution": args.resolution,
        "prompt_optimizer": True,
    }

    last_frame = image_ref(args.last_frame, args.last_frame_url)
    first_frame = image_ref(args.first_frame, args.first_frame_url)

    if last_frame:
        payload["last_frame_image"] = last_frame
        if first_frame:
            payload["first_frame_image"] = first_frame
        submit_url = SUBMIT_URL_FIRST_LAST
    else:
        payload["first_frame_image"] = first_frame
        submit_url = SUBMIT_URL_SINGLE

    d = request_json(submit_url, api_key, payload)
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
            file_id = data.get("file_id")
            file_info = retrieve(api_key, file_id) if file_id else {}
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
