# Release-Notes · 发布说明

> **工件类型**：强制工件
> **所属 Phase**：Phase 9
> **责任角色**：@Documenter / @DevOps
> **状态**：⏳ PENDING → 🔄 IN_PROGRESS → ✅ COMPLETED
> **融合验收标准**：g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md

| 字段 | 值 |
|------|-----|
| **文档版本** | v1.0 |
| **创建日期** | YYYY-MM-DD |
| **最后更新** | YYYY-MM-DD |
| **作者** | @Documenter |
| **审核者** | @Final-Reviewer |
| **关联工件** | Quality-Check-Report.md / Code-Review-Report.md / UX-Review-Report.md |

---

## 1. 版本信息

| 项目 | 值 |
|------|-----|
| **产品名称** | |
| **版本号** | vX.Y.Z |
| **发布日期** | YYYY-MM-DD |
| **上一版本** | vX.Y.Z |
| **发布类型** | Major / Minor / Patch |
| **代码分支** | |
| **Commit SHA** | |
| **构建编号** | |

### 1.1 版本号规则

- **Major（X.0.0）**：破坏性变更
- **Minor（x.Y.0）**：新功能，向后兼容
- **Patch（x.y.Z）**：Bug 修复，向后兼容

---

## 2. 变更摘要

<!-- 填写指引：用 2-3 句话概括本次发布的核心变更。 -->

### 2.1 一句话摘要

<!-- 如："本次发布新增了用户认证模块，修复了 3 个已知问题，无破坏性变更。" -->

### 2.2 关键指标

| 指标 | 值 |
|------|-----|
| 新增功能数 | |
| 修复问题数 | |
| 破坏性变更数 | |
| 变更文件数 | |
| 新增代码行 | |
| 删除代码行 | |
| Gate 1-3 通过状态 | ✅ 全部通过 |

---

## 3. 新功能

<!-- 填写指引：列出所有新功能，每个功能包含编号、描述和关联需求。 -->

| 编号 | 功能名称 | 描述 | 关联需求（Product-Spec） | 影响页面 |
|------|----------|------|--------------------------|----------|
| NF-001 | | | F-XXX | PG-XXX |
| NF-002 | | | | |

### 3.1 功能详细说明

#### NF-001：[功能名称]

- **功能描述**：<!-- 详细说明功能内容 -->
- **使用方式**：<!-- 用户如何使用此功能 -->
- **配置选项**：<!-- 是否有可配置项 -->
- **已知限制**：<!-- 当前已知限制 -->

<!-- 按相同格式补充 NF-002... -->

---

## 4. 修复

<!-- 填写指引：列出所有 Bug 修复，每个修复包含编号、描述和关联问题。 -->

| 编号 | 问题描述 | 根因 | 修复方式 | 关联 Issue |
|------|----------|------|----------|-----------|
| FX-001 | | | | #XXX |
| FX-002 | | | | |

---

## 5. 破坏性变更

<!-- 填写指引：列出所有破坏性变更，必须包含迁移指南。如无破坏性变更，标注"无"。 -->

### 5.1 破坏性变更清单

| 编号 | 变更描述 | 影响范围 | 迁移方式 | 关联需求 |
|------|----------|----------|----------|----------|
| BC-001 | | | | |

### 5.2 迁移指南

#### BC-001：[变更名称]

**变更前**：
```typescript
// 旧用法
```

**变更后**：
```typescript
// 新用法
```

**迁移步骤**：
1. <!-- 步骤 1 -->
2. <!-- 步骤 2 -->
3. <!-- 步骤 3 -->

---

## 6. 部署前提

<!-- 填写指引：列出部署前必须满足的所有前提条件。 -->

### 6.1 基础设施前提

| 前提条件 | 要求 | 当前状态 | 说明 |
|----------|------|----------|------|
| 服务器资源 | CPU ≥ X 核 / 内存 ≥ X GB / 磁盘 ≥ X GB | | |
| 数据库 | <!-- 版本 / 迁移脚本 --> | | |
| 缓存 | <!-- Redis 版本 --> | | |
| CDN | <!-- 配置要求 --> | | |
| SSL 证书 | <!-- 域名 / 有效期 --> | | |
| DNS | <!-- 域名解析 --> | | |

### 6.2 依赖服务前提

| 服务 | 版本 | 状态 | 说明 |
|------|------|------|------|
| <!-- 如：Supabase --> | | | |
| <!-- 如：MiniMax API --> | | | |
| <!-- 如：Cloudflare --> | | | |

### 6.3 数据迁移前提

| 迁移项 | 脚本路径 | 预估时间 | 是否可回滚 | 说明 |
|--------|----------|----------|-----------|------|
| | `scripts/migrate-xxx.sql` | | ✅/❌ | |

---

## 7. 环境变量

<!-- 填写指引：列出所有需要配置的环境变量，标注是否必填。 -->

### 7.1 环境变量清单

| 变量名 | 必填 | 默认值 | 说明 | 示例值 |
|--------|------|--------|------|--------|
| `NODE_ENV` | ✅ | production | 运行环境 | production |
| `PORT` | ❌ | 3000 | 服务端口 | 3000 |
| `DATABASE_URL` | ✅ | — | 数据库连接串 | postgresql://user:pass@host:5432/db |
| `JWT_SECRET` | ✅ | — | JWT 签名密钥 | <!-- 32+ 字符随机字符串 --> |
| `API_KEY_XXX` | ✅ | — | 第三方 API 密钥 | |
| | | | | |

### 7.2 密钥管理说明

- 所有密钥通过环境变量注入，禁止硬编码
- 生产环境密钥通过 CI/CD Secrets 管理
- 密钥轮换周期：<!-- 90 天 / 180 天 -->
- 密钥存储位置：<!-- 如：GitHub Secrets / Vault -->

---

## 8. 部署步骤

<!-- 填写指引：详细列出部署的每一步操作，确保可重复执行。 -->

### 8.1 部署流程

```bash
# Step 1: 拉取最新代码
git clone <repo> && cd <project>
git checkout <tag/branch>

# Step 2: 安装依赖
npm ci --production

# Step 3: 执行数据库迁移
npx prisma migrate deploy

# Step 4: 构建生产包
npm run build

# Step 5: 配置环境变量
cp .env.example .env.production
# 编辑 .env.production 填入实际值

# Step 6: 启动服务
npm run start:prod

# Step 7: 验证服务
curl -f http://localhost:3000/health || exit 1

# Step 8: 配置 Nginx
# (详见 Nginx 配置段)

# Step 9: 申请 SSL 证书
# (详见 SSL 配置段)
```

### 8.2 Nginx 配置

```nginx
server {
    listen 80;
    server_name <domain>;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name <domain>;

    ssl_certificate     /etc/letsencrypt/live/<domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 8.3 SSL 证书申请

```bash
# 使用 certbot 申请 Let's Encrypt 证书
sudo certbot certonly --nginx -d <domain>

# 自动续期
sudo certbot renew --dry-run
```

### 8.4 部署验证

| 验证项 | 命令/方式 | 预期结果 |
|--------|-----------|----------|
| 服务启动 | `curl http://localhost:3000/health` | HTTP 200 |
| HTTPS 可访问 | 浏览器访问 `https://<domain>` | 页面正常 |
| API 可用 | `curl https://<domain>/api/health` | HTTP 200 |
| 数据库连接 | 查看应用日志 | 无连接错误 |
| 静态资源 | 检查 CDN 缓存 | 资源可加载 |

---

## 9. 回滚策略

<!-- 填写指引：定义回滚触发条件、回滚步骤和数据恢复方案。 -->

### 9.1 回滚触发条件

| 条件 | 阈值 | 监控方式 |
|------|------|----------|
| 错误率飙升 | > 5% | 应用日志 |
| 响应时间劣化 | P95 > 3s | APM |
| 核心功能不可用 | 无法登录/无法下单 | 冒烟测试 |
| 数据异常 | 数据丢失/损坏 | 数据校验 |

### 9.2 回滚步骤

```bash
# Step 1: 停止当前服务
pm2 stop <app-name>

# Step 2: 切换到上一版本代码
git checkout <previous-tag>

# Step 3: 安装依赖
npm ci --production

# Step 4: 回滚数据库（如需要）
npx prisma migrate resolve --rolled-back <migration-name>

# Step 5: 构建并启动
npm run build && npm run start:prod

# Step 6: 验证回滚
curl -f http://localhost:3000/health

# Step 7: 通知团队
# [BC] @DevOps → ALL: 已回滚至 vX.Y.Z，原因：xxx
```

### 9.3 数据恢复方案

| 场景 | 恢复方式 | 预估时间 | 数据损失 |
|------|----------|----------|----------|
| 数据库迁移回滚 | `prisma migrate rollback` | 5min | 无 |
| 数据误删 | 数据库备份恢复 | 30min | 备份点后的数据 |
| 配置错误 | 恢复配置文件 | 5min | 无 |

---

## 10. 冒烟测试清单

<!-- 填写指引：列出部署后必须验证的关键功能点，确保系统可用。 -->

### 10.1 核心功能验证

| 编号 | 测试项 | 测试步骤 | 预期结果 | 实际结果 | 通过 |
|------|--------|----------|----------|----------|------|
| SM-001 | 用户注册 | 1. 访问注册页 2. 填写信息 3. 提交 | 注册成功，跳转首页 | | ⏳ |
| SM-002 | 用户登录 | 1. 访问登录页 2. 输入凭证 3. 提交 | 登录成功，显示用户信息 | | ⏳ |
| SM-003 | 核心业务流程 | 1. <!-- 步骤 --> | <!-- 预期 --> | | ⏳ |
| SM-004 | 数据展示 | 1. 访问列表页 | 数据正确加载 | | ⏳ |
| SM-005 | 表单提交 | 1. 填写表单 2. 提交 | 提交成功 | | ⏳ |

### 10.2 非功能验证

| 编号 | 测试项 | 测试步骤 | 预期结果 | 实际结果 | 通过 |
|------|--------|----------|----------|----------|------|
| SM-006 | HTTPS 正常 | 浏览器访问 | 证书有效，无警告 | | ⏳ |
| SM-007 | 页面加载速度 | 首屏加载 | ≤ 3s | | ⏳ |
| SM-008 | 移动端适配 | 手机访问 | 布局正常 | | ⏳ |
| SM-009 | 错误页面 | 访问不存在路径 | 显示 404 页面 | | ⏳ |
| SM-010 | API 健康检查 | `curl /api/health` | HTTP 200 | | ⏳ |

### 10.3 冒烟测试判定

| 判定 | 条件 |
|------|------|
| ✅ PASS | 所有测试项通过 |
| ❌ FAIL | 任一核心功能测试项失败 → 触发回滚 |

**最终判定**：⏳ 待定

---

## 附录

### A. 工件完整性检查

| 工件 | 路径 | 状态 |
|------|------|------|
| Product-Spec.md | | ✅/❌ |
| Design-Brief.md | | ✅/❌ |
| UI-Design.md | | ✅/❌ |
| Component-Library.md | | ✅/❌ |
| DEV-PLAN.md | | ✅/❌ |
| Quality-Check-Report.md | | ✅/❌ |
| Code-Review-Report.md | | ✅/❌ |
| UX-Review-Report.md | | ✅/❌ |
| Release-Notes.md | | ✅/❌ |

### B. 门禁通过记录

| 门禁 | 角色 | 通过时间 | 报告链接 |
|------|------|----------|----------|
| Gate 1 | @Code-Reviewer | | Code-Review-Report.md |
| Gate 2 | @Professional-Performance | | |
| Gate 3 | @全栈测试员 | | |
| Gate 4 | @Final-Reviewer | | |

### C. 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| YYYY-MM-DD | v1.0 | 初始版本 | @Documenter |
