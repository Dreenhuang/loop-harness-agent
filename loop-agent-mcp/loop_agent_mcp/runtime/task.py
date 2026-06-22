"""任务模型与任务级上下文。

提供 TaskStatus 枚举、Task 数据类以及 TaskContext 执行隔离上下文。
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from loop_agent_mcp.core.config import find_workspace_root
from loop_agent_mcp.core.state import StateManager

logger = logging.getLogger(__name__)


def _resolve_tasks_root() -> Path:
    """解析 per-task workspace 根目录（无 I/O，每次按当前 StateManager 重新计算）。

    优先级：
    1. 环境变量 ``LOOP_AGENT_TASKS_DIR``（用户显式指定）。
    2. 默认：``<project_workspace>/.loop-agent-tasks``。
    3. 跨盘 fallback：默认盘不可写（盘满/权限不足）时，回退到系统临时目录。

    注意：此函数只做路径计算，不做 I/O。实际目录创建在 :meth:`TaskContext.prepare_workspace` 中。
    """
    explicit = os.environ.get("LOOP_AGENT_TASKS_DIR")
    if explicit:
        return Path(explicit).resolve()

    base_str = StateManager.get().state.workspace
    try:
        base = Path(base_str) if base_str else find_workspace_root()
    except Exception:
        base = find_workspace_root()
    return base / ".loop-agent-tasks"


_TEMP_TASKS_ROOT = Path(tempfile.gettempdir()) / "loop-agent-tasks"


def _ensure_workspace_writable(workspace: Path, output_dir: Path, shared_dir: Path) -> tuple[Path, Path, Path]:
    """确保 workspace/output/shared 目录可写；不可写时回退到系统 temp 目录。"""
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(exist_ok=True)
        shared_dir.mkdir(parents=True, exist_ok=True)
        return workspace, output_dir, shared_dir
    except OSError as exc:
        logger.warning(
            "工作区 %s 创建失败（%s），回退到临时目录 %s",
            workspace, exc, _TEMP_TASKS_ROOT,
        )
        fb_workspace = _TEMP_TASKS_ROOT / workspace.name
        fb_output = fb_workspace / "output"
        fb_shared = _TEMP_TASKS_ROOT / "shared"
        fb_workspace.mkdir(parents=True, exist_ok=True)
        fb_output.mkdir(exist_ok=True)
        fb_shared.mkdir(parents=True, exist_ok=True)
        return fb_workspace, fb_output, fb_shared


class TaskStatus(Enum):
    """任务生命周期状态。"""

    PENDING = "pending"           # 等待依赖满足
    QUEUED = "queued"             # 已进入调度队列
    RUNNING = "running"           # 正在执行
    SUCCEEDED = "succeeded"       # 成功完成
    FAILED = "failed"             # 失败（可重试次数已耗尽）
    CANCELLED = "cancelled"       # 被取消
    TIMEOUT = "timeout"           # 超时
    BLOCKED = "blocked"           # 依赖未满足或被门禁阻塞


@dataclass
class Task:
    """单个 agent 任务抽象。"""

    task_id: str
    loop_id: str
    agent_name: str
    task_input: dict[str, Any]

    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None

    priority: int = 5
    dependencies: list[str] = field(default_factory=list)
    max_retries: int = 2
    retry_count: int = 0
    timeout_seconds: float = 600.0

    context: "TaskContext | None" = None

    result: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    logs: list[dict[str, Any]] = field(default_factory=list)
    audit_trail: list[dict[str, Any]] = field(default_factory=list)

    def is_terminal(self) -> bool:
        return self.status in (
            TaskStatus.SUCCEEDED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        )

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典（用于持久化）。"""
        return {
            "task_id": self.task_id,
            "loop_id": self.loop_id,
            "agent_name": self.agent_name,
            "task_input": self.task_input,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "result": self.result,
            "error": self.error,
            "logs": self.logs,
            "audit_trail": self.audit_trail,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """从字典恢复任务对象。"""
        status = TaskStatus(data.get("status", "pending"))
        data = dict(data)
        data["status"] = status
        # 过滤掉 dataclass 不需要的字段
        for key in list(data.keys()):
            if key not in {f.name for f in cls.__dataclass_fields__.values()}:
                data.pop(key, None)
        return cls(**data)

    def add_audit(self, event: str, **kwargs: Any) -> None:
        entry: dict[str, Any] = {"event": event, "timestamp": time.time()}
        entry.update(kwargs)
        self.audit_trail.append(entry)


class TaskContext:
    """任务级执行上下文，提供隔离的 workspace、日志和输出目录。"""

    _workspace_lock = threading.Lock()

    def __init__(self, task: Task):
        self.task = task
        self._tasks_root = _resolve_tasks_root()
        self.workspace = self._tasks_root / self.task.task_id
        self.log_path = self.workspace / "task.log"
        self.output_dir = self.workspace / "output"
        self.shared_dir = self._tasks_root / "shared"

    @classmethod
    def create(cls, task: Task) -> "TaskContext":
        ctx = cls(task)
        ctx.prepare_workspace()
        return ctx

    def prepare_workspace(self) -> None:
        """创建任务私有工作区（默认盘不可写时回退到临时目录）。"""
        with self._workspace_lock:
            self.workspace, self.output_dir, self.shared_dir = _ensure_workspace_writable(
                self.workspace, self.output_dir, self.shared_dir,
            )
            self.log_path = self.workspace / "task.log"
            if not self.log_path.exists():
                self.log_path.write_text(
                    f"# Task {self.task.task_id} log\n", encoding="utf-8"
                )

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """写入任务私有日志。"""
        entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
        }
        entry.update(kwargs)
        self.task.logs.append(entry)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{level}] {message}\n")
        except OSError:
            logger.warning("写入任务日志失败: %s", self.log_path)

    def finalize(self, result: dict[str, Any]) -> None:
        """任务结束时记录结果到审计链。"""
        self.task.add_audit(
            "finished",
            workspace=str(self.workspace),
            result_status=result.get("status", "unknown"),
        )

    def commit_output(self, target_workspace: Path) -> list[str]:
        """将任务产出合并到项目工作区（带冲突检测）。"""
        committed: list[str] = []
        if not self.output_dir.exists():
            return committed

        with self._workspace_lock:
            for src in self.output_dir.rglob("*"):
                if not src.is_file():
                    continue
                rel = src.relative_to(self.output_dir)
                dst = target_workspace / rel
                if dst.exists():
                    dst = dst.with_suffix(dst.suffix + ".conflict")
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                committed.append(str(dst))
        return committed


def new_task_id() -> str:
    """生成全局唯一任务 ID。"""
    return f"task-{uuid.uuid4().hex[:12]}"
