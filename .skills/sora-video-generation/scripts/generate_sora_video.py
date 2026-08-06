#!/usr/bin/env python3
"""
Submit a Sora 2 video generation task (Create Video / Video from Reference / Remix Video)
and poll until done.

Usage:
    # Create Video - 文生视频
    python3 generate_sora_video.py --prompt "A cat riding a motorcycle at night" \
        [--size 720x1280] [--seconds 8] [--output /path/to/output.mp4]

    # Create Video - 图生视频（可选参考图，作为 input_reference）
    python3 generate_sora_video.py --prompt "..." --image /path/to/ref.jpg \
        [--size 720x1280] [--seconds 8] --output /path/to/output.mp4

    # Video from Reference（以参考图为首帧锚点，强制匹配分辨率）
    python3 generate_sora_video.py --from-reference --prompt "..." \
        --image /path/to/ref.jpg --size 720x1280 [--seconds 8] --output /path/to/output.mp4

    # Remix Video（对已完成视频做局部编辑）
    python3 generate_sora_video.py --remix-video-id video_abc123 --prompt "把光照调暗" \
        --output /path/to/output.mp4

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
import urllib.parse
import urllib.error


CREATE_VIDEO_URL = "https://app-dvtmyuucfs3l-api-Xa6Jew6JjAqa-gateway.appmiaoda.com/openai/v1/videos"
VIDEO_FROM_REFERENCE_URL = "https://app-dvtmyuucfs3l-api-W9z3qro1AVZL-gateway.appmiaoda.com/openai/v1/videos"
REMIX_VIDEO_URL = "https://app-dvtmyuucfs3l-api-M9v0wP10kQjY-gateway.appmiaoda.com/openai/v1/videos/remix"
QUERY_URL = "https://app-dvtmyuucfs3l-api-M9v0w87KjxoY-gateway.appmiaoda.com/query"

POLL_INTERVAL_S = 8
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", help="视频描述（Create Video / Video from Reference 必填；Remix Video 时为修改指令，必填）")
    p.add_argument("--image", help="参考图本地路径（作为 input_reference）")
    p.add_argument("--image-url", dest="image_url", help="参考图 URL（作为 input_reference，会自动下载）")
    p.add_argument("--size", default="720x1280", choices=["720x1280", "1280x720"], help="分辨率，默认 720x1280")
    p.add_argument("--seconds", type=int, default=8, choices=[4, 8, 12], help="视频时长，默认 8")
    p.add_argument("--model", default="sora-2")
    p.add_argument("--from-reference", dest="from_reference", action="store_true",
                    help="触发 Video from Reference 模式（需要参考图，强制匹配分辨率）")
    p.add_argument("--remix-video-id", dest="remix_video_id", help="触发 Remix Video 模式：已完成视频的 ID")
    p.add_argument("--output", help="下载生成视频到该本地路径（可选）")
    args = p.parse_args()

    modes = [bool(args.from_reference), bool(args.remix_video_id)]
    if sum(modes) > 1:
        p.error("--from-reference 与 --remix-video-id 互斥，只能选择一种提交模式")

    if args.remix_video_id:
        if not args.prompt:
            p.error("Remix Video 模式需要 --prompt 描述修改内容")
    elif args.from_reference:
        if not args.prompt:
            p.error("Video from Reference 模式需要 --prompt")
        if not (args.image or args.image_url):
            p.error("Video from Reference 模式需要 --image 或 --image-url 提供参考图")
    else:
        if not args.prompt:
            p.error("Create Video 模式需要 --prompt")

    return args


def guess_content_type(path_or_url: str) -> str:
    """根据文件名或 URL 猜测图片的 Content-Type。"""
    lower = path_or_url.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def load_image_bytes(path: str, url: str):
    """Return (filename, content_type, raw_bytes) for the reference image, from a local
    path or a URL. Bytes are used as-is, no re-encoding/compression."""
    if path:
        with open(path, "rb") as f:
            data = f.read()
        filename = os.path.basename(path) or "reference.jpg"
        return filename, guess_content_type(path), data

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            content_type = resp.headers.get("Content-Type") or guess_content_type(url)
    except urllib.error.HTTPError as e:
        print(f"Failed to fetch reference image: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Failed to fetch reference image: {e}", file=sys.stderr)
        sys.exit(1)
    filename = url.split("/")[-1].split("?")[0] or "reference.jpg"
    return filename, content_type, data


def build_multipart_body(fields: dict, file_field: str = None, filename: str = None,
                          file_content_type: str = None, file_bytes: bytes = None):
    """Hand-build a multipart/form-data body (standard library only)."""
    boundary = "----SoraVideoBoundary" + str(int(time.time() * 1000))
    crlf = "\r\n"
    parts = []

    for name, value in fields.items():
        if value is None:
            continue
        parts.append(
            f"--{boundary}{crlf}"
            f'Content-Disposition: form-data; name="{name}"{crlf}{crlf}'
            f"{value}{crlf}".encode("utf-8")
        )

    if file_field and file_bytes is not None:
        header = (
            f"--{boundary}{crlf}"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"{crlf}'
            f"Content-Type: {file_content_type}{crlf}{crlf}"
        ).encode("utf-8")
        parts.append(header + file_bytes + crlf.encode("utf-8"))

    parts.append(f"--{boundary}--{crlf}".encode("utf-8"))
    body = b"".join(parts)
    content_type_header = f"multipart/form-data; boundary={boundary}"
    return body, content_type_header


def post_multipart(url: str, api_key: str, fields: dict, file_field=None, filename=None,
                    file_content_type=None, file_bytes=None) -> dict:
    """构造 multipart 表单并调用上游接口，返回响应。"""
    body, content_type_header = build_multipart_body(
        fields, file_field, filename, file_content_type, file_bytes
    )
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": content_type_header,
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


def post_json(url: str, api_key: str, payload: dict) -> dict:
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


def submit_create_video(api_key: str, args) -> str:
    """提交文生视频（Create Video）任务并返回 video_id。"""
    fields = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "seconds": str(args.seconds),
    }
    file_field = filename = file_content_type = file_bytes = None
    if args.image or args.image_url:
        filename, file_content_type, file_bytes = load_image_bytes(args.image, args.image_url)
        file_field = "input_reference"

    d = post_multipart(
        CREATE_VIDEO_URL, api_key, fields,
        file_field=file_field, filename=filename,
        file_content_type=file_content_type, file_bytes=file_bytes,
    )
    if "id" not in d:
        print(f"Create video failed: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return d["id"]


def submit_video_from_reference(api_key: str, args) -> str:
    """提交以参考图为首帧锚点的视频生成任务并返回 video_id。"""
    filename, file_content_type, file_bytes = load_image_bytes(args.image, args.image_url)
    fields = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "seconds": str(args.seconds),
    }
    d = post_multipart(
        VIDEO_FROM_REFERENCE_URL, api_key, fields,
        file_field="input_reference", filename=filename,
        file_content_type=file_content_type, file_bytes=file_bytes,
    )
    if "id" not in d:
        print(f"Video from reference failed: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return d["id"]


def submit_remix_video(api_key: str, args) -> str:
    """提交对已完成视频的局部编辑（Remix）任务并返回 video_id。"""
    d = post_json(REMIX_VIDEO_URL, api_key, {
        "video_id": args.remix_video_id,
        "prompt": args.prompt,
    })
    if "id" not in d:
        print(f"Remix video failed: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return d["id"]


def query(api_key: str, video_id: str) -> dict:
    """查询指定视频任务的当前状态。"""
    return post_json(QUERY_URL, api_key, {"video_id": video_id})


def download(url: str, output: str):
    """下载文件并保存到本地路径。"""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp, open(output, "wb") as f:
        f.write(resp.read())


def poll_until_done(api_key: str, video_id: str, output: str):
    """轮询任务直到完成或超时。"""
    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        time.sleep(POLL_INTERVAL_S)
        data = query(api_key, video_id)
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
        # queued / started / in_progress → 继续轮询

    print(json.dumps({"status": "processing", "video_id": video_id}))


def main():
    """入口：提交 Sora 视频生成任务并轮询直到完成，输出结果 JSON。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if args.remix_video_id:
        video_id = submit_remix_video(api_key, args)
    elif args.from_reference:
        video_id = submit_video_from_reference(api_key, args)
    else:
        video_id = submit_create_video(api_key, args)

    poll_until_done(api_key, video_id, args.output)


if __name__ == "__main__":
    main()
