"""
WebSocket Connection Manager - handles real-time connections
"""

import json
import asyncio
import logging
from typing import Dict, Set, List, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # active_connections: Dict[websocket_id, {"ws": WebSocket, "channels": Set[str]}]
        self.active_connections: Dict[int, dict] = {}
        self._connection_id_counter = 0

    async def connect(self, websocket: WebSocket) -> int:
        """Accept a new WebSocket connection and return its ID."""
        await websocket.accept()
        conn_id = self._connection_id_counter
        self._connection_id_counter += 1
        self.active_connections[conn_id] = {
            "websocket": websocket,
            "channels": set(),
            "connected_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"🔌 WS Client connected (ID: {conn_id}, Total: {len(self.active_connections)})")
        return conn_id

    async def disconnect(self, conn_id: int):
        """Remove a WebSocket connection."""
        if conn_id in self.active_connections:
            del self.active_connections[conn_id]
            logger.info(f"🔌 WS Client disconnected (ID: {conn_id}, Remaining: {len(self.active_connections)})")

    def subscribe(self, conn_id: int, channels: List[str]):
        """Subscribe connection to channels."""
        if conn_id in self.active_connections:
            for channel in channels:
                self.active_connections[conn_id]["channels"].add(channel)
            logger.debug(f"📡 Client {conn_id} subscribed to: {channels}")

    def unsubscribe(self, conn_id: int, channels: List[str]):
        """Unsubscribe connection from channels."""
        if conn_id in self.active_connections:
            for channel in channels:
                self.active_connections[conn_id]["channels"].discard(channel)

    async def send_personal_message(self, message: dict, conn_id: int):
        """Send a message to a specific client."""
        if conn_id in self.active_connections:
            try:
                await self.active_connections[conn_id]["websocket"].send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send to client {conn_id}: {e}")

    async def broadcast(self, message: dict, channel: Optional[str] = None):
        """Broadcast a message to all or specific channel subscribers."""
        disconnected = []
        for conn_id, conn_info in self.active_connections.items():
            # If channel specified, only send to subscribers of that channel
            if channel and channel not in conn_info["channels"]:
                continue

            try:
                await conn_info["websocket"].send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ Broadcast failed to client {conn_id}: {e}")
                disconnected.append(conn_id)

        # Clean up disconnected clients
        for conn_id in disconnected:
            await self.disconnect(conn_id)

    async def broadcast_to_channel(self, channel: str, message: dict):
        """Alias for broadcast with explicit channel."""
        await self.broadcast(message, channel=channel)

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

    def get_connection_stats(self) -> dict:
        """Get statistics about current connections."""
        return {
            "total_connections": len(self.active_connections),
            "channel_subscribers": {
                "agent_status": sum(
                    1 for c in self.active_connections.values()
                    if "agent_status" in c["channels"]
                ),
                "logs": sum(
                    1 for c in self.active_connections.values()
                    if "logs" in c["channels"]
                ),
                "overview": sum(
                    1 for c in self.active_connections.values()
                    if "overview" in c["channels"]
                ),
            },
        }


# Singleton instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint handler.
    Handles connection lifecycle and message routing.
    """
    from app.services.data_collector import collector_service

    conn_id = await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            # Handle different message types
            if msg_type == "subscribe":
                channels = message.get("channels", ["agent_status", "logs", "overview"])
                manager.subscribe(conn_id, channels)

                # Send initial full data on subscribe
                cached = collector_service.get_cached_data()
                init_message = {
                    "type": "init",
                    "data": {
                        "agents": cached.get("agents", []),
                        "overview": cached.get("project_overview", {}),
                        "recentLogs": [],
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await manager.send_personal_message(init_message, conn_id)

            elif msg_type == "unsubscribe":
                channels = message.get("channels", [])
                manager.unsubscribe(conn_id, channels)

            elif msg_type == "ping":
                await manager.send_personal_message({"type": "pong"}, conn_id)

            elif msg_type == "request_full_sync":
                # Request full data sync (after reconnection)
                cached = collector_service.collect_all()
                sync_message = {
                    "type": "init",
                    "data": {
                        "agents": cached.get("agents", []),
                        "overview": cached.get("project_overview", {}),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await manager.send_personal_message(sync_message, conn_id)

            else:
                # Unknown message type - send error
                await manager.send_personal_message(
                    {"type": "error", "data": {"message": f"Unknown message type: {msg_type}"}},
                    conn_id,
                )

    except WebSocketDisconnect:
        logger.debug(f"WS Client {conn_id} disconnected normally")
    except Exception as e:
        logger.error(f"WS Error for client {conn_id}: {e}")
    finally:
        await manager.disconnect(conn_id)
