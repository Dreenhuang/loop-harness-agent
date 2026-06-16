# Skill: open-loop-mode 受控 Open Loop 模式

> **Skill ID**: `open-loop-mode`
> **类型**: 模式类
> **解决偏差**: D-04（Open Loop 模式缺失）
> **蓝皮书**: 第七章 Open vs Closed Loop

## 一、用途

**支持探索性任务的 Open Loop 模式**。在受控范围内提供 Agent 自由度，适用于：
- 技术选型探索（多种方案对比）
- 架构原型验证
- 未知领域调研

## 二、Closed Loop vs Open Loop 对比

| 维度 | Closed Loop（默认） | Open Loop（新） |
|------|---------------------|-----------------|
| 目标 | 明确 | 探索性 |
| 路径 | 预设 | 自由 |
| 评估 | 客观门禁 | 主观评估 |
| 预算 | 严格 | 宽松 |
| 风险 | 低 | 中高 |

## 三、Open Loop 安全约束

```yaml
open_loop_constraints:
  max_agents: 5                  # 最多 5 个并行 Agent
  max_duration_hours: 4          # 最多 4 小时（vs 9 小时）
  max_budget_usd: 30.0           # $30 上限（vs $100）
  require_explicit_go_signal: true  # 必须用户明确 GO 才继续
  require_snapshot_every: 30     # 每 30 分钟快照
  forbidden_operations:          # 禁止操作
    - "production_deploy"
    - "data_deletion"
    - "key_rotation"
    - "irreversible_action"
```

## 四、调用方式

```text
@Orchestrator 接收用户输入
    ↓
检测是否需要 Open Loop
    ├─ 关键词："探索"、"对比"、"调研"、"试试"、"POC"
    ├─ 任务评分（applicability-check 评分 3-5）
    └─ 任务特征：目标模糊 + 多种可能路径
    ↓
激活 open-loop-mode
    ├─ 输出："🔓 Open Loop 模式激活"
    ├─ 输出："⏰ 时间预算：4 小时 / 💰 Token 预算：$30"
    └─ 输出："📋 禁止操作清单"
```

## 五、与 Closed Loop 的切换

```yaml
mode_transition:
  open_to_closed:
    condition: "找到可行方案后"
    action: "激活 Closed Loop 跑实施"
  closed_to_open:
    condition: "遇到未预期问题"
    action: "激活 Open Loop 探索新方案"
```
