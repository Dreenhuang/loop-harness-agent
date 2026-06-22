"""MCP 工具调度器：将工具调用路由到 engines/orchestrator 或 executors 实现。

v1.2 升级：
- spawn_agent 现在会执行实际开发操作（不再仅返回提示）
- 新增 write_file / read_file / list_files 文件操作工具
- 区分 executed（已执行）和 hint_only（仅返回提示）两种响应模式

v1.3 升级：
- 分类异常（ToolNotFoundError / ValidationError / SecurityError / InternalError）
- 工具调用审计日志
- 改进错误信息（包含 error_code）

v1.4 升级（并行调度）：
- spawn_agent 支持 async/sync 双模式
- 新增 cancel_task / get_task_status 工具
- 引入 TaskScheduler 实现真正并行执行
"""
from __future__ import annotations

import asyncio
import time
import traceback
from typing import Any

from loop_agent_mcp.core.config import find_workspace_root
from loop_agent_mcp.core.logging import get_audit_logger, logger
from loop_agent_mcp.engines import orchestrator as orch
from loop_agent_mcp.engines import evidence as ev_engine
from loop_agent_mcp.engines.executors import execute_agent
from loop_agent_mcp.engines.executors import (
    _write_file,
    _read_file,
    _list_files,
)
from loop_agent_mcp.runtime.scheduler import TaskScheduler
from loop_agent_mcp.runtime.task import TaskStatus


# ==================== 异常分类（v1.3）====================


class DispatcherError(Exception):
    """调度器基础异常。"""

    def __init__(self, message: str, error_code: str = "DISPATCH_ERROR") -> None:
        super().__init__(message)
        self.error_code = error_code


class ToolNotFoundError(DispatcherError):
    """工具不存在。"""

    def __init__(self, tool_name: str) -> None:
        super().__init__(f"未知工具: {tool_name}", error_code="TOOL_NOT_FOUND")
        self.tool_name = tool_name


class ValidationError(DispatcherError):
    """参数验证失败。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="VALIDATION_ERROR")


class SecurityError(DispatcherError):
    """安全违规。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="SECURITY_VIOLATION")


# ==================== TaskScheduler 单例 ====================

_scheduler: TaskScheduler | None = None
_scheduler_lock = asyncio.Lock()


async def get_scheduler() -> TaskScheduler:
    """获取全局 TaskScheduler 单例。"""
    global _scheduler
    if _scheduler is None:
        async with _scheduler_lock:
            if _scheduler is None:
                _scheduler = TaskScheduler()
    return _scheduler


def reset_scheduler() -> None:
    """重置 scheduler（仅用于测试）。"""
    global _scheduler
    _scheduler = None


# ==================== 同步兼容入口 ====================


def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """同步兼容调度入口（v1.4：内部转异步执行）。

    注意：本函数必须在**没有运行中事件循环**的同步上下文调用。
    若调用方已处于运行中的事件循环（如 async 测试、Jupyter、asyncio 服务内部），
    请直接使用 `async_dispatch()`。
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            return {
                "status": "error",
                "error_code": "ASYNC_CONTEXT_ERROR",
                "error": "dispatch() 在运行中的事件循环中被调用，请改用 async_dispatch()",
            }
        # loop 存在但未运行（极罕见），回退到 run_until_complete
        return loop.run_until_complete(async_dispatch(name, arguments))
    except RuntimeError:
        # 当前线程没有事件循环，安全使用 asyncio.run
        return asyncio.run(async_dispatch(name, arguments))
    except Exception as e:
        return {
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "error": f"调度失败: {e}",
        }


async def async_dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """异步调度入口（v1.4 主入口）。"""
    start = time.time()
    result: dict[str, Any] = {}

    try:
        result = await _async_dispatch_internal(name, arguments)
    except ToolNotFoundError as e:
        result = {
            "status": "error",
            "error_code": e.error_code,
            "error": str(e),
            "tool": name,
        }
    except ValidationError as e:
        result = {
            "status": "error",
            "error_code": e.error_code,
            "error": str(e),
            "tool": name,
        }
    except ValueError as e:
        result = {
            "status": "error",
            "error_code": "VALIDATION_ERROR",
            "error": f"参数错误: {e}",
            "tool": name,
        }
    except Exception as e:
        logger.error(
            f"工具执行异常: {name} - {e}",
            exc_info=True,
            extra={"tool_name": name},
        )
        result = {
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "error": str(e),
            "tool": name,
            "traceback": traceback.format_exc() if logger.isEnabledFor(10) else None,
        }
    finally:
        duration_ms = (time.time() - start) * 1000
        if result:
            try:
                get_audit_logger().log_call(name, arguments, result, duration_ms)
            except Exception:
                pass

    return result


async def _async_dispatch_internal(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """内部异步调度逻辑。"""
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
        return await _handle_spawn_agent(arguments)

    if name == "cancel_task":
        return await _handle_cancel_task(arguments)

    if name == "get_task_status":
        return await _handle_get_task_status(arguments)

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

    # 新增：文件操作工具（v1.2）
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
            "message": f"文件已写入: {relative_path}",
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
                "content": content[:5000],
                "bytes": len(content),
                "message": f"已读取文件: {relative_path}",
            }
        except FileNotFoundError as e:
            return {
                "status": "error",
                "action": "file_read_failed",
                "error": str(e),
                "message": f"文件不存在: {relative_path}",
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
            "files": files[:100],
            "message": f"列出 {len(files)} 个文件",
        }

    # 未找到工具
    raise ToolNotFoundError(name)


async def _handle_spawn_agent(arguments: dict[str, Any]) -> dict[str, Any]:
    """处理 spawn_agent：支持 async/sync 两种模式。"""
    agent_name = arguments.get("agent_name", "")
    task_input = arguments.get("task_input", {})
    if not isinstance(task_input, dict):
        raise ValidationError("task_input 必须是对象")

    async_mode = bool(arguments.get("async", False))
    priority = int(arguments.get("priority", 5))
    dependencies = arguments.get("dependencies", []) or []
    timeout = arguments.get("timeout")
    if timeout is not None:
        timeout = float(timeout)

    # 1. 先执行 orchestrator 的状态更新（线程安全）
    orch_result = orch.spawn_agent(
        agent_name=agent_name,
        task_input=task_input,
    )

    scheduler = await get_scheduler()

    if async_mode:
        # 2a. 异步提交，立即返回 task_id
        task = await scheduler.submit_task(
            agent_name=agent_name,
            task_input=task_input,
            priority=priority,
            dependencies=dependencies,
            timeout=timeout,
        )
        return {
            "status": "queued",
            "task_id": task.task_id,
            "agent_name": agent_name,
            "loop_id": task.loop_id,
            "mode": "async",
            "message": "任务已加入队列，可通过 get_task_status 查询进度",
        }

    # 2b. 同步兼容：等待任务完成
    task = await scheduler.submit_and_wait(
        agent_name=agent_name,
        task_input=task_input,
        priority=priority,
        dependencies=dependencies,
        timeout=timeout,
    )
    execution_result = task.result or {}
    mode = "executed" if task.status == TaskStatus.SUCCEEDED else "hint_only"
    return {
        **orch_result,
        **execution_result,
        "task_id": task.task_id,
        "status": task.status.value,
        "mode": mode,
        "message": (
            f"已执行 {agent_name} 任务"
            if mode == "executed"
            else f"{agent_name} 提示: {execution_result.get('output', '')}"
        ),
    }


async def _handle_cancel_task(arguments: dict[str, Any]) -> dict[str, Any]:
    """处理 cancel_task。"""
    task_id = arguments.get("task_id", "")
    if not task_id:
        raise ValidationError("task_id 不能为空")
    scheduler = await get_scheduler()
    cancelled = await scheduler.cancel_task(task_id)
    task = scheduler.get_task(task_id) or await scheduler.load_task(task_id)
    return {
        "status": "cancelled" if cancelled else "cancel_failed",
        "task_id": task_id,
        "task_status": task.status.value if task else "unknown",
        "message": "任务已取消" if cancelled else "任务无法取消（可能已完成或不存在）",
    }


async def _handle_get_task_status(arguments: dict[str, Any]) -> dict[str, Any]:
    """处理 get_task_status。"""
    task_id = arguments.get("task_id", "")
    if not task_id:
        raise ValidationError("task_id 不能为空")
    scheduler = await get_scheduler()
    task = scheduler.get_task(task_id) or await scheduler.load_task(task_id)
    if task is None:
        return {
            "status": "not_found",
            "task_id": task_id,
            "message": "任务不存在",
        }
    return {
        "status": "ok",
        "task_id": task.task_id,
        "loop_id": task.loop_id,
        "agent_name": task.agent_name,
        "task_status": task.status.value,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "retry_count": task.retry_count,
        "error": task.error,
        "result_preview": _preview_result(task.result),
    }


def _preview_result(result: dict[str, Any]) -> dict[str, Any]:
    """返回结果摘要，避免返回过大。"""
    if not result:
        return {}
    preview = {
        "status": result.get("status"),
        "agent": result.get("agent"),
        "output": result.get("output"),
        "files_count": len(result.get("files_created", [])),
    }
    return preview


def _maybe_workspace(arguments: dict[str, Any]):
    """从参数中提取 workspace 路径。"""
    ws = arguments.get("workspace")
    if ws:
        from pathlib import Path
        return Path(ws)
    return None
