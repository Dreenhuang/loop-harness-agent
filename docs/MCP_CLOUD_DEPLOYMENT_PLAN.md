# Loop-Harness-Agent MCP 功能迁移到腾讯云 - 项目实施计划

**文档版本**: v1.0  
**创建日期**: 2026-06-22  
**负责人**: @Product-Manager  
**状态**: 待审批

---

## 一、项目概述

### 1.1 项目目标

将 Loop-Harness-Agent MCP 功能从本地开发环境全量迁移到腾讯云服务器，实现生产级部署，支持团队远程访问和持续集成。

### 1.2 项目范围

**包含**:
- 后端 FastAPI 服务部署（端口 8001）
- MCP Streamable-HTTP 桥接层部署（端口 8765）
- 前端静态资源构建与部署
- Nginx 反向代理配置
- SSL 证书申请与配置
- 端到端功能验证
- 运维文档归档

**不包含**:
- 现有项目（aichat, clipsync, nao, taolun, vibepm）的任何修改
- 数据库迁移（使用现有 SQLite）
- 新功能开发

### 1.3 项目约束

- **服务器环境**: OpenCloudOS 9.4（RHEL 系，dnf 包管理器）
- **域名**: loopmcp.renrenup.cn（需用户添加 A 记录）
- **可用端口**: 8001（后端）、8765（MCP 桥接）
- **不能影响**: 服务器上已有项目的正常运行
- **安全要求**: P0 安全问题全部修复，P1 问题 ≤ 2 个

---

## 二、任务拆分（WBS）

### 任务清单

| 任务编号 | 任务名称 | 负责人 | 前置依赖 | 预计工时 | 输入 | 输出 | 验收标准 |
|---------|---------|--------|---------|---------|------|------|----------|
| **T1** | 一般安全问题修复（G1-G9） | @Bug-Defect-Repairer | 无 | 2h | 安全审查报告 | 修复后的代码 | 所有 G1-G9 问题已修复，无新增 P0 问题 |
| **T2** | 代码上传到服务器 | @DevOps | T1 | 0.5h | 本地代码库 | 服务器代码目录 | 代码完整上传，目录结构正确 |
| **T3** | Python 虚拟环境与依赖安装 | @DevOps | T2 | 1h | requirements.txt | 虚拟环境 + 依赖 | 所有依赖安装成功，无版本冲突 |
| **T4** | 后端服务部署（systemd + Uvicorn） | @DevOps | T3 | 1.5h | 后端代码 | systemd 服务文件 | 服务启动成功，端口 8001 监听正常 |
| **T5** | MCP Streamable-HTTP 桥接层部署 | @DevOps | T3 | 1h | MCP 桥接代码 | systemd 服务文件 | 服务启动成功，端口 8765 监听正常 |
| **T6** | 前端构建与部署 | @DevOps | T1 | 1h | 前端源码 | dist 目录 | 构建成功，无 TypeScript 错误 |
| **T7** | Nginx 站点配置 | @DevOps | T4, T5, T6 | 1h | 域名证书 | nginx.conf | 配置语法正确，服务重载成功 |
| **T8** | SSL 证书申请与配置 | @DevOps | T7 | 1h | 域名解析 | SSL 证书 | HTTPS 访问正常，证书有效 |
| **T9** | 端到端功能验证 | @全栈测试员 | T8 | 2h | 测试用例集 | 测试报告 | 145 用例通过率 ≥ 95% |
| **T10** | 性能压测 | @Professional-Performance | T9 | 1.5h | 性能基准 | 压测报告 | API 响应 < 200ms，WebSocket 延迟 < 100ms |
| **T11** | 文档归档 | @Documenter | T9, T10 | 1h | 部署记录 | 运维手册 | 文档完整，包含所有运维命令 |

**任务总数**: 11 个  
**总预计工时**: 13.5 小时

---

## 三、执行步骤与时间节点

### 甘特图（表格形式）

| 阶段 | Day 1 (上午) | Day 1 (下午) | Day 2 (上午) | Day 2 (下午) |
|------|-------------|-------------|-------------|-------------|
| **安全修复** | T1 (2h) | - | - | - |
| **代码上传** | - | T2 (0.5h) | - | - |
| **环境配置** | - | T3 (1h) | - | - |
| **后端部署** | - | - | T4 (1.5h) | - |
| **MCP 桥接部署** | - | - | T5 (1h) | - |
| **前端构建** | - | T6 (1h) | - | - |
| **Nginx 配置** | - | - | - | T7 (1h) |
| **SSL 配置** | - | - | - | T8 (1h) |
| **功能验证** | - | - | - | T9 (2h) |
| **性能压测** | - | - | - | T10 (1.5h) |
| **文档归档** | - | - | - | T11 (1h) |

### 关键路径

```
T1 (安全修复) → T2 (代码上传) → T3 (环境配置) → T4 (后端部署) → T7 (Nginx 配置) → T8 (SSL 配置) → T9 (功能验证) → T11 (文档归档)
```

**最长依赖链**: 8 个任务  
**总工期**: 2 天（假设并行执行 T5、T6）

---

## 四、最终验收标准

### 4.1 功能完整性

- [ ] 145 个测试用例通过率 ≥ 95%
- [ ] 所有核心功能可用：
  - [ ] Agent 状态监控
  - [ ] 日志实时推送
  - [ ] 项目状态查看
  - [ ] 系统状态监控
  - [ ] WebSocket 实时通信
  - [ ] MCP Streamable-HTTP 桥接

### 4.2 性能指标

- [ ] API 平均响应时间 < 200ms
- [ ] API P95 响应时间 < 500ms
- [ ] WebSocket 连接延迟 < 100ms
- [ ] 页面首次加载时间 < 3s
- [ ] 并发用户支持 ≥ 10 人

### 4.3 安全合规

- [ ] P0 安全问题全部修复（3/3）
- [ ] P1 安全问题 ≤ 2 个
- [ ] 一般安全问题修复率 ≥ 80%（7/9）
- [ ] API 鉴权机制正常工作
- [ ] CORS 策略正确配置
- [ ] 命令注入防护有效

### 4.4 用户体验

- [ ] 页面加载无控制台错误
- [ ] WebSocket 连接稳定，无频繁断线
- [ ] 响应式布局正常（桌面/平板/手机）
- [ ] 主题切换正常（亮色/暗色）

### 4.5 可用性

- [ ] 服务可用性 ≥ 99.5%（月度）
- [ ] 服务自动重启（systemd 配置）
- [ ] 日志轮转配置（防止磁盘占满）
- [ ] 监控告警配置（可选）

---

## 五、风险与缓解

### 风险矩阵

| 风险项 | 概率 | 影响 | 风险等级 | 缓解措施 |
|-------|------|------|---------|---------|
| **R1**: 域名 DNS 解析延迟 | 中 | 高 | 高 | 提前 24 小时添加 A 记录，使用多个 DNS 服务器验证 |
| **R2**: 端口被防火墙阻止 | 低 | 高 | 中 | 提前检查腾讯云安全组规则，准备备用端口方案 |
| **R3**: Python 依赖版本冲突 | 中 | 中 | 中 | 使用虚拟环境隔离，提前在本地验证依赖兼容性 |
| **R4**: Nginx 配置冲突 | 低 | 中 | 低 | 使用独立配置文件，不修改默认配置 |
| **R5**: SSL 证书申请失败 | 低 | 中 | 低 | 准备手动申请方案，使用 HTTP 验证方式 |
| **R6**: 服务启动失败 | 中 | 高 | 高 | 准备详细的启动日志，配置 systemd 自动重启 |
| **R7**: 性能不达标 | 中 | 中 | 中 | 提前进行本地性能基准测试，准备优化方案 |
| **R8**: 数据丢失 | 低 | 高 | 中 | 部署前备份现有数据，使用 SQLite 事务保护 |
| **R9**: 影响现有项目 | 低 | 高 | 中 | 使用独立端口和目录，Nginx 配置隔离 |
| **R10**: 安全漏洞未修复 | 中 | 高 | 高 | 强制 P0 问题修复完成才能进入部署阶段 |

**风险项数量**: 10 个  
**高风险项**: 3 个（R1, R6, R10）  
**中风险项**: 5 个（R2, R3, R7, R8, R9）  
**低风险项**: 2 个（R4, R5）

---

## 六、回滚方案

### 6.1 回滚触发条件

- 部署后功能验证通过率 < 90%
- 性能指标不达标且无法在 2 小时内优化
- 出现 P0 安全漏洞
- 影响现有项目正常运行
- 服务可用性 < 95%

### 6.2 回滚步骤

**Step 1: 停止新服务**
```bash
sudo systemctl stop loop-harness-agent-backend
sudo systemctl stop loop-harness-agent-mcp-bridge
sudo systemctl disable loop-harness-agent-backend
sudo systemctl disable loop-harness-agent-mcp-bridge
```

**Step 2: 恢复 Nginx 配置**
```bash
sudo cp /etc/nginx/conf.d/loopmcp.renrenup.cn.conf.backup /etc/nginx/conf.d/loopmcp.renrenup.cn.conf
sudo nginx -t
sudo systemctl reload nginx
```

**Step 3: 清理部署文件（可选）**
```bash
# 保留日志和数据，删除代码
sudo rm -rf /opt/loop-harness-agent/code
sudo rm -rf /opt/loop-harness-agent/venv
```

**Step 4: 验证回滚**
- 确认 loopmcp.renrenup.cn 无法访问（或指向旧服务）
- 确认现有项目正常运行
- 确认端口 8001、8765 已释放

### 6.3 回滚时间

- **预计回滚时间**: 15 分钟
- **回滚负责人**: @DevOps
- **回滚验证人**: @全栈测试员

---

## 七、运维手册

### 7.1 服务管理命令

**启动服务**
```bash
sudo systemctl start loop-harness-agent-backend
sudo systemctl start loop-harness-agent-mcp-bridge
```

**停止服务**
```bash
sudo systemctl stop loop-harness-agent-backend
sudo systemctl stop loop-harness-agent-mcp-bridge
```

**重启服务**
```bash
sudo systemctl restart loop-harness-agent-backend
sudo systemctl restart loop-harness-agent-mcp-bridge
```

**查看服务状态**
```bash
sudo systemctl status loop-harness-agent-backend
sudo systemctl status loop-harness-agent-mcp-bridge
```

**查看服务日志**
```bash
sudo journalctl -u loop-harness-agent-backend -f
sudo journalctl -u loop-harness-agent-mcp-bridge -f
```

### 7.2 Nginx 管理命令

**测试配置**
```bash
sudo nginx -t
```

**重载配置**
```bash
sudo systemctl reload nginx
```

**查看访问日志**
```bash
sudo tail -f /var/log/nginx/loopmcp.renrenup.cn.access.log
```

**查看错误日志**
```bash
sudo tail -f /var/log/nginx/loopmcp.renrenup.cn.error.log
```

### 7.3 SSL 证书管理

**证书续期**
```bash
sudo certbot renew --dry-run
sudo certbot renew
```

**查看证书信息**
```bash
sudo certbot certificates
```

### 7.4 数据库管理

**备份数据库**
```bash
cp /opt/loop-harness-agent/data/loop_agent.db /opt/loop-harness-agent/backups/loop_agent_$(date +%Y%m%d).db
```

**恢复数据库**
```bash
cp /opt/loop-harness-agent/backups/loop_agent_YYYYMMDD.db /opt/loop-harness-agent/data/loop_agent.db
sudo systemctl restart loop-harness-agent-backend
```

### 7.5 日志管理

**日志轮转配置**
```bash
# /etc/logrotate.d/loop-harness-agent
/opt/loop-harness-agent/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl restart loop-harness-agent-backend
    endscript
}
```

**手动清理日志**
```bash
sudo journalctl --vacuum-time=7d
```

### 7.6 监控命令

**查看端口占用**
```bash
sudo netstat -tlnp | grep -E '8001|8765'
```

**查看进程状态**
```bash
ps aux | grep uvicorn
```

**查看系统资源**
```bash
top -p $(pgrep -d ',' -f uvicorn)
```

### 7.7 故障排查

**服务无法启动**
1. 检查日志：`sudo journalctl -u loop-harness-agent-backend -n 50`
2. 检查端口占用：`sudo netstat -tlnp | grep 8001`
3. 检查权限：`ls -la /opt/loop-harness-agent/`
4. 检查虚拟环境：`source /opt/loop-harness-agent/venv/bin/activate && python -c "import fastapi"`

**502 Bad Gateway**
1. 检查后端服务：`sudo systemctl status loop-harness-agent-backend`
2. 检查 Nginx 配置：`sudo nginx -t`
3. 检查上游连接：`curl http://localhost:8001/health`

**WebSocket 连接失败**
1. 检查防火墙：`sudo firewall-cmd --list-ports`
2. 检查 Nginx WebSocket 配置
3. 查看浏览器控制台错误

**性能问题**
1. 查看慢查询日志
2. 检查数据库索引
3. 分析 Uvicorn worker 数量
4. 检查系统资源使用率

---

## 附录

### A. 服务器信息

- **IP**: 43.139.1.48
- **SSH Key**: C:\Users\Administrator\Documents\腾讯云服务器私钥code.pem
- **用户**: root
- **系统**: OpenCloudOS 9.4（RHEL 系）
- **域名**: loopmcp.renrenup.cn
- **端口**: 8001（后端）、8765（MCP 桥接）、443（HTTPS）

### B. 参考文档

- [部署参考脚本](file://g:/ai-gongju/prd-debate/aichat-app/deploy.sh)
- [安全审查报告](file://g:/ai-gongju/Loop-agent/docs/AUDIT_REPORT.md)
- [功能测试报告](file://g:/ai-gongju/Loop-agent/docs/FUNCTIONAL_TEST_REPORT.md)
- [架构设计文档](file://g:/ai-gongju/Loop-agent/docs/mcp-monitor-dashboard/Architecture.md)

### C. 联系人

- **项目经理**: @Product-Manager
- **DevOps**: @DevOps
- **测试负责人**: @全栈测试员
- **安全负责人**: @Code-Reviewer

---

**文档结束**
