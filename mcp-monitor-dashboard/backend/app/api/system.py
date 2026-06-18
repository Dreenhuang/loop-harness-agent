"""
System Control API endpoints - start/stop/restart MCP Server
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.process_manager import process_manager

router = APIRouter()


class StopRequest(BaseModel):
    force: bool = False


@router.post("/start")
async def start_mcp_server():
    """Start MCP Server process."""
    result = process_manager.start()
    if result["success"]:
        return {"code": 0, "message": result.get("message", "MCP Server 启动成功"), "data": result}
    return {"code": 1, "message": result.get("error", "启动失败"), "data": None}


@router.post("/stop")
async def stop_mcp_server(request: Optional[StopRequest] = None):
    """Stop MCP Server process."""
    force = request.force if request else False
    result = process_manager.stop(force=force)
    if result["success"]:
        return {"code": 0, "message": result.get("message", "MCP Server 已停止"), "data": result}
    return {"code": 1, "message": result.get("error", "停止失败"), "data": None}


@router.post("/restart")
async def restart_mcp_server():
    """Restart MCP Server process."""
    result = process_manager.restart()
    if result["success"]:
        return {"code": 0, "message": result.get("message", "MCP Server 重启成功"), "data": result}
    return {"code": 1, "message": result.get("error", "重启失败"), "data": None}


@router.get("/status")
async def get_system_status():
    """Get system running status."""
    mcp_status = process_manager.get_status()

    from app.websocket.manager import manager

    return {
        "code": 0,
        "data": {
            "mcp_server": mcp_status,
            "monitor_system": {
                "version": "1.0.0",
                "websocket_connections": manager.connection_count,
                "uptime_seconds": 7200,
            },
        },
    }
