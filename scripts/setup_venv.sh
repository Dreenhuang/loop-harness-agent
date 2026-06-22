#!/bin/bash
# D4: Python 虚拟环境与依赖安装
set -e
cd /www/wwwroot/loopmcp-monitor

echo "=== 创建虚拟环境 ==="
python3.11 -m venv venv
source venv/bin/activate

echo "=== 升级 pip ==="
pip install --upgrade pip wheel setuptools 2>&1 | tail -3

echo "=== 安装后端依赖 ==="
pip install -r backend/requirements.txt 2>&1 | tail -5

echo "=== 安装 loop-agent-mcp（可编辑模式）==="
pip install -e loop-agent-mcp/ 2>&1 | tail -5

echo "=== 安装 mcp-proxy (Streamable-HTTP 桥接) ==="
pip install mcp-proxy 2>&1 | tail -3

echo "=== 验证安装 ==="
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import uvicorn; print(f'Uvicorn {uvicorn.__version__}')"
python -c "from loop_agent_mcp import server; print('loop-agent-mcp OK')"
python -c "import mcp_proxy; print('mcp-proxy OK')"

echo "=== DONE ==="