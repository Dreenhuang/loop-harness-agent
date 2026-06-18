# Skill: orchestrate-map-reduce 高阶发散-收敛编排

> **Skill ID**: `orchestrate-map-reduce`
> **类型**: 编排类（高阶 Skill）
> **解决偏差**: D-02（Orchestrate-Map-Reduce 缺 Skill）
> **蓝皮书**: 第五章 场景 6

## 一、用途

**实施高阶编排模式**：Map（多 Agent 并行发散探索）→ Reduce（收敛到最优解）。是高阶 Skill（接受另一个 Skill 作为输入的 Skill）。

## 二、模式定义

```yaml
orchestrate_map_reduce:
  diverge:
    description: "将问题扇出给多个 Agent，每个探索不同解法"
    agents: 5  # 并行 5 个 Agent
    budget_per_agent:
      tokens: 5000
      time: "10min"
  
  converge:
    description: "收集所有方案，按标准评分收敛"
    scoring:
      coverage: "测试覆盖率"
      diff_size: "代码改动量"
      performance: "性能提升"
      risk: "风险评估"
    selection: "加权评分最高"
```

## 三、典型应用

### 3.1 Bug 修复（多方案对比）

```yaml
bug: "P95 响应时间 800ms 超标"
map:
  - agent: "@Bug-Defect-Repairer-A"
    approach: "加 Redis 缓存"
  - agent: "@Bug-Defect-Repairer-B"
    approach: "SQL 优化 + 复合索引"
  - agent: "@Bug-Defect-Repairer-C"
    approach: "分库分表"
  - agent: "@Bug-Defect-Repairer-D"
    approach: "异步队列削峰"
  - agent: "@Bug-Defect-Repairer-E"
    approach: "前端预加载 + 接口合并"
reduce:
  scoring:
    p95_improvement: "weight 0.4"
    diff_size: "weight 0.2"
    risk: "weight 0.2"
    implementation_time: "weight 0.2"
  selection: "加权最高分"
  output: "blackboard/bugs/best-solution.md"
```

### 3.2 架构选型（多技术栈对比）

```yaml
decision: "前端框架选型"
map:
  - agent: "@Architect-1"
    approach: "Vue 3 + Vite"
  - agent: "@Architect-2"
    approach: "React 18 + Next.js"
  - agent: "@Architect-3"
    approach: "Svelte 4 + SvelteKit"
  - agent: "@Architect-4"
    approach: "Solid.js + Vite"
  - agent: "@Architect-5"
    approach: "Astro + 任意框架"
reduce:
  scoring:
    team_expertise: "weight 0.3"
    ecosystem: "weight 0.2"
    performance: "weight 0.2"
    learning_curve: "weight 0.2"
    long_term_maintainability: "weight 0.1"
  output: "blackboard/architecture/framework-decision.md"
```

## 四、调用方式

```text
@Orchestrator 检测需要多方案对比
    ↓
激活 orchestrate-map-reduce
    ├─ 设置问题空间
    ├─ 分配 N 个 Agent
    └─ 设置评分标准
    ↓
并行执行（Map 阶段）
    ↓
评分收敛（Reduce 阶段）
    ↓
输出最优解 + 评分理由
```

## 五、决策日志

每次 Map-Reduce 完整记录到 `blackboard/map_reduce/<id>.json`，含：
- 议题
- 5 个 Agent 的方案
- 评分明细
- 最终选择 + 理由
