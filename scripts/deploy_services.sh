#!/bin/bash
# D6+D7: systemd 服务 + 环境变量 + 数据库初始化
set -e
cd /www/wwwroot/loopmcp-monitor

# 生成强 API Key
API_KEY=$(openssl rand -hex 32)
echo "Generated API_KEY=$API_KEY"

# 创建后端 .env
cat > backend/.env << EOF
APP_NAME=MCP Monitor Dashboard
APP_ENV=production
APP_DEBUG=false
APP_HOST=127.0.0.1
APP_PORT=8001

DATABASE_URL=sqlite:///./data/mcp_monitor.db

WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=200
COLLECTION_INTERVAL_SECONDS=2.0

LOG_LEVEL=INFO
LOG_FILE=/www/wwwroot/loopmcp-monitor/logs/backend.log

# Security
API_KEY=$API_KEY
CORS_ORIGINS=https://loopmcp.renrenup.cn
ALLOWED_HOSTS=loopmcp.renrenup.cn,127.0.0.1

# MCP Engine
MCP_WORKSPACE=/www/wwwroot/loopmcp-monitor/workspace
MCP_SERVER_CMD=python -m loop_agent_mcp.server
MCP_BRIDGE_URL=http://127.0.0.1:8765
DASHBOARD_URL=https://loopmcp.renrenup.cn
EOF

echo "=== .env created ==="

# 创建 systemd 服务 - API
cat > /etc/systemd/system/loopmcp-api.service << EOF
[Unit]
Description=LoopMCP Monitor Dashboard API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/www/wwwroot/loopmcp-monitor/backend
Environment="PATH=/www/wwwroot/loopmcp-monitor/venv/bin"
EnvironmentFile=/www/wwwroot/loopmcp-monitor/backend/.env
ExecStart=/www/wwwroot/loopmcp-monitor/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 2 --no-access-log
Restart=always
RestartSec=10
StandardOutput=append:/www/wwwroot/loopmcp-monitor/logs/api.out.log
StandardError=append:/www/wwwroot/loopmcp-monitor/logs/api.err.log

[Install]
WantedBy=multi-user.target
EOF

# 创建 systemd 服务 - MCP Bridge
cat > /etc/systemd/system/loopmcp-bridge.service << EOF
[Unit]
Description=LoopMCP Streamable-HTTP Bridge (mcp-proxy)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/www/wwwroot/loopmcp-monitor/loop-agent-mcp
Environment="PATH=/www/wwwroot/loopmcp-monitor/venv/bin"
ExecStart=/www/wwwroot/loopmcp-monitor/venv/bin/mcp-proxy --host 127.0.0.1 --port 8765 --transport streamablehttp -- python -m loop_agent_mcp.server
Restart=always
RestartSec=10
StandardOutput=append:/www/wwwroot/loopmcp-monitor/logs/bridge.out.log
StandardError=append:/www/wwwroot/loopmcp-monitor/logs/bridge.err.log

[Install]
WantedBy=multi-user.target
EOF

echo "=== systemd services created ==="

# 启动服务
systemctl daemon-reload
systemctl enable loopmcp-api.service
systemctl enable loopmcp-bridge.service
systemctl start loopmcp-api.service
systemctl start loopmcp-bridge.service

sleep 3

echo "=== service status ==="
systemctl status loopmcp-api.service --no-pager | head -10
echo "---"
systemctl status loopmcp-bridge.service --no-pager | head -10

echo "=== port check ==="
ss -tln | grep -E ':8001|:8765' || echo "no listening yet"

echo "=== API_KEY saved to /tmp/api_key.txt ==="
echo "$API_KEY" > /tmp/api_key.txt
chmod 600 /tmp/api_key.txt
cat /tmp/api_key.txt

echo "=== DONE ==="