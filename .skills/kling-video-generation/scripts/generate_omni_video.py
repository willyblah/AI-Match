#!/usr/bin/env python3
"""提交可灵 Omni-Video 视频生成任务并在进程内轮询直到完成或达到安全时限。

支持文生视频、图生视频（首帧/尾帧参考）两种最常用模式。

用法：
    python3 generate_omni_video.py --prompt "一只橘猫在草地上慵懒地打滚" --output /path/to/output.mp4
    python3 generate_omni_video.py --prompt "让<<<image_1>>>中的人物向镜头挥手" \
        --image /path/to/first.png --output /path/to/output.mp4
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

SUBMIT_URL = "https://app-dvtmyuucfs3l-api-oLpZb03wbNBa-gateway.appmiaoda.com/v1/videos/omni-video"
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


def image_to_data(path):
    """读取本地图片文件并编码为接口所需的数据。"""
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return b64


def request_json(url, api_key, method="GET", body=None):
    """发送 HTTP 请求并返回解析后的 JSON 响应。"""
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


def build_image_list(image, image_url, image_tail, image_tail_url):
    """构建首尾帧图片列表参数。"""
    image_list = []
    if image:
        image_list.append({"image_url": image_to_data(image), "type": "first_frame"})
    elif image_url:
        image_list.append({"image_url": image_url, "type": "first_frame"})
    if image_tail:
        image_list.append({"image_url": image_to_data(image_tail), "type": "end_frame"})
    elif image_tail_url:
        image_list.append({"image_url": image_tail_url, "type": "end_frame"})
    return image_list or None


def submit(api_key, args):
    """提交 Omni-Video 视频生成任务并返回任务 ID。"""
    body = {"model_name": args.model_name, "mode": args.mode}
    if args.prompt:
        body["prompt"] = args.prompt
    image_list = build_image_list(args.image, args.image_url, args.image_tail, args.image_tail_url)
    if image_list:
        body["image_list"] = image_list
        # 有首帧参考时不传 aspect_ratio（上游不支持）
        if not any(i.get("type") == "first_frame" for i in image_list) and args.aspect_ratio:
            body["aspect_ratio"] = args.aspect_ratio
    elif args.aspect_ratio:
        body["aspect_ratio"] = args.aspect_ratio
    if args.duration:
        body["duration"] = args.duration

    json_resp = request_json(SUBMIT_URL, api_key, method="POST", body=body)
    if json_resp.get("code") != 0:
        print(f"Error: API error {json_resp.get('code')}: {json_resp.get('message')}", file=sys.stderr)
        sys.exit(1)
    return json_resp["data"]["task_id"]


def query(api_key, task_id):
    """查询视频生成任务并返回结果数据。"""
    url = f"{QUERY_URL}/{task_id}"
    json_resp = request_json(url, api_key, method="GET")
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
    """入口：解析参数、提交并轮询 Omni-Video 任务，输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="提交可灵 Omni-Video 视频生成任务并轮询直到完成")
    parser.add_argument("--prompt", help="文本提示词，最多 2500 字符；文生视频必填")
    parser.add_argument(
        "--model-name", default="kling-video-o1",
        choices=["kling-video-o1", "kling-v3-omni"],
        help="模型名称，默认 kling-video-o1",
    )
    parser.add_argument("--mode", default="pro", choices=["std", "pro"], help="生成模式，默认 pro")
    parser.add_argument("--aspect-ratio", choices=["16:9", "9:16", "1:1"], help="画面纵横比；未使用首帧参考时建议指定")
    parser.add_argument("--duration", default="5", help="视频时长（秒），3~15，默认 5")
    parser.add_argument("--image", help="首帧参考图本地路径")
    parser.add_argument("--image-url", help="首帧参考图 URL")
    parser.add_argument("--image-tail", help="尾帧参考图本地路径")
    parser.add_argument("--image-tail-url", help="尾帧参考图 URL")
    parser.add_argument("--output", help="下载视频到本地路径（可选）")
    args = parser.parse_args()

    if not args.prompt and not (args.image or args.image_url):
        print("Error: 必须提供 --prompt 或 --image/--image-url 中的至少一项", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key()
    task_id = submit(api_key, args)

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
