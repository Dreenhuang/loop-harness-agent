"""融合验收引擎：5 大融合目标 + 工件完整性 + 证据充分性 + 一票否决。

融合 v1.2 验收标准来源：
g:\\ai-gongju\\Loop-agent\\docs\\integration\\融合验收标准.md
"""
from __future__ import annotations

from typing import Any

from loop_agent_mcp.core.state import StateManager
from loop_agent_mcp.engines.deviation import VETO_ITEMS, detect_violations

# 强制工件清单（融合 v1.2）
MANDATORY_ARTIFACTS: list[str] = [
    "Product-Spec.md",
    "Design-Brief.md",
    "UI-Design.md",
    "Component-Library.md",
    "Architecture.md",
    "API-Spec.md",
    "DEV-PLAN.md",
    "Quality-Check-Report.md",
    "Test-Report.md",
    "Code-Review-Report.md",
    "Release-Notes.md",
]

# 强制证据清单（融合 v1.2）
MANDATORY_EVIDENCE: list[str] = [
    "failing_test",
    "passing_test",
    "verification_commands",
    "review_feedback",
    "deploy_smoke_test",
]


def check_artifact_completeness(required: list[str] | None = None) -> dict[str, Any]:
    """检查强制工件完整性。"""
    state = StateManager.get().snapshot()
    required = required or MANDATORY_ARTIFACTS
    artifacts = state["artifact_status"]
    missing = [a for a in required if artifacts.get(a) != "COMPLETED"]
    in_progress = [a for a in required if artifacts.get(a) == "IN_PROGRESS"]
    completed = [a for a in required if artifacts.get(a) == "COMPLETED"]
    return {
        "complete": len(missing) == 0,
        "required_count": len(required),
        "completed_count": len(completed),
        "in_progress_count": len(in_progress),
        "missing_count": len(missing),
        "missing": missing,
        "in_progress": in_progress,
        "completed": completed,
    }


def check_evidence_sufficiency(required: list[str] | None = None) -> dict[str, Any]:
    """检查强制证据充分性。"""
    state = StateManager.get().snapshot()
    required = required or MANDATORY_EVIDENCE
    have = state["evidence_status"]
    missing = [c for c in required if not have.get(c)]
    return {
        "sufficient": len(missing) == 0,
        "required": required,
        "missing": missing,
        "present": {c: have.get(c, []) for c in required if have.get(c)},
    }


def check_veto_items() -> dict[str, Any]:
    """一票否决项检查。"""
    state = StateManager.get().snapshot()
    violations = detect_violations(StateManager.get().state)
    triggered = [v for v in VETO_ITEMS if any(v in str(x) for x in violations)]
    return {
        "veto_triggered": len(triggered) > 0,
        "items": VETO_ITEMS,
        "triggered": triggered,
        "violations": violations,
    }


def check_fusion_targets() -> dict[str, Any]:
    """5 大融合目标达成度评估。"""
    state = StateManager.get().snapshot()
    artifacts = check_artifact_completeness()
    evidence = check_evidence_sufficiency()
    veto = check_veto_items()
    budget = state["budget_used_usd"] < 95.0

    targets = {
        "full_auto_closed_loop": bool(state["completed_tasks"]),
        "production_grade_delivery": artifacts["complete"],
        "direct_deploy_ready": (
            artifacts["complete"]
            and "deploy_smoke_test" in state["evidence_status"]
        ),
        "token_efficiency_ok": budget,
        "flow_convergence_ok": not veto["veto_triggered"] and budget,
    }
    # 写回状态
    StateManager.get().mutate(lambda s: s.fusion_targets.update(targets))

    return {
        "targets": targets,
        "artifact_complete": artifacts["complete"],
        "evidence_sufficient": evidence["sufficient"],
        "veto_triggered": veto["veto_triggered"],
        "budget_ok": budget,
        "overall_pass": all(targets.values()),
    }


def fusion_final_gate() -> dict[str, Any]:
    """融合终审：所有验收项一并检查。"""
    artifacts = check_artifact_completeness()
    evidence = check_evidence_sufficiency()
    veto = check_veto_items()
    targets = check_fusion_targets()
    all_pass = (
        artifacts["complete"]
        and evidence["sufficient"]
        and not veto["veto_triggered"]
        and targets["overall_pass"]
    )
    return {
        "decision": "GO" if all_pass else "BLOCKED",
        "artifacts": artifacts,
        "evidence": evidence,
        "veto": veto,
        "targets": targets,
    }
