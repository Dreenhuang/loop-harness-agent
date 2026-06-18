"""证据收集引擎：分类、登记、状态查询。

证据类型（融合 v1.2 强制）：
- failing_test
- passing_test
- refactor_evidence
- verification_commands
- review_feedback
- deploy_smoke_test
"""
from __future__ import annotations

from typing import Any

from loop_agent_mcp.core.state import StateManager

EVIDENCE_CATEGORIES: list[str] = [
    "failing_test",
    "passing_test",
    "refactor_evidence",
    "verification_commands",
    "review_feedback",
    "deploy_smoke_test",
]


def register_evidence(category: str, evidence_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """登记一条证据。"""
    if category not in EVIDENCE_CATEGORIES:
        raise ValueError(f"invalid evidence category: {category}")
    StateManager.get().mutate(
        lambda s: s.evidence_status.setdefault(category, []).append(evidence_id)
    )
    return {
        "status": "ok",
        "category": category,
        "evidence_id": evidence_id,
        "payload": payload or {},
    }


def list_evidence(category: str | None = None) -> dict[str, list[str]]:
    """列出某类或全部证据。"""
    state = StateManager.get().snapshot()
    if category:
        return {category: state["evidence_status"].get(category, [])}
    return state["evidence_status"]


def evidence_sufficiency_check(required_for_phase: list[str]) -> dict[str, Any]:
    """检查指定证据是否齐全（用于 Gate 阻断决策）。"""
    state = StateManager.get().snapshot()
    have = state["evidence_status"]
    missing = [c for c in required_for_phase if not have.get(c)]
    return {
        "sufficient": len(missing) == 0,
        "required": required_for_phase,
        "missing": missing,
        "present": {c: have.get(c, []) for c in required_for_phase if have.get(c)},
    }
