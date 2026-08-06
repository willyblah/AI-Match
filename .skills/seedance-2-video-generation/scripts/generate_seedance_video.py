#!/usr/bin/env python3
"""提交 Seedance 2.0 视频生成任务并在进程内轮询直到完成或达到安全时限。

用法：
    # 纯文生视频
    python3 generate_seedance_video.py --prompt "一只猫在草地上奔跑"

    # 图生视频（首帧）
    python3 generate_seedance_video.py --prompt "让画面动起来" \
        --first-frame-url "https://example.com/frame1.jpg"

    # 图生视频（首尾帧）
    python3 generate_seedance_video.py --prompt "从白天渐变为黑夜" \
        --first-frame-url "https://.../start.jpg" \
        --last-frame-url "https://.../end.jpg"

    # 完全自定义 content 数组
    python3 generate_seedance_video.py --content '[{"type":"text","text":"..."}]'

脚本执行超时为 600s，内部安全时限 550s。
成功输出：{"status":"succeed","task_id":"...","url":"..."}
超时输出：{"status":"processing","task_id":"..."} （可用 query_seedance_video.py 继续轮询）

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

SUBMIT_URL = "https://app-dvtmyuucfs3l-api-nYWN4kMJ1v7L-gateway.appmiaoda.com/doubao/v3/contents/generations/tasks"
QUERY_URL_TPL = "https://app-dvtmyuucfs3l-api-Q9KWPzO1Eg69-gateway.appmiaoda.com/doubao/v3/contents/generations/tasks/{task_id}"

POLL_INTERVAL_S = 5
SAFE_LIMIT_S = 550

# 上游任务状态：queued（排队）→ running（生成中）→ succeeded（完成）；失败为 failed/error 等。
SUCCESS_STATES = {"succeeded", "succeed", "completed", "done", "success"}
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


def request_json(url, api_key, method="GET", body=None):
    """发起 HTTP 请求并返回解析后的 JSON。"""
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (e.code, err_body[:1000]))
    except urllib.error.URLError as e:
        fail("Network error: %s" % e.reason)


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser(description="提交 Seedance 2.0 视频任务并轮询直到完成")
    p.add_argument("--prompt", help="视频描述文本（与 --content 二选一）")
    p.add_argument("--content", help='完整 content 数组 JSON，覆盖 --prompt 及各 *-url 参数')
    p.add_argument("--first-frame-url", help="首帧图片 URL")
    p.add_argument("--last-frame-url", help="尾帧图片 URL")
    p.add_argument("--reference-image-url", action="append", default=[],
                   help="参考图 URL，可重复 (最多 9 个)")
    p.add_argument("--reference-audio-url", action="append", default=[],
                   help="参考音频 URL，可重复 (最多 3 个)")
    p.add_argument("--model", default="doubao-seedance-2-0-260128",
                   help="模型 ID，默认 doubao-seedance-2-0-260128")
    p.add_argument("--ratio", help="视频比例：16:9/4:3/1:1/3:4/9:16/21:9/adaptive")
    p.add_argument("--duration", type=int, help="时长（秒），默认 5")
    p.add_argument("--resolution", help="480p/720p/1080p，默认 720p")
    p.add_argument("--generate-audio", choices=["true", "false"], help="是否含同步音频")
    p.add_argument("--watermark", choices=["true", "false"], help="是否含水印")
    p.add_argument("--output", help="下载视频到本地路径（可选）")
    return p.parse_args()


def build_content(args):
    """构造 content 数组。"""
    if args.content:
        try:
            return json.loads(args.content)
        except json.JSONDecodeError as exc:
            fail("--content is not valid JSON: " + str(exc))

    if not args.prompt:
        fail("Either --prompt or --content is required")

    content = [{"type": "text", "text": args.prompt}]
    if args.first_frame_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": args.first_frame_url},
            "role": "first_frame",
        })
    if args.last_frame_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": args.last_frame_url},
            "role": "last_frame",
        })
    for url in args.reference_image_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": url},
            "role": "reference_image",
        })
    for url in args.reference_audio_url:
        content.append({
            "type": "audio_url",
            "audio_url": {"url": url},
            "role": "reference_audio",
        })
    return content


def submit(api_key, args):
    """提交视频生成任务并返回 task_id。"""
    payload = {"model": args.model, "content": build_content(args)}
    if args.ratio:
        payload["ratio"] = args.ratio
    if args.duration is not None:
        payload["duration"] = args.duration
    if args.resolution:
        payload["resolution"] = args.resolution
    if args.generate_audio is not None:
        payload["generate_audio"] = args.generate_audio == "true"
    if args.watermark is not None:
        payload["watermark"] = args.watermark == "true"

    result = request_json(SUBMIT_URL, api_key, method="POST", body=payload)
    task_id = result.get("id")
    if not task_id:
        fail("Create task did not return an id: " + json.dumps(result, ensure_ascii=False))
    return task_id


def query_task(api_key, task_id):
    """查询指定任务的当前状态。"""
    url = QUERY_URL_TPL.format(task_id=task_id)
    return request_json(url, api_key, method="GET")


def download(url, output_path):
    """下载文件并保存到本地路径。"""
    try:
        urllib.request.urlretrieve(url, output_path)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        fail("Failed to download result: %s" % e)


def main():
    """入口：提交视频生成任务并轮询直到完成，输出结果 JSON。"""
    args = parse_args()
    api_key = get_api_key()
    task_id = submit(api_key, args)

    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
        data = query_task(api_key, task_id)
        status = (data.get("status") or "").lower()
        if status in SUCCESS_STATES:
            video_url = (data.get("content") or {}).get("video_url", "")
            result = {"status": "succeed", "task_id": task_id, "url": video_url}
            if args.output and video_url:
                download(video_url, args.output)
                result["file"] = args.output
            print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
            return
        if status in FAILED_STATES:
            fail("Task failed: " + json.dumps(data, ensure_ascii=False))
        # queued / running / processing / pending → keep polling

    # 超时：输出 task_id 以便 query 脚本继续轮询
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
