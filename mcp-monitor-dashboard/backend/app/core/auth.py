"""
API Authentication Middleware - API Key based authentication
"""

import os
import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

logger = logging.getLogger(__name__)

# API Key configuration
API_KEY = os.getenv("API_KEY", "dev-api-key-change-in-production")

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/health",
    "/health/ready",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def validate_api_key(api_key: str) -> bool:
    """Validate API key against configured value."""
    if not api_key:
        return False
    return api_key == API_KEY


def extract_api_key_from_request(request: Request) -> str | None:
    """Extract API key from request headers."""
    # Try Authorization: Bearer <key>
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix
    
    # Try X-API-Key header
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        return api_key_header
    
    return None


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract API key from request
        api_key = extract_api_key_from_request(request)
        
        # Validate API key
        if not api_key or not validate_api_key(api_key):
            logger.warning(f"Unauthorized access attempt to {request.url.path} from {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing or invalid API key",
                    "hint": "Provide API key via 'Authorization: Bearer <key>' or 'X-API-Key: <key>' header"
                }
            )
        
        return await call_next(request)


def validate_ws_api_key(websocket) -> bool:
    """Validate API key for WebSocket connections."""
    # Try query parameter
    api_key = websocket.query_params.get("api_key")
    if api_key and validate_api_key(api_key):
        return True
    
    # Try headers (note: browsers don't allow custom headers in WebSocket,
    # but non-browser clients can use this)
    auth_header = websocket.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        api_key = auth_header[7:]
        if validate_api_key(api_key):
            return True
    
    api_key_header = websocket.headers.get("X-API-Key")
    if api_key_header and validate_api_key(api_key_header):
        return True
    
    return False
