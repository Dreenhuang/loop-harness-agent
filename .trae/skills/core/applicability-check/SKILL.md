# Skill: applicability-check Loop 适用性智能判断

> **Skill ID**: `applicability-check`
> **类型**: 决策类（反过度工程）
> **解决偏差**: D-03（8 大反模式 #8 防御）
> **蓝皮书**: 第六章 8 大反模式

## 一、用途

**防止"对一次性任务强上 Loop"过度工程**。在启动 Loop Agent 之前，先评估当前任务是否值得用 Loop。

## 二、判断矩阵

### 2.1 必须用 Loop 的场景（高价值）

| 场景特征 | 评分 |
|----------|------|
| 工作可重复（≥ 2 次） | +3 |
| 验收条件可量化（测试可写） | +3 |
| 涉及多角色协作 | +2 |
| 涉及多 Phase（≥ 3） | +2 |
| 有时间预算约束 | +1 |
| **Loop 价值评分** | **≥ 6 = 推荐用 Loop** |

### 2.2 不建议用 Loop 的场景（低价值）

| 反模式 | 触发条件 | 建议 |
|--------|----------|------|
| 一次性原型 | "做个 demo 看看" | 手动 prompt 即可 |
| 一次性脚本 | "写个脚本" | 直接写 |
| 1 小时内完成 | "快速验证" | 单次 prompt |
| 模糊需求 | "做个差不多的" | 先澄清需求 |
| 强人工审美 | "设计稿要好看" | 人工为主 |

## 三、决策算法

```python
def should_use_loop(task):
    score = 0
    if task.repeatable: score += 3
    if task.has_quantifiable_acceptance: score += 3
    if task.multi_role: score += 2
    if task.phases_count >= 3: score += 2
    if task.time_budget_specified: score += 1

    if score >= 6:
        return "RECOMMEND_LOOP", score
    elif score >= 3:
        return "OPTIONAL", score
    else:
        return "OVERKILL", score
```

## 四、输出格式

```json
{
  "task": "<用户任务>",
  "score": 8,
  "decision": "RECOMMEND_LOOP",
  "reasons": [
    "+3 工作可重复",
    "+3 验收可量化",
    "+2 涉及多角色"
  ],
  "recommendation": "强烈建议使用 Loop Agent 模式",
  "alternative": null
}
```

## 五、调用方式

```text
@Orchestrator 启动前先调 applicability-check
→ 输出评分 + 建议
→ 如果 OVERKILL：警告用户，建议改用单次 prompt
→ 如果 RECOMMEND_LOOP：正常启动 Loop
```
