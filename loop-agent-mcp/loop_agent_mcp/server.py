"""Loop-Harness-Agent MCP Server 入口（stdio）。

使用方式：
  # 1) 安装依赖
  pip install mcp>=1.0.0
  # 2) 启动 stdio 服务器
  python -m loop_agent_mcp.server
  # 3) 在 Trae/Claude/Cursor 的 mcp.json 中注册：
  {
    "mcpServers": {
      "loop-harness-agent": {
        "command": "python",
        "args": ["-m", "loop_agent_mcp.server"],
        "cwd": "g:/ai-gongju/Loop-agent/loop-agent-mcp"
      }
    }
  }
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# 保证以 `python server.py` 直接运行也能找到包
_PKG_PARENT = Path(__file__).resolve().parent.parent
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

_MCP_IMPORT_ERROR: str | None = None
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError as exc:
    Server = None  # type: ignore
    stdio_server = None  # type: ignore
    Tool = None  # type: ignore
    TextContent = None  # type: ignore
    _MCP_IMPORT_ERROR = (
        "未安装 mcp 依赖。请先运行: pip install mcp>=1.0.0\n"
        "或: pip install -e g:/ai-gongju/Loop-agent/loop-agent-mcp"
    )

from loop_agent_mcp import __version__, __loop_agent_version__, __fusion_standard__
from loop_agent_mcp.tools.schemas import TOOL_SCHEMAS
from loop_agent_mcp.tools.dispatcher import dispatch

SERVER_NAME = "loop-harness-agent"


def build_server():
    if Server is None:
        raise RuntimeError(_MCP_IMPORT_ERROR)
    app = Server(SERVER_NAME)

    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name=schema["name"],
                description=schema["description"],
                inputSchema=schema["inputSchema"],
            )
            for schema in TOOL_SCHEMAS
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]):
        result = dispatch(name, arguments or {})

        # 融合 v1.2 升级：根据结果类型智能格式化响应
        mode = result.get("mode", "metadata")
        action = result.get("action", name)

        if mode == "executed" or result.get("status") == "executed":
            # 实际执行成功：返回结构化结果（包含文件列表）
            text = json.dumps(result, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=text)]

        elif action in ("file_written", "file_read", "files_listed"):
            # 文件操作：返回简洁结果
            message = result.get("message", "操作完成")
            if action == "file_read":
                # 读取文件时返回内容预览
                content_preview = result.get("content", "")[:1000]
                text = f"{message}\n\n```{content_preview}\n```\n\n完整结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            else:
                text = f"{message}\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            return [TextContent(type="text", text=text)]

        elif result.get("status") == "error":
            # 错误响应
            error_msg = result.get("error", result.get("message", "未知错误"))
            text = f"❌ 执行失败: {error_msg}\n\n详情:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            return [TextContent(type="text", text=text, isError=True)]

        else:
            # 元操作（状态查询、黑板更新等）：返回简洁提示 + 完整JSON
            hint_message = result.get("message", f"✅ {name} 完成")
            text = f"{hint_message}\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            return [TextContent(type="text", text=text)]

    return app


mcp = build_server() if Server is not None else None


async def _run_stdio():
    if mcp is None or stdio_server is None:
        raise RuntimeError(_MCP_IMPORT_ERROR)
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


def main():
    import asyncio
    print(
        f"[{SERVER_NAME} v{__version__} | Loop Agent {__loop_agent_version__}] starting...",
        file=sys.stderr,
    )
    print(f"Fusion standard: {__fusion_standard__}", file=sys.stderr)
    print(f"Tools exposed: {len(TOOL_SCHEMAS)}", file=sys.stderr)
    asyncio.run(_run_stdio())


if __name__ == "__main__":
    main()
