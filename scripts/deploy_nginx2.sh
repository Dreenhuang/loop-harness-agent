#!/bin/bash
# D8: Nginx 站点配置
set -e

mkdir -p /var/www/certbot

cat > /usr/local/nginx/conf/vhost/loopmcp.renrenup.cn.conf << 'EOF'
server {
    listen 80;
    server_name loopmcp.renrenup.cn;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    root /www/wwwroot/loopmcp-monitor/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8001/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
    }

    location /mcp/ {
        proxy_pass http://127.0.0.1:8765/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location = /health {
        proxy_pass http://127.0.0.1:8001/health;
    }

    access_log /var/log/nginx/loopmcp_access.log;
    error_log  /var/log/nginx/loopmcp_error.log;
}
EOF

echo "=== nginx -t ==="
nginx -t 2>&1

echo "=== reload nginx ==="
systemctl reload nginx

sleep 2
echo "=== test by IP ==="
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://43.139.1.48/health
echo "=== DONE ==="