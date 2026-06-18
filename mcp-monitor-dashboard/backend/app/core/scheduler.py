"""
Scheduler Service - periodic data collection and broadcasting
"""

import asyncio
import logging
from datetime import datetime

from app.services.data_collector import collector_service
from app.websocket.manager import manager
from app.config import settings

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None


async def _data_collection_loop():
    """Background task that collects data and broadcasts updates."""
    logger.info(f"⏰ Data collection loop started (interval: {settings.collection_interval_seconds}s)")

    while True:
        try:
            # Collect all data
            data = collector_service.collect_all()

            # Broadcast agent status updates
            if data.get("agents"):
                await manager.broadcast(
                    {
                        "type": "agent_status_update",
                        "data": data["agents"],
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    channel="agent_status",
                )

            # Broadcast project overview update
            if data.get("project_overview"):
                await manager.broadcast_to_channel(
                    "overview",
                    {
                        "type": "project_overview_update",
                        "data": data["project_overview"],
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        except Exception as e:
            logger.error(f"❌ Error in data collection loop: {e}")

        await asyncio.sleep(settings.collection_interval_seconds)


def start_scheduler():
    """Start the background scheduler."""
    global _scheduler_task

    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_data_collection_loop())
        logger.info("✅ Scheduler started")


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler_task

    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("🛑 Scheduler stopped")
