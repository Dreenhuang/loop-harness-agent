# Loop-Harness-Agent 模式 · Claude Code 适配版 v1.2

> **正式命名**：loop-harness-agent（Loop Agent × Boss-auto-harness 融合模式）
> **来源**：从 G:\ai-gongju\Loop-agent\ 移植
> **目标**：在 Claude Code 中复用 Loop-Harness-Agent 全套模式
> **生效日期**：2026-06-17
> **融合版本**：v1.2（正式命名 loop-harness-agent + 5 级封装）
> **融合验收标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md`

---

## 一、触发机制

### 1.1 显式触发（Slash Commands）

| 命令 | 含义 | 默认行为 |
|------|------|----------|
| `/loop-harness-agent` | 启动完整 Loop-Harness-Agent 流程 | 调用 `mcp__loop-agent__start_loop` |
| `/loop-harness-agent status` | 查询当前状态 | 调用 `mcp__loop-agent__get_status` |
| `/loop-harness-agent resume` | 接续上次未完成流程 | 调用 `mcp__loop-agent__start_loop`（resume 模式）|
| `/loop-harness-agent abort` | 中止当前 Loop | 调用 `mcp__loop-agent__abort_loop` |
| `/loop-agent` | 兼容旧命令 | 同 `/loop-harness-agent` |
| `/unattended` | 无人值守模式 | 调用 `mcp__loop-agent__start_loop`（unattended 模式）|
| `/spawn-agent` | 手动派发 Agent 任务 | 调用 `mcp__loop-agent__spawn_agent` |

### 1.2 隐式触发（自然语言）

以下表述**任意一条**命中即激活 Loop-Harness-Agent 模式（大小写不敏感，格式容错）：

**主触发词**：
```
- "loop-harness-agent"
- "loop harness agent"
- "loop_harness_agent"
- "loopharnessagent"
- "LHA"
```

**中文触发词**：
```
- "用 Loop-Harness-Agent 模式开发"
- "启动 Loop-Harness-Agent"
- "用 Loop Agent 模式开发"
- "启动 Loop Agent"
- "按 Loop Engineering 流程做"
- "按 PRD→生产 流水线做"
- "全自动化开发"
- "按 16 角色团队开发"
- "按照 Agent Loop 模式"
- "Loop 模式启动"
- "走 Loop Agent 流程"
- "用循环工程开发"
- "用 Harness Engineering 模式"
- "融合模式开发"
- "Harness 模式"
```

**容错匹配规则**：
- 大小写不敏感：`LOOP-HARNESS-AGENT`、`Loop-Harness-Agent` 均可触发
- 连字符容错：`loop harness agent`（空格）、`loop_harness_agent`（下划线）均可触发
- 简写容错：`loop agent`、`LHA`、`lha` 均可触发

### 1.3 无人值守模式触发

```
- "用 Loop Agent 模式开发，今晚完成明天早上给我结果"
- "进入无人值守模式"
- "今晚完成，明天早上给我结果"
- "通宵跑"
- "Auto Mode"
- "set it and forget it"
- "时间预算 X 小时"
```

---

## 二、激活后的强制响应

**触发后必须按以下顺序执行（不可跳步）**：

```
【第 1 步】识别触发源
    ├─ 斜杠命令 → 解析参数
    ├─ 自然语言 → 确认触发词命中
    └─ 提取时间预算参数（如有）

【第 2 步】调用 MCP 工具初始化
    ├─ 调用 mcp__loop-agent__list_agents 确认 16 角色就位
    ├─ 读取 <项目根>/项目进度记录.md（黑板）
    └─ 如不存在 → 调用 mcp__loop-agent__save_blackboard 初始化

【第 3 步】调用 mcp__loop-agent__start_loop
    ├─ 参数：prd_path, time_budget_hours, mode
    └─ 返回：loop_id, initial_status

【第 4 步】切换到 @Orchestrator 视角
    ├─ 输出："@Orchestrator 已就位"
    ├─ 输出："⏰ 时间预算：X 小时"（如已提取）
    ├─ 调用 mcp__loop-agent__get_status 查询当前状态
    └─ 询问用户："请提供 PRD 或确认启动 Phase 0"
```

---

## 三、16 角色速查（@调用）

| 层级 | 角色 | 职责 | 关键 Skills |
|------|------|------|-------------|
| 调度 | @Orchestrator | 总控调度、任务分派 | budget-track, progress-detect, state-snapshot |
| 决策 | @Product-Manager | 业务决策、需求澄清 | knowledge-extract |
| 业务 | @Requirements | PRD 编写、需求基线 | bug-triaging |
| 业务 | @UX-Researcher | 交互流程、用户旅程 | - |
| 业务 | @UI-Designer | 视觉设计、组件库 | - |
| 技术 | @Architect | 架构设计、技术选型 | orchestrate-map-reduce |
| 技术 | @Backend | 后端开发、API、数据库 | gate1-code-review, progress-detect |
| 技术 | @Fullstack-Coder | 前端开发、页面、组件 | gate1-code-review |
| 技术 | @Bug-Defect-Repairer | Bug 定位修复 | bug-triaging, gate1-code-review |
| 质量 | @Code-Reviewer | 代码审查（Gate 1）| gate1-code-review |
| 质量 | @Professional-Performance | 性能压测（Gate 2）| gate2-performance |
| 质量 | @全栈测试员 | 全栈测试（Gate 3）| gate3-testing, bug-triaging |
| 知识 | @Knowledge-Curator | 经验沉淀、知识库 | knowledge-extract |
| 交付 | @Documenter | 全文档归档 | - |
| 交付 | @Final-Reviewer | 终审、Gate 4 | gate4-final |
| 交付 | @DevOps | 部署、CI/CD、运维 | progress-detect |

调用 Agent 时使用 `mcp__loop-agent__spawn_agent`，参数：
- `agent_type`: 角色名（如 "backend", "code-reviewer"）
- `task_input`: 任务输入（PRD 路径、Phase 编号、依赖任务 ID）

---

## 四、10 相位工作流

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
Phase 5: 并行开发 [@Backend || @Fullstack-Coder]  ◀─── 并行扇出
    ↓
Phase 6: 多层质量门禁 [@Code-Reviewer → @Professional-Performance → @全栈测试员]
    ↓
Phase 7: 知识沉淀 [@Knowledge-Curator]
    ↓
Phase 8: 文档生成 [@Documenter]
    ↓
Phase 9: 最终终审 [@Final-Reviewer]   ◀─── Gate 4
    ↓
Phase 10: 部署上线 [@DevOps]  🎉
```

每完成一个 Phase → 调用 `mcp__loop-agent__save_blackboard` 更新黑板。

---

## 五、3 道硬刹车（全局护栏）

```yaml
global_guardrails:
  max_iterations: 200          # 第 1 道：最大迭代次数
  max_budget_usd: 100.0        # 第 2 道：Token 预算上限
  no_progress_detection: 3     # 第 3 道：连续 3 轮无进展即停
  max_attempts_per_task: 3     # 单任务最多重试 3 次
  loud_failure_only: true      # 禁止静默失败
```

**调用 `mcp__loop-agent__get_status` 时检查：**
- 如果 `budget_used > 80%` → 警告
- 如果 `budget_used > 95%` → 停止
- 如果 `iterations >= 200` → 紧急停止

---

## 六、4 道质量门禁

| 门禁 | 角色 | 通过条件 | 不通过处理 |
|------|------|----------|------------|
| Gate 1 | @Code-Reviewer | 0 Blocker + 0 Major | → @Bug-Defect-Repairer |
| Gate 2 | @Professional-Performance | P95 ≤ 300ms + 错误率 ≤ 0.1% | → @Bug-Defect-Repairer |
| Gate 3 | @全栈测试员 | P0=0 + P1=0 + P2≤3 | → @Bug-Defect-Repairer |
| Gate 4 | @Final-Reviewer | 风险等级 ≤ LOW | 回到对应 Phase |

**调用 `mcp__loop-agent__spawn_agent` 时检查：**
- 如果 Phase 5 完成后 → 必须先调用 `mcp__loop-agent__spawn_agent` with `agent_type="code-reviewer"`（Gate 1）
- 通过后才能进入 Phase 6

---

## 七、强制行为准则

### ✅ 必须做
1. 触发后 → 强制调用 `mcp__loop-agent__list_agents` 确认 16 角色就位
2. 触发后 → 强制读取黑板（调用 `mcp__loop-agent__get_status` 间接读取）
3. 每完成一个 Phase → 强制调用 `mcp__loop-agent__save_blackboard` 更新黑板
4. 任务失败 → 强制 Loud Failure（绝不允许静默替代）
5. 门禁不通过 → 强制回到 Phase 5 修复
6. 超出预算 → 强制调用 `mcp__loop-agent__abort_loop` 并输出报告
7. **强制工件齐全后才能进入终审**（缺少 Product-Spec.md、DEV-PLAN.md、Quality-Check-Report.md、Test-Report.md、Release-Notes.md 等关键工件时不得放行）
8. **强制证据齐全后才能宣告完成**（缺少 failing_test、passing_test、verification_commands、review_feedback 等关键证据时不得放行）
9. **强制执行 Token 治理**（黑板优先、工件优先、摘要优先、增量优先，防止上下文膨胀）
10. **强制执行防偏离检查**（每轮 Loop 必须确认目标一致性、Phase 一致性、角色一致性、结果一致性）

### ❌ 禁止做
1. 禁止 Orchestrator 做领域推理（只路由）
2. 禁止生成者验证自己（Maker-Checker 分离）
3. 禁止 Agent 直接通信（必须经黑板）
4. 禁止静默失败或占位替代
5. 禁止无停止条件的死循环
6. 禁止绕过门禁
7. 禁止在 MCP 工具调用之外直接修改 blackboard/ 目录
8. **禁止缺证据宣告完成**
9. **禁止输出 demo 级结果却标记为生产级交付**
10. **禁止在缺少部署前提、回滚说明、环境变量说明时宣称"可直接部署"**
11. **禁止重复分析、重复生成、重复失败却无恢复动作**
12. **禁止角色越权替代其他角色的核心职责**

### 融合执行纪律（v1.1 新增）

1. **需求阶段 → 强制澄清**：苏格拉底式需求澄清，一次一问，必须探索 2-3 个替代方案
2. **计划阶段 → 强制微任务化**：进入开发前，必须形成可执行的微任务级计划（2-5 分钟粒度）
3. **开发阶段 → 强制 TDD 证据化**：关键新功能不得跳过 failing test → passing test → refactor 的最小闭环
4. **完成声明前 → 强制 Fresh Evidence**：任何"已完成""已通过""可发布"声明前，必须有当场验证证据
5. **审查阶段 → 强制反馈闭环**：代码审查反馈必须逐项回应、逐项修复、逐项复核
6. **发布前 → 强制部署完备性**：缺少部署脚本、部署说明、环境变量说明、回滚说明时，不得宣告"可直接部署"

### 一票否决项（v1.1 新增）

命中以下任一情况，当前融合流程必须立即阻断：
1. 无法稳定生成完整工件链
2. Gate 可被绕过或存在无证据放行
3. 无法在失败后基于黑板恢复执行
4. 输出仍停留在 demo 级，却宣称满足生产级交付
5. Token 消耗明显失控且无法通过摘要/增量/回退策略收敛
6. 无人值守模式下出现长时间空转、重复执行或伪完成

---

## 八、时间预算参数解析

```yaml
# 显式时间预算
- "时间预算 X 小时"    → max_duration_hours = X
- "X 小时"              → max_duration_hours = X

# 隐式（基于时间场景）
- "今晚完成"            → 9 小时
- "明天早上给我结果"    → 9 小时
- "通宵跑"              → 8 小时
- "auto-overnight"      → 8 小时
- "午饭前完成"          → 4 小时
- "下午完成"            → 6 小时
- "周末前完成"          → 48 小时

# 默认（无时间指定）
- 默认                  → 9 小时
```

**调用 `mcp__loop-agent__start_loop` 时传递：**
- `time_budget_hours`: 解析后的数字

---

## 九、黑板写入规则

每完成一个 Phase 或修复一个 Bug，调用 `mcp__loop-agent__save_blackboard`：

```typescript
{
  "phase": "Phase 5 完成",
  "completed_items": ["后端 API 实现", "前端组件开发"],
  "uncertain_items": ["性能是否达标"],
  "open_issues": ["需要优化数据库查询"],
  "next_plan": ["进入 Gate 1 代码审查"],
  "blackboard_updates": {
    "new_nodes": ["CODE-001", "CODE-002"],
    "status_changes": ["DOC-005: in_progress → completed"],
    "snapshot": "CP-002"
  },
  // v1.1 新增：工件与证据记录
  "artifact_updates": {
    "new_artifacts": ["DEV-PLAN.md", "Quality-Check-Report.md"],
    "artifact_status": {"DEV-PLAN.md": "COMPLETED", "Quality-Check-Report.md": "IN_PROGRESS"}
  },
  "evidence_updates": {
    "new_evidence": ["failing_test", "passing_test"],
    "evidence_status": {"failing_test": "COMPLETED", "passing_test": "COMPLETED"}
  },
  // v1.1 新增：偏离与恢复记录
  "deviation_log": {
    "deviation_type": "none",  // 流程偏离 / 角色偏离 / 目标偏离 / 资源偏离 / 结果偏离
    "recovery_action": "none"  // 重试 / 回退 / 降级 / 待人工确认
  }
}
```

---

## 十、与 MCP 工具的映射

| Loop Agent 概念 | MCP 工具 |
|----------------|----------|
| 启动 Loop | `mcp__loop-agent__start_loop` |
| 查询状态 | `mcp__loop-agent__get_status` |
| 中止 Loop | `mcp__loop-agent__abort_loop` |
| 派发 Agent | `mcp__loop-agent__spawn_agent` |
| 列出 16 角色 | `mcp__loop-agent__list_agents` |
| 保存黑板 | `mcp__loop-agent__save_blackboard` |

**所有状态变更必须通过 MCP 工具完成，不要直接修改文件。**

---

**【Loop-Harness-Agent 模式 · Claude Code 适配版 v1.2 · 融合 Boss-auto-harness · 生效中】**
