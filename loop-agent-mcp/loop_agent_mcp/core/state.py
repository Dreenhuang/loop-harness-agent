"""Loop 全局状态管理：单例状态对象，跨工具调用持久化。

v1.3 重大升级（修复 v1.2 的 Critical 缺陷）：
- 原实现：单例 + 纯内存 + 单一 LoopState，进程重启 = 状态全丢
- 新实现：
  - 支持多 Loop 隔离（以 loop_id 为 key）
  - 集成 StatePersistence 实现磁盘持久化
  - 每次 mutate 后自动保存（write-through）
  - 支持从磁盘恢复 Loop
  - 向后兼容：通过 .state 属性访问当前活跃 Loop

向后兼容：
- StateManager.get() 单例模式不变
- mutate/snapshot 接口不变
- .state 属性仍返回当前活跃 Loop
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from loop_agent_mcp.core.persistence import StatePersistence


@dataclass
class LoopState:
    """Loop Agent 全局状态。"""

    loop_id: str = ""
    mode: str = "default"  # default / resume / abort / unattended
    time_budget_hours: float = 9.0
    started_at: float = 0.0
    iterations: int = 0
    budget_used_usd: float = 0.0
    current_phase: str = "Phase 0"
    current_role: str = ""
    active_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    blocked_tasks: list[str] = field(default_factory=list)
    artifact_status: dict[str, str] = field(default_factory=dict)
    evidence_status: dict[str, list[str]] = field(default_factory=dict)
    gate_status: dict[str, str] = field(default_factory=dict)
    deviation_log: list[dict[str, Any]] = field(default_factory=list)
    fusion_targets: dict[str, bool] = field(default_factory=dict)
    last_action: str = ""
    last_update: float = 0.0
    blackboard_path: str = ""
    workspace: str = ""

    def reset(self) -> None:
        self.loop_id = f"loop-{uuid.uuid4().hex[:8]}"
        self.started_at = time.time()
        self.iterations = 0
        self.budget_used_usd = 0.0
        self.current_phase = "Phase 0"
        self.current_role = ""
        self.active_tasks = []
        self.completed_tasks = []
        self.blocked_tasks = []
        self.artifact_status = {}
        self.evidence_status = {}
        self.gate_status = {
            "gate1_code_review": "PENDING",
            "gate2_performance": "PENDING",
            "gate3_testing": "PENDING",
            "gate4_final": "PENDING",
        }
        self.deviation_log = []
        self.fusion_targets = {
            "full_auto_closed_loop": False,
            "production_grade_delivery": False,
            "direct_deploy_ready": False,
            "token_efficiency_ok": True,
            "flow_convergence_ok": True,
        }
        self.last_action = "init"
        self.last_update = time.time()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def bump(self, action: str) -> None:
        self.iterations += 1
        self.last_action = action
        self.last_update = time.time()


class StateManager:
    """线程安全的状态管理器，支持多 Loop 隔离 + 持久化（v1.3）。"""

    _instance: "StateManager | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        # v1.3: 多 Loop 隔离，以 loop_id 为 key
        self._states: dict[str, LoopState] = {}
        self._active_loop_id: str | None = None
        self._state_lock = threading.Lock()
        self._persistence: StatePersistence | None = None
        self._persistence_workspace: Path | None = None
        # v1.4: 线程局部当前 loop_id，避免并行任务切换冲突
        self._local = threading.local()

    @classmethod
    def get(cls) -> "StateManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（仅用于测试）。"""
        with cls._lock:
            cls._instance = None

    def init_persistence(self, workspace: Path | str) -> None:
        """初始化持久化管理器。

        Args:
            workspace: 工作区根目录。
        """
        if isinstance(workspace, str):
            workspace = Path(workspace)
        workspace = workspace.resolve()

        with self._state_lock:
            if (
                self._persistence is None
                or self._persistence_workspace != workspace
            ):
                self._persistence = StatePersistence(workspace)
                self._persistence_workspace = workspace
                # 自动恢复最新 Loop
                self._auto_restore_latest()

    def _auto_restore_latest(self) -> None:
        """自动从磁盘恢复最新 Loop 状态（如果存在）。"""
        if self._persistence is None:
            return
        latest = self._persistence.get_latest_loop()
        if latest is None:
            return
        loop_id = latest.get("_loop_id", latest.get("loop_id", ""))
        if not loop_id:
            return
        # 恢复状态（不触发保存）
        state = self._dict_to_state(latest)
        self._states[loop_id] = state
        # 仅在没有活跃 Loop 时才激活
        if self._active_loop_id is None:
            self._active_loop_id = loop_id

    @staticmethod
    def _dict_to_state(data: dict[str, Any]) -> LoopState:
        """从字典构造 LoopState（忽略 _ 开头字段）。"""
        clean = {k: v for k, v in data.items() if not k.startswith("_")}
        # 移除已废弃的 key 以避免冲突
        clean.pop("last_update", None)
        return LoopState(**clean)

    @property
    def state(self) -> LoopState:
        """获取当前活跃的 Loop 状态（向后兼容）。

        优先使用线程局部 active_loop_id，避免多任务同时切换冲突。
        若无活跃 Loop 则自动创建一个新的（生成新的 loop_id）。
        """
        with self._state_lock:
            local_loop_id = getattr(self._local, "loop_id", None)
            if local_loop_id and local_loop_id in self._states:
                return self._states[local_loop_id]
            if self._active_loop_id is None or self._active_loop_id not in self._states:
                # 创建新 Loop（不影响已有 Loop）
                default = LoopState()
                default.reset()
                self._states[default.loop_id] = default
                self._active_loop_id = default.loop_id
            return self._states[self._active_loop_id]

    @state.setter
    def state(self, value: LoopState) -> None:
        """设置当前活跃 Loop 状态。

        注意：这会重置活跃 Loop ID 为 value.loop_id，
        但不会删除已存在的其他 Loop。
        """
        with self._state_lock:
            if value.loop_id:
                self._states[value.loop_id] = value
                self._active_loop_id = value.loop_id

    @property
    def active_loop_id(self) -> str | None:
        """获取当前活跃 Loop ID。"""
        local_loop_id = getattr(self._local, "loop_id", None)
        if local_loop_id:
            return local_loop_id
        with self._state_lock:
            return self._active_loop_id

    def set_thread_loop(self, loop_id: str | None) -> None:
        """设置当前线程的 Loop 上下文（线程局部）。

        Args:
            loop_id: 要设置的 Loop ID，None 表示清除。
        """
        if loop_id:
            self._local.loop_id = loop_id
        else:
            self.clear_thread_loop()

    def get_thread_loop(self) -> str | None:
        """获取当前线程的 Loop 上下文（线程局部）。"""
        return getattr(self._local, "loop_id", None)

    def clear_thread_loop(self) -> None:
        """清除当前线程的 Loop 上下文。"""
        if hasattr(self._local, "loop_id"):
            del self._local.loop_id

    def switch_loop(self, loop_id: str) -> bool:
        """切换到指定 Loop。

        Args:
            loop_id: 要切换到的 Loop ID。

        Returns:
            切换是否成功。
        """
        with self._state_lock:
            if loop_id in self._states:
                self._active_loop_id = loop_id
                return True
            # 尝试从磁盘加载
            if self._persistence:
                data = self._persistence.load_state(loop_id)
                if data:
                    state = self._dict_to_state(data)
                    self._states[loop_id] = state
                    self._active_loop_id = loop_id
                    return True
            return False

    def list_loops(self) -> list[dict[str, Any]]:
        """列出所有 Loop（内存 + 磁盘）。"""
        loops: dict[str, dict[str, Any]] = {}

        # 内存中的 Loop
        for loop_id, state in self._states.items():
            loops[loop_id] = {
                "loop_id": loop_id,
                "mode": state.mode,
                "current_phase": state.current_phase,
                "iterations": state.iterations,
                "source": "memory",
            }

        # 磁盘上的 Loop
        if self._persistence:
            for loop_summary in self._persistence.list_loops():
                lid = loop_summary["loop_id"]
                if lid not in loops:
                    loops[lid] = {**loop_summary, "source": "disk"}
                else:
                    loops[lid]["source"] = "memory+disk"

        return list(loops.values())

    def save_current(self) -> bool:
        """保存当前活跃 Loop 到磁盘。"""
        with self._state_lock:
            if self._persistence is None or self._active_loop_id is None:
                return False
            state = self._states.get(self._active_loop_id)
            if state is None:
                return False
            return self._persistence.save_state(self._active_loop_id, state.to_dict())

    def mutate(self, fn) -> Any:
        """以锁保护方式修改当前状态（自动持久化）。

        Args:
            fn: 接收 state 对象并修改的函数。

        Returns:
            fn 的返回值。
        """
        with self._state_lock:
            # v1.4: 优先使用线程局部 loop_id，避免多任务切换冲突
            local_loop_id = getattr(self._local, "loop_id", None)
            if local_loop_id and local_loop_id in self._states:
                state = self._states[local_loop_id]
            elif self._active_loop_id is not None and self._active_loop_id in self._states:
                state = self._states[self._active_loop_id]
            else:
                default = LoopState()
                default.reset()
                self._states[default.loop_id] = default
                self._active_loop_id = default.loop_id
                state = default

            old_id = state.loop_id
            result = fn(state)
            state.last_update = time.time()
            # 如果 fn 修改了 loop_id（如 reset），同步更新 _states 字典
            if state.loop_id != old_id:
                # 删除旧 key（如果还在）
                self._states.pop(old_id, None)
                self._states[state.loop_id] = state
                self._active_loop_id = state.loop_id
                if local_loop_id:
                    self._local.loop_id = state.loop_id
            # 自动持久化
            if self._persistence and state.loop_id:
                self._persistence.save_state(state.loop_id, state.to_dict())
            return result

    def snapshot(self) -> dict[str, Any]:
        """获取当前状态快照。"""
        # state 属性内部已加锁，此处不再重复加锁，避免同线程死锁
        return self.state.to_dict()


def default_blackboard_path(workspace: Path) -> Path:
    return workspace / "项目进度记录.md"
