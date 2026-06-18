# /loop-agent status - 查询 Loop Agent 状态

请执行：

1. 调用 `mcp__loop-agent__get_status`
2. 输出格式化的状态报告：

```
📊 Loop Agent 状态报告
├─ 当前 Phase: <phase>
├─ 进度: <progress>%
├─ 预算: $<used> / $<max>
├─ 活跃任务: <active_count>
├─ 已完成任务: <completed_count>
├─ 失败任务: <failed_count>
└─ 门禁状态:
   ├─ Gate 1 (Code Review): <passed/failed/pending>
   ├─ Gate 2 (Performance): <passed/failed/pending>
   ├─ Gate 3 (Testing): <passed/failed/pending>
   └─ Gate 4 (Final Review): <passed/failed/pending>
```

**3 道硬刹车检查**（见 `CLAUDE.md` §五）：
- 预算 > 80% → 警告
- 预算 > 95% → 停止
- 迭代 ≥ 200 → 紧急停止
