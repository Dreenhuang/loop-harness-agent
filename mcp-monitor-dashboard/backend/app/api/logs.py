"""
Log API endpoints
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime

from app.services.data_collector import collector_service
from app.models import LogLevel

router = APIRouter()


@router.get("")
async def get_logs(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    start_time: Optional[str] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[str] = Query(None, description="End time (ISO 8601)"),
):
    """Query operation logs with filtering and pagination."""
    result = collector_service.get_logs(
        agent_id=agent_id,
        level=level.value if level else None,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return {"code": 0, "data": result}
