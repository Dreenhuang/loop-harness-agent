"""
API Router - aggregates all API endpoints
"""

from fastapi import APIRouter
from .agents import router as agents_router
from .logs import router as logs_router
from .project import router as project_router
from .system import router as system_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_router.include_router(logs_router, prefix="/logs", tags=["Logs"])
api_router.include_router(project_router, prefix="/project", tags=["Project"])
api_router.include_router(system_router, prefix="/system", tags=["System"])
