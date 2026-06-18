"""Orchestrator 主调度引擎：Loop 推进、Phase 切换、Agent 派发、状态机。

融合 v1.2 强制的 4 阶段门禁 + 一票否决 + Token 治理。
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from loop_agent_mcp.core.config import (
    GATE_ORDER,
    PHASE_ORDER,
    ROLE_NAMES,
    find_workspace_root,
    load_agent_profile,
    load_all_agent_profiles,
    load_fusion_standard,
    load_workflow_blueprint,
)
from loop_agent_mcp.core.state import StateManager
from loop_agent_mcp.engines import blackboard as bb_engine
from loop_agent_mcp.engines import deviation as dev_engine
from loop_agent_mcp.engines import fusion as fusion_engine
from loop_agent_mcp.engines import token as token_engine


# 阶段到角色映射（融合 v1.2）
PHASE_ROLE_MAP: dict[str, list[str]] = {
    "Phase 0": ["orchestrator"],
    "Phase 1": ["product-manager", "requirements"],
    "Phase 2": ["ux-researcher"],
    "Phase 3": ["ui-designer"],
    "Phase 4": ["architect"],
    "Phase 5": ["backend", "frontend"],
    "Phase 6": ["code-reviewer", "performance", "tester"],
    "Phase 7": ["knowledge-curator"],
    "Phase 8": ["documenter"],
    "Phase 9": ["final-reviewer"],
    "Phase 10": ["devops"],
}


def start_loop(
    workspace: Path | None = None,
    mode: str = "default",
    time_budget_hours: float = 9.0,
) -> dict[str, Any]:
    """启动一个新 Loop。"""
    ws = workspace or find_workspace_root()
    StateManager.get().state.reset()
    StateManager.get().mutate(
        lambda s: (
            setattr(s, "mode", mode),
            setattr(s, "time_budget_hours", time_budget_hours),
            setattr(s, "workspace", str(ws)),
            setattr(s, "last_action", "start_loop"),
        )
    )
    # 一次性加载资产（供工具调用时复用）
    workspace_assets = _load_workspace_assets(ws)
    return {
        "loop_id": StateManager.get().state.loop_id,
        "mode": mode,
        "time_budget_hours": time_budget_hours,
        "workspace": str(ws),
        "started_at": StateManager.get().state.started_at,
        "current_phase": StateManager.get().state.current_phase,
        "assets_loaded": {k: bool(v.get("_loaded", True)) for k, v in workspace_assets.items()},
    }


def resume_loop(workspace: Path | None = None) -> dict[str, Any]:
    """恢复一个未完成的 Loop（从黑板状态恢复）。"""
    ws = workspace or find_workspace_root()
    # 从黑板读取最近状态
    bb = bb_engine.read_blackboard(ws)
    if not bb:
        return {
            "status": "no_blackboard",
            "message": "黑板不存在，无法恢复，请使用 start_loop 启动新流程",
        }
    # 简化：直接 reset 并尝试回到 Phase 0（实际应解析黑板进度）
    return start_loop(ws, mode="resume")


def abort_loop(reason: str = "user_abort") -> dict[str, Any]:
    """中止当前 Loop。"""
    StateManager.get().mutate(
        lambda s: (
            setattr(s, "mode", "abort"),
            setattr(s, "last_action", f"abort_loop:{reason}"),
        )
    )
    dev_engine.record_deviation_entry({
        "type": "流程偏离",
        "description": f"Loop 中止：{reason}",
        "recovery": "中止",
    })
    return {
        "status": "aborted",
        "loop_id": StateManager.get().state.loop_id,
        "reason": reason,
        "aborted_at": time.time(),
        "final_state": StateManager.get().snapshot(),
    }


def get_status() -> dict[str, Any]:
    """获取 Loop 完整状态。"""
    state = StateManager.get().snapshot()
    budget = token_engine.get_budget_status()
    deviations = dev_engine.get_deviation_log(limit=10)
    return {
        "loop_id": state["loop_id"],
        "mode": state["mode"],
        "current_phase": state["current_phase"],
        "current_role": state["current_role"],
        "iterations": state["iterations"],
        "last_action": state["last_action"],
        "last_update": state["last_update"],
        "active_tasks": state["active_tasks"],
        "completed_tasks": state["completed_tasks"],
        "blocked_tasks": state["blocked_tasks"],
        "gate_status": state["gate_status"],
        "artifact_status": state["artifact_status"],
        "evidence_summary": {k: len(v) for k, v in state["evidence_status"].items()},
        "fusion_targets": state["fusion_targets"],
        "deviation_count": len(deviations),
        "recent_deviations": deviations,
        "budget": budget,
        "time_budget_hours": state["time_budget_hours"],
    }


def list_agents(workspace: Path | None = None) -> dict[str, Any]:
    """列出 16 角色及 harness_discipline 摘要。"""
    ws = workspace or find_workspace_root()
    profiles = load_all_agent_profiles(ws)
    summary = []
    for name in ROLE_NAMES:
        p = profiles.get(name, {})
        hd = p.get("harness_discipline", {}) if isinstance(p, dict) else {}
        summary.append({
            "name": name,
            "loaded": p.get("_loaded", False),
            "role_type": hd.get("role_type", "unknown"),
            "fusion_version": hd.get("fusion_version", "v1.2"),
            "has_harness_discipline": bool(hd),
        })
    return {
        "count": len(summary),
        "agents": summary,
        "workspace": str(ws),
    }


def spawn_agent(agent_name: str, task_input: dict[str, Any]) -> dict[str, Any]:
    """派发任务给指定 Agent。"""
    if agent_name not in ROLE_NAMES:
        raise ValueError(f"unknown agent: {agent_name}")
    workspace = Path(StateManager.get().state.workspace or find_workspace_root())
    profile = load_agent_profile(workspace, agent_name)
    hd = profile.get("harness_discipline", {}) if isinstance(profile, dict) else {}

    def _op(s):
        s.current_role = agent_name
        s.active_tasks.append(f"{agent_name}:{int(time.time())}")
        s.last_action = f"spawn_agent:{agent_name}"
    StateManager.get().mutate(_op)

    return {
        "spawned_to": agent_name,
        "task_input": task_input,
        "harness_discipline_applied": bool(hd),
        "role_type": hd.get("role_type", "unknown"),
        "mandatory_checks": hd.get("mandatory_checks", {}),
        "deviation_guard": hd.get("deviation_guard", {}),
        "next_step_hint": _hint_for_role(agent_name, task_input),
    }


def advance_phase(target_phase: str | None = None) -> dict[str, Any]:
    """推进到指定 Phase 或下一 Phase。先做偏离检测。"""
    state = StateManager.get()
    current = state.state.current_phase
    target = target_phase or _next_phase(current)
    if target not in PHASE_ORDER:
        raise ValueError(f"unknown phase: {target}")

    # 偏离检测
    skip = dev_engine.detect_phase_skip(current, target)
    if skip:
        dev_engine.record_deviation_entry(skip)
        return {
            "status": "blocked",
            "deviation": skip,
            "current_phase": current,
        }

    # 推进
    StateManager.get().mutate(
        lambda s: (
            setattr(s, "current_phase", target),
            setattr(s, "last_action", f"advance_phase:{target}"),
        )
    )
    return {
        "status": "advanced",
        "from": current,
        "to": target,
        "suggested_roles": PHASE_ROLE_MAP.get(target, []),
    }


def run_gate(gate: str) -> dict[str, Any]:
    """运行指定 Gate（含融合检查）。"""
    if gate not in GATE_ORDER:
        raise ValueError(f"unknown gate: {gate}")
    bb_engine.update_gate_status(gate, "RUNNING")

    artifacts = fusion_engine.check_artifact_completeness()
    evidence = fusion_engine.check_evidence_sufficiency()
    veto = fusion_engine.check_veto_items()

    # Phase 6 阶段 gate：要求工件部分齐全
    # Phase 9 终审：要求全部齐全
    is_final = gate == "gate4_final"
    artifact_required_complete = is_final

    decision = "PASSED"
    reasons: list[str] = []
    if veto["veto_triggered"]:
        decision = "FAILED"
        reasons.append(f"一票否决触发：{veto['triggered']}")
    if artifact_required_complete and not artifacts["complete"]:
        decision = "FAILED"
        reasons.append(f"工件不完整：缺少 {artifacts['missing']}")
    if not evidence["sufficient"] and is_final:
        decision = "FAILED"
        reasons.append(f"证据不充分：缺少 {evidence['missing']}")

    bb_engine.update_gate_status(gate, decision)
    StateManager.get().mutate(lambda s: setattr(s, "last_action", f"run_gate:{gate}:{decision}"))
    return {
        "gate": gate,
        "decision": decision,
        "reasons": reasons,
        "artifacts": artifacts,
        "evidence": evidence,
        "veto": veto,
    }


def save_blackboard(
    workspace: Path | None = None,
    content: str | None = None,
    append_section: str | None = None,
) -> dict[str, Any]:
    """保存/追加黑板。"""
    ws = workspace or Path(StateManager.get().state.workspace or find_workspace_root())
    if append_section is not None:
        return bb_engine.append_blackboard_section(ws, append_section)
    if content is None:
        # 自动从状态生成摘要
        content = _render_blackboard_from_state()
    return bb_engine.write_blackboard(ws, content)


def run_deviation_scan() -> dict[str, Any]:
    """执行一轮偏离扫描。"""
    return dev_engine.run_deviation_scan()


def check_artifact_completeness() -> dict[str, Any]:
    return fusion_engine.check_artifact_completeness()


def check_evidence_sufficiency() -> dict[str, Any]:
    return fusion_engine.check_evidence_sufficiency()


def check_fusion_targets() -> dict[str, Any]:
    return fusion_engine.check_fusion_targets()


def check_veto_items() -> dict[str, Any]:
    return fusion_engine.check_veto_items()


def get_token_budget_status() -> dict[str, Any]:
    return token_engine.token_efficiency_check()


# ---- 内部辅助函数 ----


def _next_phase(current: str) -> str:
    if current not in PHASE_ORDER:
        return "Phase 0"
    idx = PHASE_ORDER.index(current)
    if idx + 1 >= len(PHASE_ORDER):
        return current
    return PHASE_ORDER[idx + 1]


def _load_workspace_assets(workspace: Path) -> dict[str, Any]:
    return {
        "agents": {"all": load_all_agent_profiles(workspace), "_loaded": True},
        "workflow": load_workflow_blueprint(workspace),
        "fusion_standard": load_fusion_standard(workspace),
    }


def _hint_for_role(agent_name: str, task_input: dict[str, Any]) -> str:
    hints = {
        "orchestrator": "请执行调度路由，不要做领域推理。",
        "product-manager": "苏格拉底式澄清需求，探索 2-3 个替代方案。",
        "requirements": "0 歧义 + 100% 可测试。",
        "ux-researcher": "100% 场景覆盖 + 边界流程。",
        "ui-designer": "调用 6 个 UI Skill，反模式审计。",
        "architect": "多方案对比 + 可实施非概念级。",
        "backend": "TDD RED-GREEN-REFACTOR + 微任务化。",
        "frontend": "TDD + Design Token 强制 + Lighthouse ≥ 90。",
        "bug-fix": "四阶段根因分析 + 最小修复 + 知识沉淀。",
        "code-reviewer": "Maker-Checker 分离 + 0 容忍。",
        "performance": "SLA 不可放宽。",
        "tester": "5 维度强制 + P0/P1 清零。",
        "knowledge-curator": "6 段式模板 + 相似度匹配。",
        "documenter": "4 个 100%（最新/完整/可执行/准确）。",
        "final-reviewer": "6 项一票否决 + 全部工件/证据/门禁。",
        "devops": "灰度发布 + 监控先于流量 + 回滚方案。",
    }
    return hints.get(agent_name, "请按 role prompt 执行。")


def _render_blackboard_from_state() -> str:
    """从当前 StateManager 状态生成一份黑板 Markdown 摘要。"""
    state = StateManager.get().snapshot()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    lines = [
        f"# 项目进度记录（自动生成 @ {ts}）",
        "",
        f"- Loop ID: `{state['loop_id']}`",
        f"- Mode: `{state['mode']}`",
        f"- Current Phase: `{state['current_phase']}`",
        f"- Iterations: `{state['iterations']}`",
        f"- Budget Used: `${state['budget_used_usd']:.4f}` / $100.00",
        "",
        "## 工件状态",
    ]
    for art, st in state["artifact_status"].items():
        lines.append(f"- {art}: {st}")
    lines.append("")
    lines.append("## Gate 状态")
    for g, st in state["gate_status"].items():
        lines.append(f"- {g}: {st}")
    lines.append("")
    lines.append("## 融合目标")
    for k, v in state["fusion_targets"].items():
        lines.append(f"- {k}: {'✅' if v else '❌'}")
    return "\n".join(lines) + "\n"
