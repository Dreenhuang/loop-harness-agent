"""
Application configuration management
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "MCP Monitor Dashboard"
    app_env: str = "development"  # development/staging/production
    app_debug: bool = True
    app_port: int = 8000

    # MCP Server
    mcp_server_cwd: str = ""
    mcp_server_cmd: str = "python -m loop_agent_mcp.server"

    # Database
    database_url: str = "sqlite:///./data/mcp_monitor.db"

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100

    # Data Collection
    collection_interval_seconds: float = 2.0  # Min: 0.5s, Max: 60s

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
