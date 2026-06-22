#!/bin/bash
# 修复 FastAPI/Starlette 版本兼容
set -e

echo "=== 卸载冲突的 starlette ==="
/www/wwwroot/loopmcp-monitor/venv/bin/pip uninstall -y starlette 2>&1 | tail -3

echo "=== 安装兼容版本 starlette==0.37.2 ==="
/www/wwwroot/loopmcp-monitor/venv/bin/pip install "starlette==0.37.2" 2>&1 | tail -5

echo "=== 重启 API 服务 ==="
systemctl restart loopmcp-api
sleep 3
systemctl is-active loopmcp-api
echo "=== 端口检查 ==="
ss -tln | grep 8001

echo "=== 测试 health ==="
curl -s http://127.0.0.1:8001/health
echo ""
echo "=== 测试 API 鉴权 (应 401) ==="
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8001/api/v1/agents

echo "=== DONE ==="