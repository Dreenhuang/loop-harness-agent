"""
Process Manager Service - manages MCP Server process lifecycle
"""

import subprocess
import signal
import logging
import time
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class ProcessManagerService:
    """Service for managing MCP Server process."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._pid: Optional[int] = None
        self._start_time: Optional[float] = None

    @property
    def is_running(self) -> bool:
        """Check if MCP Server is currently running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def pid(self) -> Optional[int]:
        """Get current process PID."""
        return self._pid

    @property
    def uptime_seconds(self) -> int:
        """Get uptime in seconds."""
        if not self._start_time:
            return 0
        return int(time.time() - self._start_time)

    def start(self) -> dict:
        """Start MCP Server process."""
        if self.is_running:
            return {
                "success": False,
                "error": "MCP Server is already running",
                "pid": self._pid,
            }

        try:
            logger.info(f"🚀 Starting MCP Server: {settings.mcp_server_cmd}")

            # Start the process
            cwd = settings.mcp_server_cwd or "."
            self._process = subprocess.Popen(
                settings.mcp_server_cmd.split(),
                shell=True if " " in settings.mcp_server_cmd else False,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._pid = self._process.pid
            self._start_time = time.time()

            # Wait a moment to verify it started
            time.sleep(2)

            if self.is_running:
                logger.info(f"✅ MCP Server started successfully (PID: {self._pid})")
                return {
                    "success": True,
                    "pid": self._pid,
                    "status": "running",
                    "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "message": "MCP Server 启动成功",
                }
            else:
                # Process died immediately
                stderr = self._process.stderr.read().decode() if self._process.stderr else "Unknown error"
                logger.error(f"❌ MCP Server failed to start: {stderr}")
                self._process = None
                self._pid = None
                self._start_time = None
                return {
                    "success": False,
                    "error": f"MCP Server failed to start: {stderr}",
                }
        except Exception as e:
            logger.error(f"❌ Failed to start MCP Server: {e}")
            return {"success": False, "error": str(e)}

    def stop(self, force: bool = False) -> dict:
        """Stop MCP Server process."""
        if not self.is_running and not force:
            return {
                "success": False,
                "error": "MCP Server is not running",
            }

        try:
            pid_to_stop = self._pid

            if self._process:
                if force:
                    self._process.kill()
                    logger.warning(f"⚠️ Force killed MCP Server (PID: {pid_to_stop})")
                else:
                    self._process.terminate()
                    logger.info(f"🛑 Stopping MCP Server (PID: {pid_to_stop})...")

                    # Wait up to 5 seconds for graceful shutdown
                    try:
                        self._process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning("⏰ Graceful shutdown timeout, forcing kill")
                        self._process.kill()

            stopped_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            uptime = self.uptime_seconds

            self._process = None
            self._pid = None
            self._start_time = None

            logger.info(f"✅ MCP Server stopped (was running for {uptime}s)")
            return {
                "success": True,
                "pid": pid_to_stop,
                "stopped_at": stopped_at,
                "uptime_seconds": uptime,
                "message": "MCP Server 已停止",
            }
        except Exception as e:
            logger.error(f"❌ Failed to stop MCP Server: {e}")
            return {"success": False, "error": str(e)}

    def restart(self) -> dict:
        """Restart MCP Server process."""
        stop_result = self.stop(force=False)
        if not stop_result["success"] and "not running" not in stop_result.get("error", ""):
            return stop_result

        # Brief pause before restart
        time.sleep(1)
        return self.start()

    def get_status(self) -> dict:
        """Get current process status."""
        if not self.is_running:
            return {
                "status": "stopped",
                "pid": None,
                "uptime_seconds": 0,
                "memory_usage_mb": 0.0,
                "cpu_usage_percent": 0.0,
            }

        # In production, you'd use psutil for real metrics
        return {
            "status": "running",
            "pid": self._pid,
            "uptime_seconds": self.uptime_seconds,
            "memory_usage_mb": 85.2,  # Mock value - use psutil in production
            "cpu_usage_percent": 12.5,  # Mock value - use psutil in production
        }


# Singleton instance
process_manager = ProcessManagerService()
