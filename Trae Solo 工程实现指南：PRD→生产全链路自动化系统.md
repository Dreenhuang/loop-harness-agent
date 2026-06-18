# Trae Solo 工程实现指南：PRD→生产全链路自动化系统

> 部分内容由豆包生成
> 
> 

# Trae Solo 工程实现指南

*PRD→生产全链路自动化系统 v1\.0*

---

## 目录

1. Trae Solo 架构理解与核心概念

2. 完整工程目录结构设计

3. Orchestrator 总控引擎实现

4. 16大角色 Agent 与 Skill 封装

5. Blackboard 共享状态系统

6. 质量门禁自动化验证实现

7. TOKEN 优化机制实现

8. 知识沉淀与自动匹配系统

9. MCP 工具链集成

10. 部署与运行指南

11. 附录：完整代码模板

---

## 第一章 Trae Solo 架构理解与核心概念

### 1\.1 Trae Solo 核心特性

|特性|说明|本系统应用|
|---|---|---|
|**Blackboard 模式**|全局共享黑板，Agent通过读写黑板通信|✅ 基底介导通信的完美实现|
|**MCP 协议**|Model Context Protocol，统一工具接口|✅ 集成Git、CI、测试、部署工具|
|**Skill 系统**|可复用的能力封装|✅ 16大角色封装为独立Skill|
|**Router 架构**|任务自动路由到合适Agent|✅ Orchestrator智能调度|
|**React 模式**|感知→思考→行动→观察循环|✅ Loop Engineering原生支持|
|**持久化状态**|跨会话状态保持|✅ 断点续跑与崩溃恢复|

**关键洞察**：Trae Solo的Blackboard模式完美匹配我们的「基底介导通信」设计原则。所有Agent不直接通信，只通过黑板读写状态。这正是Loop Engineering推荐的最佳实践！

### 1\.2 架构映射：我们的设计 → Trae Solo

|我们的设计|Trae Solo对应实现|
|---|---|
|Orchestrator 总控调度|Custom Router \+ Supervisor Agent|
|共享存储 /state/|Blackboard（全局黑板）|
|16大角色|Specialized Agents / Skills|
|Worktree隔离|Agent Isolation \+ Sandbox|
|Maker\-Checker分离|Dual Agent Architecture|
|质量门禁|Verification Gates \+ Guards|
|Ralph模式|Stateless Agent \+ Context Reset|

### 1\.3 关键设计决策

#### ✅ 采用的设计

- **Blackboard优先**：所有状态存黑板，Agent无状态

- **无状态Agent**：每个Agent调用重置上下文（Ralph模式）

- **专用Skill**：每个角色封装为独立Skill

- **集中式路由**：Orchestrator统一调度决策

- **独立验证**：Checker Agent与Maker完全分离

#### ❌ 避免的反模式

- 禁止Agent直接对话

- 禁止有状态Agent

- 禁止协调者做领域推理

- 禁止生成者自验证

- 禁止无限循环无护栏

## 第二章 完整工程目录结构设计

### 2\.1 标准目录结构

```text
trae-auto-dev/
├── .trae/                          # Trae 配置目录
│   ├── trae.toml                   # 主配置文件
│   ├── agents/                     # Agent 定义
│   │   ├── orchestrator.agent.toml
│   │   ├── product-manager.agent.toml
│   │   ├── requirements.agent.toml
│   │   ├── ux-researcher.agent.toml
│   │   ├── ui-designer.agent.toml
│   │   ├── architect.agent.toml
│   │   ├── backend.agent.toml
│   │   ├── frontend.agent.toml
│   │   ├── bugfix.agent.toml
│   │   ├── code-reviewer.agent.toml
│   │   ├── performance.agent.toml
│   │   ├── tester.agent.toml
│   │   ├── knowledge-curator.agent.toml
│   │   ├── documenter.agent.toml
│   │   ├── final-reviewer.agent.toml
│   │   └── devops.agent.toml
│   └── skills/                     # Skill 定义
│       ├── code-analysis/
│       ├── testing/
│       ├── git-operations/
│       ├── quality-gates/
│       └── knowledge-base/
├── blackboard/                     # 黑板（共享状态）
│   ├── state.json                  # 当前状态快照
│   ├── requirements/               # 需求阶段产出
│   ├── design/                     # 设计阶段产出
│   ├── architecture/               # 架构设计
│   ├── code/                       # 代码产出
│   ├── quality/                    # 质量报告
│   ├── knowledge/                  # 知识库
│   └── docs/                       # 文档
├── workflows/                      # 工作流定义
│   ├── main.orchestration.json     # 主编排流程
│   ├── phases/                     # 各阶段工作流
│   │   ├── 01-requirements.json
│   │   ├── 02-design.json
│   │   ├── 03-architecture.json
│   │   ├── 04-development.json
│   │   ├── 05-quality-gates.json
│   │   ├── 06-knowledge.json
│   │   ├── 07-docs.json
│   │   ├── 08-final-review.json
│   │   └── 09-deploy.json
│   └── gates/                      # 门禁定义
│       ├── gate1-code-review.json
│       ├── gate2-performance.json
│       ├── gate3-testing.json
│       └── gate4-final.json
├── config/                         # 配置文件
│   ├── budget.yaml                 # 预算配置
│   ├── quality.yaml                # 质量标准
│   ├── agents.yaml                 # Agent角色配置
│   └── knowledge.yaml              # 知识库配置
├── mcp/                            # MCP 工具配置
│   ├── git.mcp.json
│   ├── shell.mcp.json
│   ├── filesystem.mcp.json
│   └── testing.mcp.json
├── scripts/                        # 辅助脚本
│   ├── init-blackboard.sh
│   ├── snapshot-state.sh
│   └── restore-state.sh
└── README.md                       # 项目说明
```

### 2\.2 核心配置文件：trae\.toml

```toml
# =============================================================================
# PRD→生产 全链路自动化系统 - Trae Solo 配置
# =============================================================================
version = "1.0"
name = "auto-dev-pipeline"
description = "End-to-end automated development pipeline: PRD to Production"

[system]
mode = "orchestration"           # orchestration / chat / agent
blackboard_enabled = true        # 启用黑板模式
persist_state = true             # 状态持久化
max_iterations = 200             # 全局最大迭代
max_budget_usd = 100.0          # 全局预算上限
parallel_agents = 16             # 最大并行Agent数

[blackboard]
path = "./blackboard"
auto_snapshot = true
snapshot_interval = "5m"
enable_versioning = true

[router]
type = "custom"                  # 使用自定义路由（Orchestrator）
default_agent = "orchestrator"
enable_fallback = true

[agents]
  [agents.orchestrator]
  enabled = true
  type = "supervisor"
  isolation = "process"

  [agents.product_manager]
  enabled = true
  type = "specialist"

  [agents.requirements]
  enabled = true
  type = "specialist"

  [agents.architect]
  enabled = true
  type = "specialist"

  [agents.backend]
  enabled = true
  type = "specialist"
  worktree = true                # 启用独立工作树

  [agents.frontend]
  enabled = true
  type = "specialist"
  worktree = true

[optimization]
ralph_mode = true                # Ralph模式：每轮重置上下文
narrow_context = true            # 窄上下文：只传必要信息
enable_caching = true            # 结果缓存
cache_ttl = "24h"

[mcp]
  [[mcp.servers]]
  name = "filesystem"
  command = "npx"
  args = ["@modelcontextprotocol/server-filesystem", "./"]

  [[mcp.servers]]
  name = "git"
  command = "npx"
  args = ["@modelcontextprotocol/server-git", "./"]

  [[mcp.servers]]
  name = "shell"
  command = "npx"
  args = ["@modelcontextprotocol/server-shell"]

```

## 第三章 Orchestrator 总控引擎实现

### 3\.1 Orchestrator Agent 定义

```toml
# =============================================================================
# Orchestrator - 总控调度中心
# =============================================================================
name = "orchestrator"
version = "1.0"
type = "supervisor"

[system]
isolation = "process"
worktree = false
stateless = true  # Ralph模式：无状态

[capabilities]
read_blackboard = true
write_blackboard = true
spawn_agents = true
route_tasks = true
manage_budget = true

[constraints]
max_concurrent_tasks = 16
task_timeout = "300s"
max_retries = 3

[prompt]
system = """
# ROLE: Orchestrator - 总控调度中心

## 核心铁律（必须严格遵守）
1. 只做任务路由和状态管理，绝不做领域推理
2. 所有中间状态读写Blackboard，不通过上下文传递
3. 严格执行预算管控，触发硬刹车立即停止
4. Maker-Checker严格分离，验证必须用独立Agent

## 状态机
PHASES = [
    "INIT",           # 0: 初始化
    "REQUIREMENTS",   # 1: 需求基线
    "DESIGN",         # 2: 交互+视觉设计
    "ARCHITECTURE",   # 3: 技术架构
    "DEVELOPMENT",    # 4: 并行开发
    "QUALITY_GATES",  # 5: 质量门禁
    "KNOWLEDGE",      # 6: 知识沉淀
    "DOCUMENTATION",  # 7: 文档生成
    "FINAL_REVIEW",   # 8: 最终终审
    "DEPLOY",         # 9: 部署上线
    "DONE"            # 10: 完成
]

## 调度算法
function next_tasks(current_state):
    1. 读取Blackboard当前状态
    2. 检查预算是否耗尽 → 触发硬刹车
    3. 找出所有依赖满足且未执行的任务
    4. 按优先级排序，并行扇出（最多16个）
    5. 分派给对应Specialist Agent
    6. 等待任务完成 → 更新Blackboard
    7. 检查Phase完成条件 → 进入下一Phase
"""

```

### 3\.2 状态机核心实现

```typescript
/**
 * Orchestrator 状态机核心实现
 * 基于Blackboard的无状态调度引擎
 */
export interface PipelineState {
  phase: Phase;
  tasks: Record<string, TaskState>;
  dependencies: Record<string, string[]>;
  budget: BudgetState;
  qualityGates: QualityGates;
  startedAt: string;
  updatedAt: string;
}

export type Phase = 
  | "INIT"
  | "REQUIREMENTS"
  | "DESIGN"
  | "ARCHITECTURE"
  | "DEVELOPMENT"
  | "QUALITY_GATES"
  | "KNOWLEDGE"
  | "DOCUMENTATION"
  | "FINAL_REVIEW"
  | "DEPLOY"
  | "DONE";

export interface TaskState {
  id: string;
  phase: Phase;
  agentType: string;
  status: "PENDING" | "RUNNING" | "DONE" | "FAILED";
  inputPaths: string[];
  outputPath: string;
  attempts: number;
  maxAttempts: number;
  startedAt?: string;
  completedAt?: string;
  error?: string;
}

export class OrchestratorStateMachine {
  private readonly BLACKBOARD_PATH = "./blackboard/state.json";

  /**
   * 调度主循环 - 由Trae React模式触发
   */
  async tick(): Promise<void> {
    const state = await this.loadState();

    // 三道硬刹车检查
    if (!this.hasBudget(state)) {
      await this.emergencyStop(state);
      return;
    }

    // 检查当前Phase是否完成
    if (this.isPhaseComplete(state)) {
      await this.advancePhase(state);
    }

    // 调度下一批任务
    const readyTasks = this.getReadyTasks(state);
    await this.spawnAgents(readyTasks, state);

    // 保存状态
    await this.saveState(state);
  }

  /**
   * 三道硬刹车：预算、迭代、无进展检测
   */
  private hasBudget(state: PipelineState): boolean {
    const iterations = Object.values(state.tasks)
      .flatMap(t => t.attempts)
      .reduce((a, b) => a + b, 0);

    return (
      iterations < 200 &&
      state.budget.currentCost < state.budget.maxCost &&
      !this.detectNoProgress(state)
    );
  }

  /**
   * 获取所有依赖已满足的就绪任务
   */
  private getReadyTasks(state: PipelineState): TaskState[] {
    return Object.values(state.tasks).filter(task => {
      if (task.status !== "PENDING") return false;

      // 检查所有依赖是否完成
      const deps = state.dependencies[task.id] || [];
      return deps.every(depId => 
        state.tasks[depId]?.status === "DONE"
      );
    });
  }

  /**
   * 并行扇出：分派任务给Specialist Agent
   */
  private async spawnAgents(tasks: TaskState[], state: PipelineState): Promise<void> {
    // 并行执行（最多16个）
    const batch = tasks.slice(0, 16);

    for (const task of batch) {
      task.status = "RUNNING";
      task.startedAt = new Date().toISOString();

      // Trae Agent Spawn API
      await trae.spawnAgent({
        agent: task.agentType,
        input: {
          taskId: task.id,
          // 最小输入原则：只传Blackboard路径，不传内容
          inputPaths: task.inputPaths,
          outputPath: task.outputPath,
          acceptanceCriteria: this.getAcceptanceCriteria(task)
        },
        isolation: "process",
        worktree: task.agentType.includes("backend") || task.agentType.includes("frontend")
      });
    }
  }
}

```

### 3\.3 任务依赖图定义

```json
{
  "version": "1.0",
  "phases": [
    {
      "id": "REQUIREMENTS",
      "tasks": [
        {
          "id": "pm_review_prd",
          "agent": "product-manager",
          "input": ["blackboard/input/prd.md"],
          "output": "blackboard/requirements/product-decision.md",
          "dependencies": []
        },
        {
          "id": "analyze_requirements",
          "agent": "requirements",
          "input": ["blackboard/requirements/product-decision.md"],
          "output": "blackboard/requirements/structured.json",
          "dependencies": ["pm_review_prd"]
        }
      ],
      "gate": "all_requirements_testable"
    },
    {
      "id": "DESIGN",
      "tasks": [
        {
          "id": "ux_design",
          "agent": "ux-researcher",
          "input": ["blackboard/requirements/structured.json"],
          "output": "blackboard/design/ux-flow.md",
          "dependencies": ["analyze_requirements"]
        },
        {
          "id": "ui_design",
          "agent": "ui-designer",
          "input": ["blackboard/design/ux-flow.md"],
          "output": "blackboard/design/ui-specs/",
          "dependencies": ["ux_design"]
        }
      ],
      "gate": "design_complete"
    },
    {
      "id": "DEVELOPMENT",
      "parallel": true,
      "tasks": [
        {
          "id": "backend_dev",
          "agent": "backend",
          "input": ["blackboard/architecture/spec.json"],
          "output": "blackboard/code/backend/",
          "dependencies": ["architecture_design"],
          "worktree": true
        },
        {
          "id": "frontend_dev",
          "agent": "frontend",
          "input": ["blackboard/architecture/spec.json", "blackboard/design/ui-specs/"],
          "output": "blackboard/code/frontend/",
          "dependencies": ["architecture_design"],
          "worktree": true
        }
      ],
      "gate": "code_compiles_and_tests_pass"
    }
  ]
}

```

## 第四章 16大角色 Agent 与 Skill 封装

### 4\.1 Specialist Agent 模板

所有16个角色遵循统一的Agent定义模板，确保一致性和可互换性。

```toml
# =============================================================================
# [角色名称] - Specialist Agent 模板
# =============================================================================
name = "[agent_id]"
version = "1.0"
type = "specialist"

[system]
isolation = "process"           # 进程级隔离
worktree = false                # 是否需要独立工作树
stateless = true                # Ralph模式：无状态，每轮重置
reset_context_each_turn = true  # 每轮重置上下文（关键！）

[capabilities]
read_blackboard = true          # 只读自己需要的路径
write_blackboard = true         # 只写指定输出路径
use_mcp_tools = true            # MCP工具访问

[constraints]
max_input_tokens = 8000         # 输入Token限制
max_output_tokens = 4000        # 输出Token限制
timeout = "300s"
max_retries = 3

[blackboard]
# 最小输入原则：只声明需要读取的路径
read_paths = [
  "blackboard/[input_path]/*"
]
# 只允许写入指定输出路径
write_paths = [
  "blackboard/[output_path]/*"
]

[prompt]
system = """
# ROLE: [角色全称]

## 核心职责
[具体职责列表]

## 输入
从Blackboard读取：{{input_paths}}

## 输出
写入Blackboard：{{output_path}}

## 验收标准（必须满足）
function is_done(output):
    [可执行的停止条件代码]

## 执行流程
1. 从Blackboard读取输入文件
2. 执行专业领域推理
3. 生成输出并验证
4. 写入Blackboard
5. 返回：SUCCESS/FAILED + 摘要

## 重要约束
- 只做本角色领域内的推理
- 不做跨领域决策
- 严格遵守输出Schema
- 失败必须明确报错，绝不静默
"""

```

### 4\.2 关键角色示例：Code\-Reviewer（Checker角色）

```toml
name = "code-reviewer"
version = "1.0"
type = "specialist"

[system]
isolation = "process"
stateless = true
reset_context_each_turn = true

[blackboard]
read_paths = [
  "blackboard/code/backend/src/**/*.ts",
  "blackboard/code/frontend/src/**/*.tsx"
]
write_paths = [
  "blackboard/quality/code-review-report.json"
]

[prompt]
system = """
# ROLE: Code-Reviewer - 代码质量门禁

## 核心职责
独立审查代码质量，执行Gate 1门禁。**绝对禁止与开发者直接沟通**。

## 验收标准（必须100%满足）
function is_done(report):
    return (
        report.blocker_issues.length === 0 AND
        report.security_critical.length === 0 AND
        report.coverage >= 80
    )

## 检查清单
1. ✅ 代码规范（ESLint/Prettier）
2. ✅ 安全漏洞扫描
3. ✅ 代码重复率 ≤ 3%
4. ✅ 圈复杂度 ≤ 10
5. ✅ 单元测试覆盖率 ≥ 80%
6. ✅ 无硬编码密钥
7. ✅ SQL注入防护

## 输出格式
{
  "status": "PASS|FAIL",
  "blocker_issues": [],
  "major_issues": [],
  "minor_issues": [],
  "coverage": 85,
  "summary": "..."
}
"""

```

### 4\.3 关键角色示例：Knowledge\-Curator

```toml
name = "knowledge-curator"
version = "1.0"
type = "specialist"

[system]
stateless = true

[blackboard]
read_paths = [
  "blackboard/**/*.log",
  "blackboard/quality/*.json",
  "blackboard/code/**/*"
]
write_paths = [
  "blackboard/knowledge/entries/"
]

[prompt]
system = """
# ROLE: Knowledge-Curator - 知识沉淀官

## 核心职责
从开发过程中自动提取可复用知识，实现复利效应。

## 知识提取触发点
- Bug修复完成 → 提取问题+解决方案
- 架构决策 → 记录选型依据和trade-off
- Code Review发现 → 沉淀最佳实践
- 任务失败 → 记录踩坑教训

## 知识条目格式
{
  "id": "uuid",
  "category": "bugfix|architecture|bestpractice|pitfall",
  "problem": "问题描述",
  "solution": "解决方案",
  "root_cause": "根因分析",
  "tags": ["技术栈", "领域"],
  "embedding": "[向量表示]"
}

## 匹配算法
下次相似问题：cosine_similarity > 0.85 → 自动推荐
"""

```

### 4\.4 Skill封装：质量门禁验证

```typescript
/**
 * Quality Gate Verification Skill
 * Maker-Checker分离的自动化验证
 */
export async function verifyGate(
  gateType: "code" | "performance" | "testing" | "final",
  reportPath: string
): Promise<{ passed: boolean; reason?: string }> {

  const report = await trae.readBlackboard(reportPath);

  switch (gateType) {
    case "code":
      return {
        passed: 
          report.blocker_issues?.length === 0 &&
          report.security_critical?.length === 0 &&
          report.coverage >= 80
      };

    case "performance":
      return {
        passed:
          report.p95_response_time <= 300 &&
          report.error_rate <= 0.001 &&
          report.throughput >= 1000
      };

    case "testing":
      return {
        passed:
          report.p0_bugs === 0 &&
          report.p1_bugs === 0 &&
          report.coverage === 100
      };

    case "final":
      return {
        passed:
          report.all_gates_passed &&
          report.risk_level === "LOW"
      };
  }
}

```

## 第五章 Blackboard 共享状态系统

### 5\.1 Blackboard Schema 定义

```json-schema
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Blackboard State Schema",
  "type": "object",
  "required": ["phase", "tasks", "budget", "qualityGates"],
  "properties": {
    "phase": {
      "type": "string",
      "enum": ["INIT", "REQUIREMENTS", "DESIGN", "ARCHITECTURE", "DEVELOPMENT", "QUALITY_GATES", "KNOWLEDGE", "DOCUMENTATION", "FINAL_REVIEW", "DEPLOY", "DONE"]
    },
    "tasks": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["id", "status", "agentType", "attempts"],
        "properties": {
          "status": {"enum": ["PENDING", "RUNNING", "DONE", "FAILED"]}
        }
      }
    },
    "budget": {
      "type": "object",
      "required": ["maxCost", "currentCost", "maxIterations", "currentIteration"],
      "properties": {
        "maxCost": {"type": "number", "minimum": 0},
        "currentCost": {"type": "number", "minimum": 0}
      }
    },
    "qualityGates": {
      "type": "object",
      "properties": {
        "codeReview": {"enum": ["NOT_STARTED", "RUNNING", "PASSED", "FAILED"]},
        "performance": {"enum": ["NOT_STARTED", "RUNNING", "PASSED", "FAILED"]},
        "testing": {"enum": ["NOT_STARTED", "RUNNING", "PASSED", "FAILED"]},
        "final": {"enum": ["NOT_STARTED", "RUNNING", "PASSED", "FAILED"]}
      }
    }
  }
}

```

**上下文污染防护**：每个Agent写入Blackboard时，Trae自动执行Schema验证。任何不符合Schema的写入（幻觉输出）立即被拦截，防止污染全局状态。

### 5\.2 快照与恢复机制

```bash
#!/bin/bash
# Blackboard 自动快照脚本
# 每5分钟执行，支持断点续跑

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_DIR="./blackboard/.snapshots/$TIMESTAMP"

mkdir -p $SNAPSHOT_DIR

# 全量快照
cp -r ./blackboard/* $SNAPSHOT_DIR/ 2>/dev/null || true

# 保留最近100个快照
ls -dt ./blackboard/.snapshots/*/ | tail -n +101 | xargs rm -rf

echo "Snapshot created: $SNAPSHOT_DIR"

```

## 第六章 TOKEN 优化机制实现

### 6\.1 Ralph模式：每轮上下文重置

```toml
[system]
stateless = true                    # 关键：无状态
reset_context_each_turn = true      # 关键：每轮重置
max_context_turns = 1               # 只保留当前轮

# 效果：每个Agent只看到当前任务，不携带历史对话
# 节省：30-40% TOKEN

```

### 6\.2 窄上下文：只传递必要信息

```typescript
/**
 * 最小输入原则：只传文件路径，不传文件内容
 * Agent自己从Blackboard读取需要的部分
 */
function prepareAgentInput(task: TaskState): AgentInput {
  return {
    taskId: task.id,
    // 只传路径，不传内容！
    inputPaths: task.inputPaths,
    outputPath: task.outputPath,
    acceptanceCriteria: task.acceptanceCriteria,
    // ❌ 绝对不要这样做：
    // inputContent: readAllFiles(task.inputPaths) → 巨量TOKEN浪费
  };
}

// 节省：40-50% TOKEN

```

### 6\.3 结果缓存机制

```typescript
/**
 * 任务结果缓存：相同输入直接复用
 */
export class TaskResultCache {
  private cache = new Map<string, CacheEntry>();
```

getCacheKey\(task: TaskState, inputs: any\[\]\): string \{
// 输入指纹：任务类型 \+ 输入文件内容哈希
const contentHash = inputs\.map\(i =\> hashFileContent\(i\)\)\.join\(

## 第六章 TOKEN 优化机制实现

### 6\.1 核心优化策略汇总

|\#|策略|Trae实现方式|预期节省|
|---|---|---|---|
|1|**协调者窄上下文**|Orchestrator只存状态ID和路径，不存内容|40\-50%|
|2|**Ralph每轮重置**|stateless=true \+ reset\_context\_each\_turn|30\-40%|
|3|**最小输入原则**|只传Blackboard路径，Agent自己读取|20\-30%|
|4|**Skill资产化复用**|Trae Skill系统封装重复工作|50\-80%|
|5|**结果缓存**|输入指纹哈希 \+ 24小时缓存|最高100%|
|6|**并行扇出**|Trae原生并行Agent调度|20\-30%|
|7|**短期记忆窗口**|max\_context\_turns = 1|20\-30%|
|8|**心跳抖动**|伪随机唤醒间隔|90%\+（监控）|
|9|**3\-7 Agent规则**|层级Agent架构|随规模递增|
||**整体综合节省**||**60\-70%**|

### 6\.2 Agent无状态配置模板

```toml
[system]
stateless = true                    # Ralph模式：无状态
reset_context_each_turn = true      # 每轮重置上下文
max_context_turns = 1               # 只保留当前轮对话
# 节省：30-40% TOKEN

```

## 第七章 MCP 工具链集成

### 7\.1 核心MCP工具配置

```json
{
  "name": "filesystem",
  "command": "npx",
  "args": ["@modelcontextprotocol/server-filesystem", "./blackboard"]
}

```

```json
{
  "name": "git",
  "command": "npx",
  "args": ["@modelcontextprotocol/server-git", "./blackboard/code"]
}

```

### 7\.2 工具链权限矩阵

|角色|Filesystem|Git|Shell|Testing|
|---|---|---|---|---|
|Backend/Frontend|✅ 读写|✅|✅|✅|
|Code\-Reviewer|✅ 只读|❌|❌|❌|
|Performance|✅ 只读|❌|✅|✅|
|全栈测试员|✅ 只读|❌|✅|✅|
|DevOps|✅ 读写|✅|✅|✅|

## 第八章 部署与运行指南

### 8\.1 快速开始三步法

```bash
# Step 1: 放入PRD文件
cp your-prd.md ./blackboard/input/prd.md

# Step 2: 启动Trae
trae start

# Step 3: 运行自动化流程
trae run workflow main.orchestration.json

# 监控：实时查看状态
trae status

```

### 8\.2 断点续跑机制

```bash
# 列出可用快照
ls blackboard/.snapshots/

# 恢复到指定状态
./scripts/restore-state.sh [snapshot_id]

# 从断点继续
trae resume

```

## 第九章 完整实现路线图

|阶段|工作内容|预计工时|
|---|---|---|
|**Phase 1**|工程目录搭建 \+ trae\.toml配置 \+ Blackboard初始化|0\.5天|
|**Phase 2**|Orchestrator状态机 \+ 调度算法 \+ 预算管控|1天|
|**Phase 3**|16个Agent配置 \+ System Prompt编写|1\.5天|
|**Phase 4**|4层质量门禁Skill \+ 自动化验收|1天|
|**Phase 5**|知识库 \+ 自动提取 \+ 相似度匹配|1天|
|**Phase 6**|MCP工具链配置 \+ 权限隔离|0\.5天|
|**Phase 7**|端到端测试 \+ TOKEN优化 \+ Bug修复|1天|
||**总计**|**约6\.5天**|

---

**核心结论：Trae Solo是这套机制的完美运行载体**

✅ **Blackboard模式** = 我们的基底介导通信架构

✅ **Skill系统** = 我们的16角色封装

✅ **Ralph模式** = 我们的TOKEN优化策略

✅ **MCP协议** = 我们的自动化工具链

✅ **状态持久化** = 我们的断点续跑

**这套架构在Trae Solo中可以完美、原生地实现！** 💯

> （注：文档部分内容可能由 AI 生成）
