# Evidence Collector

> 证据收集目录，用于存储 TDD、测试、验证、审查等关键证据

## 用途

- 收集 TDD 证据（failing_test / passing_test / refactor_evidence）
- 收集验证证据（verification_commands）
- 收集审查反馈（review_feedback）
- 收集部署验证（deploy_smoke_test / build_verification）

## 数据格式

每类证据存储为 JSON 文件，命名格式：`{evidence-type}.json`

```json
{
  "evidence_type": "failing_test",
  "source_role": "@Backend",
  "task_id": "T5-BE",
  "command": "bun test src/auth.test.ts",
  "result_summary": "3 tests failed as expected (RED phase)",
  "attachments": ["test-output-red.txt"],
  "timestamp": "2026-06-16T10:30:00Z"
}
```

## 铁律

- Phase 5 完成前必须至少有 failing_test + passing_test 证据
- Phase 6 完成前必须至少有 verification_commands + review_feedback 证据
- 终审放行前所有证据类型必须齐全
