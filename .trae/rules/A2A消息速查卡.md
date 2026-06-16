# A2A 消息速查卡（Loop-Harness-Agent 版）

> **本速查卡被 Loop-Harness-Agent 系统完整继承自 A2A-Agent**
> **唯一差异**：消息接收方从 A2A Agent 名映射到 Loop-Harness-Agent 的 @角色名
> **v1.2 更新**：正式命名 loop-harness-agent，新增融合验收类 Topic + 证据/工件/偏离类消息模板

---

## 🚦 5 种消息类型（必须掌握）

| 类型 | 用途 | 模板 |
|------|------|------|
| `REQUEST` | 我请你做事 | `[REQ] 我（sender）请你（receiver）做xxx，请回 RESPONSE` |
| `RESPONSE` | 我做完了回你 | `[RESP] 我（sender）已完成xxx，结果：yyy` |
| `BROADCAST` | 通知所有人 | `[BC] 各位：xxx 已完成，请各角色按新状态工作` |
| `NOTIFICATION` | 单向通知 | `[NOTIFY] 提示：xxx（不需要回复）` |
| `ERROR` | 报错 | `[ERR] xxx 失败，原因：yyy，请 xxx 处理` |

---

## 🏷️ Topic 命名速查（domain.action.subject）

```text
# 任务类
task.requirement.collect      需求收集
task.prd.complete             PRD 完成
task.ux.design                交互设计
task.ui.design                视觉设计
task.architecture.request     请求架构设计
task.architecture.complete    架构设计完成
task.api.spec                 API 规范
task.engineer.start           工程师开始编码
task.code.review              代码审查
task.performance.test         性能压测
task.test.report              测试报告
task.knowledge.extract        知识沉淀
task.doc.generate             文档生成
task.final.review             最终终审
task.deploy.complete          部署完成

# 门禁类
gate.code.review.request      Gate 1 触发
gate.performance.request      Gate 2 触发
gate.testing.request          Gate 3 触发
gate.final.request            Gate 4 触发
gate.passed                   门禁通过
gate.failed                   门禁失败

# 记忆类
memory.agent_pm.save          保存产品经理记忆
memory.blackboard.update      更新黑板
memory.snapshot.save          保存快照
memory.knowledge.add          知识库新增

# 检查点类
checkpoint.phase_X.save       保存第 X 相位检查点
checkpoint.full.restore       完整恢复

# 错误类
error.dependency.missing      依赖缺失
error.test.failed             测试失败
error.budget.exceeded         预算超限
error.no.progress             无进展
error.gate.failed             门禁失败

# 融合验收类（v1.1 新增）
fusion.artifact.missing       强制工件缺失
fusion.evidence.insufficient  证据不充分
fusion.deviation.detected     偏离检测
fusion.target.not_met         融合目标未达成
fusion.veto.triggered         一票否决触发
fusion.recovery.action        恢复动作执行
fusion.token.over_budget      Token 超预算
fusion.demo_as_production     demo 级伪装生产级
```

---

## 👥 角色分工速查（Loop Agent 16 角色）

| 角色（@调用） | 职责 | 接收 Topic 前缀 | 主要输出节点 |
|----------------|------|------------------|---------------|
| **@Orchestrator** | 全局调度、任务分派 | ALL | - |
| **@Product-Manager** | 产品规划、业务决策 | `task.requirement.*` `memory.agent_pm.*` | PRD |
| **@Requirements** | 需求细化、PRD 编写 | `task.requirement.*` | PRD |
| **@UX-Researcher** | 交互流程、用户旅程 | `task.ux.*` | UX |
| **@UI-Designer** | 视觉设计、组件库 | `task.ui.*` | UI |
| **@Architect** | 架构设计、技术选型 | `task.architecture.*` `task.api.*` | Architecture / API |
| **@Backend** | 后端服务、API、数据库 | `task.engineer.start (后端)` | Code / DB / API |
| **@Fullstack-Coder** | 前端页面、组件 | `task.engineer.start (前端)` | Code |
| **@Bug-Defect-Repairer** | Bug 修复、故障应急 | `error.*` `task.bug.*` | Code |
| **@Code-Reviewer** | 代码审查、Gate 1 | `gate.code.review.*` `task.code.review` | Gate |
| **@Professional-Performance** | 性能压测、Gate 2 | `gate.performance.*` `task.performance.*` | Gate / Test |
| **@全栈测试员** | 全栈测试、Gate 3 | `gate.testing.*` `task.test.*` | Test |
| **@Knowledge-Curator** | 知识沉淀、6 段式教程 | `task.knowledge.*` `memory.knowledge.*` | Knowledge |
| **@Documenter** | 全文档归档 | `task.doc.*` | DOC |
| **@Final-Reviewer** | 最终终审、Gate 4 | `gate.final.*` `task.final.*` | Gate |
| **@DevOps** | 部署、CI/CD、运维 | `task.deploy.*` | Config |

---

## 📊 12 种节点类型 + 5 种状态

### 节点类型（Loop Agent 扩展版）

| 类型 | 含义 | 创建角色 |
|------|------|----------|
| `PRD` | 需求文档 | @Requirements |
| `UX` | 交互设计 | @UX-Researcher |
| `UI` | 视觉设计 | @UI-Designer |
| `Architecture` | 架构设计 | @Architect |
| `API` | 接口文档 | @Backend / @Architect |
| `Code` | 源代码 | @Backend / @Fullstack-Coder |
| `DB` | 数据库 | @Backend |
| `Config` | 配置文件 | @DevOps |
| `Test` | 测试报告 | @全栈测试员 |
| `Gate` | 门禁报告 | 4 个门禁角色 |
| `Knowledge` | 知识条目 | @Knowledge-Curator |
| `DOC` | 项目文档 | @Documenter |

### 节点状态

- ✅ `completed` 已完成
- 🔄 `in_progress` 进行中
- ⏳ `pending` 待创建
- 🚫 `blocked` 被阻塞
- ❌ `failed` 失败

---

## 🔗 4 种依赖关系

| 关系 | 含义 | 示例 |
|------|------|------|
| `informs` | A 为 B 提供信息 | PRD `informs` Architecture |
| `depends_on` | B 依赖 A | Code `depends_on` Architecture |
| `extends` | B 是 A 的扩展 | DetailPage `extends` BasePage |
| `replaces` | B 替换 A | NewAPI `replaces` OldAPI |

---

## 🛠️ 快捷模板（直接复制使用）

### 模板 1：发起需求（@Orchestrator → @Requirements）

```text
[REQ] @Orchestrator → @Requirements
topic: task.requirement.collect
payload: "PRD 输入位于 docs/prd.md，请基于此生成结构化需求基线"
priority: 8
requiresResponse: true
```

### 模板 2：完成任务（@Requirements → @Orchestrator）

```text
[RESP] @Requirements → @Orchestrator
topic: task.prd.complete
payload: "需求基线完成，详见 docs/requirements-v1.0.md，含 23 个验收点"
priority: 6
requiresResponse: false
```

### 模板 3：广播开工（@Architect → ALL）

```text
[BC] @Architect → ALL
topic: task.engineer.start
payload: "架构已确定（Vue3 + Bun + PostgreSQL），@Backend 和 @Fullstack-Coder 可以开始编码"
priority: 9
requiresResponse: false
```

### 模板 4：报错（@Backend → @Architect）

```text
[ERR] @Backend → @Architect
topic: error.dependency.missing
payload: "/api/login 接口需要 Supabase Auth 集成，架构文档未明确 token 刷新策略"
priority: 10
requiresResponse: true
```

### 模板 5：门禁失败（@Code-Reviewer → @Backend）

```text
[ERR] @Code-Reviewer → @Backend
topic: gate.code.review.failed
payload: "发现 1 个 Blocker 级别安全漏洞（SQL 注入风险在 src/api/users.ts:42），请立即修复"
priority: 10
requiresResponse: true
```

### 模板 6：知识沉淀（@Knowledge-Curator → ALL）

```text
[NOTIFY] @Knowledge-Curator → ALL
topic: memory.knowledge.add
payload: "新知识条目已入库：SQL 注入防护 6 段式教程（位于 docs/knowledge/sql-injection-prevention.md）"
priority: 3
requiresResponse: false
```

### 模板 7：工件缺失告警（@Orchestrator → @对应角色）（v1.1 新增）

```text
[ERR] @Orchestrator → @Backend
topic: fusion.artifact.missing
payload: "Phase 5 完成但缺少 DEV-PLAN.md，请补充后重新提交"
priority: 9
requiresResponse: true
```

### 模板 8：证据不充分阻断（@Code-Reviewer → @Backend）（v1.1 新增）

```text
[ERR] @Code-Reviewer → @Backend
topic: fusion.evidence.insufficient
payload: "Gate 1 审查缺少 failing_test + passing_test 证据，无法判定 TDD 合规，请补充证据"
priority: 9
requiresResponse: true
```

### 模板 9：偏离检测告警（@Orchestrator → ALL）（v1.1 新增）

```text
[BC] @Orchestrator → ALL
topic: fusion.deviation.detected
payload: "检测到目标偏离：当前输出为 demo 级但标记为生产级，回到 Phase 5 修复"
priority: 10
requiresResponse: false
```

### 模板 10：一票否决触发（@Final-Reviewer → @Orchestrator）（v1.1 新增）

```text
[ERR] @Final-Reviewer → @Orchestrator
topic: fusion.veto.triggered
payload: "一票否决：工件链不完整（缺少 Quality-Check-Report.md + Release-Notes.md），终审阻断"
priority: 10
requiresResponse: true
```

---

## ⚡ Loop-Harness-Agent 与黑板配合的 5 条铁律

1. **每轮 Loop 完成 → 立即更新 `项目进度记录.md`**
2. **切换模型 / 新开会话 → 强制读取 `项目进度记录.md` 后再启动 Loop**
3. **触发 Loop-Harness-Agent → 强制读取黑板 + 加载 5 级封装资产**
4. **每完成一个 Phase → 强制更新知识图谱 + 状态快照 + 工件注册表 + 证据收集器**
5. **门禁失败 → 强制回到 Phase 5 修复，绝不允许绕过**

---

## 📋 完整规则位置

| 文档 | 路径 |
|------|------|
| **Loop-Harness-Agent 主入口** | `.trae/rules/loop-agent.md` |
| **A2A 全局规则 v2.1** | `全局规则_v2.1_黑板增强版.md` |
| **问题解决经验模板** | `docs/问题解决经验教程/` |
| **黑板模板** | `项目进度记录.md` |
| **Agent Profile** | `.trae/agents/*.agent.toml` |
| **Skill 资产库** | `.trae/skills/*/SKILL.md` |
| **Workflow 蓝图** | `.trae/workflows/prd-to-production.json` |
| **Domain Chip** | `domain-chips/web-feature-chip/chip.json` |
| **工件模板** | `templates/*.md` |
| **工件注册表** | `artifacts/registry/` |
| **证据收集器** | `artifacts/evidence/` |
| **引擎代码** | `loop-agent-engine/` |
| **MCP Server** | `loop-agent-mcp/` |
| **融合验收标准** | `docs/integration/融合验收标准.md` |

---

**【Loop-Harness-Agent 模式 v1.2 · A2A 协议就绪 · 融合 Boss-auto-harness】**
