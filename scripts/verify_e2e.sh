#!/bin/bash
# 端到端验证
API_KEY=$(cat /tmp/api_key.txt)
echo "=== API Key ==="
echo "$API_KEY"

echo "=== Test 1: /health (no auth) ==="
curl -s -o /dev/null -w 'HTTP %{http_code}\n' -H "Host: loopmcp.renrenup.cn" http://127.0.0.1/health

echo "=== Test 2: /api/v1/agents without key (expect 401) ==="
curl -s -H "Host: loopmcp.renrenup.cn" http://127.0.0.1/api/v1/agents

echo "=== Test 3: /api/v1/agents with key (expect 200) ==="
curl -s -H "Host: loopmcp.renrenup.cn" -H "X-API-Key: $API_KEY" http://127.0.0.1/api/v1/agents | head -c 500

echo "=== Test 4: Frontend ==="
curl -s -o /dev/null -w 'HTTP %{http_code}\n' -H "Host: loopmcp.renrenup.cn" http://127.0.0.1/

echo "=== Test 5: MCP Bridge (mcp-proxy) ==="
curl -s -o /dev/null -w 'HTTP %{http_code}\n' -H "Host: loopmcp.renrenup.cn" http://127.0.0.1/mcp/

echo "=== Service Status ==="
systemctl status loopmcp-api --no-pager | head -5
systemctl status loopmcp-bridge --no-pager | head -5
echo "=== Ports ==="
ss -tln | grep -E ':8001|:8765|:80|:443'
echo "=== DONE ==="