"""
Agent API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.data_collector import collector_service

router = APIRouter()


@router.get("")
async def get_all_agents():
    """Get all agent statuses."""
    data = collector_service.collect_all()
    return {"code": 0, "data": data["agents"], "total": len(data["agents"])}


@router.get("/{agent_id}")
async def get_agent_detail(agent_id: str):
    """Get single agent detail."""
    data = collector_service.collect_all()
    agents = {a["id"]: a for a in data["agents"]}

    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    agent_data = agents[agent_id]

    # Add recent logs for this agent
    logs_result = collector_service.get_logs(agent_id=agent_id, page_size=10)
    agent_data["recent_logs"] = logs_result["items"]
    agent_data["error_history"] = []

    return {"code": 0, "data": agent_data}
