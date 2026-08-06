#!/usr/bin/env python3
"""
Poll an already-submitted Kling image-expand task by task_id (does NOT submit a new task).

Use this when generate_image_expand.py returned {"status": "processing", "task_id": "..."}.

Exit codes:
    0 - success, prints JSON:
        {"status":"succeed","task_id":"...","images":[{"url":"https://...","file":"/path/to/img_0.png"}]}
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


QUERY_URL_BASE = "https://app-dvtmyuucfs3l-api-rLobR6vwZJJ9-gateway.appmiaoda.com/v1/images/editing/expand"
POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True, dest="task_id")
    p.add_argument("--output-dir", help="结果图片输出目录（可选，多张图会依次编号命名）")
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
        time.sleep(POLL_INTERVAL_S)
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


def main():
    """入口：查询图片扩展任务并输出结果 JSON。"""
    args = parse_args()
    key = api_key()
    try:
        poll_task(args.task_id, key, args.output_dir)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
