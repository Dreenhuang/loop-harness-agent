# 安装指南

> **Loop-Harness-Agent v1.2 详细安装与集成文档**

---

## 一、环境要求

### 1.1 必装依赖

| 依赖 | 版本要求 | 用途 | 安装方式 |
|------|----------|------|----------|
| **Git** | ≥ 2.30 | 代码克隆 | https://git-scm.com |
| **Trae IDE** | 最新版 | 使用规则触发 | https://trae.ai |
| **Bun** | ≥ 1.0 | 引擎运行时 | `curl -fsSL https://bun.sh/install \| bash` |

### 1.2 可选依赖

| 依赖 | 用途 |
|------|------|
| Node.js ≥ 18 | 替代 Bun（部分场景） |
| TypeScript ≥ 5.0 | 类型检查 |
| Docker | 容器化部署 |

---

## 二、安装方式

### 方式 1：完整克隆（推荐用于试用）

```bash
# 1. 克隆仓库
git clone https://github.com/Dreenhuang/loop-harness-agent.git
cd loop-harness-agent

# 2. （可选）安装 MCP Server 依赖
cd loop-agent-mcp
bun install
cd ..

# 3. 验证安装
ls .trae/rules/loop-agent.md
```

### 方式 2：作为 Trae IDE 规则集成到现有项目

```bash
# 在你的项目根目录执行
PROJECT_DIR=$(pwd)

# 克隆到临时目录
git clone https://github.com/Dreenhuang/loop-harness-agent.git /tmp/lha

# 复制核心资产
cp -r /tmp/lha/.trae $PROJECT_DIR/
cp -r /tmp/lha/artifacts $PROJECT_DIR/
cp -r /tmp/lha/templates $PROJECT_DIR/
cp -r /tmp/lha/domain-chips $PROJECT_DIR/
cp -r /tmp/lha/blackboard $PROJECT_DIR/

# 复制文档
cp /tmp/lha/CLAUDE.md $PROJECT_DIR/
cp -r /tmp/lha/docs/integration $PROJECT_DIR/docs/

# 清理
rm -rf /tmp/lha

echo "✅ Loop-Harness-Agent 集成完成"
```

### 方式 3：仅复制规则文件（最小化集成）

```bash
# 仅复制 .trae 目录
cp -r /path/to/loop-harness-agent/.trae <your-project>/
```

适用于：只想使用规则触发能力，不需要工件模板和引擎。

### 方式 4：作为 MCP Server 全局安装

```bash
# 克隆
git clone https://github.com/Dreenhuang/loop-harness-agent.git
cd loop-harness-agent/loop-agent-mcp

# 安装依赖
bun install

# 全局链接
npm link

# 验证
which loop-agent-mcp
```

---

## 三、Trae IDE 集成

### 3.1 项目级集成

1. 打开 Trae IDE
2. 打开项目根目录
3. 确保 `.trae/` 目录在项目根目录
4. Trae IDE 会自动加载规则

### 3.2 验证集成

在 Trae IDE 对话框输入：

```
/loop-harness-agent
```

预期响应：

```
🚀 Loop-Harness-Agent 模式已激活 v1.2
@Orchestrator 已就位
正在加载 5 级封装资产...
- Skill 层：18 个 SKILL.md 已加载
- Agent 层：16 个 Agent Profile 已加载
- Workflow 层：prd-to-production.json 已加载
- Domain Chip 层：web-feature-chip 已加载
- Artifact 层：registry + evidence 已加载
```

### 3.3 触发词测试

| 输入 | 预期 |
|------|------|
| `/loop-harness-agent` | ✅ 激活 |
| `/loop-harness-agent status` | ✅ 显示状态 |
| `loop-harness-agent` | ✅ 激活（自然语言）|
| `Loop-Harness-Agent` | ✅ 激活（大小写不敏感）|
| `LOOP_HARNESS_AGENT` | ✅ 激活（下划线）|
| `LHA` | ✅ 激活（简写）|
| `loop agent` | ✅ 激活（兼容旧名）|

---

## 四、Claude Code 集成

### 4.1 复制 CLAUDE.md

将 `CLAUDE.md` 复制到项目根目录，Claude Code 会自动识别为项目规则。

```bash
cp CLAUDE.md <your-project>/
```

### 4.2 调用 MCP 工具

Claude Code 可以通过 MCP 调用 6 个工具：

```typescript
// 启动 Loop
mcp__loop-agent__start_loop({
  prd_path: "docs/PRD.md",
  time_budget_hours: 9,
  mode: "interactive"
})

// 查询状态
mcp__loop-agent__get_status()

// 派发 Agent
mcp__loop-agent__spawn_agent({
  agent_type: "backend",
  task_input: { phase: 5, task_id: "T5-1" }
})
```

---

## 五、命令行使用

### 5.1 启动 CLI 入口

```bash
cd loop-harness-agent
bun run loop-agent-engine/cli.ts
```

### 5.2 启动 Webhook 服务

```bash
cd loop-harness-agent
bun run loop-agent-engine/webhook.ts
```

默认端口：`3000`

### 5.3 启动 MCP Server

```bash
cd loop-agent-mcp
bun run dev
```

---

## 六、验证安装

运行以下命令验证所有组件就位：

```bash
# 1. 检查目录结构
test -d .trae/rules && echo "✅ .trae/rules" || echo "❌ 缺失 .trae/rules"
test -d .trae/agents && echo "✅ .trae/agents" || echo "❌ 缺失 .trae/agents"
test -d .trae/skills/core && echo "✅ .trae/skills" || echo "❌ 缺失 .trae/skills"
test -d artifacts/registry && echo "✅ artifacts/registry" || echo "❌ 缺失 artifacts/registry"
test -d artifacts/evidence && echo "✅ artifacts/evidence" || echo "❌ 缺失 artifacts/evidence"
test -d templates && echo "✅ templates" || echo "❌ 缺失 templates"
test -d domain-chips && echo "✅ domain-chips" || echo "❌ 缺失 domain-chips"

# 2. 统计文件数量
echo "Agent Profile: $(ls .trae/agents/*.toml | wc -l) 个"
echo "Skill: $(find .trae/skills/core -name SKILL.md | wc -l) 个"
echo "工件模板: $(ls templates/*.md | wc -l) 个"

# 3. 验证 JSON 文件
for f in .trae/workflows/prd-to-production.json domain-chips/web-feature-chip/chip.json; do
  node -e "JSON.parse(require('fs').readFileSync('$f','utf8'))" && echo "✅ $f" || echo "❌ $f"
done
```

预期输出：

```
✅ .trae/rules
✅ .trae/agents
✅ .trae/skills
✅ artifacts/registry
✅ artifacts/evidence
✅ templates
✅ domain-chips
Agent Profile: 16 个
Skill: 18 个
工件模板: 9 个
✅ .trae/workflows/prd-to-production.json
✅ domain-chips/web-feature-chip/chip.json
```

---

## 七、卸载

```bash
# 删除项目目录
rm -rf loop-harness-agent

# 或仅删除 Trae 规则
rm -rf .trae
```

---

## 八、常见问题

### Q1：触发不生效怎么办？

A：检查 `.trae/rules/loop-agent.md` 是否在项目根目录的 `.trae/rules/` 下。

### Q2：MCP Server 启动失败？

A：检查 Bun 是否安装：`bun --version`，并重新运行 `bun install`。

### Q3：如何升级到新版本？

A：
```bash
cd loop-harness-agent
git pull origin master
```

### Q4：能否修改触发词？

A：可以。编辑 `.trae/rules/loop-agent.md` 的 1.1 和 1.2 章节。

### Q5：能否新增自定义 Agent？

A：可以。在 `.trae/agents/` 下新增 `*.agent.toml` 文件。

---

## 九、技术支持

- **GitHub Issues**：https://github.com/Dreenhuang/loop-harness-agent/issues
- **文档**：[docs/](docs/)
- **融合验收标准**：[docs/integration/融合验收标准.md](docs/integration/融合验收标准.md)

---

**【Loop-Harness-Agent v1.2 · 安装就绪】**
