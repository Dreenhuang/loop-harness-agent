# Skill: agent-mode-decision 多 Agent vs 单 Agent 决策矩阵

> **Skill ID**: `agent-mode-decision`
> **类型**: 决策类
> **解决偏差**: D-05（多/单 Agent 决策矩阵缺失）
> **蓝皮书**: 第七章选择战场

## 一、用途

**辅助用户在"多 Agent"和"单 Agent"之间做选择**。

## 二、决策矩阵（6 项判断）

```yaml
use_multi_agent_when:
  - "任务有真正独立的并行路径"
  - "工作超出单 Agent 上下文窗口"
  - "需要对抗验证（debate 模式）"
  - "任务运行数小时到数天，需要检查点"
  - "流程可重复，编排本身应成为可复用资产"
  - "上下文压缩不可接受"

use_single_agent_when:
  - "任务纯串行无并行性"
  - "工作舒适地装在一个上下文窗口里"
  - "协调开销超过执行时间"
  - "你还在快速迭代系统（多 Agent 重构成本高）"
  - "任务 < 30 分钟"
  - "对协调复杂度敏感"
```

## 三、决策算法

```python
def choose_mode(task):
    score = 0
    
    # 加分项
    if task.has_parallel_paths: score += 2
    if task.estimated_context > 50000: score += 2
    if task.requires_adversarial: score += 1
    if task.duration_hours > 2: score += 1
    if task.is_repeatable: score += 1
    if task.coordination_overhead < 0.3: score += 1
    
    # 减分项
    if task.is_serial: score -= 2
    if task.estimated_context < 10000: score -= 2
    if task.duration_minutes < 30: score -= 2
    if task.is_prototype: score -= 1
    
    if score >= 4:
        return "MULTI_AGENT"
    elif score >= 0:
        return "DEFAULT_TO_MULTI"  # 默认多 Agent
    else:
        return "SINGLE_AGENT"
```

## 四、输出格式

```json
{
  "task": "<任务描述>",
  "score": 5,
  "decision": "MULTI_AGENT",
  "reasons": [
    "+2 有并行路径",
    "+2 上下文超 50K",
    "+1 需要对抗验证"
  ],
  "recommendation": "使用多 Agent 模式（Orchestrator + 多个 Specialist）",
  "alternative": "如果时间紧，可用单 Agent + 串行"
}
```
