# MCP 实时监控看板系统 - 部署文档

## 1. 系统概述

MCP 实时监控看板系统是一个基于 FastAPI + React + WebSocket 的实时监控平台，用于可视化展示 MCP 系统中 16 个 Agent 的运行状态、操作日志和项目进度。

### 1.1 技术栈

- **后端**: Python 3.14 + FastAPI + SQLAlchemy + SQLite
- **前端**: React 18 + TypeScript + Ant Design + Tailwind CSS
- **实时通信**: WebSocket (心跳检测 + 自动重连)
- **部署**: Nginx + SSL (Let's Encrypt)

### 1.2 系统要求

- **操作系统**: Linux (Ubuntu 20.04+) / Windows Server 2019+
- **Python**: 3.10 或更高版本
- **Node.js**: 18.x 或更高版本
- **内存**: 最低 2GB，推荐 4GB
- **磁盘**: 最低 10GB 可用空间

---

## 2. 云服务器部署

### 2.1 服务器信息

- **IP**: 43.139.1.48
- **SSH**: `ssh root@43.139.1.48` (使用私钥认证)
- **私钥路径**: `C:\Users\Administrator\Documents\腾讯云服务器私钥code.pem`
- **域名**: `monitor.renrenup.cn` (需配置 DNS A 记录指向 43.139.1.48)

### 2.2 后端部署

#### 步骤 1: 上传代码到服务器

```bash
# 本地执行
cd g:\ai-gongju\Loop-agent
scp -i "C:\Users\Administrator\Documents\腾讯云服务器私钥code.pem" -r mcp-monitor-dashboard root@43.139.1.48:/opt/
```

#### 步骤 2: 安装 Python 依赖

```bash
# SSH 登录服务器
ssh root@43.139.1.48

# 进入项目目录
cd /opt/mcp-monitor-dashboard/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install fastapi uvicorn[standard] sqlalchemy pydantic-settings python-dotenv

# 创建数据目录
mkdir -p data
```

#### 步骤 3: 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
APP_NAME=MCP Monitor Dashboard
APP_ENV=production
APP_DEBUG=false
APP_PORT=8000

DATABASE_URL=sqlite:///./data/mcp_monitor.db

WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100

COLLECTION_INTERVAL_SECONDS=2.0

LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

MCP_SERVER_CWD=/opt/mcp-monitor-dashboard
MCP_SERVER_CMD=python -m loop_agent_mcp.server
EOF
```

#### 步骤 4: 测试后端启动

```bash
# 测试启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 验证健康检查
curl http://localhost:8000/health
# 应返回: {"status":"ok","version":"1.0.0"}

# 停止服务 (Ctrl+C)
```

#### 步骤 5: 使用 systemd 管理服务

```bash
# 创建 systemd 服务文件
cat > /etc/systemd/system/mcp-monitor.service << 'EOF'
[Unit]
Description=MCP Monitor Dashboard Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-monitor-dashboard/backend
Environment="PATH=/opt/mcp-monitor-dashboard/backend/venv/bin"
ExecStart=/opt/mcp-monitor-dashboard/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl start mcp-monitor
systemctl enable mcp-monitor

# 查看状态
systemctl status mcp-monitor

# 查看日志
journalctl -u mcp-monitor -f
```

### 2.3 前端部署

#### 步骤 1: 构建前端

```bash
# 本地执行
cd g:\ai-gongju\Loop-agent\mcp-monitor-dashboard\frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建产物在 dist/ 目录
```

#### 步骤 2: 上传前端文件

```bash
# 上传到服务器
scp -i "C:\Users\Administrator\Documents\腾讯云服务器私钥code.pem" -r dist/* root@43.139.1.48:/var/www/monitor/
```

### 2.4 Nginx 配置

#### 步骤 1: 安装 Nginx

```bash
# SSH 登录服务器
ssh root@43.139.1.48

# 安装 Nginx
apt update
apt install -y nginx
```

#### 步骤 2: 配置 Nginx

```bash
# 创建 Nginx 配置
cat > /etc/nginx/sites-available/monitor << 'EOF'
server {
    listen 80;
    server_name monitor.renrenup.cn;

    # 前端静态文件
    root /var/www/monitor;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # 健康检查
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/monitor /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

### 2.5 SSL 证书配置 (Let's Encrypt)

#### 步骤 1: 安装 Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

#### 步骤 2: 申请 SSL 证书

```bash
certbot --nginx -d monitor.renrenup.cn

# 按提示操作：
# - 输入邮箱地址
# - 同意服务条款
# - 选择是否重定向 HTTP 到 HTTPS (推荐选择 2 - Redirect)
```

#### 步骤 3: 自动续期

```bash
# 测试续期
certbot renew --dry-run

# Certbot 会自动设置 cron 任务，每天检查续期
```

---

## 3. 验证部署

### 3.1 检查服务状态

```bash
# 检查后端服务
systemctl status mcp-monitor

# 检查 Nginx
systemctl status nginx

# 检查端口监听
netstat -tlnp | grep -E '80|443|8000'
```

### 3.2 访问测试

- **HTTP**: http://monitor.renrenup.cn (应自动跳转到 HTTPS)
- **HTTPS**: https://monitor.renrenup.cn
- **健康检查**: https://monitor.renrenup.cn/health

### 3.3 功能验证

1. **Agent 状态矩阵**: 应显示 16 个 Agent 的状态卡片
2. **实时日志流**: 应能看到日志实时更新
3. **项目概览**: 应显示项目进度和关键指标
4. **WebSocket 连接**: 打开浏览器开发者工具，查看 Network > WS，应看到 WebSocket 连接成功

---

## 4. 运维手册

### 4.1 日志管理

```bash
# 后端日志
journalctl -u mcp-monitor -f

# Nginx 访问日志
tail -f /var/log/nginx/access.log

# Nginx 错误日志
tail -f /var/log/nginx/error.log

# 应用日志 (如果配置了文件日志)
tail -f /opt/mcp-monitor-dashboard/backend/logs/app.log
```

### 4.2 服务管理

```bash
# 重启后端服务
systemctl restart mcp-monitor

# 停止后端服务
systemctl stop mcp-monitor

# 重启 Nginx
systemctl restart nginx

# 重新加载 Nginx 配置
systemctl reload nginx
```

### 4.3 数据库备份

```bash
# 备份数据库
cp /opt/mcp-monitor-dashboard/backend/data/mcp_monitor.db /opt/mcp-monitor-dashboard/backend/data/mcp_monitor.db.backup.$(date +%Y%m%d)

# 恢复数据库
cp /opt/mcp-monitor-dashboard/backend/data/mcp_monitor.db.backup.YYYYMMDD /opt/mcp-monitor-dashboard/backend/data/mcp_monitor.db
systemctl restart mcp-monitor
```

### 4.4 性能监控

```bash
# 查看系统资源
top

# 查看内存使用
free -h

# 查看磁盘使用
df -h

# 查看网络连接数
netstat -an | grep ESTABLISHED | wc -l
```

### 4.5 故障排查

#### 问题 1: 后端服务无法启动

```bash
# 查看详细错误
journalctl -u mcp-monitor -n 50

# 检查端口占用
lsof -i :8000

# 检查 Python 环境
/opt/mcp-monitor-dashboard/backend/venv/bin/python --version
```

#### 问题 2: WebSocket 连接失败

```bash
# 检查 Nginx WebSocket 配置
grep -A 10 "location /ws" /etc/nginx/sites-enabled/monitor

# 检查后端 WebSocket 端点
curl -v http://localhost:8000/ws

# 查看后端日志
journalctl -u mcp-monitor | grep -i websocket
```

#### 问题 3: SSL 证书问题

```bash
# 检查证书状态
certbot certificates

# 手动续期
certbot renew

# 查看 Certbot 日志
tail -f /var/log/letsencrypt/letsencrypt.log
```

---

## 5. 安全加固

### 5.1 防火墙配置

```bash
# 启用 UFW
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable

# 查看状态
ufw status
```

### 5.2 禁用 root 登录

```bash
# 创建普通用户
adduser deploy
usermod -aG sudo deploy

# 配置 SSH 密钥登录
su - deploy
mkdir .ssh
chmod 700 .ssh
# 复制公钥到 .ssh/authorized_keys

# 修改 SSH 配置
sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# 重启 SSH
systemctl restart sshd
```

### 5.3 定期更新

```bash
# 更新系统包
apt update && apt upgrade -y

# 更新 Python 依赖
cd /opt/mcp-monitor-dashboard/backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## 6. 联系与支持

- **技术支持**: support@renrenup.cn
- **文档版本**: v1.0
- **最后更新**: 2026-06-19
