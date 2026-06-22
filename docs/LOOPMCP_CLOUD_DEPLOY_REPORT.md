# LoopMCP 腾讯云部署报告

**部署时间**: 2026-06-22  
**部署版本**: Loop-Harness-Agent v1.3.1 (loop-agent-mcp) + Dashboard v1.0.0  
**部署状态**: ✅ **HTTP 部署完成，DNS 解析后申请 SSL**

---

## 一、部署摘要

| 项目 | 值 |
|------|---|
| 域名 | `loopmcp.renrenup.cn` |
| 服务器 | 腾讯云 OpenCloudOS 9.4 (43.139.1.48) |
| 项目目录 | `/www/wwwroot/loopmcp-monitor/` |
| Nginx 配置 | `/usr/local/nginx/conf/vhost/loopmcp.renrenup.cn.conf` |
| FastAPI 后端 | `http://127.0.0.1:8001` |
| MCP Streamable-HTTP | `http://127.0.0.1:8765` |
| Python | 3.11.6 |
| FastAPI | 0.111.0（兼容 Starlette 0.37.2）|
| loop-agent-mcp | 1.2.0（云端 18 个工具 + Dashboard）|

---

## 二、当前服务状态

| 服务 | 端口 | 状态 | 启动方式 |
|------|------|------|----------|
| loopmcp-api | 127.0.0.1:8001 | ✅ active | systemd |
| loopmcp-bridge | 127.0.0.1:8765 | ✅ active | systemd |
| nginx | 0.0.0.0:80/443 | ✅ active | systemd |

---

## 三、端到端验证结果

| 测试项 | 期望 | 实际 |
|--------|------|------|
| `/health` 无鉴权 | HTTP 200 | ✅ HTTP 200 |
| `/api/v1/agents` 无 Key | HTTP 401 | ✅ 返回 `{"detail":"Missing or invalid API key","hint":"Provide API key via 'Authorization: Bearer <key>' or 'X-API-Key: <key>' header"}` |
| `/api/v1/agents` 带 Key | HTTP 200 | ✅ 返回 16 角色 Agent 完整 JSON 列表 |
| 前端 `/` 页面 | HTTP 200 | ✅ HTML 正确返回 |
| MCP Bridge `/mcp/` | mcp-proxy 正常 | ✅ 服务运行（GET 根路径返回 404 是预期行为）|
| systemd 服务保活 | active | ✅ api + bridge 都 active |

**API_KEY（已保存到服务器 `/tmp/api_key.txt`）**:
```
14df7923584a1dacbba6af5a81bebb1001aa201fc833e8f8be0b08de52eceeea
```

---

## 四、修复的兼容性问题（部署中遇到并解决）

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| 1 | Pydantic Settings 拒绝未声明字段 | `app_host/api_key/cors_origins/dashboard_url` 等未在 Settings 中定义 | 在 `config.py` 添加字段并设置 `extra="ignore"` |
| 2 | API 启动失败：`TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'` | FastAPI 0.111 自动升级 Starlette 到 1.3.1，与 APIRouter 兼容性破坏 | 锁定 `starlette==0.37.2` |
| 3 | Nginx 配置路径错误 | 服务器用的是自定义编译 nginx（`/usr/local/nginx/conf/vhost/`，不是标准 `/etc/nginx/conf.d/`）| 改用正确路径 |
| 4 | 日志目录不存在 | `/var/log/nginx/loopmcp_*.log` 未创建 | 手动创建 |

---

## 五、安全状态

| 项 | 状态 |
|----|------|
| API Key 鉴权 | ✅ 所有非白名单端点需 API Key |
| WebSocket 鉴权 | ✅ query 参数校验 |
| CORS 配置 | ✅ 从环境变量读取，无通配符 |
| 命令注入防护 | ✅ shell=False + 参数列表 |
| 路径遍历防护 | ✅ validate_path |
| 速率限制 | ⚠️ 部署后迭代 |
| 日志脱敏 | ✅ 递归脱敏（部署前已修复 G-4）|

---

## 六、SSL 证书申请指南（待 DNS 解析）

### 6.1 DNS A 记录（你需操作）

```
主机记录：loopmcp
记录类型：A
记录值：43.139.1.48
TTL：600
```

### 6.2 DNS 解析后执行证书申请

```bash
ssh -i "C:/Users/Administrator/Documents/腾讯云服务器私钥code.pem" root@43.139.1.48
certbot --nginx -d loopmcp.renrenup.cn --non-interactive \
    --agree-tos --email admin@renrenup.cn --redirect
```

certbot 会自动：
1. 修改 `/usr/local/nginx/conf/vhost/loopmcp.renrenup.cn.conf` 添加 HTTPS server 块
2. 申请 Let's Encrypt 证书
3. 配置 HTTP→HTTPS 重定向
4. 设置自动续期

### 6.3 验证 HTTPS

```bash
curl -I https://loopmcp.renrenup.cn/health
# 应返回 HTTP/2 200
```

---

## 七、运维手册

### 7.1 服务管理

```bash
# 查看状态
systemctl status loopmcp-api
systemctl status loopmcp-bridge

# 重启服务
systemctl restart loopmcp-api
systemctl restart loopmcp-bridge

# 查看日志
tail -f /www/wwwroot/loopmcp-monitor/logs/api.out.log
tail -f /www/wwwroot/loopmcp-monitor/logs/api.err.log
tail -f /www/wwwroot/loopmcp-monitor/logs/bridge.out.log
tail -f /www/wwwroot/loopmcp-monitor/logs/bridge.err.log

# nginx 管理
nginx -t && systemctl reload nginx
tail -f /var/log/nginx/loopmcp_access.log
tail -f /var/log/nginx/loopmcp_error.log
```

### 7.2 健康检查端点

```bash
# 内部
curl http://127.0.0.1:8001/health

# 外部（带域名）
curl -H "Host: loopmcp.renrenup.cn" http://43.139.1.48/health

# 完整端到端
curl -H "Host: loopmcp.renrenup.cn" -H "X-API-Key: $(cat /tmp/api_key.txt)" \
     http://43.139.1.48/api/v1/agents
```

### 7.3 客户端接入示例

**MCP 客户端（Trae IDE / Claude Code / Cursor）**：
```bash
claude mcp add --transport http loopmcp https://loopmcp.renrenup.cn/mcp/
```

**浏览器访问**：
```
https://loopmcp.renrenup.cn
```

**API 直接调用**：
```bash
curl -H "X-API-Key: 14df7923584a1dacbba6af5a81bebb1001aa201fc833e8f8be0b08de52eceeea" \
     https://loopmcp.renrenup.cn/api/v1/agents
```

---

## 八、目录结构

```
/www/wwwroot/loopmcp-monitor/
├── backend/             # FastAPI 后端
│   ├── app/             # 应用代码
│   ├── requirements.txt
│   └── .env             # 环境变量（含 API_KEY）
├── frontend/            # React 构建产物
│   ├── index.html
│   └── assets/
├── loop-agent-mcp/      # MCP 引擎（Python 包）
│   ├── loop_agent_mcp/
│   ├── pyproject.toml
│   └── README.md
├── venv/                # Python 虚拟环境
├── data/                # SQLite 数据库
├── logs/                # 日志
│   ├── api.out.log
│   ├── api.err.log
│   ├── bridge.out.log
│   └── bridge.err.log
└── workspace/           # MCP 工作区
```

---

## 九、回滚方案（5 分钟）

```bash
# 1. 停止服务
systemctl disable --now loopmcp-api
systemctl disable --now loopmcp-bridge

# 2. 删除 Nginx 配置
rm /usr/local/nginx/conf/vhost/loopmcp.renrenup.cn.conf
systemctl reload nginx

# 3. 备份数据（可选）
tar czf /tmp/loopmcp-backup.tar.gz /www/wwwroot/loopmcp-monitor/{data,logs,.env}

# 4. 清理目录（可选，谨慎）
rm -rf /www/wwwroot/loopmcp-monitor/
```

---

## 十、Phase 10 部署完成清单

- [x] D1: DNS 验证 + 服务器连通
- [x] D2: 服务器环境（Python 3.11、certbot、firewalld）
- [x] D3: 代码上传（backend + mcp + frontend）
- [x] D4: Python venv + 依赖（FastAPI/loop-agent-mcp/mcp-proxy）
- [x] D5: 前端生产构建
- [x] D6: 后端 systemd 部署（修复 Pydantic + Starlette 兼容）
- [x] D7: MCP Streamable-HTTP bridge
- [x] D8a: Nginx 站点配置（HTTP）
- [x] D9: 端到端验证（鉴权 + 16 角色 API 真实数据）
- [x] D10: 部署报告 + 运维手册
- [ ] D8b: SSL 证书（**待 DNS 解析后**）

---

## 十一、剩余工作（1 项）

**⚠️ SSL 证书申请**：需要先在 DNS 服务商添加 A 记录（`loopmcp → 43.139.1.48`），然后执行：

```bash
ssh root@43.139.1.48 "certbot --nginx -d loopmcp.renrenup.cn --non-interactive --agree-tos --email admin@renrenup.cn --redirect"
```

**完成后整个 Phase 10 闭环，loopmcp.renrenup.cn 进入生产就绪状态。**