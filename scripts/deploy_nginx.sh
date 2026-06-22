#!/bin/bash
# D8: Nginx 站点配置（HTTP 版本，DNS 解析后申请 SSL）
set -e

# 创建 HTTP 站点（先用 HTTP，等 DNS 解析后用 certbot 自动添加 SSL）
cat > /usr/local/nginx/conf/vhost/loopmcp.renrenup.cn.conf << 'EOF'
server {
    listen 80;
    server_name loopmcp.renrenup.cn;

    # certbot ACME challenge（保留给证书申请）
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # 前端静态文件
    root /www/wwwroot/loopmcp-monitor/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # FastAPI 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8001/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
    }

    # MCP Streamable-HTTP 桥
    location /mcp/ {
        proxy_pass http://127.0.0.1:8765/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    # 健康检查（无需鉴权）
    location = /health {
        proxy_pass http://127.0.0.1:8001/health;
    }

    access_log /var/log/nginx/loopmcp_access.log;
    error_log  /var/log/nginx/loopmcp_error.log;
}
EOF

echo "=== nginx config ==="
nginx -t 2>&1 | tail -5

echo "=== reload nginx ==="
systemctl reload nginx

echo "=== test http (expect 401 if DNS not yet resolved, otherwise 200) ==="
sleep 2
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://loopmcp.renrenup.cn/health 2>&1 || true
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://43.139.1.48/health 2>&1 || true

echo "=== DONE ==="