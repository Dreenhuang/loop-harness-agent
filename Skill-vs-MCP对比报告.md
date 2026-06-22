# Skill vs MCP 深度对比报告

> **报告生成时间**：2026-06-22
> **项目路径**：`g:\ai-gongju\Loop-agent`（Loop-Harness-Agent v1.2）
> **报告目的**：从代码、规则、运行机制三个维度，深入剖析用户使用 Skill 与 MCP 两种能力的本质区别
> **覆盖范围**：`.trae/skills/*`、`loop-agent-mcp/`、`.trae/agents/*`、`.trae/workflows/*`、`.claude/mcp_servers.json`

---

## 一、TL;DR（一句话总结）

| 维度 | Skill | MCP |
|------|-------|-----|
| **本质** | 一份"提示词 + 工作流规范"的 Markdown 文档 | 一个在客户端外独立运行的进程，通过 JSON-RPC 暴露工具 |
| **执行者** | 客户端 LLM（你当前正在对话的模型） | 独立进程（Python stdio / Node.js） |
| **触发方式** | AI 在思考时识别"该用哪个 Skill" → 自己读 SKILL.md → 按规范思考 → 输出 | 客户端调用 `run_mcp` → 进程计算 → 返回结构化结果 |
| **Token 消耗** | 文档会进 LLM 上下文，每次调用都重新读 | 默认不进上下文（除非 AI 主动读工具描述），由进程承载计算 |
| **状态能力** | 无独立状态（黑板是文件，靠 AI 自己读写） | 有完整内存状态机（StateManager、A2ABus、TaskScheduler、WorkerPool） |
| **并行能力** | LLM 串行思考（除非开多 Agent） | 真正的多 Worker 并发（线程池、优先级队列、依赖图） |
| **产物类型** | 检查清单 / 评分标准 / 输出契约 Schema | 实际写入磁盘的文件 + 返回的 JSON 结果 |

---

## 二、它们在 Loop-Harness-Agent 项目里分别扮演什么角色？

### 2.1 5 级封装资产中的位置

```
┌─────────────────────────────────────────────────────┐
│ 第 5 层：Artifact & Evidence  ──  工件与证据地基    │
├─────────────────────────────────────────────────────┤
│ 第 4 层：Domain Chip                                │
├─────────────────────────────────────────────────────┤
│ 第 3 层：Workflow Blueprint  ──  .trae/workflows/    │
├─────────────────────────────────────────────────────┤
│ 第 2 层：Agent Profile  ──  .trae/agents/*.toml     │
├─────────────────────────────────────────────────────┤
│ 第 1 层：Skill  ──  .trae/skills/*/SKILL.md  ◀─ 这次对比的 Skill
└─────────────────────────────────────────────────────┘
                                                      
而 MCP 是另一条平行链路：                               
┌─────────────────────────────────────────────────────┐
│ loop-agent-mcp/  ──  独立 Python 进程                │
│   ├─ 15 个 MCP 工具（暴露给 Trae/Claude/Cursor）    │
│   ├─ 内含 StateManager / A2ABus / TaskScheduler     │
│   └─ spawn_agent 会真写文件（v1.2 智能执行器）       │
└─────────────────────────────────────────────────────┘
```

### 2.2 Skill 是什么：18 个原子能力清单

```
.trae/skills/core/
├── agent-mode-decision/        # AI 决定走哪种模式
├── applicability-check/        # 检查任务是否适用
├── budget-track/               # Token 预算跟踪
├── bug-triaging/               # Bug 分级 P0/P1/P2/P3
├── cognitive-surrender-defense # 反"AI 投降"防御
├── comprehension-debt-defense  # 防"理解债务"
├── debate-mode/                # 多方案辩论模式
├── gate1-code-review/          # Gate 1：代码审查门禁
├── gate2-performance/          # Gate 2：性能门禁
├── gate3-testing/              # Gate 3：测试门禁
├── gate4-final/                # Gate 4：终审门禁
├── knowledge-extract/          # 6 段式知识沉淀
├── open-loop-mode/             # 开环模式
├── orchestrate-map-reduce/     # Map-Reduce 高阶编排
├── pre-flight-check/           # 起飞前自检
├── progress-detect/            # 无进展检测
├── state-snapshot/             # 状态快照
└── unattended-mode/            # 无人值守模式
```

**Skill 的物理形态**：每个 Skill 是一个 `.trae/skills/core/<skill-id>/SKILL.md` 文件，本质是 Markdown 文档。例如 [gate1-code-review/SKILL.md](file:///g:/ai-gongju/Loop-agent/.trae/skills/core/gate1-code-review/SKILL.md) 包含：
- 用途、调用方式
- 检查标准（B1-B7 / M1-M6 / m1-m3 共 16 项规则）
- 执行流程（5 步）
- 输出契约（JSON Schema）
- 停止条件

### 2.3 MCP 是什么：loop-agent-mcp 的 15 个工具

`loop-agent-mcp/loop_agent_mcp/` 是一个 Python 包，通过 stdio 与客户端通信，对外暴露工具（参见 [schemas.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/tools/schemas.py)）：

```
核心编排工具（12 个）：
1.  start_loop              启动 / 恢复 Loop
2.  get_status              查询状态（隐式读黑板）
3.  abort_loop              中止 Loop
4.  list_agents             列出 16 角色
5.  spawn_agent             ★ 派发任务并实际执行（写文件）
6.  cancel_task             取消任务
7.  get_task_status         查询任务状态
8.  save_blackboard         保存 / 追加黑板
9.  check_artifact_completeness  12 工件完整性
10. check_evidence_sufficiency   5 类证据充分性
11. detect_deviation             5 类偏离检测
12. check_veto_items             6 项一票否决
13. check_fusion_targets         5 大融合目标评估
14. get_token_budget_status      Token 预算状态

文件操作工具（v1.2 新增 3 个）：
15. write_file / read_file / list_files
```

**MCP 的物理形态**：一个 Python 包，启动命令为 `python -m loop_agent_mcp.server`，客户端通过 `.claude/mcp_servers.json` 注册（参见 [mcp_servers.json](file:///g:/ai-gongju/Loop-agent/.claude/mcp_servers.json)）。

---

## 三、核心机制对比（深度版）

### 3.1 调用流程对比

#### Skill 调用（以 gate1-code-review 为例）

```
用户输入："请审查这段代码"
   ↓
Trae IDE 把用户输入送给 LLM
   ↓
LLM 内部推理（prompt 里写了"遇到代码审查请调用 gate1-code-review"）
   ↓
LLM 自己"读" .trae/skills/core/gate1-code-review/SKILL.md
   ↓
LLM 按文档里的 5 步流程：
   第1步：收集审查范围  ← LLM 自己模拟
   第2步：执行自动化检查 ← LLM 实际执行 bun run build / bun test
   第3步：执行人工/AI 审查 ← LLM 自己推理
   第4步：生成审查报告 ← LLM 输出 JSON
   第5步：发送 A2A 消息 ← LLM 在 .blackboard/ 写文件
   ↓
返回结果给用户
```

**关键点**：每一步都是 LLM 在做。Skill 文档是被 LLM "阅读并执行"的剧本。

#### MCP 调用（以 spawn_agent 为例）

```
用户输入："帮我生成一个用户管理 API"
   ↓
Trae IDE 把用户输入送给 LLM
   ↓
LLM 推理后决定调用工具 spawn_agent(agent_name="backend", task_input={...})
   ↓
Trae IDE 通过 stdio 把 JSON-RPC 请求发给 Python 进程
   ↓
Python 进程内：
   ├─ dispatcher.async_dispatch() 路由
   ├─ TaskScheduler.submit_task() 入优先级队列
   ├─ WorkerPool 起线程执行
   ├─ executors.execute_backend_agent() 真写文件
   └─ StateManager 更新内存状态
   ↓
Python 进程返回 JSON-RPC 响应（包含 files_created、execution_status）
   ↓
Trae IDE 把结果给 LLM，LLM 组织语言回复用户
```

**关键点**：计算/写文件/状态维护全在 Python 进程内完成。LLM 只负责"调用工具"和"理解结果"。

### 3.2 代码实证对比

#### 实证 1：路径校验逻辑

**Skill（gate1-code-review/SKILL.md）** 中描述的检查项是**自然语言规则**：

```yaml
# 来自 SKILL.md 第 3 节
B5: 硬编码密钥/凭证 | 0 处 | 扫描所有 .env、配置文件、源代码
```

这条规则由 LLM 自己读、自己理解、自己想办法扫描文件。**没有代码强制执行**。

**MCP（security.py）** 中同样的逻辑是**真正的 Python 代码**：

```python
# loop-agent-mcp/loop_agent_mcp/core/security.py
def validate_path(workspace, relative_path, operation):
    # 真·路径校验：阻止 ../ 越界、白名单控制
    ...
```

**区别**：
- Skill 的规则 = LLM 的"良心"
- MCP 的代码 = 系统的"铁闸"

#### 实证 2：任务调度

**Skill（orchestrate-map-reduce/SKILL.md）** 描述的是编排模式：

```yaml
# SKILL.md 第 2 节
diverge:
  agents: 5   # 并行 5 个 Agent
  budget_per_agent: {tokens: 5000, time: "10min"}
```

**MCP（runtime/scheduler.py）** 实现的是真正的调度器：

```python
# loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py
class TaskScheduler:
    def __init__(self, max_concurrent=4, ...):
        self._queue: list[tuple[int, float, str]] = []  # heapq 优先级队列
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._pool = WorkerPool()  # 真正的线程池
        ...
```

**区别**：
- Skill 的"5 Agent 并行" = 文档里的描述，最终由 LLM 决定要不要真的并行
- MCP 的"max_concurrent=4" = 进程内的硬约束，最多只能并发 4 个任务

#### 实证 3：状态管理

**Skill** 没有自己的状态机，所有"状态"都依赖：
- `.trae/` 下的 TOML 配置文件
- `项目进度记录.md` 文件
- 客户端 LLM 的上下文窗口

**MCP** 有完整的进程内状态机：

```python
# loop-agent-mcp/loop_agent_mcp/core/state.py
class StateManager:
    _states: dict[str, LoopState]  # 内存里的多 Loop 状态
    _persistence: Persistence       # 磁盘持久化（.loop-agent-state/）
    mutate(lambda)                  # 状态变更
    snapshot()                       # 状态快照
```

```python
# loop-agent-mcp/loop_agent_mcp/runtime/a2a_bus.py
class A2ABus:
    _subscribers: dict[str, list[Handler]]  # pub/sub
    _history: deque(maxlen=10000)            # 消息历史
```

**区别**：
- Skill 的状态 = 文件 + LLM 记忆，进程重启 = 状态丢失（除非有文件）
- MCP 的状态 = 进程内 StateManager + 持久化层 + A2A 总线 + TaskScheduler 四件套

---

## 四、关键差异矩阵

### 4.1 架构维度

| 维度 | Skill | MCP |
|------|-------|-----|
| **物理形态** | Markdown 文档 | Python 包（stdio 进程） |
| **运行环境** | 客户端 LLM 上下文 | 独立的 Python 进程 |
| **代码量级** | 数百行 Markdown | 数千行 Python |
| **依赖** | 无（纯文档） | mcp>=1.0.0、Python>=3.10 |
| **启动方式** | AI 读文件即可 | 注册到 mcp_servers.json 后自动 spawn 进程 |
| **跨客户端** | 跟着 prompt 走，可移植 | 一次注册，Trae/Claude/Cursor 通用 |

### 4.2 调用方式维度

| 维度 | Skill | MCP |
|------|-------|-----|
| **触发信号** | LLM 内部识别（prompt + 语义） | 客户端显式调用工具 |
| **执行主体** | LLM 自己推理 + 执行 shell 命令 | MCP 进程内代码 |
| **结果返回** | LLM 生成的自然语言 + 可能写入文件 | 结构化 JSON-RPC 响应 |
| **错误处理** | LLM 自己判断 + 重试 | 分类异常（ToolNotFoundError / ValidationError / SecurityError / InternalError） |
| **调用嵌套** | Skill 内部可调用其他 Skill（见 orchestrate-map-reduce） | 工具可调用其他工具（dispatcher 内部路由） |

### 4.3 能力维度

| 能力 | Skill | MCP |
|------|-------|-----|
| **真实写文件** | ❌ 不能直接写（只能引导 LLM 调用工具） | ✅ write_file 直接写入 + 安全校验 |
| **状态机** | ❌ 无独立状态 | ✅ StateManager + 持久化 + 快照 |
| **并行调度** | ⚠️ 文档描述可并行，但 LLM 实际未必真并行 | ✅ 真正的优先级队列 + WorkerPool + Semaphore |
| **优先级控制** | ❌ LLM 自己决定先后 | ✅ priority 1-10 数字硬约束 |
| **依赖图** | ⚠️ 文档描述依赖 | ✅ dependencies 参数硬约束（必须全部成功才开始） |
| **超时控制** | ❌ 靠 LLM 自己注意 | ✅ timeout 参数（默认 600s） |
| **取消任务** | ❌ 不支持 | ✅ cancel_task 工具 |
| **审计日志** | ❌ 靠 LLM 自觉 | ✅ get_audit_logger().log_call() |
| **Token 预算治理** | ⚠️ budget-track Skill 只能建议 | ✅ token.py 内置估算 + 阈值告警（80%/95%） |
| **安全沙箱** | ❌ 没有边界 | ✅ validate_path + sanitize_identifier + validate_content |
| **融合验收检查** | ⚠️ Skill 里有清单但执行靠 LLM | ✅ check_artifact_completeness / check_evidence_sufficiency / check_veto_items / check_fusion_targets 4 个独立工具 |

### 4.4 用户体验维度

| 体验点 | Skill | MCP |
|--------|-------|-----|
| **首次响应速度** | 快（LLM 直接读文档） | 慢（要启动 Python 进程） |
| **文档可读性** | ✅ 高（人类可读的 Markdown） | ❌ 低（代码 + JSON Schema） |
| **可被 LLM 修改** | ✅ 可以（修改 SKILL.md 即可） | ⚠️ 改代码，需测试 |
| **跨会话一致性** | ⚠️ 依赖 LLM 每次都遵守 | ✅ 强（代码不变行为不变） |
| **调试难度** | 容易（看 SKILL.md） | 中等（要懂 Python + MCP 协议） |
| **离线运行** | ✅ 完全离线 | ⚠️ 第一次启动需安装 mcp 依赖 |

---

## 五、用一个具体场景说明差异

**场景**：用户在 Loop 完成后说"帮我审查刚才那段代码"

### 路径 A：纯 Skill 方案

```
1. 用户输入
2. LLM 看到 prompt 里 "审查请调用 gate1-code-review Skill"
3. LLM 读 .trae/skills/core/gate1-code-review/SKILL.md
4. LLM 按 5 步执行：
   ├─ 第1步：列出要审查的文件路径（LLM 自己推断）
   ├─ 第2步：调用 RunCommand 跑 bun test、bun run build
   ├─ 第3步：LLM 自己逐文件检查 SQL 注入/XSS/硬编码密钥
   ├─ 第4步：LLM 自己输出 CR JSON
   └─ 第5步：LLM 写 .blackboard/reviews/review_xxx.json
5. LLM 告诉用户审查结果

风险：
- LLM 可能在第3步偷懒跳过某些文件
- "应该没问题"等软性声明可能通过
- 没有"审查报告"的结构化校验
```

### 路径 B：纯 MCP 方案

```
1. 用户输入
2. LLM 调用 MCP 工具 detect_deviation() 或类似的门禁工具
3. Python 进程内执行检测逻辑，返回 JSON 报告
4. LLM 拿到结果，组织语言回复

特点：
- 检测逻辑在 Python 代码里，LLM 不能跳过
- 结果结构化，客户端 LLM 收到 JSON 后再做总结
```

### 路径 C：融合方案（项目实际采用）

```
Skill 提供"剧本"：定义什么是 Blocker、什么是 Major、输出 Schema 长什么样
MCP 提供"执行器"：实际跑检测、写文件、维护状态

具体来说：
- gate1-code-review Skill 定义了 B1-B7/M1-M6 检查项
- @Code-Reviewer Agent Profile 绑定这个 Skill
- MCP spawn_agent(agent_name="code-reviewer") 会让 LLM 扮演 Code-Reviewer
- LLM 读 SKILL.md，知道该怎么审查
- LLM 调用 MCP 工具 read_file / shell 来实际执行
- LLM 按 Skill 要求的 JSON Schema 输出报告
- LLM 调 save_blackboard 写报告
- MCP 进程记录状态 + 审计日志
```

---

## 六、何时该用 Skill，何时该用 MCP？

### 6.1 推荐用 Skill 的场景

✅ **规则定义、规范说明、清单要求**
例：什么是 Blocker？怎么算 P0 Bug？输出 JSON 长什么样？

✅ **工作流编排模式**
例：Map-Reduce 怎么用？预算超限怎么办？无进展怎么检测？

✅ **可被 LLM 解释并灵活执行的逻辑**
例：UI 设计原则、PRD 模板、代码审查标准

✅ **跨 IDE/工具的可移植知识**
例：bug-triaging 的 4 级标准 → 任何 AI 都能读

### 6.2 推荐用 MCP 的场景

✅ **需要真实副作用（写文件、发请求、跑命令）**
例：spawn_agent 写代码、write_file 落盘

✅ **需要状态机管理**
例：Loop 状态、Phase 进度、Gate 通过情况、任务队列

✅ **需要并发/并行/优先级**
例：5 个 Agent 同时跑，依赖图管理，超时取消

✅ **需要审计/日志/可观测**
例：谁什么时候调用了哪个工具、花了多少 token

✅ **需要安全沙箱**
例：路径校验、内容大小限制、标识符清洗

✅ **需要跨客户端复用**
例：同一套编排能力，在 Trae / Claude Code / Cursor 都用

### 6.3 Loop-Harness-Agent 项目的实际分层策略

```
Layer 1 - Skill：定义"是什么"、"为什么"、"标准是什么"
Layer 2 - Agent Profile：定义"谁来做"、"边界在哪里"
Layer 3 - Workflow Blueprint：定义"先做什么后做什么"
Layer 4 - Domain Chip：领域知识封装
Layer 5 - Artifact & Evidence：产物和证据地基

而 MCP 是这一切的"运行时"：
- 把 Workflow 跑起来
- 把 Agent 派发出去
- 把 Skill 变成可调度的代码
- 把状态记录下来
```

---

## 七、代码定位速查

### 7.1 Skill 相关

| 用途 | 路径 |
|------|------|
| Skill 定义目录 | [.trae/skills/core/](file:///g:/ai-gongju/Loop-agent/.trae/skills/core) |
| Skill 规则说明 | [.trae/rules/loop-agent.md](file:///g:/ai-gongju/Loop-agent/.trae/rules/loop-agent.md) 第 1 节 |
| Skill 调用模板 | [.trae/rules/A2A消息速查卡.md](file:///g:/ai-gongju/Loop-agent/.trae/rules/A2A消息速查卡.md) |
| Skill 编排定义 | [.trae/skills/core/orchestrate-map-reduce/SKILL.md](file:///g:/ai-gongju/Loop-agent/.trae/skills/core/orchestrate-map-reduce/SKILL.md) |
| 门禁类 Skill 范例 | [.trae/skills/core/gate1-code-review/SKILL.md](file:///g:/ai-gongju/Loop-agent/.trae/skills/core/gate1-code-review/SKILL.md) |

### 7.2 MCP 相关

| 用途 | 路径 |
|------|------|
| MCP 包入口 | [loop-agent-mcp/loop_agent_mcp/server.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/server.py) |
| 15 个工具 Schema | [loop-agent-mcp/loop_agent_mcp/tools/schemas.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/tools/schemas.py) |
| 调度器 | [loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py) |
| 任务执行器 | [loop-agent-mcp/loop_agent_mcp/engines/executors.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/engines/executors.py) |
| 状态机 | [loop-agent-mcp/loop_agent_mcp/core/state.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/core/state.py) |
| 安全沙箱 | [loop-agent-mcp/loop_agent_mcp/core/security.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/core/security.py) |
| 融合验收 | [loop-agent-mcp/loop_agent_mcp/engines/fusion.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/engines/fusion.py) |
| Token 治理 | [loop-agent-mcp/loop_agent_mcp/engines/token.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/engines/token.py) |
| A2A 总线 | [loop-agent-mcp/loop_agent_mcp/runtime/a2a_bus.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/a2a_bus.py) |
| 客户端注册 | [.claude/mcp_servers.json](file:///g:/ai-gongju/Loop-agent/.claude/mcp_servers.json) |
| MCP 文档 | [loop-agent-mcp/README.md](file:///) |

### 7.3 配置/规则关联

| 用途 | 路径 |
|------|------|
| Agent Profile（绑定 Skill） | [.trae/agents/*.agent.toml](file:///g:/ai-gongju/Loop-agent/.trae/agents) |
| Workflow Blueprint | [.trae/workflows/prd-to-production.json](file:///g:/ai-gongju/Loop-agent/.trae/workflows/prd-to-production.json) |
| 融合验收标准 | [docs/integration/融合验收标准.md](file:///g:/ai-gongju/Loop-agent/docs/integration/融合验收标准.md) |
| 黑板模板 | [blackboard/templates/项目进度记录.md](file:///g:/ai-gongju/Loop-agent/blackboard/templates/%E9%A1%B9%E7%9B%AE%E8%BF%9B%E5%BA%A6%E8%AE%B0%E5%BD%95.md) |

---

## 八、总结：核心心智模型

```
┌──────────────────────────────────────────────────────────────┐
│  Skill = 剧本                                                   │
│  谁演？→ LLM                                                   │
│  演给谁看？→ 用户                                              │
│  怎么演？→ LLM 读 SKILL.md → 按规范推理 → 输出结果             │
│  强项？→ 灵活、可解释、跨工具、零依赖                          │
│  弱点？→ 依赖 LLM 自觉，无强制力，状态靠文件                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  MCP = 舞台 + 演员                                            │
│  谁演？→ Python 进程（独立执行体）                              │
│  演给谁看？→ 客户端 LLM（收到 JSON-RPC 结果）                  │
│  怎么演？→ 进程内代码 + 状态机 + 调度器 + WorkerPool           │
│  强项？→ 真实副作用、并发、状态、安全、可观测、跨客户端        │
│  弱点？→ 重、需要装依赖、调试成本高、修改需测试                │
└──────────────────────────────────────────────────────────────┘
```

**Loop-Harness-Agent 的精髓**：**Skill 提供智力，MCP 提供执行力**。

- Skill 让 LLM 知道"什么是好的代码审查"
- MCP 让 LLM 真的能"调用工具审查 + 写报告 + 记录状态"

二者协同，才能实现"PRD→生产"的全自动化流水线。

---

## 九、附录：可验证的实验

如果想亲自验证差异，可以尝试：

### 实验 1：Skill 的"软性"特征

1. 打开 [.trae/skills/core/gate1-code-review/SKILL.md](file:///g:/ai-gongju/Loop-agent/.trae/skills/core/gate1-code-review/SKILL.md)
2. 直接对 AI 说："请按 gate1-code-review 的标准审查下面这段代码：[故意写一段有 SQL 注入的代码]"
3. 观察：AI 可能会跳过某些检查项，或者用"看起来没问题"代替硬判断
4. 这是 Skill 的本质：依赖 LLM 自觉

### 实验 2：MCP 的"硬性"特征

1. 启动 MCP 进程：`cd g:\ai-gongju\Loop-agent\loop-agent-mcp && pip install -e .`
2. 调用 `run_mcp` → `mcp_cloudbase`（不存在的服务器名）
3. 观察：返回结构化错误 `TOOL_NOT_FOUND`，而不是 LLM 的"猜你喜欢"
4. 这是 MCP 的本质：所有边界都在代码里硬约束

### 实验 3：状态对比

1. **Skill 状态**：打开 `项目进度记录.md`，你会看到所有状态都是文本段落
2. **MCP 状态**：打开 `.loop-agent-state/loop-*.json`，你会看到结构化状态机
3. 前者人类可读、后者机器可处理

---

**【Skill vs MCP 深度对比报告 · Loop-Harness-Agent v1.2 · 完成】**