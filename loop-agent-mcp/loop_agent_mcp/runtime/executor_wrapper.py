"""AgentExecutor：包装现有 execute_agent，注入任务级隔离。

每个任务在独立的 TaskContext 中运行，切换 Loop 上下文，捕获结果/异常。
"""
from __future__ import annotations

import time
from typing import Any

from loop_agent_mcp.core.state import StateManager
from loop_agent_mcp.engines.executors import execute_agent
from loop_agent_mcp.runtime.task import Task, TaskContext


class AgentExecutor:
    """包裹现有 execute_agent，注入任务级隔离。"""

    def __init__(self, task: Task):
        self.task = task
        self.context = task.context or TaskContext.create(task)

    def run(self, _task: Task | None = None) -> dict[str, Any]:
        """执行任务并返回结果。

        Args:
            _task: 兼容 worker_pool 的调用签名（实际使用 self.task）。

        Returns:
            执行结果字典。
        """
        task = _task or self.task
        self.context = task.context or TaskContext.create(task)

        # 1. 创建/确认私有工作区 sandbox
        self.context.prepare_workspace()

        # 2. 切换当前 Loop 上下文（线程局部）
        sm = StateManager.get()
        old_loop_id = sm.get_thread_loop()
        if task.loop_id:
            sm.set_thread_loop(task.loop_id)

        self.context.log("INFO", f"任务开始执行: {task.agent_name}")
        task.add_audit("started")

        result: dict[str, Any] | None = None
        try:
            # 3. 在 TaskContext 内运行现有执行器
            enriched_input = {
                **task.task_input,
                "_task_id": task.task_id,
                "_workspace": str(self.context.workspace),
            }
            result = execute_agent(task.agent_name, enriched_input)

            # 标准化结果
            if not isinstance(result, dict):
                result = {"status": "ok", "result": result}

            # 记录成功/失败审计
            if result.get("status") == "error":
                task.error = result
                self.context.log("ERROR", f"执行返回错误: {result.get('error', '')}")
            else:
                self.context.log("INFO", f"任务执行成功: {result.get('output', '')}")

            return result
        except Exception as e:
            self.context.log("ERROR", f"执行异常: {e}")
            result = {
                "status": "error",
                "agent": task.agent_name,
                "error": str(e),
                "execution_failed": True,
            }
            return result
        finally:
            # 4. 使用本次执行得到的实际结果记录审计，恢复线程 Loop 上下文
            self.context.finalize(result or {})
            sm.set_thread_loop(old_loop_id)
