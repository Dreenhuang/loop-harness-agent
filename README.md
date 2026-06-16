# Loop-Harness-Agent

> **Loop Agent × Boss-auto-harness 融合模式**  
> 5 级封装的自动化开发引擎，让用户说一句"用 loop-harness-agent"，系统就自动按 PRD→生产 流水线跑完全流程。

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-success)

---

## 🎯 这是什么？

**Loop-Harness-Agent** 是一个把 Loop Agent 多角色协作系统与 Boss-auto-harness 融合验收标准结合的自动化开发框架。它提供了：

- **5 级分层封装**：Skill → Agent → Workflow → Domain Chip → Artifact
- **16 个角色**：@Orchestrator、@Backend、@UI-Designer 等
- **18 个原子 Skill**：含 4 道质量门禁（Gate 1-4）
- **10 相位完整工作流**：从需求到部署的全自动流水线
- **融合验收标准**：5 个顶层目标（闭环、生产级、可部署、Token 效率、流程收敛）

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Dreenhuang/loop-harness-agent.git
cd loop-harness-agent
```

### 2. 安装依赖（可选，仅当使用 MCP Server 时）

```bash
cd loop-agent-mcp
bun install
```

### 3. 触发 Loop-Harness-Agent 模式

**方式 A：斜杠命令**（在 Trae IDE 对话框输入）

```
/loop-harness-agent
```

**方式 B：自然语言**（容错识别）

```
"用 loop-harness-agent 模式开发"
"启动 LHA 模式"
"loop agent 模式启动"
"启动 Loop-Harness-Agent"
```

**支持的触发词**（大小写不敏感，格式容错）：

| 格式 | 示例 |
|------|------|
| 连字符 | `loop-harness-agent` |
| 空格 | `loop harness agent` |
| 下划线 | `loop_harness_agent` |
| 简写 | `LHA` / `lha` |
| 中文 | `Loop-Harness-Agent 模式` |

### 4. 提供 PRD

激活后，系统会询问您提供 PRD 或启动指令。

---

## 📁 项目结构

```
loop-harness-agent/
├── .trae/                      # Trae IDE 规则
│   ├── rules/                  # 规则文件
│   │   ├── loop-agent.md       # 主入口规则 v1.2
│   │   └── A2A消息速查卡.md    # A2A 协议
│   ├── agents/                 # 16 个 Agent Profile
│   ├── skills/                 # 18 个原子 Skill
│   └── workflows/              # 10 相位 + 4 Gate JSON
├── artifacts/                  # 工件与证据
│   ├── registry/               # 工件注册表
│   └── evidence/               # 证据收集器
├── blackboard/                 # 黑板系统
│   ├── templates/              # 黑板模板
│   └── state.json              # 状态文件
├── domain-chips/               # 领域芯片
│   └── web-feature-chip/       # Web 功能芯片
│       ├── chip.json
│       ├── knowledge/          # 知识库
│       └── benchmark/          # 评估基准
├── docs/                       # 文档
│   └── integration/            # 融合规范
├── loop-agent-engine/          # 引擎代码
│   ├── orchestrator.ts         # 状态机
│   ├── cli.ts                  # CLI 入口
│   └── webhook.ts              # Webhook
├── loop-agent-mcp/             # MCP Server
├── scripts/                    # 工具脚本
│   └── fusion-metrics.ts       # 融合指标采集
├── templates/                  # 9 个工件模板
├── workflows/                  # Phase/Gate JSON
├── CLAUDE.md                   # Claude Code 适配版
├── INSTALL.md                  # 安装指南
├── EXAMPLES.md                 # 使用示例
└── CHANGELOG.md                # 版本变更
```

---

## 🏗️ 5 级封装架构

```
┌─────────────────────────────────────────────────────┐
│ 第 5 层：Artifact & Evidence  ──  工件与证据地基    │
│           (artifacts/registry/ + artifacts/evidence/)│
├─────────────────────────────────────────────────────┤
│ 第 4 层：Domain Chip  ──  领域黑盒芯片              │
│           (domain-chips/web-feature-chip/)          │
├─────────────────────────────────────────────────────┤
│ 第 3 层：Workflow Blueprint  ──  多角色编排蓝图     │
│           (.trae/workflows/prd-to-production.json)  │
├─────────────────────────────────────────────────────┤
│ 第 2 层：Agent Profile  ──  单角色循环单元          │
│           (.trae/agents/*.agent.toml)               │
├─────────────────────────────────────────────────────┤
│ 第 1 层：Skill  ──  原子能力资产                    │
│           (.trae/skills/*/SKILL.md)                 │
└─────────────────────────────────────────────────────┘
```

---

## 🎭 16 角色矩阵

| 层级 | 角色 | 职责 |
|------|------|------|
| 调度 | @Orchestrator | 全局调度、任务分派 |
| 决策 | @Product-Manager | 业务决策、需求澄清 |
| 业务 | @Requirements | PRD 编写 |
| 业务 | @UX-Researcher | 交互流程 |
| 业务 | @UI-Designer | 视觉设计 |
| 技术 | @Architect | 架构设计 |
| 技术 | @Backend | 后端开发 |
| 技术 | @Fullstack-Coder | 前端开发 |
| 技术 | @Bug-Defect-Repairer | Bug 修复 |
| 质量 | @Code-Reviewer | 代码审查（Gate 1）|
| 质量 | @Professional-Performance | 性能压测（Gate 2）|
| 质量 | @全栈测试员 | 全栈测试（Gate 3）|
| 知识 | @Knowledge-Curator | 经验沉淀 |
| 交付 | @Documenter | 文档归档 |
| 交付 | @Final-Reviewer | 终审（Gate 4）|
| 交付 | @DevOps | 部署运维 |

---

## 🚦 10 相位工作流

```
Phase 0: 初始化（建黑板 + 加载资产）
    ↓
Phase 1: 需求基线 [@Product-Manager + @Requirements]
    ↓
Phase 2: 交互设计 [@UX-Researcher]
    ↓
Phase 3: 视觉设计 [@UI-Designer]
    ↓
Phase 4: 技术架构 [@Architect]
    ↓
Phase 5: 并行开发 [@Backend || @Fullstack-Coder]
    ↓
Phase 6: 多层质量门禁 [@Code-Reviewer → @Professional-Performance → @全栈测试员]
    ↓
Phase 7: 知识沉淀 [@Knowledge-Curator]
    ↓
Phase 8: 文档生成 [@Documenter]
    ↓
Phase 9: 最终终审 [@Final-Reviewer]
    ↓
Phase 10: 部署上线 [@DevOps]  🎉
```

---

## 🛡️ 4 道质量门禁

| 门禁 | 角色 | 触发条件 | 通过条件 |
|------|------|----------|----------|
| Gate 1 | @Code-Reviewer | Phase 5 完成 | 0 Blocker + 0 Major + 证据齐全 |
| Gate 2 | @Professional-Performance | Gate 1 通过 | P95 ≤ 300ms + 错误率 ≤ 0.1% |
| Gate 3 | @全栈测试员 | Gate 2 通过 | P0=0 + P1=0 + TDD 覆盖率 ≥ 80% |
| Gate 4 | @Final-Reviewer | 所有 Phase 完成 | 工件齐全 + 证据充分 + 6 项一票否决全通过 |

---

## 📚 核心文档

| 文档 | 用途 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | Claude Code 用户快速入门 |
| [INSTALL.md](INSTALL.md) | 详细安装与集成指南 |
| [EXAMPLES.md](EXAMPLES.md) | 实战使用示例 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更日志 |
| [.trae/rules/loop-agent.md](.trae/rules/loop-agent.md) | 完整模式规则 v1.2 |
| [docs/integration/融合验收标准.md](docs/integration/融合验收标准.md) | 5 个顶层目标 + 验收清单 |
| [docs/integration/boss-auto-harness-loop-mapping.md](docs/integration/boss-auto-harness-loop-mapping.md) | Phase/Step 映射表 |

---

## 🌙 无人值守模式

支持"今晚完成，明天早上给我结果"的全自动模式。

```
"用 loop-harness-agent 模式开发，今晚完成明天早上给我结果"
"进入无人值守模式"
"时间预算 9 小时"
```

6 条铁律：不中断、最小影响、完整执行、决策可审计、时间有预算、早晨有报告。

---

## 🧪 统计指标

```bash
# 运行融合验收指标采集
bun run scripts/fusion-metrics.ts
```

输出：工件完成率、证据覆盖率、TDD 执行率、审查闭环完成率、Harness 协议注入率。

---

## 🤝 贡献

欢迎贡献 Skill、Agent Profile、Domain Chip、评估基准等扩展资产。

---

## 📜 许可证

MIT License

---

## 🔗 相关项目

- **Loop Agent**：基础多角色协作系统
- **Boss-auto-harness**：融合验收标准来源
- **A2A-Agent**：A2A 通信协议

---

**【Loop-Harness-Agent v1.2 · 5级封装 · 融合验收 · 生产级交付】**
