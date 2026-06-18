"""Loop-Harness-Agent MCP Server - 内置 stdlib 测试运行器（无 pytest 依赖）。"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

# 确保包可导入
sys.path.insert(0, str(Path(__file__).parent))

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
from loop_agent_mcp.engines import evidence as ev_engine
from loop_agent_mcp.engines import fusion as fusion_engine
from loop_agent_mcp.engines import orchestrator as orch
from loop_agent_mcp.engines import token as token_engine
from loop_agent_mcp.engines import deviation as dev_engine
from loop_agent_mcp.tools.dispatcher import dispatch

WORKSPACE = Path("g:/ai-gongju/Loop-agent").resolve()

PASS = "✅"
FAIL = "❌"

results: list[tuple[str, bool, str]] = []


def reset():
    StateManager._instance = None


def expect(name, cond, detail=""):
    ok = bool(cond)
    results.append((name, ok, detail))
    sym = PASS if ok else FAIL
    print(f"{sym} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def expect_raises(name, fn, exc_type=Exception):
    try:
        fn()
        expect(name, False, "应抛异常但未抛")
    except exc_type:
        expect(name, True)
    except Exception as e:
        expect(name, False, f"抛了 {type(e).__name__}，期望 {exc_type.__name__}")


# ============== 1. 配置加载 ==============

def test_config():
    reset()
    expect("配置: 16 角色常量", len(ROLE_NAMES) == 16)
    expect("配置: 11 Phase 常量", len(PHASE_ORDER) == 11)
    expect("配置: 4 Gate 常量", len(GATE_ORDER) == 4)
    ws = find_workspace_root(WORKSPACE)
    expect("配置: 找到工作区根", ws == WORKSPACE)
    expect("配置: .trae 存在", (ws / ".trae").is_dir())
    profiles = load_all_agent_profiles(ws)
    expect("配置: 加载 16 profiles", len(profiles) == 16)
    loaded = sum(1 for p in profiles.values() if p.get("_loaded"))
    expect("配置: 至少 10 个 profile 实加载", loaded >= 10, f"实际 {loaded}")
    bp = load_workflow_blueprint(ws)
    expect("配置: 蓝图含 phases", "phases" in bp)
    expect("配置: 蓝图含 quality_gates", "quality_gates" in bp)
    std = load_fusion_standard(ws)
    expect("配置: 融合标准加载", std.get("_loaded"))
    expect("配置: 融合标准含检查项", len(std.get("checks", {})) > 0)


# ============== 2. StateManager ==============

def test_state():
    reset()
    sm = StateManager.get()
    sm.state.loop_id = "test"
    sm.state.reset()
    expect("State: reset 后 loop_id 重新生成", sm.state.loop_id.startswith("loop-"))
    expect("State: reset 后当前 Phase=0", sm.state.current_phase == "Phase 0")
    expect("State: 4 Gate PENDING", all(v == "PENDING" for v in sm.state.gate_status.values()))
    s1 = sm.snapshot()
    s1["iterations"] = 999
    s2 = sm.snapshot()
    expect("State: snapshot 隔离", s2["iterations"] != 999)


# ============== 3. start_loop / get_status / abort_loop ==============

def test_lifecycle():
    reset()
    res = orch.start_loop(workspace=WORKSPACE, mode="default", time_budget_hours=4.0)
    expect("生命周期: start_loop 返回 loop_id", res["loop_id"].startswith("loop-"))
    expect("生命周期: mode=default", res["mode"] == "default")
    expect("生命周期: time_budget=4.0", res["time_budget_hours"] == 4.0)
    expect("生命周期: current_phase=Phase 0", res["current_phase"] == "Phase 0")

    status = orch.get_status()
    expect("生命周期: get_status 含 iterations", "iterations" in status)
    expect("生命周期: get_status 含 budget", "budget" in status)
    expect("生命周期: get_status 含 gate_status", "gate_status" in status)

    res2 = orch.abort_loop(reason="test")
    expect("生命周期: abort 返回 status=aborted", res2["status"] == "aborted")
    expect("生命周期: abort 后 mode=abort", StateManager.get().state.mode == "abort")


# ============== 4. list_agents / spawn_agent ==============

def test_agents():
    reset()
    res = orch.list_agents(workspace=WORKSPACE)
    expect("Agent: list 返回 16", res["count"] == 16)
    types = {a["role_type"] for a in res["agents"]}
    expect("Agent: 含 controller", "controller" in types)
    expect("Agent: 含 decision_maker", "decision_maker" in types)
    expect("Agent: 含 specialist", "specialist" in types)
    expect("Agent: 含 gate_keeper", "gate_keeper" in types)

    expect_raises("Agent: 未知角色抛异常", lambda: orch.spawn_agent("ghost", {}))

    res2 = orch.spawn_agent("backend", {"phase": 5})
    expect("Agent: spawn backend", res2["spawned_to"] == "backend")
    expect("Agent: backend 应用 harness", res2["harness_discipline_applied"])
    expect("Agent: backend role_type=specialist", res2["role_type"] == "specialist")
    expect("Agent: backend next_step_hint 非空", bool(res2["next_step_hint"]))


# ============== 5. advance_phase ==============

def test_phase_advance():
    reset()
    r = orch.advance_phase(target_phase="Phase 1")
    expect("Phase: 正常推进到 Phase 1", r["status"] == "advanced")
    expect("Phase: 包含建议角色 product-manager", "product-manager" in r["suggested_roles"])

    r2 = orch.advance_phase(target_phase="Phase 10")
    expect("Phase: 跳跃被阻断", r2["status"] == "blocked")
    expect("Phase: 偏离类型=流程偏离", r2["deviation"]["type"] == "流程偏离")


# ============== 6. run_gate ==============

def test_gates():
    reset()
    expect_raises("Gate: 未知 gate 抛异常", lambda: orch.run_gate("ghost"))
    r = orch.run_gate("gate1_code_review")
    expect("Gate: gate1 决策合法", r["decision"] in ("PASSED", "FAILED"))
    expect("Gate: gate1 含 artifacts", "artifacts" in r)
    expect("Gate: gate1 含 evidence", "evidence" in r)
    expect("Gate: gate1 含 veto", "veto" in r)


# ============== 7. evidence / fusion ==============

def test_evidence_fusion():
    reset()
    ev_engine.register_evidence("failing_test", "t1")
    ev_engine.register_evidence("passing_test", "t1")
    res = fusion_engine.check_evidence_sufficiency(["failing_test", "passing_test"])
    expect("证据: 2 个齐全时 sufficient=True", res["sufficient"])

    res2 = fusion_engine.check_evidence_sufficiency(["failing_test", "deploy_smoke_test"])
    expect("证据: 缺 deploy_smoke_test 时 sufficient=False", not res2["sufficient"])
    expect("证据: 缺失列表含 deploy_smoke_test", "deploy_smoke_test" in res2["missing"])

    ac = fusion_engine.check_artifact_completeness()
    expect("工件: 初始 complete=False", not ac["complete"])
    expect("工件: required_count=11", ac["required_count"] == 11)

    ft = fusion_engine.check_fusion_targets()
    expect("融合: 5 大目标", len(ft["targets"]) == 5)
    expect("融合: overall_pass=初始 False", ft["overall_pass"] is False)

    veto = fusion_engine.check_veto_items()
    expect("否决: 6 项", len(veto["items"]) == 6)
    expect("否决: 含 veto_triggered 字段", "veto_triggered" in veto)


# ============== 8. token ==============

def test_token():
    reset()
    res = token_engine.record_usage("hello world " * 100, label="test")
    expect("Token: 估算 > 0", res["tokens_estimated"] > 0)
    expect("Token: 预算累加", StateManager.get().state.budget_used_usd > 0)

    token_engine.record_usage("x" * 10000, label="big")
    status = token_engine.get_budget_status()
    expect("Token: usage_percent > 0", status["usage_percent"] > 0)
    expect("Token: 含 warning/halt 字段", "warning" in status and "halt" in status)

    expect("Token: 10000 字应摘要", token_engine.should_summarize("x" * 10000))
    expect("Token: 10 字不摘要", not token_engine.should_summarize("x" * 10))

    text = "\n".join(f"line {i}" for i in range(200))
    summary = token_engine.summarize_for_orchestrator(text, max_lines=5)
    expect("Token: 摘要含省略标记", "省略" in summary)
    expect("Token: 摘要短于原文", len(summary) < len(text))

    eff = token_engine.token_efficiency_check()
    expect("Token: efficiency_check 含 budget_status", "budget_status" in eff)
    expect("Token: efficiency_check 含 fusion_target 字段", "fusion_target_token_efficiency_ok" in eff)


# ============== 9. deviation ==============

def test_deviation():
    reset()
    r = orch.run_deviation_scan()
    expect("偏离: 含 scanned_at", "scanned_at" in r)
    expect("偏离: 含 findings", "findings" in r)
    expect("偏离: findings_count >= 0", r["findings_count"] >= 0)

    StateManager.get().state.budget_used_usd = 85.0
    issue = dev_engine.detect_budget_overrun(StateManager.get().state)
    expect("偏离: 85 USD 触发告警", issue is not None)
    expect("偏离: 告警类型=资源偏离", issue["type"] == "资源偏离" if issue else False)


# ============== 10. save_blackboard ==============

def test_blackboard(tmp_dir):
    reset()
    res = orch.save_blackboard(workspace=tmp_dir, content="# Test\nOK")
    expect("黑板: 保存返回 ok", res["status"] == "ok")
    expect("黑板: 文件存在", (tmp_dir / "项目进度记录.md").exists())

    res2 = orch.save_blackboard(workspace=tmp_dir, append_section="hello")
    expect("黑板: 追加返回 ok", res2["status"] == "ok")
    text = (tmp_dir / "项目进度记录.md").read_text(encoding="utf-8")
    expect("黑板: 追加内容可见", "hello" in text)

    res3 = orch.save_blackboard(workspace=tmp_dir)  # 自动渲染
    text3 = (tmp_dir / "项目进度记录.md").read_text(encoding="utf-8")
    expect("黑板: 自动渲染含 Loop ID", "Loop ID" in text3)


# ============== 11. dispatcher 端到端 ==============

def test_dispatcher():
    reset()
    res = dispatch("start_loop", {"time_budget_hours": 2.0})
    expect("Dispatcher: start_loop", "loop_id" in res and res["time_budget_hours"] == 2.0)

    res = dispatch("get_status", {})
    expect("Dispatcher: get_status", "iterations" in res)

    res = dispatch("nonexistent", {})
    expect("Dispatcher: 未知工具 error", "error" in res)

    tool_names = [
        "start_loop", "get_status", "abort_loop", "list_agents", "spawn_agent",
        "save_blackboard", "check_artifact_completeness", "check_evidence_sufficiency",
        "detect_deviation", "check_veto_items", "check_fusion_targets",
        "get_token_budget_status",
    ]
    for name in tool_names:
        if name == "spawn_agent":
            res = dispatch(name, {"agent_name": "backend", "task_input": {}})
        else:
            res = dispatch(name, {})
        expect(f"Dispatcher: {name}", "error" not in res, detail=str(res.get("error")))


# ============== 12. 端到端集成 ==============

def test_e2e(tmp_dir):
    reset()
    dispatch("start_loop", {"workspace": str(tmp_dir), "time_budget_hours": 1.0})

    for phase in ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]:
        r = orch.advance_phase(target_phase=phase)
        expect(f"E2E: 推进到 {phase}", r["status"] == "advanced")

    res = dispatch("spawn_agent", {"agent_name": "backend", "task_input": {"phase": 5}})
    expect("E2E: spawn backend", res["spawned_to"] == "backend")

    ev_engine.register_evidence("failing_test", "t1")
    ev_engine.register_evidence("passing_test", "t1")
    ev_engine.register_evidence("verification_commands", "pytest")

    fusion = dispatch("check_fusion_targets", {})
    expect("E2E: fusion targets", "targets" in fusion)

    artifacts = dispatch("check_artifact_completeness", {})
    expect("E2E: artifact check", artifacts["required_count"] == 11)

    bb = dispatch("save_blackboard", {"append_section": "E2E done", "workspace": str(tmp_dir)})
    expect("E2E: save blackboard", bb["status"] == "ok")
    expect("E2E: blackboard 文件存在", (tmp_dir / "项目进度记录.md").exists())

    final_gate = dispatch("check_veto_items", {})
    expect("E2E: veto check", "veto_triggered" in final_gate)


# ============== Main ==============

def main():
    import tempfile
    tmp_dir = Path(tempfile.mkdtemp(prefix="lha_test_"))
    print(f"Workspace: {WORKSPACE}")
    print(f"Temp dir: {tmp_dir}")
    print("=" * 60)

    suites = [
        ("1. 配置加载", test_config),
        ("2. StateManager", test_state),
        ("3. Loop 生命周期", test_lifecycle),
        ("4. Agent 派发", test_agents),
        ("5. Phase 推进", test_phase_advance),
        ("6. Gate 运行", test_gates),
        ("7. 证据与融合", test_evidence_fusion),
        ("8. Token 治理", test_token),
        ("9. 偏离检测", test_deviation),
        ("10. 黑板", lambda: test_blackboard(tmp_dir)),
        ("11. Dispatcher", test_dispatcher),
        ("12. 端到端集成", lambda: test_e2e(tmp_dir)),
    ]
    for name, fn in suites:
        print(f"\n--- {name} ---")
        try:
            fn()
        except Exception as e:
            traceback.print_exc()
            expect(f"{name} 套件异常", False, f"{type(e).__name__}: {e}")

    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 通过")
    if passed == total:
        print("【全部通过】✅")
        return 0
    print("【部分失败】❌")
    for name, ok, detail in results:
        if not ok:
            print(f"  {FAIL} {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
