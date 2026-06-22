# 失败案例 2026-06-22-AGENT_HOLLOW

## 1. 事件摘要

- **现象**：某次任务派发后，@Dedicated-Coding-Engineer 返回了一份详细的执行计划，描述了"将修改 xxx 文件、新增 yyy 函数"，但实际上没有调用任何文件写入或编辑工具。`@Orchestrator` 误将计划文本视为完成输出，将黑板状态标记为 `completed`，导致下游 3 个任务依赖了不存在的工件。
- **时间**：2026-06-22 10:05 ~ 12:20
- **触发条件**：Agent Profile 未强制要求"每个执行任务必须附带 diff 证据"；@Orchestrator 未验证文件系统存在性。

## 2. 影响范围

- **直接损失**：3 个下游任务因依赖缺失工件而阻塞，其中 1 个任务基于空假设继续生成了错误代码。
- **影响模块 / 角色**：@Dedicated-Coding-Engineer、@Orchestrator、下游 @Backend 与 @Fullstack-Coder、黑板状态一致性。
- **阻塞时长**：发现并修复空壳输出共耗时 2 小时 15 分钟；额外花费 1 小时回滚错误代码。

## 3. 根因分析（5 Whys）

1. **为什么下游任务阻塞？** 因为上游 Agent 未实际产出文件，仅返回了文本计划。
2. **为什么未产出文件？** 因为 Agent 在响应中只描述了计划，未调用 Write/Edit 等文件操作工具。
3. **为什么未调用工具？** 因为 Agent Profile 的验收标准只关注输出文本质量，未强制"工具调用 + diff 证据"。
4. **为什么未强制工具调用？** 因为设计者默认 Agent 会主动使用工具完成分配任务，缺少执行验证层。
5. **为什么缺少执行验证层？** 因为证据收集器（evidence collector）未将"文件系统存在性校验"作为必检项。

## 4. 修复措施

- **临时止血**：回滚下游错误代码，重新派发任务给 @Dedicated-Coding-Engineer，明确要求每步修改后提交 diff。
- **永久修复**：
  - Agent 完成编码任务必须返回 `modified_files` 列表与 `diff_summary`，否则视为未完成。
  - @Orchestrator 在标记任务 `completed` 前，必须验证 `modified_files` 中每个文件在磁盘上存在且已被 git 追踪。
  - 引入 evidence collector 的"执行验证"钩子：无 diff/无文件变更则自动回退到 `in_progress`。
- **流程补丁**：`task-delegation-execution.md` 增加"Agent 输出必须附带文件 diff 与证据收集器校验"的强制条款。

## 5. 防御措施代码化（lint / test）

- **lint 规则**：新增 `agent-output-requires-diff` 规则，校验编码类 Agent 的响应中必须包含 `modified_files` 或 `diff_summary`。
- **测试用例**：
  - `tests/test_agent_execution_verifier.py`：模拟 Agent 返回纯文本计划，断言 Orchestrator 拒绝标记 `completed`。
  - `tests/test_evidence_collector_fs_check.py`：模拟 `modified_files` 中文件不存在，断言 evidence collector 抛出 `fusion.evidence.insufficient`。
- **自动化门禁**：每次 Agent 任务完成后，CI 自动运行 `git diff --name-only` 并与任务声明的 `modified_files` 比对，不一致则标记失败。

## 6. 知识库同步

- **更新规则**：`g:\ai-gongju\Loop-agent\.trae\rules\task-delegation-execution.md` 第 4 节"Agent 分配原则"增加"执行验证"子项。
- **新增知识条目**：`docs/knowledge/agent-hollow-detection.md` —— 《如何识别并防止 Agent 空壳执行》。
- **复盘结论**：文本计划不等于交付物，Agent 执行必须以可验证的文件变更与 diff 证据作为完成标准。
