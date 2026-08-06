#!/usr/bin/env python3
"""提交可灵 Omni-Image 图像生成任务并在进程内轮询直到完成或达到安全时限。

用法：
    python3 generate_omni_image.py --prompt "一只在雪地里奔跑的金毛犬" --output-dir /path/to/dir
    python3 generate_omni_image.py --prompt "..." --result-type series --series-amount 4 --output-dir /path/to/dir
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

SUBMIT_URL = "https://app-dvtmyuucfs3l-api-DLEO4zbkvoea-gateway.appmiaoda.com/v1/images/omni-image"
QUERY_URL = "https://app-dvtmyuucfs3l-api-79jK6nw4zxDL-gateway.appmiaoda.com/v1/images/omni-image"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def get_api_key():
    """从环境变量读取 API Key，未设置则报错退出。"""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        print("Error: INTEGRATIONS_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    return key


def image_to_b64(path):
    """读取本地图片文件并编码为 Base64 字符串。"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def build_image_list(images, image_urls):
    """将本地图片路径和图片 URL 合并为接口所需的图片列表。"""
    image_list = []
    for path in images or []:
        image_list.append({"image": image_to_b64(path)})
    for url in image_urls or []:
        image_list.append({"image": url})
    return image_list or None


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


def submit(api_key, args):
    """提交 Omni-Image 图像生成任务并返回任务 ID。"""
    body = {
        "prompt": args.prompt,
        "model_name": args.model_name,
        "resolution": args.resolution,
    }
    if args.aspect_ratio:
        body["aspect_ratio"] = args.aspect_ratio
    image_list = build_image_list(args.image, args.image_url)
    if image_list:
        body["image_list"] = image_list

    if args.result_type == "series":
        if not args.series_amount:
            print("Error: --series-amount is required when --result-type=series", file=sys.stderr)
            sys.exit(1)
        body["result_type"] = "series"
        body["series_amount"] = args.series_amount
    else:
        body["result_type"] = "single"
        body["n"] = args.num

    json_resp = request_json(SUBMIT_URL, api_key, method="POST", body=body)
    if json_resp.get("code") != 0:
        print(f"Error: API error {json_resp.get('code')}: {json_resp.get('message')}", file=sys.stderr)
        sys.exit(1)
    return json_resp["data"]["task_id"]


def query(api_key, task_id):
    """查询图像生成任务并返回结果数据。"""
    url = f"{QUERY_URL}/{task_id}"
    json_resp = request_json(url, api_key, method="GET")
    if json_resp.get("code") != 0:
        print(f"Error: API error {json_resp.get('code')}: {json_resp.get('message')}", file=sys.stderr)
        sys.exit(1)
    return json_resp["data"]


def download(url, output_path):
    """下载图片文件并保存到本地路径。"""
    try:
        urllib.request.urlretrieve(url, output_path)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"Error: failed to download result: {e}", file=sys.stderr)
        sys.exit(1)


def collect_images(task_result):
    """从任务结果中提取生成的图片列表。"""
    result_type = task_result.get("result_type")
    key = "series_images" if result_type == "series" else "images"
    return task_result.get(key) or []


def save_images(images, output_dir, task_id):
    """将生成的图片下载保存到输出目录，未指定目录则只返回 URL。"""
    if not output_dir:
        return [{"url": img["url"]} for img in images]
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    for idx, img in enumerate(images):
        file_path = os.path.join(output_dir, f"{task_id}_{idx}.jpg")
        download(img["url"], file_path)
        saved.append({"url": img["url"], "file": file_path})
    return saved


def main():
    """入口：解析参数、提交并轮询 Omni-Image 任务，输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="提交可灵 Omni-Image 图像生成任务并轮询直到完成")
    parser.add_argument("--prompt", required=True, help="文本提示词，最多 2500 字符")
    parser.add_argument(
        "--model-name", default="kling-image-o1",
        choices=["kling-image-o1", "kling-v3-omni"],
        help="模型名称，默认 kling-image-o1",
    )
    parser.add_argument("--resolution", default="1k", choices=["1k", "2k", "4k"], help="清晰度，默认 1k")
    parser.add_argument("--result-type", default="single", choices=["single", "series"], help="结果类型，默认 single")
    parser.add_argument("-n", "--num", type=int, default=1, help="single 模式下生成数量 [1,9]，默认 1")
    parser.add_argument("--series-amount", type=int, help="series 模式下组图数量 [2,9]，series 模式必填")
    parser.add_argument("--aspect-ratio", help="画面纵横比，如 16:9/9:16/1:1/auto 等")
    parser.add_argument("--image", action="append", help="参考图本地路径，可重复传入")
    parser.add_argument("--image-url", action="append", help="参考图 URL，可重复传入")
    parser.add_argument("--output-dir", help="下载图片到该目录（可选）")
    args = parser.parse_args()

    api_key = get_api_key()
    task_id = submit(api_key, args)

    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
        data = query(api_key, task_id)
        status = data.get("task_status")
        if status == "succeed":
            task_result = data.get("task_result") or {}
            images = collect_images(task_result)
            if not images:
                print("Error: task succeeded but no image returned", file=sys.stderr)
                sys.exit(1)
            saved = save_images(images, args.output_dir, task_id)
            result = {"status": "succeed", "task_id": task_id, "images": saved}
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
