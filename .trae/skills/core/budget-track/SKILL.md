# Skill: budget-track 预算统计

> **Skill ID**: `budget-track`
> **所属层级**: 第 1 层 - Skill 层（原子能力）
> **调用方**: 任何 Agent
> **调用时机**: 每个 Phase 开始前 / 结束后

---

## 一、用途

实时统计 Loop Agent 的 Token 消耗、迭代次数、预算占比，防止预算耗尽。

---

## 二、预算模型

```yaml
global_budget:
  max_cost_usd: 100.0        # 全局硬上限
  max_iterations: 200        # 全局最大迭代
  warn_threshold: 0.8        # 80% 警告
  stop_threshold: 0.95       # 95% 硬停止

phase_budget:
  REQUIREMENTS: { cost: 5, iter: 10 }
  DESIGN: { cost: 10, iter: 20 }
  ARCH: { cost: 10, iter: 15 }
  DEV: { cost: 40, iter: 80 }
  QA: { cost: 25, iter: 50 }
  KNOWLEDGE: { cost: 5, iter: 10 }
  DOC: { cost: 5, iter: 10 }
  FINAL: { cost: 3, iter: 5 }
  DEPLOY: { cost: 2, iter: 5 }
```

---

## 三、调用方式

```text
调用 budget-track Skill：
- 当前 phase: DEV
- 本次消耗: 2.3 USD
- 本次迭代: +3
```

---

## 四、输出

```json
{
  "global": {
    "used_usd": 23.5,
    "limit_usd": 100.0,
    "used_percent": 23.5,
    "status": "NORMAL"
  },
  "phase": {
    "name": "DEV",
    "used_usd": 8.2,
    "limit_usd": 40.0,
    "used_percent": 20.5,
    "iterations": 15,
    "iter_limit": 80
  },
  "action": "CONTINUE",
  "warnings": []
}
```

---

## 五、停止条件

```yaml
stop_conditions:
  - status == "STOP" → 立即停止 Loop
  - status == "WARN" → 输出警告信息，继续执行
  - status == "NORMAL" → 静默通过
```

---

**【budget-track · Loop Agent v1.0】**
