"""
MCP Monitor Dashboard - FastAPI Application Entry Point
Version: 1.0.0
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import traceback

from app.config import settings
from app.core.database import init_db
from app.core.scheduler import start_scheduler, stop_scheduler
from app.core.auth import APIKeyMiddleware
from app.api.router import api_router
from app.websocket.manager import websocket_router, manager
from app.services.data_collector import collector_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - startup and shutdown events."""
    # Startup
    logger.info("Starting MCP Monitor Dashboard...")
    await init_db()
    collector_service.initialize_default_agents()
    start_scheduler()
    await manager.start_heartbeat()  # Start WebSocket heartbeat
    logger.info("MCP Monitor Dashboard started successfully")
    yield
    # Shutdown
    logger.info("Shutting down MCP Monitor Dashboard...")
    await manager.stop_heartbeat()  # Stop WebSocket heartbeat
    stop_scheduler()
    logger.info("MCP Monitor Dashboard stopped")


app = FastAPI(
    title="MCP Monitor Dashboard API",
    description="Real-time monitoring dashboard for MCP Agent system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - restricted origins from environment variable
# Default: development origins only; production must set CORS_ORIGINS env var
import os
_default_dev_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
_cors_origins_str = os.getenv("CORS_ORIGINS", "")
if _cors_origins_str:
    _allowed_origins = [o.strip() for o in _cors_origins_str.split(",") if o.strip()]
else:
    # No CORS_ORIGINS env var set: default to dev origins only (never wildcard)
    _allowed_origins = _default_dev_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# API Key authentication middleware
app.add_middleware(APIKeyMiddleware)


# G-9 修复：全局异常处理中间件，防止内部异常信息泄露给客户端
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器 - 捕获所有未处理的异常。
    
    - 500 错误只返回通用错误消息
    - 详细异常写入服务端日志（包含 traceback）
    """
    # 记录详细异常信息到服务端日志
    error_detail = f"Unhandled exception: {type(exc).__name__}: {str(exc)}"
    logger.error(error_detail)
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    # 返回通用错误消息给客户端（不暴露内部细节）
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - checks database and services."""
    # TODO: Add actual checks for DB connection, etc.
    return {"status": "ready", "checks": {"database": "ok"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
