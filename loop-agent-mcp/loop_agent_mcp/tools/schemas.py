"""MCP 工具 schema 定义：13 个工具的输入输出规范。"""
from __future__ import annotations

from typing import Any

# 13 个对外工具的 schema（按融合 v1.2 设计）
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
        "description": "向指定 Agent 派发任务。支持同步等待（默认）或异步并行（async=true）。",
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
                "async": {"type": "boolean", "default": False, "description": "是否异步提交，提交后立即返回 task_id"},
                "priority": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10, "description": "任务优先级，数值越小优先级越高"},
                "dependencies": {"type": "array", "items": {"type": "string"}, "default": [], "description": "依赖的 task_id 列表，必须全部成功后才开始"},
                "timeout": {"type": "number", "default": 600, "minimum": 1, "description": "任务超时时间（秒）"},
            },
            "required": ["agent_name"],
        },
    },
    {
        "name": "cancel_task",
        "description": "取消一个已提交但未完成的任务。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务 ID"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "get_task_status",
        "description": "查询指定任务的当前状态与结果摘要。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务 ID"},
            },
            "required": ["task_id"],
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
    # 融合 v1.3.1 新增：Dashboard 信息工具
    {
        "name": "get_dashboard_info",
        "description": "获取 MCP Monitor Dashboard 的访问信息（URL、状态、版本）",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
]
