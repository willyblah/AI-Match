#!/usr/bin/env python3
"""提交文生视频任务（百度千帆 Kling）并在进程内轮询直到完成或达到安全时限。

用法：
    python3 generate_text_to_video.py --prompt "一只猫在草地上奔跑" --output /path/to/output.mp4
    python3 generate_text_to_video.py --prompt "..." --duration 10 --model-name kling-v2-master
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SUBMIT_URL = "https://app-dvtmyuucfs3l-api-o9wN672BkyMa-gateway.appmiaoda.com/beta/video/generations/kling/text2video"
QUERY_URL = "https://app-dvtmyuucfs3l-api-nYWNozBb5qML-gateway.appmiaoda.com/beta/video/generations/kling/text2video"

POLL_INTERVAL_S = 5
SAFE_LIMIT_S = 550


def get_api_key():
    """读取环境变量中的 API Key，缺失则报错退出。"""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        print("Error: INTEGRATIONS_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    return key


def request_json(url, api_key, method="GET", body=None):
    """发起 HTTP 请求并返回解析后的 JSON。"""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-Gateway-Authorization", f"Bearer {api_key}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
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


def submit(api_key, prompt, duration, model_name):
    """提交文生视频任务并返回 task_id。"""
    body = {"model_name": model_name, "prompt": prompt, "duration": duration}
    json_resp = request_json(SUBMIT_URL, api_key, method="POST", body=body)
    if json_resp.get("code") != 0:
        print(f"Error: API error {json_resp.get('code')}: {json_resp.get('message')}", file=sys.stderr)
        sys.exit(1)
    return json_resp["data"]["task_id"]


def query(api_key, task_id):
    """查询指定任务的当前状态。"""
    url = f"{QUERY_URL}?task_id={urllib.parse.quote(task_id)}"
    json_resp = request_json(url, api_key, method="GET")
    if json_resp.get("code") != 0:
        print(f"Error: API error {json_resp.get('code')}: {json_resp.get('message')}", file=sys.stderr)
        sys.exit(1)
    return json_resp["data"]


def download(url, output_path):
    """下载文件并保存到本地路径。"""
    try:
        urllib.request.urlretrieve(url, output_path)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"Error: failed to download result: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """入口：提交文生视频任务并轮询直到完成，输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="提交文生视频任务并轮询直到完成")
    parser.add_argument("--prompt", required=True, help="正向文本提示词，最大 2500 字符")
    parser.add_argument("--duration", default="5", choices=["5", "10"], help="视频时长（秒），默认 5")
    parser.add_argument(
        "--model-name",
        default="kling-v1-6",
        choices=["kling-v1", "kling-v1-6", "kling-v2-master", "kling-v2-1-master"],
        help="生成模型，默认 kling-v1-6",
    )
    parser.add_argument("--output", help="下载视频到本地路径（可选）")
    args = parser.parse_args()

    api_key = get_api_key()
    task_id = submit(api_key, args.prompt, args.duration, args.model_name)

    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
        data = query(api_key, task_id)
        status = data.get("task_status")
        if status == "succeed":
            videos = (data.get("task_result") or {}).get("videos") or []
            if not videos:
                print("Error: task succeeded but no video returned", file=sys.stderr)
                sys.exit(1)
            video_url = videos[0]["url"]
            result = {"status": "succeed", "task_id": task_id, "url": video_url}
            if args.output:
                download(video_url, args.output)
                result["file"] = args.output
            print(json.dumps(result, ensure_ascii=False))
            return
        if status == "failed":
            msg = data.get("task_status_msg", "unknown reason")
            print(f"Error: task failed: {msg}", file=sys.stderr)
            sys.exit(1)
        # submitted / processing → keep polling

    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
