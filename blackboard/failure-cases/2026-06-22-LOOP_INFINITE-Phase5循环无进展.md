# 失败案例 2026-06-22-LOOP_INFINITE

## 1. 事件摘要

- **现象**：在一次 `/loop-harness-agent` 无人值守任务中，系统进入 Phase 5（并行开发）后，@Fullstack-Coder 连续多轮生成的组件代码与前一轮几乎一致，仅修改了注释或变量命名。黑板中该节点状态始终为 `in_progress`，@Orchestrator 误判为"正常推进中"，未触发任何告警。
- **时间**：2026-06-22 00:18 ~ 03:42（共 3 小时 24 分钟）
- **触发条件**：复杂前端页面重构任务未拆分为微任务；黑板更新模板缺少"本轮实际变更清单"字段；无进展检测护栏未启用。

## 2. 影响范围

- **直接损失**：单次 Loop 空转消耗约 47,000 Tokens，占当次预算的 62%。
- **影响模块 / 角色**：Phase 5 编码阶段、@Orchestrator 调度器、@Code-Reviewer 门禁排队。
- **阻塞时长**：Phase 6 门禁延迟 3.5 小时进入；`项目进度记录.md` 在 3 小时内未更新有效增量信息。

## 3. 根因分析（5 Whys）

1. **为什么 Phase 5 没有实质进展？** 因为每轮生成的代码与上一轮基本相同，未解决任何验收点。
2. **为什么代码重复生成？** 因为黑板只记录了"Phase 5 in_progress"的状态，没有记录每次具体修改的内容与 diff。
3. **为什么未记录具体变更？** 因为黑板更新模板缺少"本轮实际变更清单"字段，Agent 无地方填写增量证据。
4. **为什么模板缺少该字段？** 因为流程设计初期只关注阶段级状态，未关注"增量证据"与"无进展检测"。
5. **为什么未设计无进展检测？** 因为设计者默认 Agent 能够自我调节，未在全局护栏中设置硬停止条件。

## 4. 修复措施

- **临时止血**：人工终止当前 Loop，要求 @Fullstack-Coder 将任务拆分为 3 个微任务（数据层、视图层、交互层），逐个提交 diff。
- **永久修复**：
  - 黑板模板新增 `delta_summary` 字段，要求每轮必须列出本轮新增/修改/删除的文件与关键代码片段。
  - @Orchestrator 每轮自动执行 `git diff --stat`，连续 2 轮 diff 为空或仅注释变化则触发 `error.no.progress` 告警。
  - 全局护栏新增 `max_no_progress_rounds: 3`，达到即强制停止并输出无进展报告。
- **流程补丁**：Phase 5 启动前必须先通过 `@Architect` 或 `@Orchestrator` 的"微任务拆分检查"。

## 5. 防御措施代码化（lint / test）

- **lint 规则**：新增 `blackboard-delta-required` 规则，要求 `项目进度记录.md` 每次更新必须包含 `delta_summary` 区块。
- **测试用例**：
  - `tests/test_no_progress_detection.py`：模拟连续 3 轮空 diff，断言 Loop 在第 3 轮后强制停止。
  - `tests/test_blackboard_delta.py`：解析黑板 Markdown，校验 `delta_summary` 存在且非空。
- **自动化门禁**：Gate 1 代码审查时，@Code-Reviewer 必须检查本轮 diff 是否涉及实际代码变更，仅注释/格式化变更视为无效推进。

## 6. 知识库同步

- **更新规则**：`g:\ai-gongju\Loop-agent\.trae\rules\loop-agent.md` 第 6.4 节"Token 治理与防空转规则"新增"连续 3 轮无有效进展强制告警"条款。
- **新增知识条目**：`docs/knowledge/no-progress-detection.md` —— 《Loop Agent 无进展检测实现指南》。
- **复盘结论**：状态标记为 `in_progress` 不等于真的有进展，必须以可验证的 diff 或工件增量作为推进依据。
