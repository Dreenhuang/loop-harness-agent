"""
Project Overview API endpoints
"""

from fastapi import APIRouter

from app.services.data_collector import collector_service

router = APIRouter()


@router.get("/overview")
async def get_project_overview():
    """Get project overview with all key metrics."""
    data = collector_service.collect_all()
    project_data = data.get("project_overview", {})

    # Enrich with real-time agent stats
    agents = data.get("agents", [])
    active_count = sum(1 for a in agents if a["status"] == "running")
    idle_count = sum(1 for a in agents if a["status"] == "idle")
    error_count = sum(1 for a in agents if a["status"] == "error")

    from datetime import datetime

    return {
        "code": 0,
        "data": {
            "project_name": project_data.get("name", "MCP 实时监控看板系统"),
            "current_phase": project_data.get("current_phase", ""),
            "phase_progress": project_data.get("phase_progress", 0),
            "tasks": {
                "total": project_data.get("total_tasks", 0),
                "completed": project_data.get("completed_tasks", 0),
                "in_progress": active_count,
                "failed": project_data.get("failed_tasks", 0),
                "pending": max(
                    0,
                    (project_data.get("total_tasks") or 0)
                    - (project_data.get("completed_tasks") or 0)
                    - active_count
                    - (project_data.get("failed_tasks") or 0),
                ),
            },
            "token_budget": {
                "used": project_data.get("token_used", 0),
                "total": project_data.get("token_total", 100000),
                "percentage": round(
                    (project_data.get("token_used", 0) / max(project_data.get("token_total", 1), 1)) * 100, 2
                ),
            },
            "agents": {
                "total": len(agents),
                "active": active_count,
                "idle": idle_count,
                "error": error_count,
            },
            "gates": {
                "gate1_code_review": project_data.get("gate1_status", "pending"),
                "gate2_performance": project_data.get("gate2_status", "pending"),
                "gate3_testing": project_data.get("gate3_status", "pending"),
                "gate4_final_review": project_data.get("gate4_status", "pending"),
            },
            "uptime_seconds": 86400,  # Mock value
            "last_update": datetime.utcnow().isoformat(),
        },
    }
