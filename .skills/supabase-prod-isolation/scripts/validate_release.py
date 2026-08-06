"""
验证发布 diff runner。

基于当前开发环境重新计算 diff,在临时验证库 apply,
返回成功或首个失败的 SQL 及错误原因。模型修复后可反复调用直到通过。

若当前不存在失败发布残留的备份(即上一次发布成功或从未发布失败),
视为"无需验证 = 验证通过"。

appId 无需传入 —— 自动从当前工作目录(/workspace/app-xxxx)推断,
与 supabase_validate_release 原生工具的行为保持一致(上下文自动携带 appId)。

用法:
    python scripts/validate_release.py

退出码:
    0  验证通过(或当前无需验证)
    1  存在失败 SQL(修复后重跑)

环境变量 (/workspace/.env):
    MIAODA_SANDBOX_MCP_AUTHORIZATION_KEY  必需, MCP 认证密钥
    MIAODA_MCP_SERVER_HOST                必需, MCP 服务器地址(可带或不带 http/https 前缀)
"""

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


def _is_no_backup_response(text: str) -> bool:
    """识别后端"无本地备份"响应。

    该响应的语义是:当前不处于"发布失败"状态,本工具无法使用。
    备份只在一次发布失败后残留,发布成功后会被清除。
    """
    return "no local backup found" in text.lower()


async def validate() -> int:
    """返回进程退出码: 0=验证通过(或无需验证), 1=存在失败 SQL。"""
    auth_key = os.getenv("MIAODA_SANDBOX_MCP_AUTHORIZATION_KEY")
    if not auth_key:
        sys.exit("❌ 未设置 MIAODA_SANDBOX_MCP_AUTHORIZATION_KEY")

    app_id = detect_app_id()
    server_url = build_server_url()
    headers = {"x-miaoda-mcp-authorization": auth_key}

    async with streamablehttp_client(server_url, headers=headers, timeout=60) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            result = await session.call_tool(
                "supabase_validate_release",
                {"appId": app_id},
            )
            text = result.content[0].text if result.content else ""

    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        # 后端"无本地备份"提示可能以纯文本形式返回:视为无需验证,直接算通过
        if _is_no_backup_response(text):
            print("✅ 验证通过")
            return 0
        # 其它非 JSON 响应原样输出,无法判断成败时按失败处理,避免误报"通过"
        print(text)
        return 1

    # 结构化响应里也可能携带"无本地备份"错误,同样视为无需验证 = 通过
    if _is_no_backup_response(json.dumps(payload, ensure_ascii=False)):
        print("✅ 验证通过")
        return 0

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if payload.get("success"):
        print("\n✅ 发布验证通过,所有 SQL 均可正常执行")
        return 0
    print(
        "\n❌ 发布验证失败。请修复上述 error 中的首个报错 SQL"
        "(改开发环境的 migration,不要改线上),然后重新运行本脚本。"
    )
    return 1


def main() -> None:
    try:
        sys.exit(asyncio.run(validate()))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001 - runner 直接把错误反馈给使用者
        sys.exit(f"❌ 验证失败: {exc}")


if __name__ == "__main__":
    main()
