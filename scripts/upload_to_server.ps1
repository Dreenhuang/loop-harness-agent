# 上传代码到腾讯云服务器
$KEY = "C:/Users/Administrator/Documents/腾讯云服务器私钥code.pem"
$R = "root@43.139.1.48"

Write-Host "[1/4] 上传 backend/app..."
scp -i $KEY -r "g:/ai-gongju/Loop-agent/mcp-monitor-dashboard/backend/app" "${R}:/www/wwwroot/loopmcp-monitor/backend/" 2>&1 | Select-Object -Last 3
scp -i $KEY "g:/ai-gongju/Loop-agent/mcp-monitor-dashboard/backend/requirements.txt" "${R}:/www/wwwroot/loopmcp-monitor/backend/" 2>&1

Write-Host "[2/4] 上传 loop-agent-mcp..."
scp -i $KEY -r "g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp" "${R}:/www/wwwroot/loopmcp-monitor/loop-agent-mcp/" 2>&1 | Select-Object -Last 3
scp -i $KEY "g:/ai-gongju/Loop-agent/loop-agent-mcp/pyproject.toml" "${R}:/www/wwwroot/loopmcp-monitor/loop-agent-mcp/" 2>&1
scp -i $KEY "g:/ai-gongju/Loop-agent/loop-agent-mcp/README.md" "${R}:/www/wwwroot/loopmcp-monitor/loop-agent-mcp/" 2>&1

Write-Host "[3/4] 上传 frontend dist..."
scp -i $KEY "g:/ai-gongju/Loop-agent/mcp-monitor-dashboard/frontend/dist/index.html" "${R}:/www/wwwroot/loopmcp-monitor/frontend/" 2>&1
scp -i $KEY -r "g:/ai-gongju/Loop-agent/mcp-monitor-dashboard/frontend/dist/assets" "${R}:/www/wwwroot/loopmcp-monitor/frontend/" 2>&1 | Select-Object -Last 3

Write-Host "[4/4] 验证..."
ssh -i $KEY ${R} "echo 'backend:'; ls /www/wwwroot/loopmcp-monitor/backend/; echo 'mcp:'; ls /www/wwwroot/loopmcp-monitor/loop-agent-mcp/; echo 'frontend:'; ls /www/wwwroot/loopmcp-monitor/frontend/; echo 'DONE'"

Write-Host "=== ALL UPLOADED ==="