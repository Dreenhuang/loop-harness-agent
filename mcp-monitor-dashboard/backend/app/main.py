"""
MCP Monitor Dashboard - FastAPI Application Entry Point
Version: 1.0.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import init_db
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api.router import api_router
from app.websocket.manager import websocket_router

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

# CORS middleware - environment-aware configuration
_cors_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # Alternative frontend port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
# Add production origins from env if configured
import os
if _prod_origins := os.getenv("CORS_ORIGINS"):
    _cors_origins.extend([o.strip() for o in _prod_origins.split(",")])

# In development, allow all; in production, restrict strictly
if settings.app_env == "production":
    _allowed_origins = _cors_origins
else:
    _allowed_origins = ["*"]  # Dev only

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
    uvicorn.run(app.main:app, host="0.0.0.0", port=8000, reload=True)
