# 使用示例

> **Loop-Harness-Agent v1.2 实战示例集**

---

## 示例 1：从零开发 Web App

### 用户输入

```
用 loop-harness-agent 模式开发一个待办事项管理 Web App，今晚完成明天早上给我结果
```

### 系统响应

```
🚀 Loop-Harness-Agent 模式已激活 v1.2
@Orchestrator 已就位
⏰ 时间预算：9 小时

正在加载 5 级封装资产...
- Skill 层：18 个 SKILL.md 已加载
- Agent 层：16 个 Agent Profile 已加载
- Workflow 层：prd-to-production.json 已加载
- Domain Chip 层：web-feature-chip 已加载
- Artifact 层：registry + evidence 已加载

🌙 检测到无人值守意图，激活 unattended-mode Skill
📋 已建立检查点 CP-001
🤖 进入 Phase 1 需求基线
```

### 推进过程

```
[2026-06-17 22:00] Phase 1 需求基线 → @Requirements
  ✅ Product-Spec.md 已创建（含 8 大功能、5 个验收点）
  
[2026-06-17 22:15] Phase 2 交互设计 → @UX-Researcher
  ✅ Design-Brief.md 已创建
  
[2026-06-17 22:30] Phase 3 视觉设计 → @UI-Designer
  ✅ UI-Design.md + Component-Library.md 已创建
  
[2026-06-17 23:00] Phase 4 架构 → @Architect
  ✅ Architecture.md + API-Spec.md 已创建
  📊 技术栈：Next.js 14 + Bun + PostgreSQL
  
[2026-06-17 23:30] Phase 5 开发 → @Backend + @Fullstack-Coder
  ✅ DEV-PLAN.md 已创建（微任务 47 个）
  ✅ 后端 API 12 个
  ✅ 前端组件 18 个
  ✅ failing_test 23 条 + passing_test 23 条
  
[2026-06-18 02:00] Gate 1 → @Code-Reviewer
  ✅ 0 Blocker + 0 Major
  ✅ TDD 证据齐全
  
[2026-06-18 02:30] Gate 2 → @Professional-Performance
  ✅ P95 = 180ms
  ✅ 错误率 = 0.02%
  
[2026-06-18 03:00] Gate 3 → @全栈测试员
  ✅ P0=0 + P1=0
  ✅ TDD 覆盖率 = 87%
  
[2026-06-18 03:30] Phase 7 知识沉淀 → @Knowledge-Curator
  ✅ 6 段式知识条目 3 条
  
[2026-06-18 04:00] Phase 8 文档 → @Documenter
  ✅ README.md + ARCHITECTURE.md + API.md + DEPLOYMENT.md
  
[2026-06-18 04:30] Phase 9 终审 → @Final-Reviewer
  ✅ 12 项强制工件齐全
  ✅ 5 类证据齐全
  ✅ 6 项一票否决全通过
  
[2026-06-18 05:00] Phase 10 部署 → @DevOps
  ✅ 已部署到 https://todoapp.renrenup.cn
  ✅ 冒烟测试通过
  ✅ Release-Notes.md 含回滚策略

🎉 任务完成（耗时 7 小时 0 分）
```

---

## 示例 2：查询当前状态

### 用户输入

```
/loop-harness-agent status
```

### 系统响应

```
📊 Loop-Harness-Agent 当前状态

【项目整体进度】
- 项目：待办事项管理 Web App
- 当前 Phase：Phase 5（开发中）
- 进度：45%
- 任务：T5-23/47

【已完成 Phase】
- ✅ Phase 0：初始化
- ✅ Phase 1：需求基线
- ✅ Phase 2：交互设计
- ✅ Phase 3：视觉设计
- ✅ Phase 4：技术架构

【进行中】
- 🔄 Phase 5：并行开发（后端 80% + 前端 60%）

【待办任务】
- T5-24: 实现标签管理 API
- T5-25: 实现标签管理 UI
- T5-26: 标签筛选功能

【风险】
- ⚠️ TDD 覆盖率 78%，需补充 5 个测试用例

【融合验收指标】
- 工件完成率：67% (8/12)
- 证据覆盖率：40% (2/5)
- TDD 执行率：78%
- Token 使用：32% (32 USD / 100 USD)
```

---

## 示例 3：接续上次未完成流程

### 用户输入

```
/loop-harness-agent resume
```

### 系统响应

```
🔄 正在从黑板恢复执行状态...

[2026-06-17 22:00] 项目：待办事项管理 Web App
[2026-06-17 22:00] 上次中断：Phase 5 T5-23
[2026-06-17 22:00] 检查点：CP-005

✅ 黑板状态已恢复
✅ 检查点 CP-005 已加载
✅ 当前上下文已重置（Ralph 模式）

📋 上次未完成任务：
- T5-24: 实现标签管理 API
- T5-25: 实现标签管理 UI

⏰ 距离时间预算结束：6 小时 30 分

🚀 继续执行 Phase 5 ...
```

---

## 示例 4：一票否决触发场景

### 场景描述

Phase 9 终审时，发现缺少 Release-Notes.md。

### 系统响应

```
🚨 [ERR] @Final-Reviewer → @Orchestrator
topic: fusion.veto.triggered
priority: 10
requiresResponse: true

payload: "一票否决：工件链不完整（缺少 Release-Notes.md），
         终审阻断。必须补充后才能继续。"

[2026-06-18 04:30] @Orchestrator → @Documenter
  触发修复动作：创建 Release-Notes.md
  
[2026-06-18 04:45] @Documenter → @Final-Reviewer
  Release-Notes.md 已创建，含部署前提、回滚策略、冒烟测试清单
  
[2026-06-18 04:50] @Final-Reviewer
  ✅ 一票否决解除
  ✅ 12 项工件全部齐全
  ✅ 进入 Phase 10 部署
```

---

## 示例 5：Token 超预算告警

### 系统响应

```
⚠️ [NOTIFY] @Orchestrator → ALL
topic: fusion.token.over_budget
priority: 10

payload: "Token 预算已达 85%，触发告警。
         当前使用：85 USD / 100 USD
         剩余任务：T5-24 ~ T5-47
         
         自动降级策略：
         1. 跳过非关键审查（UX 审查）
         2. 合并相似代码审查
         3. 使用摘要代替全量报告"

[2026-06-18 03:00] @Orchestrator
  降级生效，Token 增长曲线已趋于平缓
  预计最终使用：92 USD
```

---

## 示例 6：多语言触发测试

### 各种触发方式

```bash
# 标准触发
/loop-harness-agent

# 大小写
/LOOP-HARNESS-AGENT
/Loop-Harness-Agent

# 下划线
/loop_harness_agent

# 空格
/loop harness agent

# 简写
/LHA
/lha

# 旧名兼容
/loop-agent

# 中文自然语言
"用 Loop-Harness-Agent 模式开发"
"启动 LHA 模式"
"loop agent 模式启动"
"用循环工程开发"
"全自动化开发"
"按 PRD→生产流水线做"
```

所有上述方式都会激活 Loop-Harness-Agent 模式。

---

## 示例 7：自定义 PRD 输入

### 用户输入

```
/loop-harness-agent

PRD 位置：docs/my-todo-app.md
技术栈：Vue 3 + TypeScript + Supabase
目标用户：远程团队的知识工作者
时间预算：4 小时
```

### 系统响应

```
🚀 Loop-Harness-Agent 模式已激活 v1.2
⏰ 时间预算：4 小时
📄 PRD 位置：docs/my-todo-app.md
🔧 技术栈：Vue 3 + TypeScript + Supabase

🤖 @Orchestrator 启动调度
🧠 @Product-Manager：需求澄清开始

[第 1 问] 目标用户的核心痛点是什么？
[第 2 问] MVP 阶段必须包含哪些功能？
[第 3 问] 数据安全和隐私要求？
[第 4 问] 性能指标（P95 响应时间）？
[第 5 问] 部署环境（自托管 vs 云服务）？
...
```

---

## 示例 8：通过 MCP Server 调用

### Claude Code 中使用

```typescript
// 启动 Loop
await mcp__loop-agent__start_loop({
  prd_path: "docs/PRD.md",
  time_budget_hours: 9,
  mode: "unattended"
});

// 查询状态
const status = await mcp__loop-agent__get_status();
console.log(status.currentPhase, status.progress);

// 派发 Agent
await mcp__loop-agent__spawn_agent({
  agent_type: "backend",
  task_input: {
    phase: 5,
    task_id: "T5-BE-12",
    description: "实现用户认证 API"
  }
});

// 保存黑板
await mcp__loop-agent__save_blackboard({
  phase: "Phase 5 完成",
  completed_items: ["后端 API 12 个", "前端组件 18 个"],
  artifact_updates: {
    new_artifacts: ["DEV-PLAN.md"],
    artifact_status: { "DEV-PLAN.md": "COMPLETED" }
  },
  evidence_updates: {
    new_evidence: ["failing_test", "passing_test"]
  }
});
```

---

## 示例 9：通过 CLI 启动

```bash
# 启动 CLI
cd loop-harness-agent
bun run loop-agent-engine/cli.ts
```

```
🚀 Loop Agent CLI v1.2

> help
可用命令：
  start <prd-path>     启动 Loop
  status               查询状态
  resume               恢复执行
  abort                中止 Loop
  list-agents          列出 16 角色
  save-blackboard      保存黑板

> start docs/PRD.md
✅ Loop 已启动 (loop_id: lh-2026-06-17-001)
✅ @Orchestrator 已就位
✅ 时间预算：9 小时
✅ 无人值守模式已激活

> status
Phase 0 | 进度 100% | 任务完成
Phase 1 | 进度 100% | 任务完成
Phase 2 | 进度 100% | 任务完成
Phase 3 | 进度  45% | 进行中
```

---

## 示例 10：融合指标采集

```bash
bun run scripts/fusion-metrics.ts
```

```
═══════════════════════════════════════════════════════
  融合验收指标采集报告
═══════════════════════════════════════════════════════

📊 工件完成率: 100.0%
  ✅ Product-Spec.md: COMPLETED (Phase 1)
  ✅ Design-Brief.md: COMPLETED (Phase 2-3)
  ✅ UI-Design.md: COMPLETED (Phase 3)
  ✅ Component-Library.md: COMPLETED (Phase 3)
  ✅ Architecture.md: COMPLETED (Phase 4)
  ✅ API-Spec.md: COMPLETED (Phase 4)
  ✅ DEV-PLAN.md: COMPLETED (Phase 5)
  ✅ Quality-Check-Report.md: COMPLETED (Phase 6)
  ✅ Test-Report.md: COMPLETED (Phase 6)
  ✅ Code-Review-Report.md: COMPLETED (Phase 6)
  ✅ UX-Review-Report.md: COMPLETED (Phase 6)
  ✅ Release-Notes.md: COMPLETED (Phase 10)

📊 证据覆盖率: 100.0%
  ✅ failing_test: 23 条记录
  ✅ passing_test: 23 条记录
  ✅ refactor_evidence: 8 条记录
  ✅ verification_commands: 12 条记录
  ✅ review_feedback: 18 条记录
  ✅ deploy_smoke_test: 1 条记录
  ✅ build_verification: 1 条记录

═══════════════════════════════════════════════════════
  达标判定（对齐融合验收标准）
═══════════════════════════════════════════════════════

  ✅ 工件完成率: 100.0% (目标 ≥ 95%)
  ✅ 证据覆盖率: 100.0% (目标 ≥ 90%)

═══════════════════════════════════════════════════════
  一票否决项检查
═══════════════════════════════════════════════════════

  ✅ 工件链完整性: 通过
  ✅ 证据充分性: 通过
  ✅ Gate 不可绕过: 通过
  ✅ 黑板恢复能力: 通过
  ✅ 生产级交付: 通过
  ✅ Token 可控: 通过

  最终结论: ✅ PASS
```

---

**【Loop-Harness-Agent v1.2 · 实战示例就绪】**
