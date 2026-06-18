"""配置加载器：从 .trae/ 工作区加载 Agent Profiles 与 Workflow Blueprint。

实现 4 级封装资产中的第 2、3 层加载。
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

# 角色类型常量
ROLE_TYPE_CONTROLLER = "controller"
ROLE_TYPE_DECISION_MAKER = "decision_maker"
ROLE_TYPE_SPECIALIST = "specialist"
ROLE_TYPE_GATE_KEEPER = "gate_keeper"

# 16 角色定义
ROLE_NAMES: list[str] = [
    "orchestrator",
    "product-manager",
    "requirements",
    "ux-researcher",
    "ui-designer",
    "architect",
    "backend",
    "frontend",
    "bug-fix",
    "code-reviewer",
    "performance",
    "tester",
    "knowledge-curator",
    "documenter",
    "final-reviewer",
    "devops",
]

# Phase 顺序定义
PHASE_ORDER: list[str] = [
    "Phase 0",
    "Phase 1",
    "Phase 2",
    "Phase 3",
    "Phase 4",
    "Phase 5",
    "Phase 6",
    "Phase 7",
    "Phase 8",
    "Phase 9",
    "Phase 10",
]

# Gate 顺序定义
GATE_ORDER: list[str] = ["gate1_code_review", "gate2_performance", "gate3_testing", "gate4_final"]


def find_workspace_root(start: Path | None = None) -> Path:
    """查找工作区根目录（含 .trae/ 的最近祖先）。"""
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".trae").is_dir():
            return parent
    # 退化：使用当前目录
    return current


def load_agent_profile(workspace: Path, agent_name: str) -> dict[str, Any]:
    """加载单个 Agent Profile（TOML）。

    Args:
        workspace: 工作区根目录
        agent_name: 角色名，如 'orchestrator'

    Returns:
        解析后的字典；若文件不存在则返回最小骨架。
    """
    profile_path = workspace / ".trae" / "agents" / f"{agent_name}.agent.toml"
    if not profile_path.is_file():
        return {
            "name": agent_name,
            "_loaded": False,
            "_path": str(profile_path),
            "harness_discipline": {
                "fusion_version": "v1.2",
                "role_type": _infer_role_type(agent_name),
            },
        }
    with profile_path.open("rb") as f:
        data = tomllib.load(f)
    data["_loaded"] = True
    data["_path"] = str(profile_path)
    return data


def load_all_agent_profiles(workspace: Path) -> dict[str, dict[str, Any]]:
    """加载全部 16 个 Agent Profile。"""
    return {name: load_agent_profile(workspace, name) for name in ROLE_NAMES}


def load_workflow_blueprint(workspace: Path) -> dict[str, Any]:
    """加载工作流蓝图（JSON）。

    返回 prd-to-production.json 的完整配置。
    """
    bp_path = workspace / ".trae" / "workflows" / "prd-to-production.json"
    if not bp_path.is_file():
        return {
            "_loaded": False,
            "_path": str(bp_path),
            "loop_agent_version": "v1.2",
            "phases": {},
            "quality_gates": {},
        }
    with bp_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_fusion_standard(workspace: Path) -> dict[str, Any]:
    """读取融合验收标准（Markdown，解析为元数据）。"""
    std_path = workspace / "docs" / "integration" / "融合验收标准.md"
    if not std_path.is_file():
        return {"_loaded": False, "_path": str(std_path), "version": "unknown"}
    text = std_path.read_text(encoding="utf-8")
    return {
        "_loaded": True,
        "_path": str(std_path),
        "version": "v1.0",
        "checks": _parse_fusion_checks(text),
    }


def _infer_role_type(agent_name: str) -> str:
    """根据角色名推断 role_type。"""
    if agent_name == "orchestrator":
        return ROLE_TYPE_CONTROLLER
    if agent_name in ("product-manager", "architect"):
        return ROLE_TYPE_DECISION_MAKER
    if agent_name in ("code-reviewer", "performance", "tester", "final-reviewer"):
        return ROLE_TYPE_GATE_KEEPER
    return ROLE_TYPE_SPECIALIST


def _parse_fusion_checks(markdown: str) -> dict[str, list[str]]:
    """简单解析融合验收 Markdown 提取检查项（按章节聚合）。"""
    sections: dict[str, list[str]] = {}
    current_section = "general"
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            current_section = stripped[3:].strip()
            sections.setdefault(current_section, [])
        elif stripped.startswith("- [ ]"):
            item = stripped[5:].strip()
            sections[current_section].append(item)
    return sections
