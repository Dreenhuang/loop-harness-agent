# Loop-Harness-Agent 模式 · 主入口规则 v1.2

> **正式命名**：loop-harness-agent（Loop Agent × Boss-auto-harness 融合模式）
> **生效范围**：所有 Trae IDE 全局规则
> **生效优先级**：最高（与「黑板+A2A 强制规则」同级）
> **生效日期**：2026-06-17
> **配套文件**：
> - 黑板模板：`项目进度记录.md`
> - A2A 速查卡：`A2A消息速查卡.md`
> - Skill 资产库：`.trae/skills/`
> - Agent Profile：`.trae/agents/`
> - Workflow 蓝图：`.trae/workflows/`
> - Domain Chip：`domain-chips/`
> - 工件模板：`templates/`
> - 工件注册表：`artifacts/registry/`
> - 证据收集器：`artifacts/evidence/`
> - 引擎代码：`loop-agent-engine/`
> - MCP Server：`loop-agent-mcp/`

---

## 一、触发机制（双通道识别）

> AI 必须在每次用户输入时**先检测**是否触发 Loop Agent 模式。

### 1.1 斜杠命令触发（显式）

| 命令 | 含义 | 默认行为 |
|------|------|----------|
| `/loop-harness-agent` | 启动完整 Loop-Harness-Agent 流程 | 读黑板 → 输出进度总结 → 等用户 PRD |
| `/loop-harness-agent status` | 仅查询当前状态 | 输出进度 + 待办 + 风险 |
| `/loop-harness-agent resume` | 接续上次未完成流程 | 读取黑板 + 恢复断点 |
| `/loop-harness-agent abort` | 中止当前 Loop | 写日志 + 状态置 failed |
| `/loop-agent` | 兼容旧命令，等同 `/loop-harness-agent` | 同上 |
| `/loop-agent status` | 兼容旧命令 | 同上 |
| `/loop-agent resume` | 兼容旧命令 | 同上 |
| `/loop-agent abort` | 兼容旧命令 | 同上 |

### 1.2 自然语言触发（隐式）

以下表述**任意一条**命中即触发 Loop-Harness-Agent 模式（支持大小写不敏感和格式容错）：

**主触发词（精确匹配）**：
```
- "loop-harness-agent"
- "loop harness agent"
- "loop_harness_agent"
- "loopharnessagent"
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
- 大小写不敏感：`LOOP-HARNESS-AGENT`、`Loop-Harness-Agent`、`loop-harness-agent` 均可触发
- 连字符容错：`loop harness agent`（空格分隔）、`loop_harness_agent`（下划线分隔）均可触发
- 简写容错：`loop agent`、`LHA`、`lha` 均可触发
- 中文混合容错：`用LHA模式`、`启动loop agent`、`走loop-harness流程` 均可触发

### 1.2.1 无人值守模式触发（夜间作业）

以下表述**任意一条**命中即触发**无人值守模式**（v1.1 新增）：

```
- "用 Loop Agent 模式开发，今晚完成明天早上给我结果"
- "进入无人值守模式"
- "今晚完成，明天早上给我结果"
- "通宵跑"
- "Auto Mode"
- "set it and forget it"
- "/unattended"
- "/auto-overnight"
- "时间预算 X 小时"
```

**无人值守模式 6 条铁律**：

1. **不中断原则**：除非命中"用户确认边界"，不暂停
2. **最小影响原则**：异常时优先回滚或降级，不破坏现有状态
3. **完整执行原则**：宁可慢也要完成，不留半成品
4. **决策可审计**：所有自动决策记录到 `blackboard/decision_log.json`
5. **时间有预算**：明确 `max_duration_hours`，到点强制保存并报告
6. **早晨有报告**：用户醒来看到完整的"夜间作业报告"

**自动决策边界**：

| ✅ AI 自动决策（90% 场景） | ❌ 需用户确认（< 5% 场景） |
|----------------------------|------------------------------|
| 文件操作（临时/路径/命名/目录） | 架构变更（技术栈/核心模块/DB 迁移） |
| 资源分配（Token/CPU/并行度/端口） | 核心功能变更（> 20% PRD 修改） |
| 非关键参数（超时/重试/日志/缓存） | 资源超阈（> 150% 预算/500% 时间） |
| 错误恢复（重试/回滚/应用知识库） | 安全/合规/不可逆操作 |
| Bug 修复（自动选方案/写根因） | 时间计划调整（> 3 天延期） |
| 代码生成（命名/结构/测试/Schema） | 异常无法恢复（连续 3 次同错） |
| 文档生成（README/注释/截图） |  |

详细规范见 `docs/UNATTENDED_MODE.md` + `.trae/skills/core/unattended-mode/SKILL.md`。


### 1.3 触发后的强制响应

触发后 AI **必须**按以下顺序执行（不可跳步）：

```
【第 1 步】识别触发源
    ├─ 斜杠命令 → 解析参数（status/resume/abort/默认）
    ├─ 自然语言 → 确认触发词命中 → 输出"Loop-Harness-Agent 模式已激活"
    └─ 【v1.2】提取时间预算参数
         ├─ 匹配模式："时间预算 X 小时" / "今晚完成" / "明天早上" / "通宵"
         ├─ 默认值：9 小时（睡觉场景）
         └─ 输出："⏰ 时间预算：X 小时"

【第 2 步】读取黑板（强制）
    ├─ 优先读 <项目根>/项目进度记录.md
    ├─ 如存在 → 复盘进度 → 输出【项目整体进度总结】
    └─ 如不存在 → 自动初始化（建黑板 + 等 PRD）

【第 3 步】加载 5 级封装资产
    ├─ 加载 .trae/skills/ 全部门禁与原子 Skill
    ├─ 加载 .trae/agents/ 全部 Agent Profile
    ├─ 加载 .trae/workflows/prd-to-production.json
    ├─ 加载 domain-chips/web-feature-chip/chip.json
    └─ 加载 artifacts/registry/ + artifacts/evidence/ + templates/

【第 4 步】切换到 @Orchestrator 视角
    ├─ 输出："@Orchestrator 已就位 · Loop-Harness-Agent v1.2"
    ├─ 输出："⏰ 时间预算：X 小时"（如已提取）
    ├─ 检测无人值守意图（如有）→ 激活 unattended-mode Skill
    ├─ 列出当前可执行任务（依赖已满足的 READY 任务）
    └─ 询问用户："请提供 PRD 或确认启动哪一个 Phase"
```

### 1.4 时间预算参数解析规范（v1.1.1 修复 V-001）

> **背景**：之前版本未识别用户的"时间预算"参数，导致 @Orchestrator 不知道何时该停止。

**触发关键词匹配规则**：

```yaml
# 显式时间预算
- "时间预算 X 小时"    → max_duration_hours = X
- "X 小时"              → max_duration_hours = X

# 隐式（基于时间场景）
- "今晚完成"            → 9 小时（默认睡觉场景）
- "明天早上给我结果"    → 9 小时
- "通宵跑"              → 8 小时
- "auto-overnight"      → 8 小时
- "午饭前完成"          → 4 小时
- "下午完成"            → 6 小时
- "周末前完成"          → 48 小时

# 默认（无时间指定）
- 默认                  → 9 小时
```

**自动激活的 Skills**：

```yaml
if time_budget_mentioned:
  activate:
    - unattended-mode  # 时间预算 > 1 小时自动激活
    - budget-track      # 持续监控
    - progress-detect   # 卡点检测
    - state-snapshot    # 每 30 分钟快照
```

---

## 二、核心架构（5 级分层封装）

> **铁律**：Skill 是砖瓦，Agent 是房间，Workflow 是楼层，Domain Chip 是整栋楼，Artifact Registry 是地基。

### 2.1 分层一览

```
┌─────────────────────────────────────────────────────┐
│ 第 5 层：Artifact & Evidence  ──  工件与证据地基    │
│           (artifacts/registry/ + artifacts/evidence/)│
│           → 强制工件追踪 + 证据收集 + 合规校验      │
├─────────────────────────────────────────────────────┤
│ 第 4 层：Domain Chip  ──  领域黑盒芯片              │
│           (domain-chips/web-feature-chip/)          │
│           → 终极形态：Workflow + Agents + Skills    │
│             + 知识库 + 评估基准 + 自优化            │
├─────────────────────────────────────────────────────┤
│ 第 3 层：Workflow Blueprint  ──  多角色编排蓝图     │
│           (.trae/workflows/prd-to-production.json)  │
│           → 10 相位 + 依赖图 + 门禁节点 + 护栏     │
├─────────────────────────────────────────────────────┤
│ 第 2 层：Agent Profile  ──  单角色循环单元          │
│           (.trae/agents/*.agent.toml)               │
│           → 16 角色 + 内部 Loop + 绑定 Skills      │
├─────────────────────────────────────────────────────┤
│ 第 1 层：Skill  ──  原子能力资产                    │
│           (.trae/skills/*/SKILL.md)                 │
│           → 4 门禁 + 5 原子能力 + 复用核心          │
└─────────────────────────────────────────────────────┘
```

### 2.2 资产加载顺序（启动 Loop-Harness-Agent 时）

```
1. Skill 层（最先加载）→ 原子能力就位
   ↓
2. Agent Profile 层 → 16 角色就位（每个角色绑定对应 Skills）
   ↓
3. Workflow Blueprint 层 → 编排蓝图就位（定义谁先谁后）
   ↓
4. Domain Chip 层 → 领域知识 + 评估 + 自优化就位
   ↓
5. Artifact & Evidence 层 → 工件注册表 + 证据收集器就位
   ↓
6. 黑板 + A2A 系统就位 → 通信与状态基础设施就位
   ↓
7. @Orchestrator 接管调度 → Loop-Harness-Agent 启动
```

---

## 三、Loop Agent 调度协议

### 3.1 角色调用机制（@角色名）

> **铁律**：Trae IDE 中调用已配置好的角色，**用 @角色名 触发**。

| 层级 | 角色名（@调用） | 触发场景 |
|------|------------------|----------|
| **调度层** | `@Orchestrator` | 流程总控、任务派发、状态管理 |
| **决策层** | `@Product-Manager` | 业务决策、需求澄清、版本规划 |
| **业务层** | `@Requirements` | PRD 编写、需求基线 |
|  | `@UX-Researcher` | 交互流程、用户旅程 |
|  | `@UI-Designer` | 视觉设计、组件库 |
| **技术层** | `@Architect` | 架构设计、技术选型 |
|  | `@Backend` | 后端开发、API、数据库 |
|  | `@Fullstack-Coder` | 前端开发、页面、组件 |
|  | `@Bug-Defect-Repairer` | Bug 定位修复、故障应急 |
| **质量层** | `@Code-Reviewer` | 代码审查、门禁 1 |
|  | `@Professional-Performance` | 性能压测、门禁 2 |
|  | `@全栈测试员` | 功能/接口/安全测试、门禁 3 |
| **知识层** | `@Knowledge-Curator` | 经验沉淀、知识库 |
| **交付层** | `@Documenter` | 全文档归档 |
|  | `@Final-Reviewer` | 终审、门禁 4 |
|  | `@DevOps` | 部署、CI/CD、运维 |

### 3.2 三道硬刹车（全局护栏）

```yaml
global_guardrails:
  max_iterations: 200          # 第 1 道：最大迭代次数
  max_budget_usd: 100.0        # 第 2 道：Token 预算上限
  no_progress_detection: true  # 第 3 道：无进展检测
  max_attempts_per_task: 3     # 单任务最多重试 3 次
  loud_failure_only: true      # 禁止静默失败
```

### 3.3 门禁（4 道质量门禁）

| 门禁 | 触发角色 | 触发条件 | 不通过处理 |
|------|----------|----------|------------|
| **Gate 1** | `@Code-Reviewer` | Phase 5 编码完成后 | → `@Bug-Defect-Repairer` 修复 → 回到 Phase 5 |
| **Gate 2** | `@Professional-Performance` | Gate 1 通过后 | 同上 |
| **Gate 3** | `@全栈测试员` | Gate 2 通过后 | 同上 |
| **Gate 4** | `@Final-Reviewer` | 所有 Phase 完成后 | 输出风险报告 → 人工介入 |

---

## 四、Loop Agent 10 相位完整工作流

> 详见 `.trae/workflows/prd-to-production.json`

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

---

## 五、Loop Agent 与黑板 + A2A 协同

### 5.0 融合验收标准（Boss-auto-harness 对齐）

> **强制关联文档**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md`

自本规则融合改造起，`Loop Agent` 不再只追求“流程跑完”，而必须满足以下 5 个融合总目标：

1. **全自动闭环目标**：从需求输入到代码、文档、测试、门禁、发布准备形成可追踪、可恢复、可回退、可审计的自动化闭环。
2. **生产级交付目标**：输出代码必须达到生产环境质量标准，不接受 demo 级、样例级或半成品级结果。
3. **直接部署目标**：交付结果必须具备部署所需的配置、说明、验证和回滚信息，能够直接进入 `@DevOps` 发布流程。
4. **Token 效率目标**：在保证质量的前提下，避免重复推理、上下文膨胀和无意义空转。
5. **流程收敛目标**：系统严格按预设 phase、gate、角色边界和黑板状态推进，不得出现 phase 漂移、角色越权、缺证据放行和伪完成。

**铁律**：如果当前任务输出不满足上述任一目标，则不得宣告“已完成”，必须返回对应 Phase 或 Gate 继续修复。

### 5.1 黑板写入规则（强制）

**每完成一个 Phase 或修复一个 Bug，必须更新 `项目进度记录.md`**：

```markdown
【YYYY-MM-DD｜Loop Agent｜Phase X 完成】
1. ✅【本轮已完成】：xxx（具体到文件/接口/节点）
2. ⚠️【本轮不确定项】：xxx
3. ❌【遗留待解决问题】：xxx
4. 📋【下一轮工作计划】：xxx
5. 🔄【黑板更新记录】：
   - 新增节点：ARCH-001（Architecture | 标题 | completed）
   - 状态变更：DOC-005（in_progress → completed）
   - 快照更新：CP-002（进度 35% → 42%）
6. 🧾【工件与证据记录】：
   - 新增工件：DEV-PLAN.md / Quality-Check-Report.md / Release-Notes.md
   - 新增证据：failing_test / passing_test / verification_commands / review_feedback
7. 🚨【偏离与恢复记录】：
   - 偏离类型：流程偏离 / 角色偏离 / 目标偏离 / 资源偏离 / 结果偏离
   - 恢复动作：重试 / 回退 / 降级 / 待人工确认
```

**新增强制要求**：

- 黑板必须能够回答“当前在哪个 Phase”“为什么能进入下一步”“有哪些强制工件”“有哪些验证证据”“发生失败后如何恢复”。
- 黑板中必须保留摘要级工件索引和证据索引，禁止让 `@Orchestrator` 反复依赖长文本全量回忆。
- 无人值守模式下，每次自动决策、自动回退、自动重试都必须同步写入黑板或决策日志。

### 5.2 A2A 消息协议

> **详细规范见 A2A消息速查卡.md**

| 消息类型 | 用途 | 示例 |
|----------|------|------|
| `[REQ]` REQUEST | 我请你做事 | `@Orchestrator → @Architect` |
| `[RESP]` RESPONSE | 我做完了回你 | `@Architect → @Orchestrator` |
| `[BC]` BROADCAST | 通知所有人 | `@Architect → ALL` |
| `[NOTIFY]` NOTIFICATION | 单向通知 | `@Orchestrator → ALL` |
| `[ERR]` ERROR | 报错 | `@Backend → @Architect` |

### 5.3 知识图谱（Loop Agent 专属）

> 在 A2A-Agent 9 节点基础上扩展为 12 节点

| 节点类型 | 含义 | 创建角色 |
|----------|------|----------|
| `PRD` | 需求文档 | @Requirements |
| `UX` | 交互设计 | @UX-Researcher |
| `UI` | 视觉设计 | @UI-Designer |
| `Architecture` | 架构设计 | @Architect |
| `API` | 接口文档 | @Backend / @Architect |
| `Code` | 源代码 | @Backend / @Fullstack-Coder |
| `DB` | 数据库 | @Backend |
| `Config` | 配置文件 | @DevOps |
| `Test` | 测试报告 | @全栈测试员 |
| `Gate` | 门禁报告 | @Code-Reviewer / @Professional-Performance / @Final-Reviewer |
| `Knowledge` | 知识条目 | @Knowledge-Curator |
| `DOC` | 项目文档 | @Documenter |

---

## 六、强制行为准则

### 6.1 ✅ 必须做

1. **触发 Loop Agent 后 → 强制读取黑板**（无黑板则先建）
2. **每完成一个 Phase → 强制更新黑板 + 知识图谱**
3. **任务失败 → 强制 Loud Failure**（绝不允许静默替代）
4. **门禁不通过 → 强制回到 Phase 5 修复**（不允许绕过）
5. **超出预算 → 强制停止 + 输出报告**
6. **每个 Agent → Ralph 模式**（每轮重置上下文，进度存黑板）
7. **强制工件齐全后才能进入终审**（缺少 `Product-Spec.md`、`DEV-PLAN.md`、`Quality-Check-Report.md`、`Test-Report.md`、`Release-Notes.md` 等关键工件时不得放行）
8. **强制证据齐全后才能宣告完成**（缺少 failing test、passing test、verification commands、review feedback 等关键证据时不得放行）
9. **强制执行 Token 治理**（黑板优先、工件优先、摘要优先、增量优先，防止上下文膨胀）
10. **强制执行防偏离检查**（每轮 Loop 必须确认目标一致性、Phase 一致性、角色一致性、结果一致性）

### 6.2 ❌ 禁止做

1. ❌ 禁止 Orchestrator 做领域推理（只路由）
2. ❌ 禁止生成者验证自己（Maker-Checker 分离）
3. ❌ 禁止 Agent 直接通信（必须经黑板+A2A）
4. ❌ 禁止静默失败或占位替代
5. ❌ 禁止无停止条件的死循环
6. ❌ 禁止绕过门禁（门禁是硬约束）
7. ❌ 禁止协调者上下文膨胀
8. ❌ 禁止缺证据宣告完成
9. ❌ 禁止输出 demo 级结果却标记为生产级交付
10. ❌ 禁止在缺少部署前提、回滚说明、环境变量说明时宣称“可直接部署”
11. ❌ 禁止重复分析、重复生成、重复失败却无恢复动作
12. ❌ 禁止角色越权替代其他角色的核心职责

### 6.3 Harness 融合执行纪律（强制）

为与 `boss-auto-harness` 融合对齐，Loop Agent 在各 Phase 内部必须遵守以下执行纪律：

1. **需求阶段 → 强制澄清**：`@Requirements` 必须执行苏格拉底式需求澄清，确保需求、目标用户、替代方案、AI 能力需求和验收标准清晰。
2. **计划阶段 → 强制微任务化**：进入开发前，必须形成可执行的微任务级计划，明确输入、输出、验收标准和依赖关系。
3. **开发阶段 → 强制 TDD 证据化**：关键新功能不得跳过 failing test → passing test → refactor 的最小闭环或等效证据链。
4. **完成声明前 → 强制 Fresh Evidence**：任何“已完成”“已通过”“可发布”声明前，必须有当场验证证据。
5. **审查阶段 → 强制反馈闭环**：代码审查反馈必须逐项回应、逐项修复、逐项复核。
6. **发布前 → 强制部署完备性**：缺少部署脚本、部署说明、环境变量说明、回滚说明时，不得宣告“可直接部署”。

### 6.4 Token 治理与防空转规则（强制）

1. `@Orchestrator` 只保留调度级上下文，不保存全部领域细节。
2. 长日志、长报告、长审查意见必须先摘要后流转，默认传递摘要和索引路径。
3. 已通过的 Gate 检查不得全量重复执行，除非相关输入发生变更。
4. 连续 3 轮无有效进展时，必须触发进展告警并执行以下动作之一：重试、回退、降级、请求人工确认。
5. 如果系统开始输出与目标无关内容，必须立即执行目标一致性检查并回归当前 Phase。
6. 如果当前结果仍为 demo 级或半成品级，禁止推进到“终审通过”或“可部署”状态。

### 6.5 一票否决项（强制）

命中以下任一情况，当前融合流程必须立即阻断，不得继续放行：

1. 无法稳定生成完整工件链。
2. Gate 可被绕过或存在无证据放行。
3. 无法在失败后基于黑板恢复执行。
4. 输出仍停留在 demo 级，却宣称满足生产级交付。
5. Token 消耗明显失控且无法通过摘要/增量/回退策略收敛。
6. 无人值守模式下出现长时间空转、重复执行或伪完成。

---

## 七、与现有全局规则的关系

| 现有规则 | 与 Loop Agent 关系 |
|----------|---------------------|
| **全局规则 v2.1-黑板增强版** | **基础层**：黑板+A2A 强制规则被 Loop Agent 完全继承 |
| **A2A 消息速查卡** | **直接复用**：5 种消息类型、Topic 命名完全一致 |
| **问题解决经验文档管理规则** | **触发**：@Knowledge-Curator 沉淀知识时按 6 段式模板 |
| **GitHub & Gitee 密钥配置** | **直接使用**：@DevOps 部署时读取密钥 |
| **Agent Team 14 大角色** | **扩展为 16 角色**：增加 @Product-Manager + @Knowledge-Curator |

---

## 八、一句话总结

> **Loop-Harness-Agent 是 Loop Agent × Boss-auto-harness 的融合模式，把规则 + Agent Team + Harness 执行纪律装进一个 5 级封装的自动化引擎里，让用户说一句"用 loop-harness-agent"，系统就自动按 PRD→生产 流水线跑完全流程，同时确保生产级交付、证据闭环和一票否决。**

---

## 九、版本与维护

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v1.0 | 2026-06-15 | 初始版本：4 级封装 + 16 角色 + 10 相位 + 黑板+A2A 集成 |
| v1.1 | 2026-06-16 | 融合 Boss-auto-harness 验收标准，新增闭环、证据、Token 治理与防偏离规则 |
| v1.2 | 2026-06-17 | 正式命名 loop-harness-agent，新增触发词容错机制，升级为 5 级封装（增加 Artifact & Evidence 层），新增工件模板和证据收集基础设施 |

> 维护者：Loop-Harness-Agent 系统自动演进
> 反馈通道：触发后说「/loop-harness-agent feedback」或「/loop-agent feedback」

---

**【Loop-Harness-Agent 模式 v1.2 · 生效中】**
