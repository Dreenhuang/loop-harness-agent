# Web Feature Development Domain Chip v1.0

> **封装层级**：第 4 层 - Domain Chip（终极形态）
> **所属系统**：Loop Agent v1.0
> **Autoloop**：✅ 已启用（自进化循环）

---

## 一、这是什么

把"PRD→生产"完整流水线打包成**领域黑盒芯片**。

**对外只暴露两个接口**：

```yaml
输入: PRD 文档
输出: 生产级可部署代码 + 完整文档 + 质量报告 + 知识沉淀
```

**内部完全黑盒化**：

```
输入 PRD
    ↓
┌─────────────────────────────────────┐
│  Web Feature Chip（黑盒）            │
│                                     │
│  Workflow Blueprint (10 相位)       │
│  + 16 Agent Profiles                 │
│  + 10 Skills (4 门禁 + 5 原子 + 1)  │
│  + 知识库                            │
│  + Benchmark 评估集                  │
│  + Autoloop 自优化                   │
│                                     │
└─────────────────────────────────────┘
    ↓
输出生产代码 + 文档 + 报告
```

---

## 二、目录结构

```text
web-feature-chip/
├── chip.json                # 芯片元数据（输入输出契约）
├── README.md                # 本文件
├── workflow/                # 编排蓝图引用
│   └── prd-to-production.json
├── agents/                  # Agent Profile 引用（链接到 .trae/agents/）
├── skills/                  # Skill 资产引用（链接到 .trae/skills/）
├── knowledge/               # 领域知识库
│   ├── problems/            # 问题解决方案库
│   ├── architectures/       # 架构决策库
│   ├── components/          # 可复用组件库
│   ├── best-practices/      # 最佳实践库
│   └── pitfalls/            # 踩坑记录库
└── benchmark/               # 评估基准
    ├── eval-set.json        # 评估集
    ├── scoring-rubric.md    # 评分标准
    └── history/             # 历史评分
```

---

## 三、使用方式

### 3.1 命令行

```bash
# 在任何项目根目录运行
loop-agent chip run web-feature-chip \
  --prd ./docs/prd.md \
  --output ./output
```

### 3.2 通过 Loop Agent 主入口

```text
@Orchestrator 请用 web-feature-chip 处理 PRD：
- PRD 路径：docs/prd.md
- 技术栈：默认（Vue3 + Bun + Supabase）
- 部署目标：CloudBase
```

### 3.3 通过黑板

将 PRD 放到 `<项目>/项目进度记录.md` 区块四，并触发 `/loop-agent`。

---

## 四、Autoloop 自进化

**核心能力**：本芯片不是静态流水线，会基于 Benchmark 自我改进。

```text
┌────────────────────────────────────┐
│  Autoloop 闭环                      │
│                                    │
│  1. 标准化工作流（形状稳定）         │
│  2. 定义 Benchmark（可度量）         │
│  3. 变异探索（小范围改动 Skills/    │
│     Prompts/Workflow）              │
│  4. 评分对比（before/after）        │
│  5. 优胜劣汰（赢了保留/输了回滚）    │
│                                    │
└────────────────────────────────────┘
```

### 4.1 评估指标

| 指标 | 说明 | 权重 |
|------|------|------|
| `code_quality_score` | 代码质量分 | 25% |
| `test_coverage_percent` | 测试覆盖率 | 20% |
| `performance_p95_ms` | P95 响应时间 | 20% |
| `security_score` | 安全评分 | 20% |
| `ux_quality_score` | UX 评分 | 15% |

### 4.2 变异策略

```yaml
mutation_targets:
  - agent_prompts       # Agent 系统提示词微调
  - skill_thresholds    # 门禁阈值微调
  - workflow_order      # Phase 顺序调整
  - parallel_strategy   # 并行策略调整

mutation_constraints:
  max_change_per_iteration: 0.05   # 最多 5% 改动
  requires_baseline_evaluation: true
  requires_rollback_capability: true
```

### 4.3 进化记录

```text
domain-chips/web-feature-chip/benchmark/history/
├── 2026-06-15_v1.0-baseline.json  # 基线
├── 2026-07-15_v1.1-mutation-001.json  # 变异 001
└── ...
```

---

## 五、与其他封装层的关系

```
┌─────────────────────────────────────────────┐
│ 第 4 层：Domain Chip（本层）                  │
│         ↓ 引用                               │
│ 第 3 层：Workflow Blueprint                   │
│         ↓ 引用                               │
│ 第 2 层：Agent Profile × 16                  │
│         ↓ 调用                               │
│ 第 1 层：Skill × 10                          │
└─────────────────────────────────────────────┘
```

**本芯片是其他 3 层的"集大成"**：
- 不重新发明 Skill
- 不重新发明 Agent
- 不重新发明 Workflow
- 只在它们之上做"领域特化 + 自进化"

---

## 六、安全与护栏

```yaml
hard_limits:
  max_budget_per_run_usd: 100.0
  max_iterations_per_run: 200
  
require_human_approval:
  - production_deploy
  - rollback_decision
  - budget_increase

forbidden:
  - 修改架构核心（不通过 PM 评审）
  - 绕过 Gate 4
  - 静默失败
```

---

## 七、版本演进

| 版本 | 日期 | 核心变更 | 评分 |
|------|------|----------|------|
| v1.0 | 2026-06-15 | 基线版本 | 待评估 |

---

## 八、一句话总结

> **Domain Chip 不是新东西，是把 Skill/Agent/Workflow 装进一个「PRD 进，代码出」的黑盒，让用户不必懂 Agent 工程也能享受 Loop Engineering 的复利。**

---

**【Web Feature Chip v1.0 · Autoloop 启用 · 等待首次评估】**
