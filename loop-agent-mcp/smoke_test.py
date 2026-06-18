"""Loop-Harness-Agent MCP Server - 启动 + Smoke 测试。"""
from __future__ import annotations

import sys
import tempfile
import pathlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loop_agent_mcp import __version__, __loop_agent_version__
from loop_agent_mcp.tools.schemas import TOOL_SCHEMAS
from loop_agent_mcp.tools.dispatcher import dispatch
from loop_agent_mcp.core.state import StateManager
from loop_agent_mcp.engines import orchestrator as orch
from loop_agent_mcp.engines import fusion as fusion_engine
from loop_agent_mcp.engines import evidence as ev_engine
from loop_agent_mcp.engines import token as token_engine
from loop_agent_mcp.engines import deviation as dev_engine

PASS = "✅"
FAIL = "❌"
fails: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    sym = PASS if cond else FAIL
    extra = f"  -- {detail}" if detail and not cond else ""
    print(f"  {sym} {name}{extra}")
    if not cond:
        fails.append(name)


print("=" * 60)
print("【1】导入 + 12 工具 schema")
print("=" * 60)
check("版本字段", bool(__version__) and bool(__loop_agent_version__))
check("12 工具全部就位", len(TOOL_SCHEMAS) == 12, f"实际 {len(TOOL_SCHEMAS)}")
names = [t["name"] for t in TOOL_SCHEMAS]
expected = [
    "start_loop", "get_status", "abort_loop", "list_agents", "spawn_agent",
    "save_blackboard", "check_artifact_completeness", "check_evidence_sufficiency",
    "detect_deviation", "check_veto_items", "check_fusion_targets",
    "get_token_budget_status",
]
check("工具名集合一致", set(names) == set(expected), f"差 {set(expected) - set(names)}")

print()
print("=" * 60)
print("【2】start_loop 启动")
print("=" * 60)
StateManager._instance = None
r = dispatch("start_loop", {"time_budget_hours": 1.0, "mode": "default"})
check("loop_id 格式", r["loop_id"].startswith("loop-"), f"实际 {r.get('loop_id')}")
check("time_budget 透传", r.get("time_budget_hours") == 1.0)
check("current_phase=Phase 0", r.get("current_phase") == "Phase 0")

print()
print("=" * 60)
print("【3】12 工具实际调用（核心 smoke）")
print("=" * 60)

# 3.1 list_agents
r = orch.list_agents(workspace=Path("g:/ai-gongju/Loop-agent"))
check("3.1 list_agents → 16", r["count"] == 16, f"实际 {r['count']}")

# 3.2 spawn_agent
r = orch.spawn_agent("backend", {"phase": 5})
check("3.2 spawn backend", r["spawned_to"] == "backend")
check("3.2 backend harness 已应用", r["harness_discipline_applied"])

# 3.3 advance_phase（逐步推进）
StateManager._instance = None
orch.start_loop(workspace=Path("g:/ai-gongju/Loop-agent"))
r = orch.advance_phase(target_phase="Phase 1")
check("3.3 advance_phase → Phase 1", r["status"] == "advanced")
check("3.3 建议角色含 product-manager", "product-manager" in r["suggested_roles"])

# 3.3.1 跳跃检测
r_skip = orch.advance_phase(target_phase="Phase 5")
check("3.3.x Phase 跳跃被阻断", r_skip["status"] == "blocked")

# 3.4 run_gate
r = orch.run_gate("gate1_code_review")
check("3.4 gate1 决策合法", r["decision"] in ("PASSED", "FAILED"), r["decision"])
check("3.4 gate1 含 artifacts/evidence/veto",
      all(k in r for k in ("artifacts", "evidence", "veto")))

# 3.5 evidence
ev_engine.register_evidence("failing_test", "auth.test")
ev_engine.register_evidence("passing_test", "auth.test")
r = fusion_engine.check_evidence_sufficiency(["failing_test", "passing_test"])
check("3.5 2 类证据齐全 sufficient=True", r["sufficient"] is True)

# 3.6 deviation
r = orch.run_deviation_scan()
check("3.6 detect_deviation 包含 findings", "findings" in r)

# 3.7 blackboard
tmp = Path(tempfile.mkdtemp(prefix="lha_smoke_"))
r = orch.save_blackboard(workspace=tmp, append_section="smoke test")
check("3.7 save_blackboard OK", r["status"] == "ok")
check("3.7 黑板文件存在", (tmp / "项目进度记录.md").exists())

# 3.8 token
r = token_engine.get_budget_status()
check("3.8 token 状态字段齐全",
      all(k in r for k in ("used_usd", "limit_usd", "usage_percent", "warning", "halt")))

# 3.9 veto
r = fusion_engine.check_veto_items()
check("3.9 否决 6 项", len(r["items"]) == 6)
check("3.9 veto_triggered 字段存在", "veto_triggered" in r)

# 3.10 fusion targets
r = fusion_engine.check_fusion_targets()
check("3.10 融合 5 目标", len(r["targets"]) == 5)

# 3.11 status
r = orch.get_status()
check("3.11 get_status 完整", "iterations" in r and "gate_status" in r)

# 3.12 abort
r = orch.abort_loop(reason="smoke_done")
check("3.12 abort 返回 status=aborted", r["status"] == "aborted")

print()
print("=" * 60)
print("【4】Ralph 模式：reset 后重启")
print("=" * 60)
StateManager._instance = None
r = dispatch("start_loop", {"time_budget_hours": 2.0})
new_id = r["loop_id"]
status = orch.get_status()
check("4.1 新 loop_id", new_id.startswith("loop-"))
check("4.2 全新 state.iterations=0", status["iterations"] == 0)
check("4.3 全新 state.current_phase=Phase 0", status["current_phase"] == "Phase 0")
check("4.4 全新 budget_used=0", status["budget"]["used_usd"] == 0.0)

print()
print("=" * 60)
if fails:
    print(f"【失败】{len(fails)} 项: {fails}")
    sys.exit(1)
print("【全部 smoke 测试通过 ✅】")
print(f"   工具数: {len(TOOL_SCHEMAS)}")
print(f"   角色数: 16")
print(f"   Phase: 11")
print(f"   Gate: 4")
print(f"   工件强制: 11")
print(f"   证据强制: 5")
print(f"   一票否决: 6")
print(f"   融合目标: 5")
print("=" * 60)
