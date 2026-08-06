#!/usr/bin/env python3
"""
Submit a Kling image-expand task and poll until done.

Exit codes:
    0 - success, prints JSON:
        {"status":"succeed","task_id":"...","images":[{"url":"https://...","file":"/path/to/img_0.png"}]}
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


SUBMIT_URL = "https://app-dvtmyuucfs3l-api-Q9KWnzwVQMk9-gateway.appmiaoda.com/v1/images/editing/expand"
QUERY_URL_BASE = "https://app-dvtmyuucfs3l-api-rLobR6vwZJJ9-gateway.appmiaoda.com/v1/images/editing/expand"
POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def ratio(value):
    """校验并转换扩图比例参数。"""
    f = float(value)
    if not (0 <= f <= 2):
        raise argparse.ArgumentTypeError("must be in range [0, 2]")
    return f


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    input_group = p.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", help="参考图片本地路径")
    input_group.add_argument("--image-url", help="参考图片 URL")
    p.add_argument("--up-ratio", type=ratio, default=0.0, help="向上扩充倍数 [0, 2]")
    p.add_argument("--down-ratio", type=ratio, default=0.0, help="向下扩充倍数 [0, 2]")
    p.add_argument("--left-ratio", type=ratio, default=0.0, help="向左扩充倍数 [0, 2]")
    p.add_argument("--right-ratio", type=ratio, default=0.0, help="向右扩充倍数 [0, 2]")
    p.add_argument("--prompt", default="", help="可选正向提示词")
    p.add_argument("-n", "--num", type=int, default=1, help="生成图片数量 [1, 9]")
    p.add_argument("--output-dir", help="结果图片输出目录（可选，多张图会依次编号命名）")
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


def unwrap_single(data):
    """校验响应状态码并提取单个数据对象。"""
    if data.get("code") not in (None, 0):
        raise RuntimeError("API error %s: %s" % (data.get("code"), data.get("message")))
    return data.get("data", data)


def unwrap_list(data):
    """校验响应状态码并提取列表数据。"""
    if data.get("code") not in (None, 0):
        raise RuntimeError("API error %s: %s" % (data.get("code"), data.get("message")))
    payload = data.get("data", data)
    if isinstance(payload, list):
        if not payload:
            raise RuntimeError("Task not found")
        return payload[0]
    return payload


def submit_task(args, key):
    """提交图片扩展任务并返回任务 ID。"""
    payload = {
        "image": args.image_url if args.image_url else file_to_base64(args.image),
        "up_expansion_ratio": args.up_ratio,
        "down_expansion_ratio": args.down_ratio,
        "left_expansion_ratio": args.left_ratio,
        "right_expansion_ratio": args.right_ratio,
        "prompt": args.prompt,
        "n": args.num,
    }
    data = unwrap_single(post_json(SUBMIT_URL, key, payload))
    task_id = data.get("task_id") or data.get("taskId")
    if not task_id:
        raise RuntimeError("submit response missing task_id: %s" % json.dumps(data, ensure_ascii=False))
    return task_id


def extract_images(data):
    """从任务结果中提取生成的图片列表。"""
    result = data.get("task_result") or data.get("taskResult") or {}
    return result.get("images") or []


def download_images(images, output_dir):
    """将生成图片下载到输出目录，未指定目录则只返回 URL。"""
    if not output_dir:
        return [{"url": img.get("url"), "file": None} for img in images]
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for img in images:
        url = img.get("url")
        idx = img.get("index", len(downloaded))
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".png"
        file_path = os.path.join(output_dir, "image_%s%s" % (idx, ext))
        urllib.request.urlretrieve(url, file_path)
        downloaded.append({"url": url, "file": file_path})
    return downloaded


def poll_task(task_id, key, output_dir):
    """轮询任务状态直到完成、失败或达到安全时限。"""
    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
        data = unwrap_list(get_json(QUERY_URL_BASE + "/" + urllib.parse.quote(task_id), key))
        status = data.get("task_status") or data.get("status")
        if status == "succeed":
            images = extract_images(data)
            if not images:
                raise RuntimeError("succeed response missing images: %s" % json.dumps(data, ensure_ascii=False))
            print(json.dumps(
                {"status": "succeed", "task_id": task_id, "images": download_images(images, output_dir)},
                ensure_ascii=False,
            ))
            return
        if status in ("failed", "failure"):
            msg = data.get("task_status_msg") or data.get("message") or "unknown error"
            raise RuntimeError("Task %s failed: %s" % (task_id, msg))
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


def main():
    """入口：解析参数、提交并轮询图片扩展任务，输出结果 JSON。"""
    args = parse_args()
    key = api_key()
    try:
        task_id = submit_task(args, key)
        poll_task(task_id, key, args.output_dir)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
