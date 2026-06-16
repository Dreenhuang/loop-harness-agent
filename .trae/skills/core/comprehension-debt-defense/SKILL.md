# Skill: comprehension-debt-defense 理解力腐蚀防御

> **Skill ID**: `comprehension-debt-defense`
> **类型**: 防御类
> **解决偏差**: D-06（理解力腐蚀防御机制缺失）
> **蓝皮书**: 第八章认知陷阱 #2

## 一、问题背景

**"存在的" ≠ "你真正理解的"**。Loop 越快产出大量 AI 生成的代码，用户对代码的理解会越来越浅。

## 二、防御机制

### 2.1 强制代码阅读点

```yaml
code_review_checkpoints:
  - phase: Phase 5 完成
    requirement: "用户必须审查核心模块 diff"
    enforcement: "hard_gate"
    fallback: "Gate 1 不通过"
    
  - phase: Gate 1 通过
    requirement: "用户必须能口头解释关键设计决策"
    enforcement: "self_assessment"
    
  - phase: Phase 8 文档生成
    requirement: "用户必须确认文档覆盖了关键理解点"
    enforcement: "checkbox_confirmation"
```

### 2.2 理解力评估

```yaml
comprehension_questions:
  - "这个模块的核心数据结构是什么？"
  - "如果某接口失败，系统会如何降级？"
  - "数据库 Schema 为什么这么设计？"
  - "关键性能瓶颈在哪里？"
  - "如何扩展支持 10 倍流量？"

user_response_required: true
pass_threshold: 80  # 80% 答对
on_fail: "触发 Code-Walkthrough Session"
```

### 2.3 文档深度自评

```yaml
document_depth_check:
  for_each_module:
    required:
      - "为什么这么设计？（not 是什么）"
      - "替代方案是什么？为什么不选？"
      - "扩展点在哪里？"
      - "已知限制是什么？"
    
    forbidden:
      - "自动生成的 boilerplate 注释"
      - "复制粘贴的函数头"
      - "无信息量的 README"
```

## 三、调用方式

```text
Gate 1 完成后
    ↓
自动触发 comprehension-debt-defense
    ├─ 生成 5 个理解力问题
    ├─ 询问用户
    ├─ 评分 < 80% → 触发 Code-Walkthrough
    └─ 评分 ≥ 80% → 通过
```

## 四、Walkthrough 模式

```yaml
code_walkthrough:
  duration: "30 min"
  format: "1-on-1 with @Architect"
  content:
    - 核心数据结构
    - 关键算法
    - 异常处理路径
    - 扩展点
  output: "用户自评已理解 100% 关键路径"
```
