# 失败案例库 · Failure Cases Library

> **路径**: `g:\ai-gongju\Loop-agent\blackboard\failure-cases\`
> **解决偏差**: D-13（无失败案例库 + 复盘机制）
> **蓝皮书**: 第八章"验证仍在你身上"

## 一、用途

记录 Loop Agent 系统的失败案例，避免重蹈覆辙。每次失败必须按 6 段式模板记录。

## 二、文件命名规范

```text
YYYY-MM-DD-<失败类型>-<简述>.md
```

| 失败类型 | 代码 |
|----------|------|
| Loop 死循环 | LOOP_INFINITE |
| 上下文爆炸 | CONTEXT_BLOAT |
| Token 超限 | BUDGET_EXCEEDED |
| 门禁绕过 | GATE_BYPASS |
| Agent 越权 | AUTH_VIOLATION |
| 决策矛盾 | DECISION_CONFLICT |
| 质量回归 | QUALITY_REGRESSION |
| 部署事故 | DEPLOY_INCIDENT |

## 三、6 段式记录模板

```markdown
# 失败案例 YYYY-MM-DD-<类型>

## 1. 症状
- 现象：xxx
- 时间：xxx
- 影响：xxx

## 2. 证据
- 错误日志
- 截图
- 监控数据

## 3. 差异
- 期望 vs 实际

## 4. 根因
- 直接原因
- 根本原因
- 系统设计缺陷

## 5. 修复
- 临时方案
- 永久方案
- 防御措施

## 6. 复盘
- 一句话教训
- 可复用的预防清单
```

## 四、复盘机制

```yaml
post_mortem:
  trigger: "任何 P0/P1 失败"
  owner: "@Knowledge-Curator"
  deadline: "24 小时内"
  review: "Final-Reviewer 审核"
  
  mandatory:
    - "根因分析（5 Whys）"
    - "防御措施代码化（lint/test）"
    - "知识库同步"
    - "规则更新"
```

## 五、案例库索引

| 案例 | 日期 | 类型 | 教训 |
|------|------|------|------|
| （待记录） | | | |

---

**【失败案例库 v1.0 · 6 段式模板 + 24h 复盘机制 · 持续累积】**
