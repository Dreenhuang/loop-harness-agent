# 失败案例 2026-06-22-GATE_BYPASS

## 1. 事件摘要

- **现象**：某次 Phase 5 完成后，@Code-Reviewer 在 Gate 1 审查中仅阅读了代码文本，未发现明显语法问题即标记"通过"。实际上该次提交缺少 `failing_test` 与 `passing_test` 证据，导致一个未覆盖的空指针 Bug 流入 Gate 2。
- **时间**：2026-06-22 14:30 ~ 15:10
- **触发条件**：@Code-Reviewer 的 `gate1-code-review` Skill 检查清单未将"测试证据链"列为必检项；黑板中 evidence collector 为空。

## 2. 影响范围

- **直接损失**：Gate 2 性能压测时触发空指针崩溃，错误率达到 12%，压测报告失效。
- **影响模块 / 角色**：Gate 1 代码审查、Gate 2 性能压测、@Bug-Defect-Repairer 回退修复、@Backend 重新提交。
- **阻塞时长**：修复 + 重跑 Gate 1/2 共耗时 4.5 小时，修复成本约为 Gate 1 阶段发现的 3 倍。

## 3. 根因分析（5 Whys）

1. **为什么 Bug 流入了 Gate 2？** 因为 Gate 1 缺少针对该分支的 failing_test 与 passing_test 证据。
2. **为什么缺少测试证据？** 因为 @Code-Reviewer 未要求 @Backend 提交测试证据。
3. **为什么未要求提交？** 因为 `gate1-code-review` Skill 的通过条件仅列出"0 Blocker + 0 Major"，未明确"证据链完整"。
4. **为什么未明确证据链？** 因为融合验收标准第 6.3 条"强制 TDD 证据化"未细化到 Gate 检查清单。
5. **为什么未细化？** 因为规则制定时默认 Agent 会自动执行 TDD，未设置显式 evidence 校验层。

## 4. 修复措施

- **临时止血**：立即驳回 Gate 1 通过状态，要求 @Backend 补充 failing_test + passing_test 证据，并重新审查。
- **永久修复**：
  - Gate 1 检查清单增加"测试证据双检"：必须看到针对新功能的 `failing_test` 与修复后的 `passing_test`。
  - 黑板 `evidence_updates` 为空时，`gate.code.review.passed` 自动拒绝。
  - @Code-Reviewer 输出必须包含 `evidence_checklist`，逐项勾选并附文件路径。
- **流程补丁**：`gate1-code-review` Skill 升级，将 evidence 检查作为第一优先级，排在代码风格与架构检查之前。

## 5. 防御措施代码化（lint / test）

- **lint 规则**：新增 `gate1-evidence-required` 规则，校验 Gate 1 报告 Markdown 中必须包含 `failing_test` 与 `passing_test` 关键字。
- **测试用例**：
  - `tests/test_gate1_evidence.py`：模拟 evidence 缺失的场景，断言 Gate 1 返回 `failed`。
  - `tests/test_evidence_collector.py`：校验 evidence collector 中至少包含两类证据（test + verification_commands）。
- **自动化门禁**：Gate 1 通过前，CI 自动检查 `artifacts/evidence/` 目录下是否存在 `failing_test` 与 `passing_test` 记录。

## 6. 知识库同步

- **更新规则**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md` 增加"Gate 1 必须以 failing + passing test 证据链为前提"条款。
- **新增知识条目**：`docs/knowledge/evidence-driven-gate.md` —— 《证据驱动门禁：从 TDD 到 Gate 放行》。
- **复盘结论**：代码审查不是单纯的代码阅读，必须以可验证的测试证据链作为通过前提。
