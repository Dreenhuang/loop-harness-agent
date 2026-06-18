"""
WebSocket Router
"""

from fastapi import APIRouter, WebSocket
from .manager import websocket_endpoint

websocket_router = APIRouter()

websocket_router.websocket("/ws")(websocket_endpoint)
