"""MCP 工具 schema 定义：12 个工具的输入输出规范。"""
from __future__ import annotations

from typing import Any

# 12 个对外工具的 schema（按融合 v1.2 设计）
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "start_loop",
        "description": "启动一个完整的 Loop-Harness-Agent 流程。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prd_path": {"type": "string", "description": "PRD 文件路径（可选）"},
                "time_budget_hours": {"type": "number", "default": 9.0, "minimum": 0.5, "maximum": 168.0},
                "mode": {"type": "string", "enum": ["default", "resume", "unattended"], "default": "default"},
            },
        },
    },
    {
        "name": "get_status",
        "description": "查询当前 Loop 完整状态（隐式读黑板）。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "abort_loop",
        "description": "中止当前 Loop。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "default": "user_abort"},
            },
        },
    },
    {
        "name": "list_agents",
        "description": "列出 16 角色及 harness_discipline 摘要。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "spawn_agent",
        "description": "向指定 Agent 派发任务。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "enum": [
                    "orchestrator", "product-manager", "requirements", "ux-researcher",
                    "ui-designer", "architect", "backend", "frontend",
                    "bug-fix", "code-reviewer", "performance", "tester",
                    "knowledge-curator", "documenter", "final-reviewer", "devops",
                ]},
                "task_input": {"type": "object", "default": {}},
            },
            "required": ["agent_name"],
        },
    },
    {
        "name": "save_blackboard",
        "description": "保存/追加黑板。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "完整内容（覆盖模式）"},
                "append_section": {"type": "string", "description": "追加段落"},
            },
        },
    },
    {
        "name": "check_artifact_completeness",
        "description": "检查 12 个强制工件完整性。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "required": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "check_evidence_sufficiency",
        "description": "检查 5 类证据充分性。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "required": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "detect_deviation",
        "description": "执行一轮偏离检测（5 类偏离 + 一票否决）。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_veto_items",
        "description": "一票否决项检查（6 项）。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_fusion_targets",
        "description": "5 大融合目标达成度评估。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_token_budget_status",
        "description": "Token 预算与效率状态。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # 融合 v1.2 新增：文件操作工具
    {
        "name": "write_file",
        "description": "写入文件到项目目录（支持任意路径和内容）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "相对路径（如 src/api/example.ts）"},
                "content": {"type": "string", "description": "文件内容"},
                "workspace": {"type": "string", "description": "工作区路径（可选，默认项目根目录）"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "读取项目中的文件内容。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "相对路径（如 src/api/example.ts）"},
                "workspace": {"type": "string", "description": "工作区路径（可选）"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "列出目录下的所有文件。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "相对目录路径（默认 . ）", "default": "."},
                "workspace": {"type": "string", "description": "工作区路径（可选）"},
            },
        },
    },
]
