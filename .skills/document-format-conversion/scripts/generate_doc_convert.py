#!/usr/bin/env python3
"""
Submit a document-format-conversion task (image/PDF -> Word/Excel) and poll until done.

Usage:
    # Local image or PDF file
    python3 generate_doc_convert.py --file /path/to/doc.pdf [--pdf-page 1]

    # Remote image URL
    python3 generate_doc_convert.py --url "https://example.com/scan.jpg"

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "task_id": "...", "word": "...", "excel": "...", "expires": "30 days"}
        or, if not finished within the safe time limit:
        {"status": "processing", "task_id": "..."}
    1 - API or argument error
"""

import os
import sys
import json
import time
import base64
import mimetypes
import argparse
import urllib.request
import urllib.parse
import urllib.error


SUBMIT_URL = "https://app-dvtmyuucfs3l-api-rY7JZ6jqrneL-gateway.appmiaoda.com/rest/2.0/ocr/v1/doc_convert/request"
QUERY_URL = "https://app-dvtmyuucfs3l-api-oYA6ZGjReooa-gateway.appmiaoda.com/rest/2.0/ocr/v1/doc_convert/get_request_result"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the 600s Bash tool timeout


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", help="本地图片或 PDF 文件路径")
    g.add_argument("--url", help="图片完整 URL（需已关闭防盗链）")
    p.add_argument("--pdf-page", dest="pdf_page", help="仅识别指定 PDF 页码（从1开始），仅 --file 为 PDF 时生效")
    return p.parse_args()


def post_form(url: str, api_key: str, params: dict) -> dict:
    """向指定 URL 发起 x-www-form-urlencoded POST 请求，返回解析后的响应体。"""
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
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


def submit(api_key: str, args) -> str:
    """提交文档转换任务，返回 task_id。"""
    params = {}
    if args.url:
        params["url"] = args.url
    else:
        mime, _ = mimetypes.guess_type(args.file)
        with open(args.file, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        if mime == "application/pdf" or args.file.lower().endswith(".pdf"):
            params["pdf_file"] = b64
            if args.pdf_page:
                params["pdf_file_num"] = args.pdf_page
        else:
            params["image"] = b64

    d = post_form(SUBMIT_URL, api_key, params)
    if not d.get("success"):
        print(f"提交失败: {d.get('message')} (code: {d.get('code')})", file=sys.stderr)
        sys.exit(1)
    return d["result"]["task_id"]


def query(api_key: str, task_id: str) -> dict:
    """查询任务结果。"""
    d = post_form(QUERY_URL, api_key, {"task_id": task_id})
    if not d.get("success"):
        print(f"查询失败: {d.get('message')} (code: {d.get('code')})", file=sys.stderr)
        sys.exit(1)
    return d.get("result", {})


def main():
    """入口：提交任务后原地轮询，直到完成或达到安全时限。"""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    task_id = submit(api_key, args)

    start = time.time()
    while time.time() - start < SAFE_LIMIT_S:
        time.sleep(POLL_INTERVAL_S)
        result = query(api_key, task_id)

        if result.get("ret_code") == 3:
            data = result.get("result_data", {})
            print(json.dumps({
                "status": "succeed",
                "task_id": task_id,
                "word": data.get("word", ""),
                "excel": data.get("excel", ""),
                "expires": "30 days",
            }))
            return
        # ret_code 1（未开始）/ 2（进行中）：继续轮询

    print(json.dumps({"status": "processing", "task_id": task_id}))


if __name__ == "__main__":
    main()
