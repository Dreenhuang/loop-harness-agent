"""黑板引擎：读写 项目进度记录.md，维护工件/证据/偏离/Phase/Gate 状态。"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from loop_agent_mcp.core.state import StateManager


def read_blackboard(workspace: Path) -> str:
    """读取项目进度记录.md 的全文。"""
    bb_path = workspace / "项目进度记录.md"
    if not bb_path.is_file():
        return ""
    return bb_path.read_text(encoding="utf-8")


def write_blackboard(workspace: Path, content: str) -> dict[str, Any]:
    """写入项目进度记录.md（追加或覆盖）。

    Args:
        workspace: 工作区
        content: 完整内容或新增段落
    """
    bb_path = workspace / "项目进度记录.md"
    bb_path.parent.mkdir(parents=True, exist_ok=True)
    bb_path.write_text(content, encoding="utf-8")
    StateManager.get().mutate(lambda s: setattr(s, "blackboard_path", str(bb_path)))
    return {
        "status": "ok",
        "path": str(bb_path),
        "bytes": len(content),
        "timestamp": time.time(),
    }


def append_blackboard_section(workspace: Path, section: str) -> dict[str, Any]:
    """向项目进度记录.md 追加一个本轮日志段。"""
    bb_path = workspace / "项目进度记录.md"
    bb_path.parent.mkdir(parents=True, exist_ok=True)

    existing = bb_path.read_text(encoding="utf-8") if bb_path.is_file() else ""
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    block = f"\n\n## 【{ts}｜Loop-Harness-Agent｜自动追加】\n{section}\n"
    new_content = existing + block
    bb_path.write_text(new_content, encoding="utf-8")
    StateManager.get().mutate(lambda s: setattr(s, "blackboard_path", str(bb_path)))
    return {
        "status": "ok",
        "path": str(bb_path),
        "appended_bytes": len(block),
        "total_bytes": len(new_content),
    }


def update_artifact_status(name: str, status: str) -> None:
    """更新工件状态：PENDING / IN_PROGRESS / COMPLETED / BLOCKED。"""
    valid = {"PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED"}
    if status not in valid:
        raise ValueError(f"invalid artifact status: {status}")
    StateManager.get().mutate(lambda s: s.artifact_status.update({name: status}))


def update_evidence_status(category: str, evidence_id: str) -> None:
    """登记一条证据。"""
    def _op(s):
        s.evidence_status.setdefault(category, []).append(evidence_id)
    StateManager.get().mutate(_op)


def record_deviation(deviation_type: str, description: str, recovery: str = "none") -> None:
    """记录一次偏离事件。"""
    entry = {
        "timestamp": time.time(),
        "type": deviation_type,
        "description": description,
        "recovery": recovery,
    }
    StateManager.get().mutate(lambda s: s.deviation_log.append(entry))


def update_gate_status(gate: str, status: str) -> None:
    """更新 Gate 状态：PENDING / RUNNING / PASSED / FAILED。"""
    StateManager.get().mutate(lambda s: s.gate_status.update({gate: status}))


def load_blackboard_json(workspace: Path) -> dict[str, Any]:
    """尝试以 JSON 形式加载 state.json（如果存在）。"""
    state_path = workspace / "blackboard" / "state.json"
    if not state_path.is_file():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_error": "state.json 格式损坏"}
