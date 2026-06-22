#!/bin/bash
# 诊断脚本
echo "=== fastapi/starlette versions ==="
/www/wwwroot/loopmcp-monitor/venv/bin/python -c 'import fastapi; print("fastapi:", fastapi.__version__); import starlette; print("starlette:", starlette.__version__)'

echo "=== try APIRouter() ==="
/www/wwwroot/loopmcp-monitor/venv/bin/python -c 'from fastapi import APIRouter; r = APIRouter(); print("OK")'

echo "=== try import app.main ==="
cd /www/wwwroot/loopmcp-monitor/backend && /www/wwwroot/loopmcp-monitor/venv/bin/python -c 'import app.main' 2>&1 | tail -20

echo "=== check websocket_router usage ==="
grep -n "websocket_router" /www/wwwroot/loopmcp-monitor/backend/app/main.py
grep -n "websocket_router" /www/wwwroot/loopmcp-monitor/backend/app/websocket/__init__.py