# Loop Agent MCP 工具链

> **版本**：v1.0
> **生效日期**：2026-06-15
> **对齐**：Trae Solo 工程实现指南 第七章

---

## 一、4 个 MCP Server 概览

| MCP Server | 文件 | 用途 | 强制 |
|------------|------|------|------|
| **filesystem** | `filesystem.mcp.json` | Blackboard 文件系统访问 | ✅ 必需 |
| **git** | `git.mcp.json` | Git 操作（commit/diff/worktree） | ⚪ 可选 |
| **shell** | `shell.mcp.json` | Shell 命令执行（沙箱） | ⚪ 可选 |
| **testing** | `testing.mcp.json` | 测试 + 性能压测 | ⚪ 可选 |

---

## 二、权限矩阵（按 Agent 维度）

| Agent | filesystem | git | shell | testing |
|-------|-----------|-----|-------|---------|
| `@Orchestrator` | read_write | read | read | read |
| `@Product-Manager` | read_write | none | none | none |
| `@Requirements` | read_write | none | none | none |
| `@UX-Researcher` | read_write | none | none | none |
| `@UI-Designer` | read_write | none | none | none |
| `@Architect` | read_write | read | none | none |
| `@Backend` | read_write | read_write | read_write | read_write |
| `@Fullstack-Coder` | read_write | read_write | read_write | read_write |
| `@Bug-Defect-Repairer` | read_write | read_write | read_write | read_write |
| `@Code-Reviewer` | **read_only** | none | none | read_write |
| `@Professional-Performance` | **read_only** | none | read_write | read_write |
| `@全栈测试员` | **read_only** | none | read_write | read_write |
| `@Knowledge-Curator` | read_write | none | none | none |
| `@Documenter` | read_write | none | none | none |
| `@Final-Reviewer` | **read_only** | none | none | read |
| `@DevOps` | read_write | read_write | read_write | read_write |

### 2.1 关键设计原则

- **Maker-Checker 分离**：4 个门禁角色（Code-Reviewer / Performance / Tester / Final-Reviewer）均为**只读 filesystem**，禁止修改代码
- **唯一全权限**：`@DevOps` 在部署阶段拥有全部权限
- **中间权限**：`@Backend` / `@Frontend` / `@Bug-Defect-Repairer` 在开发/修复阶段拥有读写权限

---

## 三、安全护栏

### 3.1 Shell 沙箱

- ✅ 沙箱模式启用
- ✅ 300 秒超时
- ✅ 2GB 内存限制
- ✅ 白名单命令（bun/npm/node/git/docker/...）
- ❌ 黑名单命令（`rm -rf /`、format、shutdown、fork 炸弹等）
- ❌ 禁止访问系统目录

### 3.2 Git 护栏

- ❌ 禁止 `git push --force`
- ❌ 禁止 `git reset --hard`
- ❌ 禁止 `git clean -fd`
- ❌ 禁止删除 main/master 分支

---

## 四、使用方式

### 4.1 Trae IDE 自动加载

`trae.toml` 中已配置 MCP servers，Trae 启动时自动加载。

### 4.2 手动启动（调试用）

```bash
# 启动 filesystem MCP
npx -y @modelcontextprotocol/server-filesystem ./blackboard

# 启动 git MCP
npx -y @modelcontextprotocol/server-git --repository .

# 启动 shell MCP（受限）
npx -y @modelcontextprotocol/server-shell --sandbox

# 启动 testing MCP
npx -y @modelcontextprotocol/server-testing
```

---

## 五、与黑板 + A2A 协同

```
┌────────────────────────────────────────────────┐
│  Agent 调用 MCP 工具                            │
│    ↓                                            │
│  MCP Server 执行（沙箱）                        │
│    ↓                                            │
│  操作结果写入 blackboard/                       │
│    ↓                                            │
│  其他 Agent 通过黑板读取结果                    │
└────────────────────────────────────────────────┘
```

**铁律**：Agent 通过 MCP 操作的结果必须写回黑板，**禁止 Agent 之间直接通信**。

---

## 六、版本演进

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v1.0 | 2026-06-15 | 初始版本：4 个 MCP（filesystem/git/shell/testing）+ 权限矩阵 |

---

**【Loop Agent MCP v1.0 · 4 个 Server 就绪】**
