# Claude Code 集成指南

> **生效日期**：2026-06-16
> **版本**：v1.0
> **目标**：在 Claude Code 中完整使用 Loop Agent 系统

---

## 一、已完成的集成

本项目已完成 Claude Code 深度集成，包含三部分：

### 1.1 方案 A：CLAUDE.md 系统规则

文件：`G:\ai-gongju\Loop-agent\CLAUDE.md`

- 触发机制（Slash Commands + 自然语言 + 无人值守）
- 激活后的强制响应流程
- 16 角色速查
- 10 相位工作流
- 3 道硬刹车
- 4 道质量门禁
- 强制行为准则
- 时间预算参数解析
- 黑板写入规则
- MCP 工具映射

### 1.2 方案 B：Slash Commands

文件：`G:\ai-gongju\Loop-agent\.claude\commands\`

| 命令 | 用途 |
|------|------|
| `/loop-agent` | 启动完整流程 |
| `/loop-agent status` | 查询状态 |
| `/loop-agent resume` | 接续未完成流程 |
| `/loop-agent abort` | 中止当前 Loop |
| `/unattended` | 无人值守模式 |
| `/spawn-agent` | 手动派发 Agent 任务 |

### 1.3 方案 C：MCP Server

文件：`G:\ai-gongju\Loop-agent\loop-agent-mcp\`

提供 6 个 MCP 工具：

| 工具 | 用途 |
|------|------|
| `mcp__loop-agent__start_loop` | 启动 Loop |
| `mcp__loop-agent__get_status` | 查询状态 |
| `mcp__loop-agent__abort_loop` | 中止 Loop |
| `mcp__loop-agent__spawn_agent` | 派发 Agent 任务 |
| `mcp__loop-agent__list_agents` | 列出 16 角色 |
| `mcp__loop-agent__save_blackboard` | 保存黑板 |

---

## 二、如何使用

### 2.1 启动 Claude Code

```bash
cd G:\ai-gongju\Loop-agent
claude
```

### 2.2 方式 1：自然语言触发

```
> 用 Loop Agent 模式开发
> 启动 Loop Agent
> 按 PRD→生产 流水线做
> 全自动化开发
> 按 16 角色团队开发
```

Claude Code 会：
1. 自动读取 `CLAUDE.md`，识别触发词
2. 调用 `mcp__loop-agent__list_agents` 确认 16 角色
3. 调用 `mcp__loop-agent__get_status` 读取黑板
4. 切换到 @Orchestrator 视角
5. 询问 PRD

### 2.3 方式 2：无人值守模式

```
> 用 Loop Agent 模式开发，今晚完成明天早上给我结果
> 进入无人值守模式
> /unattended
> 时间预算 8 小时
```

### 2.4 方式 3：Slash Commands

```
> /loop-agent
> /loop-agent status
> /loop-agent resume
> /loop-agent abort
> /unattended
> /spawn-agent
```

### 2.5 方式 4：直接调用 MCP 工具

```
> 列出所有 Agent Profile
> 调用 mcp__loop-agent__list_agents
> 查询当前 Loop 状态
> 启动 Loop，PRD 路径是 docs/todo-prd.md
> 派发 backend Agent 任务
```

---

## 三、典型使用流程

### 3.1 场景 1：开发 Todo App

```bash
# 启动 Claude Code
cd G:\ai-gongju\Loop-agent
claude

# 触发 Loop Agent
> 用 Loop Agent 模式开发

# Claude Code 输出：
✅ Loop Agent 模式已激活
✅ @Orchestrator 已就位
✅ 16 角色已确认
请提供 PRD 文档路径：

# 用户提供 PRD
> PRD 路径：docs/todo-prd.md，时间预算 8 小时

# Claude Code 调用 mcp__loop-agent__start_loop
# 自动初始化 10 相位 + 16 任务
# 切换到 @Orchestrator 视角

# 开始 Phase 1：需求基线
> 调用 mcp__loop-agent__spawn_agent，agent_type="product_manager"
> 调用 mcp__loop-agent__spawn_agent，agent_type="requirements"

# Phase 1 完成后
> 调用 mcp__loop-agent__save_blackboard 更新进度

# 查询状态
> /loop-agent status
# 或
> 调用 mcp__loop-agent__get_status
```

### 3.2 场景 2：无人值守夜间作业

```bash
# 晚上 11 点
claude
> 用 Loop Agent 模式开发，今晚完成明天早上给我结果
> PRD：docs/todo-prd.md，时间预算 9 小时

# Claude Code 激活无人值守模式
✅ 无人值守模式已激活
⏰ 时间预算：9 小时
🌙 进入夜间作业模式
6 条铁律已生效

# Claude Code 自动跑完全流程
# - 不中断原则：除非用户确认边界，不暂停
# - 完整执行：宁可慢也要完成
# - 决策可审计：所有决策记录到黑板

# 早上 8 点查看报告
> /loop-agent status
# 或查看 blackboard/项目进度记录.md
```

### 3.3 场景 3：修复 Bug

```bash
claude
> 用 Loop Agent 修复 src/api/users.ts:42 的 SQL 注入 Bug

# Claude Code：
# 1. 调用 mcp__loop-agent__list_agents 确认角色
# 2. 调用 mcp__loop-agent__spawn_agent，agent_type="tester"（复现 Bug）
# 3. 调用 mcp__loop-agent__spawn_agent，agent_type="bug_defect_repairer"（修复）
# 4. 调用 mcp__loop-agent__spawn_agent，agent_type="code_reviewer"（Gate 1 验证）
# 5. 调用 mcp__loop-agent__save_blackboard 记录修复
```

---

## 四、文件结构

```
G:\ai-gongju\Loop-agent\
├── CLAUDE.md                                 # 方案 A：系统规则
├── .claude\
│   ├── commands\                             # 方案 B：Slash Commands
│   │   ├── loop-agent.md
│   │   ├── loop-agent-status.md
│   │   ├── loop-agent-resume.md
│   │   ├── loop-agent-abort.md
│   │   ├── unattended.md
│   │   └── spawn-agent.md
│   └── mcp_servers.json                      # 方案 C：MCP Server 注册
├── loop-agent-mcp\                           # 方案 C：MCP Server 实现
│   ├── package.json
│   ├── tsconfig.json
│   ├── src\
│   │   ├── index.ts                          # MCP Server 入口
│   │   └── lib\
│   │       └── orchestrator-client.ts        # Orchestrator 封装
│   ├── dist\                                 # 编译输出
│   │   ├── index.js
│   │   └── lib\
│   │       └── orchestrator-client.js
│   └── node_modules\
└── docs\
    └── CLAUDE_CODE_INTEGRATION.md            # 本文档
```

---

## 五、验证清单

### 5.1 验证 MCP Server 启动

```bash
cd G:\ai-gongju\Loop-agent
node loop-agent-mcp\dist\index.js "G:\ai-gongju\Loop-agent"
```

应该输出：`Loop Agent MCP Server started (project: G:\ai-gongju\Loop-agent)`

### 5.2 验证 Claude Code 加载

```bash
cd G:\ai-gongju\Loop-agent
claude
```

在 Claude Code 中输入：
```
> 列出所有可用的 MCP 工具
```

应该看到 6 个 `mcp__loop-agent__*` 工具。

### 5.3 验证完整流程

```
> 用 Loop Agent 模式开发
> PRD 路径：docs/test-prd.md
> /loop-agent status
> 调用 mcp__loop-agent__list_agents
```

---

## 六、故障排查

### 6.1 Claude Code 找不到 MCP Server

**症状**：`mcp__loop-agent__*` 工具不可用

**解决**：
1. 检查 `.claude\mcp_servers.json` 路径是否正确
2. 验证 JSON 格式：`cat .claude\mcp_servers.json | python -m json.tool`
3. 手动测试 Server：`node loop-agent-mcp\dist\index.js "G:\ai-gongju\Loop-agent"`
4. 重启 Claude Code

### 6.2 MCP Server 启动失败

**症状**：`Failed to start MCP Server`

**解决**：
1. 检查 Node.js 版本：`node --version`（需要 ≥18）
2. 检查依赖：`cd loop-agent-mcp && npm install`
3. 重新编译：`npm run build`
4. 查看错误：`node dist/index.js`

### 6.3 Slash Commands 不可用

**症状**：`/loop-agent` 命令无响应

**解决**：
1. 检查 `.claude\commands\` 目录结构
2. 确认每个命令是独立的 `.md` 文件
3. 文件名必须以 `/` 后的名称命名（如 `loop-agent.md` 对应 `/loop-agent`）

### 6.4 黑板文件未创建

**症状**：`项目进度记录.md` 不存在

**解决**：
1. 调用 `mcp__loop-agent__save_blackboard` 自动创建
2. 或手动创建：`mkdir blackboard`

---

## 七、扩展开发

### 7.1 添加新工具

编辑 `loop-agent-mcp\src\index.ts`：

```typescript
// 1. 在 ListToolsRequestSchema 中添加工具定义
{
  name: "your_new_tool",
  description: "工具描述",
  inputSchema: { ... }
}

// 2. 在 CallToolRequestSchema 中添加处理逻辑
case "your_new_tool": {
  const result = await client.yourNewMethod(args);
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
}
```

### 7.2 添加新 Agent

编辑 `loop-agent-mcp\src\lib\orchestrator-client.ts`：

```typescript
// 在 listAgents() 中添加
{ id: "new_agent", display_name: "@NewAgent", layer: 5, type: "specialist", bound_skills: [] }

// 在 spawnAgent() 的 enum 中添加
"new_agent"
```

### 7.3 集成真实 LLM API

当前 `spawnAgent` 只是创建任务文件。要真实执行 Agent 任务：

```typescript
// 在 orchestrator-client.ts 中
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

async spawnAgent(agentType, taskInput) {
  // 1. 读取 Agent Profile
  const profile = await this.readAgentProfile(agentType);
  
  // 2. 调用 LLM
  const completion = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [
      { role: "system", content: profile.systemPrompt },
      { role: "user", content: JSON.stringify(taskInput) }
    ]
  });
  
  // 3. 写入结果
  // ...
}
```

---

## 八、最佳实践

### 8.1 触发时机

| 场景 | 推荐触发方式 |
|------|-------------|
| 快速开始 | `/loop-agent` |
| 复杂任务 | "用 Loop Agent 模式开发，PRD 路径 xxx" |
| 夜间作业 | "用 Loop Agent 模式开发，今晚完成明天早上给我结果" |
| 查询状态 | `/loop-agent status` |
| 修复 Bug | "用 Loop Agent 修复 xxx" |
| 性能优化 | "用 Loop Agent 模式优化 xxx" |

### 8.2 时间预算建议

| 任务复杂度 | 推荐时间预算 |
|-----------|-------------|
| 简单 Bug 修复 | 1-2 小时 |
| 小功能开发 | 4-6 小时 |
| 中等功能开发 | 6-9 小时 |
| 大型功能开发 | 12-24 小时 |
| 完整项目 | 48-72 小时 |

### 8.3 黑板更新频率

- 每个 Phase 完成后：必须更新
- 每个 Gate 完成后：必须更新
- 关键决策点：必须更新
- 异常处理后：必须更新

---

## 九、参考文档

- `CLAUDE.md` - 系统规则
- `.trae\rules\loop-agent.md` - Trae 版本主入口规则
- `docs\AUDIT_REPORT.md` - 项目审计报告
- `docs\UNATTENDED_MODE.md` - 无人值守模式
- `README.md` - Loop Agent 总览

---

**【Claude Code 集成 v1.0 · 生效中】**
