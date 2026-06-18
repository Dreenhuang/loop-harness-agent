# Skill: cognitive-surrender-defense 认知投降防御

> **Skill ID**: `cognitive-surrender-defense`
> **类型**: 防御类
> **解决偏差**: D-07（认知投降防御机制缺失）
> **蓝皮书**: 第八章认知陷阱 #3

## 一、问题背景

**当 Loop 跑得顺时，用户容易停止有主见、接受一切产出**。这是"认知投降"（Cognitive Surrender），长期会丧失技术判断力。

## 二、防御机制

### 2.1 AI 建议 vs 用户决策分歧追踪

```yaml
disagreement_tracker:
  enabled: true
  tracked_items:
    - "用户拒绝的 AI 建议"
    - "用户修改的 AI 输出"
    - "用户质疑的 AI 决策"
  
  metrics:
    - "用户干预率"
    - "用户否决率"
    - "用户修改幅度"
  
  warning_threshold:
    user_intervention_rate: 0.1  # < 10% 触发警告
    rationale: "用户干预率过低意味着用户放弃了独立判断"
```

### 2.2 强制"质疑"环节

```yaml
mandatory_questioning:
  frequency: "每个 Phase 完成后"
  questions:
    - "AI 给出的方案，你同意吗？为什么？"
    - "如果让你自己写，会怎么写？"
    - "这个方案有什么风险？"
    - "如果 AI 错了，会发生什么？"
  
  pass_criteria: "用户必须给出具体、有深度的回答"
  on_passivity: "警告：你接受得过于顺从，请深度思考"
```

### 2.3 决策审计日志

```yaml
decision_audit:
  log_path: "blackboard/cognitive_audit/"
  format: |
    {
      "timestamp": "...",
      "ai_suggestion": "...",
      "user_response": "agree|disagree|modify",
      "user_reasoning": "...",
      "depth_score": "1-10"
    }
  
  weekly_report:
    metrics:
      - "用户主动质疑率"
      - "用户深度思考得分"
      - "用户否决率"
    
    warning_if:
      - "用户质疑率 < 20%"
      - "深度思考得分 < 5"
      - "用户否决率 = 0%（从不反对 AI）"
```

## 三、调用方式

```text
每个 Phase 完成后
    ↓
触发 cognitive-surrender-defense
    ├─ 询问用户对 AI 产出的看法
    ├─ 评估用户回答深度
    ├─ 记录到 cognitive_audit/
    └─ 触发警告（如有）
```

## 四、用户自检工具

```yaml
self_check_questions:
  daily:
    - "今天我有没有完全接受 AI 的输出？"
    - "有没有我应该质疑但没质疑的？"
    - "我还能独立做出技术判断吗？"
  
  weekly:
    - "本周我否决了 AI 多少次？"
    - "本周我修改了 AI 输出多少次？"
    - "我对项目的理解是加深了还是变浅了？"
```
