#!/usr/bin/env python3
"""Fetch a web page as Markdown via the web-reader gateway (optionally SSE streaming).

Observe:
    {
        "progress",
        "status",
        "this_call": {"content_file", "content_schema", "content_length", "url", "preview", "error?"}
    }
Log:
    <project_root>/outputs/research/research_log.json
        {
        "search": [{"phase", "query", "recency_filter", "results": [{"url", "title", "snippet", "date", "website", ...}]}],
        "fetch": [{"phase", "url", "status", "content_file"}]
    }
    <project_root>/outputs/research/fetch_{url}.md
    <!-- url: ... -->
    [markdown content]
Returns success/failure per URL to LLM (full content stays on disk).
Fetch failure (403/timeout/...) does NOT die; status is recorded and returned.

--phase 硬门与 baidu_search.py 相同（无 JSON / phase 非法 / 越界 / 跳号 /
reflection 未齐 → die，不发起请求）。详见 task_progress.py。
"""

import argparse
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import task_progress as tp


BASE_URL = "https://api-ELbWqODdAgNY@36oqjsxjo775h3odjp3eev3y740deicu.lambda-url.us-west-2.on.aws"

# 脚本位置 → 项目根（向上 3 级）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
LOG_DIR = os.path.join(DEFAULT_PROJECT_ROOT, "outputs")

RESEARCH_DIR = os.path.join(LOG_DIR, "research")
CONTENT_PREVIEW_LEN = 2000


def die(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def iter_sse(response):
    """迭代解析 SSE 响应流，逐条返回 data 字段内容。"""
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        yield data


def load_log():
    """读取 research_log.json 文件，返回 (path, {search, fetch})。"""
    log_file = os.path.join(RESEARCH_DIR, "research_log.json")
    log_data = {"search": [], "fetch": []}
    if os.path.isfile(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                if isinstance(loaded.get("search"), list):
                    log_data["search"] = loaded["search"]
                if isinstance(loaded.get("fetch"), list):
                    log_data["fetch"] = loaded["fetch"]
        except (json.JSONDecodeError, OSError) as exc:
            print(f"WARNING: 读取 log 文件失败，使用新文件: {exc}", file=sys.stderr)
    return log_file, log_data


def save_log(log_file, log_data):
    """将 log 数据写回文件。"""
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def url_to_filename(url):
    safe_url = re.sub(r"[^A-Za-z0-9]+", "_", url).strip("_")
    return f"fetch_{safe_url}.md"


def save_content(url, content):
    """把正文写到 fetch_<...>.md（纯 markdown），返回绝对路径。"""
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    path = os.path.join(RESEARCH_DIR, url_to_filename(url))
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- url: {url} -->\n\n")
        f.write(content)
    return os.path.abspath(path)


def main():
    """入口：解析命令行参数，抓取网页内容并输出结果 JSON。"""
    parser = argparse.ArgumentParser(description="Fetch a web page as Markdown and print one JSON result.")
    parser.add_argument("--url", required=True, help="Target page URL.")
    parser.add_argument("--return-format", choices=["markdown", "html", "text", "screenshot", "pageshot"],
                        help="Output format.")
    parser.add_argument("--with-images-summary", action="store_true", help="Append an image summary.")
    parser.add_argument("--with-links-summary", action="store_true", help="Append a link summary.")
    parser.add_argument("--target-selector", help="CSS selector to extract only.")
    parser.add_argument("--remove-selector", help="CSS selector to remove.")
    parser.add_argument("--timeout", type=int, help="Page load timeout in seconds.")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache and force a fresh crawl.")
    parser.add_argument("--stream", action="store_true", help="Use SSE streaming and aggregate chunks.")
    parser.add_argument("--phase", required=True,
                        help="研究任务.json 里的 task-N 或 reflection（不是全局 todo 序号）")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        die("Missing INTEGRATIONS_API_KEY environment variable")

    # 阶段 4/5 进度硬门（无 JSON / phase 非法 / 越界 / 跳号 / reflection 未齐）：
    # 在发起网络请求前校验，避免违规调用浪费配额。
    log_file, log_data = load_log()
    steps, completed_ids = tp.validate_phase_for_research(LOG_DIR, args.phase, log_data)

    # Validate the target URL before constructing the endpoint
    target_url = args.url.strip()
    if not target_url:
        die("--url must not be empty")
    parsed = urllib.parse.urlparse(target_url)
    if parsed.scheme not in ("http", "https"):
        die(f"Invalid URL scheme '{parsed.scheme}': only http/https are supported")
    if not parsed.netloc:
        die(f"Invalid URL (no host): {target_url}")
    # Check hostname labels: IDNA requires each label ≤ 63 chars, non-empty
    hostname = parsed.hostname or ""
    for label in hostname.split("."):
        if not label or len(label) > 63:
            die(
                f"Invalid hostname '{hostname}': DNS label "
                f"'{label[:20]}...' is empty or exceeds 63 characters"
            )

    # Strip userinfo from BASE_URL to avoid IDNA label-too-long errors during
    # urllib's hostname encoding.  The userinfo (if any) is kept for reference
    # but authentication goes through the X-Gateway-Authorization header.
    _parsed_base = urllib.parse.urlsplit(BASE_URL)
    _netloc = _parsed_base.hostname + (f":{_parsed_base.port}" if _parsed_base.port else "")
    _clean_base = urllib.parse.urlunsplit((
        _parsed_base.scheme, _netloc, _parsed_base.path.rstrip("/"), "", ""
    ))
    endpoint = f"{_clean_base}/{urllib.parse.quote(target_url, safe='')}"

    headers = {
        "X-Gateway-Authorization": f"Bearer {api_key}",
        # 网关后端受 Cloudflare 保护，缺少浏览器 UA 会被判定为爬虫返回 403
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    if args.return_format:
        headers["X-Return-Format"] = args.return_format
    if args.with_images_summary:
        headers["X-With-Images-Summary"] = "true"
    if args.with_links_summary:
        headers["X-With-Links-Summary"] = "true"
    if args.target_selector:
        headers["X-Target-Selector"] = args.target_selector
    if args.remove_selector:
        headers["X-Remove-Selector"] = args.remove_selector
    if args.timeout is not None:
        headers["X-Timeout"] = str(args.timeout)
    if args.no_cache:
        headers["X-No-Cache"] = "true"
    headers["Accept"] = "text/event-stream" if args.stream else "text/html"

    request = urllib.request.Request(endpoint, method="GET", headers=headers)

    # 抓取失败不 die，改成 status: "failed" + error 信息落盘并返回
    content = None
    error_msg = None
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            if args.stream:
                parts = []
                for data in iter_sse(response):
                    parts.append(data)
                content = "".join(parts)
            else:
                content = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 401:
            error_msg = "HTTP 401: 鉴权失败，JWT Token 缺失或无效"
        elif exc.code == 403:
            error_msg = "HTTP 403: 目标 URL 被 GFW 过滤，无法访问"
        else:
            error_msg = f"HTTP {exc.code}: {detail}"
    except urllib.error.URLError as exc:
        error_msg = f"Request failed: {exc.reason}"
    except UnicodeError as exc:
        # IDNA 编码失败：目标 URL（或其重定向目标）的主机名含空标签或超长标签（>63 字符）
        error_msg = f"Invalid host in URL '{target_url}': {exc}"
    except http.client.HTTPException as exc:
        # IncompleteRead / BadStatusLine / RemoteDisconnected 等协议层异常
        error_msg = f"HTTP protocol error: {type(exc).__name__}: {exc}"

    if error_msg:
        print(f"WARNING: fetch 失败 {target_url}: {error_msg}", file=sys.stderr)
        content = None

    status = "success" if content else "failed"

    # 成功才写 content 文件；失败 content_file=null
    content_file = None
    if content:
        try:
            content_file = save_content(target_url, content)
        except Exception as exc:
            print(f"WARNING: 写入 content 文件失败: {exc}", file=sys.stderr)

    # 追加到 log 文件
    log_data["fetch"].append({
        "phase": args.phase,
        "url": target_url,
        "status": status,
        "content_file": content_file,
    })
    try:
        save_log(log_file, log_data)
    except Exception as exc:
        print(f"WARNING: 写入 log 文件失败: {exc}", file=sys.stderr)

    # 组装进度块（放在 this_call 前）
    progress = tp.render_progress_block(steps, completed_ids, args.phase)

    # 返回给 LLM：不返回 content，只带 preview + status + 可选 error
    this_call = {
        "content_file": content_file,
        "content_schema": "markdown (首行 <!-- url: ... --> 注释)",
        "content_length": len(content) if content else 0,
        "url": target_url,
        "preview": (content or "")[:CONTENT_PREVIEW_LEN],
    }
    if error_msg:
        this_call["error"] = error_msg
    output = {
        "progress": progress,
        "status": "succeed",
        "log_file": os.path.abspath(log_file),
        "this_call": this_call,
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
