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
| Agent 空壳 | AGENT_HOLLOW |
| 决策矛盾 | DECISION_CONFLICT |
| 质量回归 | QUALITY_REGRESSION |
| MCP 模块缺失 | MCP_MISSING |
| 部署事故 | DEPLOY_INCIDENT |

## 三、6 段式记录模板

```markdown
# 失败案例 YYYY-MM-DD-<类型>

## 1. 事件摘要
- 现象：xxx
- 时间：xxx
- 触发条件：xxx

## 2. 影响范围
- 直接损失
- 影响模块 / 角色
- 阻塞时长

## 3. 根因分析（5 Whys）
1. 为什么？
2. 为什么？
3. 为什么？
4. 为什么？
5. 为什么？

## 4. 修复措施
- 临时止血
- 永久修复
- 流程补丁

## 5. 防御措施代码化（lint / test）
- lint 规则
- 测试用例
- 自动化门禁

## 6. 知识库同步
- 更新规则
- 新增知识条目
- 复盘结论
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
| [Phase 5 循环无进展](2026-06-22-LOOP_INFINITE-Phase5循环无进展.md) | 2026-06-22 | LOOP_INFINITE | 黑板必须记录增量 diff，连续空转需硬刹车 |
| [无人值守 Token 超限](2026-06-22-BUDGET_EXCEEDED-无人值守Token超限.md) | 2026-06-22 | BUDGET_EXCEEDED | 大任务必须微任务化并强制 budget-track 检查 |
| [Gate 1 缺证据放行](2026-06-22-GATE_BYPASS-Gate1缺证据放行.md) | 2026-06-22 | GATE_BYPASS | 门禁通过必须以 failing + passing test 证据链为前提 |
| [MCP Server 模块缺失](2026-06-22-MCP_MISSING-MCPServer模块缺失.md) | 2026-06-22 | MCP_MISSING | Phase 0 必须验证 MCP Server 安装完整性 |
| [Agent 空壳未真实执行](2026-06-22-AGENT_HOLLOW-Agent空壳未真实执行.md) | 2026-06-22 | AGENT_HOLLOW | Agent 输出必须附带文件 diff 与证据收集器校验 |

---

**【失败案例库 v1.1 · 6 段式模板 + 24h 复盘机制 · 持续累积】**