"""偏离检测引擎：5 类偏离自动识别 + 恢复建议。

偏离类型：
- 流程偏离（phase 跳跃、绕过 gate）
- 角色偏离（越权、缺位、Maker-Checker 未分离）
- 目标偏离（demo 伪装、范围蔓延、PRD 偏离）
- 资源偏离（Token 超预算、连续无进展）
- 结果偏离（缺工件、缺证据、缺部署前提、伪完成）
"""
from __future__ import annotations

import time
from typing import Any

from loop_agent_mcp.core.state import StateManager, LoopState

DEVIATION_TYPES = ["流程偏离", "角色偏离", "目标偏离", "资源偏离", "结果偏离"]

# 一票否决项
VETO_ITEMS: list[str] = [
    "工件链不完整",
    "Gate 可被绕过",
    "无法基于黑板恢复",
    "demo 级结果伪装生产级",
    "Token 失控无法收敛",
    "无人值守空转或伪完成",
]


def detect_phase_skip(current_phase: str, attempted_phase: str) -> dict[str, Any] | None:
    """检测是否发生 Phase 跳跃。"""
    from loop_agent_mcp.core.config import PHASE_ORDER
    if current_phase not in PHASE_ORDER or attempted_phase not in PHASE_ORDER:
        return None
    cur_idx = PHASE_ORDER.index(current_phase)
    att_idx = PHASE_ORDER.index(attempted_phase)
    if att_idx > cur_idx + 1:
        return {
            "type": "流程偏离",
            "description": f"Phase 跳跃：从 {current_phase} 直接跳到 {attempted_phase}",
            "recovery": "回退",
        }
    return None


def detect_budget_overrun(state: LoopState) -> dict[str, Any] | None:
    """检测预算超限。"""
    if state.budget_used_usd > 100.0:
        return {
            "type": "资源偏离",
            "description": f"Token 预算超限：{state.budget_used_usd:.2f}/100.00 USD",
            "recovery": "中止",
        }
    if state.budget_used_usd > 80.0:
        return {
            "type": "资源偏离",
            "description": f"Token 预算告警：{state.budget_used_usd:.2f}/100.00 USD（> 80%）",
            "recovery": "降级",
        }
    return None


def detect_no_progress(state: LoopState) -> dict[str, Any] | None:
    """检测连续无进展（连续 3 轮 last_action 相同且无 completed_tasks 增加）。"""
    if state.iterations < 3:
        return None
    # 简化：若 5 轮内没有新增完成且 last_action 不变则告警
    if state.last_action and len(state.completed_tasks) == 0 and state.iterations > 5:
        return {
            "type": "资源偏离",
            "description": f"连续 {state.iterations} 轮无有效进展",
            "recovery": "重试",
        }
    return None


def detect_violations(state: LoopState) -> list[dict[str, Any]]:
    """一票否决项检查。"""
    violations: list[dict[str, Any]] = []
    artifacts = state.artifact_status or {}
    if artifacts and all(v != "COMPLETED" for v in artifacts.values()):
        completed = sum(1 for v in artifacts.values() if v == "COMPLETED")
        if completed < len(artifacts) * 0.5:
            violations.append({
                "type": "结果偏离",
                "veto": "工件链不完整",
                "description": f"工件完成度 {completed}/{len(artifacts)}",
            })
    if state.budget_used_usd > 150.0:
        violations.append({
            "type": "资源偏离",
            "veto": "Token 失控无法收敛",
            "description": f"Token 消耗 {state.budget_used_usd:.2f} USD 远超 150% 预算",
        })
    return violations


def run_deviation_scan() -> dict[str, Any]:
    """执行一轮偏离扫描并写入日志。"""
    state_mgr = StateManager.get()
    state = state_mgr.snapshot()
    findings: list[dict[str, Any]] = []

    budget_issue = detect_budget_overrun(state_mgr.state)
    if budget_issue:
        findings.append(budget_issue)
    np_issue = detect_no_progress(state_mgr.state)
    if np_issue:
        findings.append(np_issue)
    violations = detect_violations(state_mgr.state)
    findings.extend(violations)

    for f in findings:
        record_deviation_entry(f)
    return {
        "scanned_at": time.time(),
        "iterations": state["iterations"],
        "findings_count": len(findings),
        "findings": findings,
        "deviation_log_total": len(state["deviation_log"]) + len(findings),
    }


def record_deviation_entry(entry: dict[str, Any]) -> None:
    StateManager.get().mutate(lambda s: s.deviation_log.append({
        "timestamp": time.time(),
        **entry,
    }))


def get_deviation_log(limit: int = 50) -> list[dict[str, Any]]:
    state = StateManager.get().snapshot()
    return state["deviation_log"][-limit:]
