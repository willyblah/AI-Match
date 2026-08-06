#!/usr/bin/env python3
"""
Call MiniMax-M3 chat completions (non-streaming).

Usage:
    # 单轮
    python3 call_minimax_m3_chat.py --prompt "你好，请用一句话介绍你自己"

    # 自定义模型 / 参数
    python3 call_minimax_m3_chat.py --prompt "..." --model "MiniMax-M3" \
        --temperature 1 --top-p 0.95 --max-completion-tokens 2048 \
        --thinking adaptive

    # 完整 messages 输入（覆盖 --prompt）
    python3 call_minimax_m3_chat.py --messages '[{"role":"user","content":"你好"}]'

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one-line JSON: {"status":"succeed","result":{...}}
    1 - API or argument error, prints error line on stderr
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-dvtmyuucfs3l-api-rLobPAn0n7m9-gateway.appmiaoda.com/v1/chat/completions"


def fail(message):
    """打印错误信息并以非零状态退出。"""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser(description="MiniMax-M3 chat completion")
    p.add_argument("--prompt", help="user 消息文本（与 --messages 二选一）")
    p.add_argument("--messages", help='完整 messages JSON 数组，覆盖 --prompt')
    p.add_argument("--model", default="MiniMax-M3", help="模型名，默认 MiniMax-M3")
    p.add_argument("--temperature", type=float, help="温度")
    p.add_argument("--top-p", type=float, help="top_p")
    p.add_argument("--max-completion-tokens", type=int, help="最大生成 token")
    p.add_argument("--thinking", choices=["disabled", "adaptive"], help="思考模式")
    p.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    return p.parse_args()


def build_payload(args):
    """构造请求 body。"""
    if args.messages:
        try:
            messages = json.loads(args.messages)
        except json.JSONDecodeError as exc:
            fail("--messages is not valid JSON: " + str(exc))
    elif args.prompt:
        messages = [{"role": "user", "content": args.prompt}]
    else:
        fail("Either --prompt or --messages is required")

    payload = {"model": args.model, "messages": messages}
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    if args.top_p is not None:
        payload["top_p"] = args.top_p
    if args.max_completion_tokens is not None:
        payload["max_completion_tokens"] = args.max_completion_tokens
    if args.thinking:
        payload["thinking"] = {"type": args.thinking}
    return payload


def call_api(args):
    """调用上游接口并返回响应。"""
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    body = json.dumps(build_payload(args), ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, detail[:1000]))
    except urllib.error.URLError as exc:
        fail("Network error: " + str(exc.reason))

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fail("Response is not valid JSON: " + text[:500])


def main():
    """入口：调用 MiniMax-M3 chat 并输出结果 JSON。"""
    args = parse_args()
    result = call_api(args)
    print(json.dumps({"status": "succeed", "result": result}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
