"""MCP 工具调度器：将工具调用路由到 engines/orchestrator 或 executors 实现。

融合 v1.2 升级：
- spawn_agent 现在会执行实际开发操作（不再仅返回提示）
- 新增 write_file / read_file / list_files 文件操作工具
- 区分 executed（已执行）和 hint_only（仅提示）两种响应模式
"""
from __future__ import annotations

import json
from typing import Any

from loop_agent_mcp.core.config import find_workspace_root
from loop_agent_mcp.engines import orchestrator as orch
from loop_agent_mcp.engines import evidence as ev_engine
from loop_agent_mcp.engines.executors import execute_agent  # 新增：导入执行引擎
from loop_agent_mcp.engines.executors import (  # 新增：导入文件操作函数
    _write_file,
    _read_file,
    _list_files,
)


def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """统一调度入口。返回 dict 形式结果。"""
    try:
        if name == "start_loop":
            return orch.start_loop(
                workspace=_maybe_workspace(arguments),
                mode=arguments.get("mode", "default"),
                time_budget_hours=float(arguments.get("time_budget_hours", 9.0)),
            )
        if name == "get_status":
            return orch.get_status()
        if name == "abort_loop":
            return orch.abort_loop(reason=arguments.get("reason", "user_abort"))
        if name == "list_agents":
            return orch.list_agents(workspace=_maybe_workspace(arguments))
        if name == "spawn_agent":
            # 融合 v1.2 升级：调用实际执行引擎
            agent_name = arguments.get("agent_name", "")
            task_input = arguments.get("task_input", {})

            # 1. 先执行 orchestrator 的状态更新
            orch_result = orch.spawn_agent(
                agent_name=agent_name,
                task_input=task_input,
            )

            # 2. 调用实际执行引擎
            execution_result = execute_agent(agent_name, task_input)

            # 3. 合并结果
            return {
                **orch_result,
                **execution_result,
                "mode": "executed" if execution_result.get("status") == "executed" else "hint_only",
                "message": (
                    f"✅ 已执行 {agent_name} 任务"
                    if execution_result.get("status") == "executed"
                    else f"💡 {agent_name} 提示: {execution_result.get('output', '')}"
                ),
            }
        if name == "save_blackboard":
            return orch.save_blackboard(
                workspace=_maybe_workspace(arguments),
                content=arguments.get("content"),
                append_section=arguments.get("append_section"),
            )
        if name == "check_artifact_completeness":
            return orch.check_artifact_completeness()
        if name == "check_evidence_sufficiency":
            return orch.check_evidence_sufficiency()
        if name == "detect_deviation":
            return orch.run_deviation_scan()
        if name == "check_veto_items":
            return orch.check_veto_items()
        if name == "check_fusion_targets":
            return orch.check_fusion_targets()
        if name == "get_token_budget_status":
            return orch.get_token_budget_status()
        # 兼容测试钩子：register_evidence
        if name == "register_evidence":
            return ev_engine.register_evidence(
                category=arguments["category"],
                evidence_id=arguments["evidence_id"],
                payload=arguments.get("payload"),
            )

        # 新增：文件操作工具（融合 v1.2）
        if name == "write_file":
            workspace = _maybe_workspace(arguments) or find_workspace_root()
            relative_path = arguments.get("path", "")
            content = arguments.get("content", "")
            file_path = _write_file(workspace, relative_path, content)
            return {
                "status": "ok",
                "action": "file_written",
                "path": file_path,
                "bytes": len(content),
                "message": f"✅ 文件已写入: {relative_path}",
            }

        if name == "read_file":
            workspace = _maybe_workspace(arguments) or find_workspace_root()
            relative_path = arguments.get("path", "")
            try:
                content = _read_file(workspace, relative_path)
                return {
                    "status": "ok",
                    "action": "file_read",
                    "path": relative_path,
                    "content": content[:5000],  # 限制返回长度
                    "bytes": len(content),
                    "message": f"📄 已读取文件: {relative_path}",
                }
            except FileNotFoundError as e:
                return {
                    "status": "error",
                    "action": "file_read_failed",
                    "error": str(e),
                    "message": f"❌ 文件不存在: {relative_path}",
                }

        if name == "list_files":
            workspace = _maybe_workspace(arguments) or find_workspace_root()
            directory = arguments.get("directory", ".")
            files = _list_files(workspace, directory)
            return {
                "status": "ok",
                "action": "files_listed",
                "directory": directory,
                "count": len(files),
                "files": files[:100],  # 限制返回数量
                "message": f"📁 列出 {len(files)} 个文件",
            }
        raise ValueError(f"unknown tool: {name}")
    except Exception as e:  # loud failure
        return {
            "error": str(e),
            "tool": name,
            "arguments": arguments,
        }


def _maybe_workspace(arguments: dict[str, Any]):
    ws = arguments.get("workspace")
    if ws:
        from pathlib import Path
        return Path(ws)
    return None
