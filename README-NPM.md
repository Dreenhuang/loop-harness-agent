# Loop-Harness-Agent · npm 包使用指南

> 版本：v1.2.0
> 适用：Loop-Harness-Agent × Boss-auto-harness 融合模式

## 安装

```bash
# 全局安装
npm install -g loop-agent

# 或本地项目内
npm install --save-dev loop-agent
```

## 快速开始

```bash
# 1. 初始化项目骨架
npx loop-agent init

# 2. 写入 PRD
$EDITOR ./blackboard/input/prd.md

# 3. 启动 10 相位流水线
npx loop-agent loop

# 4. 查询进度
npx loop-agent status

# 5. 中止（如需）
npx loop-agent abort
```

## 子命令

| 命令 | 作用 |
|------|------|
| `loop-agent init` | 在当前目录创建 `blackboard/` `loop-agent-engine/` `.trae/rules/` 骨架 |
| `loop-agent loop` | 启动 Orchestrator 状态机，调度 10 相位流水线 |
| `loop-agent status` | 读取 `blackboard/state.json`，输出当前 Loop 状态 |
| `loop-agent abort` | 将 `state.json` 标记为 `aborted` |
| `loop-agent version` | 输出版本与包根路径 |

## 文件结构（init 后）

```
.
├── blackboard/
│   ├── input/                    # PRD 输入
│   ├── tasks/                    # 任务状态
│   ├── state.json                # 状态机持久化（由 loop 写入）
│   └── templates/
│       └── 项目进度记录.md       # 黑板
├── loop-agent-engine/
│   ├── orchestrator.ts           # 状态机 + 派发
│   ├── agent-worker.ts           # 子进程 worker
│   ├── autoloop.ts               # 自进化 POC
│   └── __tests__/                # vitest 单元测试
├── .trae/rules/
│   └── loop-agent.md             # 触发规则
└── LOOP_AGENT_README.md
```

## 测试

```bash
npm test
# 52+ 用例，覆盖状态机 / 4 道门禁 / Harness 协议 / Autoloop 护栏
```

## 16 角色 × 10 相位 × 4 道门禁

详见：[loop-agent-engine/orchestrator.ts](./loop-agent-engine/orchestrator.ts)

## 故障排查

| 问题 | 解决 |
|------|------|
| `npx: command not found` | 升级 Node 至 ≥ 18 |
| 状态机不推进 | 删除 `blackboard/state.json` 后重新 `loop-agent loop` |
| MCP Server 无法启动 | `cd loop-agent-mcp && npm install && npx tsx src/index.ts` |

## 链接

- [融合验收标准](./docs/integration/融合验收标准.md)
- [跨项目指南](./docs/CROSS_PROJECT_GUIDE.md)
- [成熟度自评](./docs/MATURITY_ASSESSMENT.md)
