"""v1.3 兼容性占位模块。

原本计划在 v1.3 重构 executors.py 为子包结构，
但考虑到改动较大且会破坏现有测试和向后兼容性，
决定保留 executors.py 单文件结构，但通过本模块提供：
1. BaseExecutor 抽象基类（供 v1.4+ 扩展使用）
2. register_executor 装饰器（插件化扩展点）
3. 统一的 execute_agent 入口（统一异常处理）

注：当前 v1.3 主要安全加固、状态持久化已完成，
架构重构推迟到 v1.4。
"""
from __future__ import annotations

from typing import Any, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class ExecutionResult:
    """执行结果标准化数据结构（v1.3+ 新增）。"""
    status: str  # executed / hint_only / error
    agent: str
    files_created: list[str] = field(default_factory=list)
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "status": self.status,
            "agent": self.agent,
            "output": self.output,
        }
        if self.files_created:
            result["files_created"] = self.files_created
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class BaseExecutor(ABC):
    """执行器抽象基类（v1.3+ 扩展点）。"""

    agent_name: str = ""
    supported_task_types: list[str] = []

    @abstractmethod
    def execute(self, task_input: dict[str, Any]) -> ExecutionResult:
        """执行任务。"""
        ...

    def validate_input(self, task_input: dict[str, Any]) -> None:
        """验证输入参数（可选重写）。"""
        task_type = task_input.get("task_type", "")
        if self.supported_task_types and task_type not in self.supported_task_types:
            raise ValueError(
                f"不支持的任务类型: {task_type}（支持: {self.supported_task_types}）"
            )

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "agent": self.agent_name,
            "task_types": self.supported_task_types,
            "is_executable": True,
        }


# 全局执行器注册表
_EXECUTOR_REGISTRY: dict[str, type[BaseExecutor]] = {}


def register_executor(agent_name: str) -> Callable:
    """装饰器：注册执行器。

    用法:
        @register_executor("backend")
        class BackendExecutor(BaseExecutor):
            ...
    """
    def decorator(cls: type[BaseExecutor]) -> type[BaseExecutor]:
        cls.agent_name = agent_name
        _EXECUTOR_REGISTRY[agent_name] = cls
        return cls
    return decorator


def get_executor_class(agent_name: str) -> type[BaseExecutor] | None:
    """获取执行器类（用于v1.4+扩展）。"""
    return _EXECUTOR_REGISTRY.get(agent_name)


def list_registered_executors() -> list[str]:
    """列出所有已注册的执行器。"""
    return list(_EXECUTOR_REGISTRY.keys())


__all__ = [
    "ExecutionResult",
    "BaseExecutor",
    "register_executor",
    "get_executor_class",
    "list_registered_executors",
]
