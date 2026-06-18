# Loop-Harness-Agent MCP Server

> **Loop Agent 模式的 MCP Server 实现 · 融合 Boss-auto-harness · v1.2 (智能执行器)**

将 Loop-Harness-Agent 的 16 角色 / 10 Phase / 4 Gate / 黑板 / 融合验收 暴露为 **15 个 MCP 工具**，跨 Trae IDE、Claude Code、Cursor 等任何 MCP 客户端可用。

> **v1.2 核心升级**：从"元调度器"升级为"**智能执行器**"，`spawn_agent` 现在会**实际执行开发任务**（生成代码、创建文件），而非仅返回提示信息。全面测试 **28/28 通过（100%）**。

---

## 一、这是什么

- **来源项目**：`g:\ai-gongju\Loop-agent`（Loop-Harness-Agent 模式 v1.2）
- **融合验收标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md`
- **工作流蓝图**：`g:\ai-gongju\Loop-agent\.trae\workflows\prd-to-production.json`
- **角色定义**：`g:\ai-gongju\Loop-agent\.trae\agents\*.agent.toml`（16 个）
- **测试报告**：`docs/TEST_REPORT_V1.2.md`（28/28 全部通过）

这是一个**进程内 stdio MCP Server**，把 Loop-Harness-Agent 的全部编排能力和实际执行功能封装为标准 MCP 工具，对外暴露原子能力 + 文件操作能力，避免污染客户端 LLM 上下文。

---

## 二、15 个对外工具（v1.2 新增 3 个）

### 2.1 核心编排工具（12 个）

| # | 工具 | 职责 | 响应模式 |
|---|------|------|----------|
| 1 | `start_loop` | 启动 / 恢复 Loop | 元数据返回 |
| 2 | `get_status` | 查询 Loop 完整状态（隐式读黑板）| 元数据返回 |
| 3 | `abort_loop` | 中止当前 Loop | 元数据返回 |
| 4 | `list_agents` | 列出 16 角色 + harness_discipline 摘要 | 元数据返回 |
| 5 | `spawn_agent` | **派发任务并实际执行**（代码生成）| **executed / hint_only** |
| 6 | `save_blackboard` | 保存 / 追加 `项目进度记录.md` | ok |
| 7 | `check_artifact_completeness` | 12 个强制工件完整性检查 | 元数据返回 |
| 8 | `check_evidence_sufficiency` | 5 类强制证据充分性检查 | 元数据返回 |
| 9 | `detect_deviation` | 5 类偏离检测 + 一票否决扫描 | 元数据返回 |
| 10 | `check_veto_items` | 6 项一票否决专项检查 | 元数据返回 |
| 11 | `check_fusion_targets` | 5 大融合目标达成度评估 | 元数据返回 |
| 12 | `get_token_budget_status` | Token 预算与效率状态 | 元数据返回 |

### 2.2 文件操作工具（v1.2 新增 3 个）⭐

| # | 工具 | 职责 | 响应模式 |
|---|------|------|----------|
| 13 | `write_file` | 写入文件到项目目录（支持任意路径）| ok + file_written |
| 14 | `read_file` | 读取项目中的文件内容 | ok + file_read |
| 15 | `list_files` | 列出目录下的所有文件 | ok + files_listed |

---

## 三、智能执行器模式（v1.2 核心升级）

### 3.1 可执行的 6 个角色

调用 `spawn_agent` 时，以下角色会**实际生成代码文件**：

| 角色 | 支持的任务类型 | 生成的文件示例 |
|------|----------------|----------------|
| **backend** | api, database, service, hook | `src/api/users.ts`, `src/models/user.ts`, `src/services/UserService.ts` |
| **frontend** | component, page, hook, structure | `src/components/Button.tsx`, `src/pages/Dashboard.tsx` |
| **architect** | structure, config, tech-stack | `ARCHITECTURE.md`, `tsconfig.json`, `package.json` |
| **requirements** | prd, user-story, acceptance-criteria | `docs/PRD-v1.0.md`, `docs/user-stories.md` |
| **tester** | unit, integration, e2e | `__tests__/components/Button.test.tsx` |
| **devops** | docker, nginx, ci-cd, deploy-script | `Dockerfile`, `nginx.conf`, `.github/workflows/ci.yml` |

### 3.2 提示类角色（10 个）

以下角色返回**指导性提示**（hint_only模式），由客户端LLM根据提示自主决策：

- product-manager, ux-researcher, ui-designer
- code-reviewer, performance, final-reviewer
- knowledge-curator, documenter, bug-defect-repairer, orchestrator

---

## 四、安装

### 方式 1：本地可编辑安装（推荐）

```bash
cd g:/ai-gongju/Loop-agent/loop-agent-mcp
pip install -e .
```

### 方式 2：直接安装

```bash
pip install mcp>=1.0.0
```

---

## 四、注册到 MCP 客户端

### Trae IDE

`%APPDATA%\Trae\User\mcp.json`（或 IDE 内 MCP 设置）：

```json
{
  "mcpServers": {
    "loop-harness-agent": {
      "command": "python",
      "args": ["-m", "loop_agent_mcp.server"],
      "cwd": "g:/ai-gongju/Loop-agent/loop-agent-mcp"
    }
  }
}
```

### Claude Code

```bash
claude mcp add loop-harness-agent \
  --command "python -m loop_agent_mcp.server" \
  --cwd "g:/ai-gongju/Loop-agent/loop-agent-mcp"
```

### Cursor

`~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "loop-harness-agent": {
      "command": "python",
      "args": ["-m", "loop_agent_mcp.server"],
      "cwd": "g:/ai-gongju/Loop-agent/loop-agent-mcp"
    }
  }
}
```

---

## 五、典型调用流程

```
1. start_loop({ time_budget_hours: 4, mode: "default" })
   → 返回 loop_id

2. list_agents({})
   → 返回 16 角色清单

3. spawn_agent({ agent_name: "product-manager", task_input: {prd_path: "..."} })
   → 应用 harness_discipline
   → 返回 next_step_hint

4. check_artifact_completeness({})
   → 实时检查 12 个强制工件状态

5. save_blackboard({ append_section: "..." })
   → 追加本轮日志

6. detect_deviation({})
   → 5 类偏离 + 一票否决扫描

7. check_fusion_targets({})
   → 5 大融合目标评估

8. get_token_budget_status({})
   → Token 消耗与效率

9. abort_loop({ reason: "deployment_done" })
   → 正常结束
```

---

## 六、测试

### 6.1 全面测试套件（28 个用例）

```bash
cd g:/ai-gongju/Loop-agent/loop-agent-mcp
python comprehensive_test_suite.py
```

**测试覆盖范围**：

| 类别 | 用例数 | 测试内容 |
|------|--------|----------|
| 核心功能 | 16 | start_loop, get_status, list_agents, spawn_agent*9, save_blackboard, write/read/list_files |
| 边界条件 | 6 | 空参数、无效角色、不存在文件、特殊字符路径、100KB大文件、深层目录 |
| 异常处理 | 3 | 未知工具名、参数类型错误、权限不足模拟 |
| 提示角色 | 3 | product-manager, ux-researcher, code-reviewer (hint_only模式) |

### 6.2 测试结果（v1.2 最终）

```
✅ 通过率: 28/28 (100.0%)
⚡ 性能指标:
   - 平均响应时间: < 1.5ms
   - P95 响应时间: < 2.6ms
   - P99 响应时间: < 2.6ms
   - 并发成功率(50线程): 100%
   - 总测试耗时: < 0.1s
```

详细报告：`docs/TEST_REPORT_V1.2.md`

---

## 七、目录结构

```
g:/ai-gongju/Loop-agent/loop-agent-mcp/
├── pyproject.toml                # 包配置与依赖
├── README.md                     # 本文档
├── loop_agent_mcp/               # 主包
│   ├── __init__.py               # 版本与元数据
│   ├── server.py                 # MCP Server stdio 入口
│   ├── core/                     # 核心：配置、状态
│   │   ├── config.py             #   16 角色、10 Phase、4 Gate 常量；资产加载
│   │   └── state.py              #   线程安全单例 StateManager
│   ├── engines/                  # 业务引擎
│   │   ├── orchestrator.py       #   Loop 主调度：start/advance/run_gate/spawn
│   │   ├── blackboard.py         #   黑板读写
│   │   ├── evidence.py           #   证据登记与查询
│   │   ├── deviation.py          #   偏离检测与一票否决
│   │   ├── token.py              #   Token 治理与摘要
│   │   └── fusion.py             #   5 大融合目标 + 工件/证据/否决检查
│   └── tools/                    # MCP 工具层
│       ├── schemas.py            #   12 个工具的输入输出 schema
│       └── dispatcher.py         #   工具调用统一路由
└── tests/                        # 单元测试
    └── test_engines.py           #   30+ 测试用例
```

---

## 八、融合 v1.2 关键能力

- ✅ 全自动闭环：start_loop → advance_phase → run_gate → save_blackboard 链式调用
- ✅ 生产级交付：check_artifact_completeness 阻断 12 工件缺失
- ✅ 直接部署：check_fusion_targets 校验 deploy_smoke_test 证据
- ✅ Token 效率：get_token_budget_status 实时监控，黑板优先策略
- ✅ 流程收敛：detect_deviation + check_veto_items 防 6 类偏离

---

## 九、版本

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| 1.0.0 | 2026-06-15 | 初始版本：Loop Agent MCP Server 骨架（12工具，元调度器模式）|
| 1.2.0 | 2026-06-16 | 融合 Boss-auto-harness v1.2：12 工具 + 5 引擎 + 完整测试 |
| **1.2.1** | **2026-06-19** | **智能执行器升级：新增 executors.py（6角色实际执行）+ 3个文件操作工具 + 全面测试28/28通过(100%)** |

---

## 十、快速开始示例

### 示例1：启动 Loop 并执行后端开发

```python
# 1. 启动 Loop
mcp.call("start_loop", {"time_budget_hours": 4, "mode": "default"})
# → { loop_id: "loop-xxx", mode: "default", ... }

# 2. 执行后端API开发（会生成 src/api/users.ts）
mcp.call("spawn_agent", {
    "agent_name": "backend",
    "task_input": {
        "task_type": "api",
        "endpoint": "users",
        "method": "GET",
        "description": "用户列表接口"
    }
})
# → {
#     status: "executed",
#     mode: "executed",
#     agent: "backend",
#     files_created: ["src/api/users.ts", "src/types/users.ts"],
#     output: "✅ 后端任务完成：生成 2 个文件"
#   }

# 3. 查看状态
mcp.call("get_status", {})
# → { current_phase: "Phase 5", iterations: 1, ... }

# 4. 保存黑板
mcp.call("save_blackboard", {"append_section": "完成用户API开发"})
```

### 示例2：使用文件操作工具

```python
# 写入配置文件
mcp.call("write_file", {
    "path": "config/app.json",
    "content": '{"name": "MyApp", "version": "1.0.0"}'
})
# → { status: "ok", action: "file_written", path: "config/app.json" }

# 读取文件内容
mcp.call("read_file", {"path": "config/app.json"})
# → { status: "ok", action: "file_read", content: "{...}" }

# 列出目录
mcp.call("list_files", {"directory": "src/components"})
# → { status: "ok", action: "files_listed", count: 15, files: [...] }
```

---

**【Loop-Harness-Agent MCP Server v1.2.1 · 智能执行器模式 · 100%测试通过】**
