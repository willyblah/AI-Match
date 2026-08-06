"""
线上数据库只读查询 runner。

设计要点: 查询语句应由**模型根据当前任务和真实表结构自行编写**,
再通过本脚本的 --sql 传入执行。本脚本不内置任何业务查询,
示例 SQL 只是格式参考,切勿照搬 profiles/orders 之类的表名。

appId 无需传入 —— 自动从当前工作目录(/workspace/app-xxxx)推断,
与 supabase_online_view 原生工具的行为保持一致(上下文自动携带 appId)。

用法:
    python scripts/query_online_db.py --sql "SELECT ..."

环境变量 (/workspace/.env):
    MIAODA_SANDBOX_MCP_AUTHORIZATION_KEY  必需, MCP 认证密钥
    MIAODA_MCP_SERVER_HOST                必需, MCP 服务器地址(可带或不带 http/https 前缀)
"""

import argparse
import asyncio
import json
import os
import sys

import dotenv
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

dotenv.load_dotenv("/workspace/.env")


def detect_app_id() -> str:
    """从当前工作目录推断 appId(形如 /workspace/app-xxxx)。"""
    for part in os.path.abspath(os.getcwd()).split(os.sep):
        if part.startswith("app-"):
            return part
    sys.exit(
        "❌ 无法从当前工作目录推断 appId(期望路径形如 /workspace/app-xxxx)。"
        "请确认在正确的应用工作目录下运行本脚本。"
    )


def build_server_url() -> str:
    """按 MCP 模板拼接 server URL: 去掉 http/https 前缀后拼上 daemon 路径。"""
    host = os.getenv("MIAODA_MCP_SERVER_HOST")
    if not host:
        raise RuntimeError("MIAODA_MCP_SERVER_HOST is not set")
    host = host.removeprefix("https://").removeprefix("http://")
    return f"http://{host}/v1/agentos/mcp/streamable-for-daemon"


async def query(sql: str) -> None:
    auth_key = os.getenv("MIAODA_SANDBOX_MCP_AUTHORIZATION_KEY")
    if not auth_key:
        sys.exit("❌ 未设置 MIAODA_SANDBOX_MCP_AUTHORIZATION_KEY")

    app_id = detect_app_id()
    server_url = build_server_url()
    headers = {"x-miaoda-mcp-authorization": auth_key}

    async with streamablehttp_client(server_url, headers=headers, timeout=60) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            # 注意调用签名: appId + query 两个参数(appId 由本脚本自动推断,无需用户传入)
            result = await session.call_tool(
                "supabase_online_view",
                {"appId": app_id, "query": sql},
            )
            text = result.content[0].text if result.content else ""
            try:
                print(json.dumps(json.loads(text), ensure_ascii=False, indent=2))
            except (ValueError, TypeError):
                print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="线上 Supabase 只读查询 runner")
    parser.add_argument(
        "--sql",
        required=True,
        help="要执行的 SELECT 语句(由模型按当前任务生成)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(query(args.sql))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001 - runner 直接把错误反馈给使用者
        sys.exit(f"❌ 查询失败: {exc}")


if __name__ == "__main__":
    main()
