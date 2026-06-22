# 失败案例 2026-06-22-BUDGET_EXCEEDED

## 1. 事件摘要

- **现象**：一次"今晚完成，明天早上给我结果"无人值守任务中，@Fullstack-Coder 在未拆分微任务的情况下，直接对 12 个前端文件进行全量重构。由于未启用 budget-track 检查，Token 消耗在 2 小时内达到 $8.7，占单任务预算的 87%。
- **时间**：2026-06-22 21:05 ~ 23:18
- **触发条件**：用户指定"通宵跑"；无人值守模式默认未绑定 `budget-track` Skill；任务范围未做文件数上限控制。

## 2. 影响范围

- **直接损失**：当月 Loop Agent 项目 API 预算消耗 87%，触发 `max_budget_usd: 100` 硬刹车，任务被强制终止。
- **影响模块 / 角色**：@Fullstack-Coder、@Orchestrator、夜间预算池、部分中间工件因刹车未及时保存而丢失。
- **阻塞时长**：任务失败，需次日人工介入重做，整体延期 12 小时。

## 3. 根因分析（5 Whys）

1. **为什么 Token 消耗失控？** 因为一次性处理 12 个文件，上下文累积导致每轮输出成本指数级增长。
2. **为什么一次性处理 12 个文件？** 因为任务未拆分为微任务，Agent 默认按全量范围执行。
3. **为什么未拆分微任务？** 因为无人值守模式未强制要求"计划阶段必须输出微任务级计划"。
4. **为什么未强制微任务化？** 因为默认配置下 `@Orchestrator` 未激活 `budget-track` 与 `state-snapshot` 的绑定。
5. **为什么绑定缺失？** 因为预算治理规则未将"每 N 个文件/每 N 轮必须快照 + 预算检查"作为硬约束写入 Workflow 蓝图。

## 4. 修复措施

- **临时止血**：立即终止任务，保存已完成的 4 个文件；剩余 8 个文件按优先级拆分为 3 个微任务分批执行。
- **永久修复**：
  - 无人值守模式强制激活 `budget-track`、`state-snapshot`、`progress-detect` 三个 Skill。
  - 每处理 1 个文件强制调用 `mcp__loop-agent__save_blackboard`，每 30 分钟强制快照。
  - 单次子任务处理的文件数上限设为 3，超过必须拆分。
  - 预算使用达到 80% 时触发告警，达到 95% 时强制停止并要求人工确认。
- **流程补丁**：`task-delegation-execution.md` 增加"大任务必须微任务化"的强制条款。

## 5. 防御措施代码化（lint / test）

- **lint 规则**：新增 `unattended-budget-skill-required` 规则，校验无人值守配置中是否包含 `budget-track`。
- **测试用例**：
  - `tests/test_budget_guard.py`：模拟预算达到 80% 与 95%，断言分别触发告警与停止。
  - `tests/test_microtask_split.py`：输入包含 5 个文件的子任务，断言 `@Orchestrator` 返回不少于 2 个微任务。
- **自动化门禁**：Gate 4 终审前检查 budget_used 是否低于 95%，超过则阻断发布。

## 6. 知识库同步

- **更新规则**：`g:\ai-gongju\Loop-agent\.trae\rules\loop-agent.md` 第 1.2.1 节"无人值守模式 6 条铁律"增加"预算 Skill 强制绑定"。
- **新增知识条目**：`docs/knowledge/token-budget-splitting.md` —— 《Loop Agent Token 预算切分与微任务化实践》。
- **复盘结论**：无人值守不等于无约束，预算、进度、状态快照三者必须同时启用。
