"""Loop 全局状态管理：单例状态对象，跨工具调用持久化。"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


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
    """线程安全的单例状态管理器。"""

    _instance: "StateManager | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.state = LoopState()
        self._state_lock = threading.Lock()

    @classmethod
    def get(cls) -> "StateManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def mutate(self, fn) -> Any:
        """以锁保护方式修改状态。"""
        with self._state_lock:
            result = fn(self.state)
            self.state.last_update = time.time()
            return result

    def snapshot(self) -> dict[str, Any]:
        with self._state_lock:
            return self.state.to_dict()


def default_blackboard_path(workspace: Path) -> Path:
    return workspace / "项目进度记录.md"
