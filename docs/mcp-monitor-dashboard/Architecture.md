# Architecture: MCP 实时监控看板系统 - 架构设计文档

> **版本**: v1.0.0
> **日期**: 2026-06-19
> **状态**: 设计冻结
> **基于**: PRD.md v1.0.0, Product-Spec.md v1.0.0
> **负责人**: @Architect

---

## 一、系统架构总览

### 1.1 架构风格
**前后端分离 + 事件驱动实时推送**

采用经典的 B/S 架构，前端为 SPA（单页应用），后端提供 RESTful API + WebSocket 服务，通过事件驱动模式实现实时数据推送。

### 1.2 分层架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        表现层 (Presentation)                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    React 18 SPA (TypeScript)                 │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ Agent    │ │ Log      │ │ Progress │ │ Dashboard│       │   │
│  │  │ Status   │ │ Stream   │ │ Panel    │ │ Overview │       │   │
│  │  │ (F001)   │ │ (F002)   │ │ (F003)   │ │ (F004)   │       │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │   │
│  │       └────────────┴────────────┴────────────┘              │   │
│  │                     ↓ WebSocket Client                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│                        接入层 (Gateway)                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Nginx Reverse Proxy (生产环境)                  │   │
│  │         - SSL Termination (HTTPS/WSS)                       │   │
│  │         - Static File Serving                               │   │
│  │         - WebSocket Proxy (ws:// → wss://)                  │   │
│  │         - Rate Limiting                                     │   │
│  └──────────┬──────────────────────────────────┬───────────────┘   │
├─────────────┼──────────────────────────────────┼───────────────────┤
│             ↓ HTTP/REST                       ↓ WebSocket        │
│  ┌──────────┴──────────────────────────────────┴───────────────┐   │
│  │                    应用层 (Application)                      │   │
│  │  ┌──────────────────┐  ┌────────────────────────────────┐   │   │
│  │  │ FastAPI Server    │  │ WebSocket Server               │   │   │
│  │  │ - RESTful APIs    │  │ - Real-time Push              │   │   │
│  │  │ - Process Control │  │ - Connection Management       │   │   │
│  │  │ - Health Check    │  │ - Channel Subscription        │   │   │
│  │  └────────┬─────────┘  └───────────────┬────────────────┘   │   │
│  │           ↓                              ↓                   │   │
│  │  ┌────────┴──────────────────────────────┴──────────────┐   │   │
│  │  │              Service Layer (业务逻辑)                │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │   │
│  │  │  │ Data     │ │ Process  │ │ MCP      │            │   │   │
│  │  │  │ Collector│ │ Manager  │ │ Adapter  │            │   │   │
│  │  │  └────┬─────┘ └────┬─────┘ └────┬─────┘            │   │   │
│  │  └───────┼────────────┼──────────┼─────────────────────┘   │   │
│  └──────────┼────────────┼──────────┼──────────────────────────┘   │
├─────────────┼────────────┼──────────┼──────────────────────────────┤
│             ↓            ↓          ↓                              │
│  ┌──────────┴────────────┴──────────┴──────────────────────────┐   │
│  │                    数据层 (Data)                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │ SQLite DB    │  │ File System  │  │ MCP Server       │  │   │
│  │  │ (历史日志)   │  │ (黑板文件)   │  │ (外部进程)       │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 核心设计原则

| 原则 | 描述 | 应用场景 |
|------|------|---------|
| **关注点分离** | 前后端独立部署、独立开发 | 全栈开发分工 |
| **事件驱动** | 数据变化通过事件广播，而非轮询 | 实时监控场景 |
| **单一职责** | 每个模块只做一件事 | Service 层设计 |
| **接口隔离** | 前后端通过明确契约通信 | API 设计 |
| **依赖倒置** | 上层依赖抽象，不依赖具体实现 | MCP Adapter |

---

## 二、技术选型详细说明

### 2.1 前端技术栈

| 技术 | 版本 | 选型理由 | 替代方案 |
|------|------|---------|---------|
| **React** | 18.3+ | 虚拟 DOM 性能优秀、Hooks 灵活、生态最大 | Vue 3（用户已指定 React） |
| **TypeScript** | 5.4+ | 类型安全、IDE 支持、重构成本低 | JavaScript（类型不安全） |
| **Vite** | 5.4+ | 极速 HMR（< 50ms）、ESM 原生、构建快 | Webpack（配置复杂） |
| **Ant Design** | 5.x | 企业级组件丰富、设计规范统一、中文友好 | Material UI（风格不符） |
| **ECharts** | 5.5+ | 功能强大、性能优秀、中文文档完善 | Chart.js（功能不足） |
| **Tailwind CSS** | 3.4+ | 原子化 CSS、开发效率高、体积小 | CSS Modules（写法冗长） |
| **Zustand** | 4.5+ | 轻量状态管理（1KB）、API 简洁 | Redux（过重） |
| **React Window** | 1.8+ | 虚拟滚动组件、处理大数据列表 | 自实现（成本高） |
| **WebSocket API** | 原生 | 浏览器原生支持、无需额外库 | Socket.io（协议封装） |

### 2.2 后端技术栈

| 技术 | 版本 | 选型理由 | 替代方案 |
|------|------|---------|---------|
| **Python** | 3.11+ | 与 MCP Server 同生态、异步支持好 | Node.js（MCP 适配成本高） |
| **FastAPI** | 0.111+ | 高性能异步、自动 OpenAPI 文档、类型提示 | Flask（同步性能差） |
| **uvicorn** | 0.29+ | ASGI 服务器、高性能、支持 WebSocket | gunicorn（WS 支持弱） |
| **websockets** | 12.0+ | Python WebSocket 库、asyncio 原生 | aiohttp（功能冗余） |
| **SQLite** | 3.45+ | 零配置、嵌入式、适合单实例 | PostgreSQL（过重） |
| **SQLAlchemy** | 2.0+ | ORM 抽象层、支持异步、类型安全 | raw SQL（维护成本高） |
| **pydantic** | 2.7+ | 数据验证、序列化、OpenAPI 自动生成 | dataclasses（功能不足） |
| **APScheduler** | 3.10+ | 定时任务调度、轻量级 | Celery（过重） |
| **python-dotenv** | 1.0+ | 环境变量管理 | os.environ（不优雅） |

### 2.3 开发工具链

| 工具 | 用途 |
|------|------|
| ESLint + Prettier | 代码格式化和检查 |
| Husky + lint-staged | Git hooks 自动化 |
| Vitest | 单元测试框架 |
| Playwright | E2E 测试框架 |
| TypeScript Compiler | 类型检查 |
| Vite Plugin PWA | PWA 支持（可选） |

---

## 三、目录结构设计

### 3.1 项目根目录

```
mcp-monitor-dashboard/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 配置管理
│   │   ├── dependencies.py           # 依赖注入
│   │   ├── models/                   # Pydantic 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # Agent 状态模型
│   │   │   ├── log.py                # 日志模型
│   │   │   ├── project.py            # 项目概览模型
│   │   │   └── websocket.py           # WS 消息模型
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── data_collector.py     # 数据采集服务
│   │   │   ├── process_manager.py    # 进程管理服务
│   │   │   ├── mcp_adapter.py        # MCP 适配器
│   │   │   └── cache_service.py      # 缓存服务
│   │   ├── api/                      # RESTful API 路由
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # 主路由聚合
│   │   │   ├── agents.py             # Agent 相关 API
│   │   │   ├── logs.py               # 日志相关 API
│   │   │   ├── project.py            # 项目概览 API
│   │   │   └── system.py             # 系统控制 API
│   │   ├── websocket/                # WebSocket 服务
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # 连接管理器
│   │   │   ├── handler.py            # 消息处理器
│   │   │   └── broadcaster.py        # 广播器
│   │   └── core/                     # 核心基础设施
│   │       ├── __init__.py
│   │       ├── database.py           # 数据库连接
│   │       └── scheduler.py          # 定时任务
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_websocket/
│   ├── alembic/                      # 数据库迁移（如需）
│   ├── requirements.txt              # Python 依赖
│   ├── pyproject.toml                # 项目配置
│   └── .env.example                  # 环境变量模板
│
├── frontend/                         # 前端应用
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── main.tsx                  # 入口文件
│   │   ├── App.tsx                   # 根组件
│   │   ├── vite-env.d.ts
│   │   ├── assets/                   # 静态资源
│   │   │   ├── icons/
│   │   │   └── images/
│   │   ├── components/               # 通用组件
│   │   │   ├── common/
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   └── Toast.tsx
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   └── ui/
│   │   │       ├── AgentCard.tsx
│   │   │       ├── ProgressBar.tsx
│   │   │       ├── StatusBadge.tsx
│   │   │       └── LogEntry.tsx
│   │   ├── pages/                    # 页面组件
│   │   │   ├── Dashboard.tsx         # 主仪表盘页面
│   │   │   ├── AgentDetail.tsx       # Agent 详情页
│   │   │   └── Settings.tsx          # 设置页
│   │   ├── hooks/                    # 自定义 Hooks
│   │   │   ├── useWebSocket.ts       # WebSocket 连接管理
│   │   │   ├── useAgentStatus.ts     # Agent 状态订阅
│   │   │   ├── useLogs.ts            # 日志流订阅
│   │   │   └── useProjectOverview.ts # 项目概览订阅
│   │   ├── services/                 # API 服务层
│   │   │   ├── api.ts                # Axios 实例
│   │   │   ├── agentService.ts       # Agent API
│   │   │   ├── logService.ts         # 日志 API
│   │   │   └── projectService.ts     # 项目 API
│   │   ├── store/                    # 状态管理 (Zustand)
│   │   │   ├── index.ts
│   │   │   ├── agentStore.ts
│   │   │   ├── logStore.ts
│   │   │   └── projectStore.ts
│   │   ├── types/                    # TypeScript 类型定义
│   │   │   ├── agent.ts
│   │   │   ├── log.ts
│   │   │   ├── project.ts
│   │   │   └── websocket.ts
│   │   ├── utils/                    # 工具函数
│   │   │   ├── formatters.ts
│   │   │   ├── validators.ts
│   │   │   └── constants.ts
│   │   └── styles/                   # 全局样式
│   │       ├── globals.css
│   │       └── tailwind.css
│   ├── tests/
│   │   ├── unit/
│   │   └── e2e/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── eslint.config.js
│   └── .env.example
│
├── scripts/                          # 运维脚本
│   ├── start.sh                      # 启动脚本（Linux/Mac）
│   ├── start.ps1                     # 启动脚本（Windows）
│   ├── stop.sh                       # 停止脚本
│   └── deploy.sh                     # 部署脚本
│
├── docs/                             # 文档
│   └── mcp-monitor-dashboard/        # 已有规划文档
│
├── docker-compose.yml                # Docker 编排（可选）
├── .gitignore
├── README.md
└── LICENSE
```

---

## 四、数据库设计

### 4.1 ER 图（实体关系）

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   agents     │       │   logs       │       │  projects    │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)      │       │ id (PK)      │
│ name         │  │    │ agent_id(FK) │←──────┤ name         │
│ display_name │  └───→│ timestamp    │       │ current_phase │
│ role_type    │       │ level        │       │ status       │
│ icon         │       │ message      │       │ created_at   │
│ status       │       │ metadata_json│       │ updated_at   │
│ created_at   │       │ created_at   │       └──────────────┘
│ updated_at   │       └──────────────┘
└──────────────┘

┌──────────────┐       ┌──────────────┐
│   tasks      │       │   alerts     │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │
│ phase        │       │ type         │
│ name         │       │ severity     │
│ status       │       │ message      │
│ progress     │       │ resolved     │
│ assignee_id  │       │ created_at   │
│ started_at   │       │ resolved_at  │
│ completed_at │       └──────────────┘
└──────────────┘
```

### 4.2 表结构详细定义

#### 4.2.1 agents 表（Agent 状态）
```sql
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,                    -- 'product-manager'
    display_name TEXT NOT NULL,              -- 'Product Manager'
    role_type TEXT NOT NULL,                 -- 'planning'
    icon TEXT DEFAULT '🤖',                 -- emoji 或图标路径
    status TEXT NOT NULL DEFAULT 'idle',     -- idle/running/error/complete
    current_task_name TEXT,
    current_task_phase INTEGER,
    current_task_progress REAL DEFAULT 0,    -- 0-100
    last_activity_time TIMESTAMP,
    error_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_updated ON agents(updated_at);
```

#### 4.2.2 logs 表（操作日志）
```sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL DEFAULT 'info',       -- info/warn/error/debug
    message TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',          -- JSON 格式扩展字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_logs_agent ON logs(agent_id);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_level ON logs(level);
-- 全文搜索索引（SQLite FTS5）
CREATE VIRTUAL TABLE IF NOT EXISTS logs_fts USING fts5(
    message,
    content=logs,
    content_rowid=id
);
-- 同步触发器
CREATE TRIGGER IF NOT EXISTS logs_ai AFTER INSERT ON logs BEGIN
    INSERT INTO logs_fts(rowid, message) VALUES (new.id, new.message);
END;
```

#### 4.2.3 projects 表（项目信息）
```sql
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    current_phase TEXT,
    phase_progress REAL DEFAULT 0,
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    token_used INTEGER DEFAULT 0,
    token_total INTEGER DEFAULT 100000,
    gate1_status TEXT DEFAULT 'pending',
    gate2_status TEXT DEFAULT 'pending',
    gate3_status TEXT DEFAULT 'pending',
    gate4_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.2.4 alerts 表（告警记录）
```sql
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,                     -- deviation/token_over_budget/gate_failed
    severity TEXT NOT NULL DEFAULT 'info',  -- info/warning/error/critical
    title TEXT NOT NULL,
    message TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_resolved ON alerts(resolved);
CREATE INDEX idx_alerts_created ON alerts(created_at);
```

---

## 五、API 接口规范

### 5.1 RESTful API

#### Base URL: `/api/v1`

#### 5.1.1 Agent 相关

**GET /api/v1/agents**
获取所有 Agent 状态列表

Response 200:
```json
{
  "code": 0,
  "data": [
    {
      "id": "product-manager",
      "display_name": "Product Manager",
      "role_type": "planning",
      "icon": "📋",
      "status": "idle",
      "current_task": null,
      "last_activity_time": "2026-06-19T14:32:15Z"
    },
    {
      "id": "architect",
      "display_name": "Architect",
      "role_type": "design",
      "icon": "🏗️",
      "status": "running",
      "current_task": {
        "name": "编写架构设计文档",
        "phase": 3,
        "progress": 67,
        "started_at": "2026-06-19T14:00:00Z"
      },
      "last_activity_time": "2026-06-19T14:32:10Z"
    }
  ],
  "total": 16
}
```

**GET /api/v1/agents/{agent_id}**
获取单个 Agent 详细状态

Response 200:
```json
{
  "code": 0,
  "data": {
    "id": "architect",
    "display_name": "Architect",
    "role_type": "design",
    "icon": "🏗️",
    "status": "running",
    "current_task": {
      "name": "编写架构设计文档",
      "phase": 3,
      "progress": 67,
      "started_at": "2026-06-19T14:00:00Z",
      "estimated_end": "2026-06-19T15:30:00Z"
    },
    "recent_logs": [...],
    "error_history": []
  }
}
```

#### 5.1.2 日志相关

**GET /api/v1/logs**
查询操作日志（支持分页和过滤）

Query Parameters:
- `agent_id`: 可选，按 Agent 过滤
- `level`: 可选，按级别过滤 (info/warn/error/debug)
- `keyword`: 可选，关键词搜索
- `page`: 页码（默认 1）
- `page_size`: 每页条数（默认 50，最大 200）
- `start_time`: 开始时间（ISO 8601）
- `end_time`: 结束时间（ISO 8601）

Response 200:
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 12345,
        "agent_id": "architect",
        "timestamp": "2026-06-19T14:32:15Z",
        "level": "info",
        "message": "架构设计文档已保存到 docs/mcp-monitor-dashboard/Architecture.md",
        "metadata": { "file_path": "...", "size": 15320 }
      }
    ],
    "total": 1523,
    "page": 1,
    "page_size": 50,
    "total_pages": 31
  }
}
```

#### 5.1.3 项目概览

**GET /api/v1/project/overview**
获取项目全景数据

Response 200:
```json
{
  "code": 0,
  "data": {
    "project_name": "MCP 实时监控看板系统",
    "current_phase": "Phase 3: Architecture Design",
    "phase_progress": 65,
    "tasks": {
      "total": 48,
      "completed": 12,
      "in_progress": 8,
      "failed": 2,
      "pending": 26
    },
    "token_budget": {
      "used": 45000,
      "total": 100000,
      "percentage": 45
    },
    "agents": {
      "total": 16,
      "active": 3,
      "idle": 12,
      "error": 1
    },
    "gates": {
      "gate1_code_review": "passed",
      "gate2_performance": "pending",
      "gate3_testing": "pending",
      "gate4_final_review": "pending"
    },
    "uptime_seconds": 86400,
    "last_update": "2026-06-19T14:32:15Z"
  }
}
```

#### 5.1.4 系统控制

**POST /api/v1/system/start**
启动 MCP Server 进程

Request:
```json
{}
```

Response 200:
```json
{
  "code": 0,
  "message": "MCP Server 启动成功",
  "data": {
    "pid": 12345,
    "status": "running",
    "started_at": "2026-06-19T14:33:00Z"
  }
}
```

**POST /api/v1/system/stop**
停止 MCP Server 进程

Request:
```json
{
  "force": false  // 是否强制停止
}
```

Response 200:
```json
{
  "code": 0,
  "message": "MCP Server 已停止",
  "data": {
    "pid": 12345,
    "stopped_at": "2026-06-19T14:35:00Z"
  }
}
```

**POST /api/v1/system/restart**
重启 MCP Server 进程

Request:
```json
{}
```

Response 200:
```json
{
  "code": 0,
  "message": "MCP Server 重启成功",
  "data": {
    "pid": 12346,
    "status": "running",
    "restarted_at": "2026-06-19T14:36:00Z"
  }
}
```

**GET /api/v1/system/status**
查询系统运行状态

Response 200:
```json
{
  "code": 0,
  "data": {
    "mcp_server": {
      "status": "running",  // running/stopped/error
      "pid": 12345,
      "uptime_seconds": 3600,
      "memory_usage_mb": 85.2,
      "cpu_usage_percent": 12.5
    },
    "monitor_system": {
      "version": "1.0.0",
      "websocket_connections": 5,
      "uptime_seconds": 7200
    }
  }
}
```

### 5.2 WebSocket API

#### Endpoint: `/ws`

#### 连接建立流程
```
Client                                    Server
  │                                         │
  │  ---- WebSocket Handshake (Upgrade) --->│
  │  <--- 101 Switching Protocols --------- │
  │                                         │
  │  ---- { type: 'subscribe',              │
  │        channels: ['agent_status',       │
  │                   'logs',               │
  │                   'overview'] } ------>│
  │                                         │
  │  <--- { type: 'init',                   │
  │         data: {                         │
  │           agents: [...],                │
  │           overview: {...},              │
  │           recentLogs: [...]             │
  │         }} ----------------------------│
  │                                         │
  │  <--- { type: 'agent_status_update',   │
  │         data: {...} } ------(每2s)---->│
  │  <--- { type: 'log_entry',             │
  │         data: {...} } ------(实时)---->│
  │  <--- { type: 'ping' } ---------(30s)->│
  │  ---- { type: 'pong' } --------------> │
```

#### 消息类型定义
详见 PRD.md §3.4.2 节

---

## 六、核心业务流程

### 6.1 数据采集与推送流程（核心循环）

```
[定时触发] 每 2 秒
  ↓
DataCollectorService.collect()
  ↓
┌─────────────────────────────────────────────┐
│ 1. 调用 MCPAdapter.get_status()            │
│    → 通过 subprocess 调用 MCP Server 工具   │
│    → 解析返回的 JSON 数据                  │
│                                             │
│ 2. 调用 MCPAdapter.read_blackboard()       │
│    → 读取 state.json 和 项目进度记录.md     │
│    → 结构化为 ProjectOverview 对象          │
│                                             │
│ 3. 数据比对                                 │
│    → 与内存缓存对比，识别变化项             │
│    → 仅推送变化的数据（增量更新）           │
└─────────────────────────────────────────────┘
  ↓
Broadcaster.broadcast()
  ↓
遍历所有已订阅该 channel 的 WebSocket 连接
  ↓
ws.send(message) × N (N = 在线客户端数)
```

### 6.2 进程管理流程

```
用户点击【启动】按钮
  ↓
前端 POST /api/v1/system/start
  ↓
ProcessManager.start()
  ↓
┌─────────────────────────────────────────────┐
│ 1. 检查当前状态                             │
│    → 如果已在运行 → 返回错误（幂等保护）    │
│                                             │
│ 2. 启动子进程                               │
│    subprocess.Popen([                        │
│      sys.executable, "-m",                  │
│      "loop_agent_mcp.server"                │
│    ], cwd=MCP_PROJECT_PATH)                 │
│                                             │
│ 3. 记录 PID 到内存/数据库                   │
│                                             │
│ 4. 等待 3 秒确认进程存活                    │
│    → 存活 → 返回 success                    │
│    → 死亡 → 返回 error + 错误日志           │
└─────────────────────────────────────────────┘
  ↓
返回响应给前端
  ↓
前端显示 toast 提示 + 更新按钮状态
```

### 6.3 WebSocket 断线重连流程

```
检测到 onclose 或 onerror 事件
  ↓
触发 reconnect()
  ↓
┌─────────────────────────────────────────────┐
│ if (retryCount === 0):                      │
│   delay = 0 // 立即重试                     │
│ elif (retryCount < 10):                     │
│   delay = Math.min(1000 * 2^retryCount,    │
│                    30000) // 指数退避       │
│ else:                                      │
│   delay = 30000 // 最大 30 秒间隔           │
│                                             │
│ showReconnectingUI(delay)                   │
│ await sleep(delay)                          │
│ retryCount++                                │
│                                             │
│ try:                                       │
│   new WebSocket(url)                        │
│   onSuccess:                                │
│     retryCount = 0                          │
│     hideReconnectingUI()                    │
│     requestFullSync() // 请求全量数据补齐   │
│ onError:                                   │
│   scheduleNextRetry()                       │
└─────────────────────────────────────────────┘
```

---

## 七、部署架构

### 7.1 开发环境
```
本地机器
├── 终端 1: cd backend && uvicorn app.main:app --reload --port 8000
├── 终端 2: cd frontend && npm run dev (--port 3000)
└── 浏览器: http://localhost:3000
```

### 7.2 生产环境（腾讯云）

```
腾讯云服务器 (43.139.1.48)
├── Nginx (反向代理 + SSL)
│   ├── 监听 443 (HTTPS/WSS)
│   ├── → 反向代理到 localhost:8000 (FastAPI)
│   ├── → 静态文件服务 (前端 build 产物)
│   └── SSL 证书 (Let's Encrypt / 手动申请)
│
├── Systemd Service
│   ├── mcp-monitor.service (FastAPI + WS)
│   └── mcp-server.service (MCP Server 子进程)
│
├── 目录结构
│   /opt/mcp-monitor-dashboard/
│   ├── backend/ (Python 代码 + venv)
│   ├── frontend/dist/ (React 构建产物)
│   ├── data/ (SQLite 数据库文件)
│   └── logs/ (应用日志)
│
└── 域名: mcp-monitor.renrenup.cn
```

### 7.3 Nginx 配置示例
```nginx
server {
    listen 443 ssl http2;
    server_name mcp-monitor.renrenup.cn;

    ssl_certificate /etc/nginx/ssl/mcp-monitor.renrenup.cn.pem;
    ssl_certificate_key /etc/nginx/ssl/mcp-monitor.renrenup.cn.key;

    # 前端静态文件
    location / {
        root /opt/mcp-monitor-dashboard/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # WebSocket 长连接超时
    }
}
```

---

## 八、性能优化策略

### 8.1 前端优化
| 策略 | 目标 | 实现方式 |
|------|------|---------|
| **虚拟滚动** | 10,000 条日志流畅渲染 | React Window |
| **增量更新** | 减少 setState 次数 | Immer + Zustand |
| **懒加载** | 首屏快速渲染 | React.lazy + Suspense |
| **代码分割** | 减少首屏 JS 体积 | 动态 import() |
| **图片优化** | 图标加载快 | SVG Icon / WebP |
| **防抖节流** | 减少无效重渲染 | lodash.debounce/throttle |

### 8.2 后端优化
| 策略 | 目标 | 实现方式 |
|------|------|---------|
| **异步 I/O** | 高并发处理 | asyncio + async/await |
| **连接池** | 数据库复用 | SQLAlchemy Engine pool |
| **增量推送** | 减少 WS 消息量 | 数据 diff 算法 |
| **内存缓存** | 快速读取热点数据 | dict 缓存 + TTL |
| **批量写入** | 日志高效持久化 | 批量 INSERT (每 5 秒或 100 条) |
| **索引优化** | 查询加速 | 合理创建 B-tree + FTS5 索引 |

### 8.3 WebSocket 优化
- **消息压缩**: 大 payload 使用 gzip 压缩
- **心跳保活**: 30 秒 ping/pong
- **背压控制**: 客户端处理慢时暂缓发送
- **断线补传**: 重连后请求时间戳之后的增量数据

---

## 九、安全设计

### 9.1 认证与授权
- M1 版本：无认证（内网工具，信任网络边界）
- M2/M3 版本：可集成 JWT / OAuth2（预留接口）

### 9.2 输入验证
- 所有 API 输入通过 Pydantic model 校验
- SQL 参数化查询（防止注入）
- XSS 防护：React 自动转义 + CSP 头

### 9.3 传输安全
- 生产环境强制 HTTPS/WSS
- TLS 1.2+（推荐 TLS 1.3）
- HSTS 头启用

### 9.4 CORS 策略
```python
# 生产环境严格限制
CORSMiddleware(
    allow_origins=["https://mcp-monitor.renrenup.cn"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 十、监控与运维

### 10.1 健康检查端点
```
GET /health → { "status": "ok", "timestamp": "...", "version": "1.0.0" }
GET /health/ready → 就绪探针（检查数据库、MCP 连接）
GET /health/live → 存活探针（仅返回 200）
```

### 10.2 日志规范
- **格式**: JSON 结构化日志
- **级别**: DEBUG < INFO < WARN < ERROR < CRITICAL
- **输出**: 同时输出到 stdout + 文件（logrotate 轮转）
- **采样**: DEBUG 级别生产环境默认关闭

### 10.3 告警规则（预留）
| 告警名称 | 触发条件 | 严重级别 | 通知渠道 |
|---------|---------|---------|---------|
| MCP Server Down | 进程不存在 > 30s | Critical | 弹窗 + 声音 |
| Token Over Budget | 使用率 > 90% | Warning | 黄色徽章 |
| Gate Failed | 任一 Gate 为 failed | Error | 红色卡片闪烁 |
| WS Connection High | 在线连接 > 50 | Info | 仪表盘指标 |
| Database Error | SQLite 写入失败 | Critical | 红色横幅 |

---

## 十一、决策记录

### 决策 A001: 单体 vs 微服务
- **选择**: 单体应用（前后端分离但同仓库）
- **理由**: M1 MVP 场景简单，微服务增加运维复杂度
- **升级路径**: 后续可拆分为独立的前后端仓库

### 决策 A002: SQLite vs PostgreSQL
- **选择**: SQLite
- **理由**: 单实例零配置、备份简单、性能足够
- **升级路径**: SQLAlchemy ORM 抽象层，切换仅需改连接字符串

### 决策 A003: 原生 WebSocket vs Socket.IO
- **选择**: 原生 WebSocket API
- **理由**: 协议更轻量、无额外依赖、浏览器原生支持
- **权衡**: 需自行实现重连、心跳等机制（已封装在 Hook 中）

---

## 十二、附录

### A. 环境变量清单
```bash
# .env.example
APP_NAME=MCP Monitor Dashboard
APP_ENV=development  # development/staging/production
APP_DEBUG=true
APP_PORT=8000

# MCP Server
MCP_SERVER_CWD=g:/ai-gongju/Loop-agent/loop-agent-mcp
MCP_SERVER_CMD=python -m loop_agent_mcp.server

# Database
DATABASE_URL=sqlite:///./data/mcp_monitor.db

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### B. 依赖版本锁定
见 `backend/requirements.txt` 和 `frontend/package.json`

### C. 参考文档
- [PRD.md](./PRD.md)
- [Product-Spec.md](./Product-Spec.md)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

**[NOTIFY] 本文档由 @Architect 在第3阶段产出，总控验收通过后并行流转至 @UX-Researcher + @UI-Designer**
