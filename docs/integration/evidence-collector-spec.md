# Evidence Collector 规范

> **版本**：v1.0
> **日期**：2026-06-16
> **用途**：定义证据收集器的数据模型、接口和操作规范

---

## 1. 概述

Evidence Collector 是融合验收体系中收集和验证关键执行证据的核心组件。它负责：

- 收集 TDD 证据（failing_test / passing_test / refactor_evidence）
- 收集验证证据（verification_commands）
- 收集审查反馈（review_feedback）
- 收集部署验证（deploy_smoke_test / build_verification）
- 供 Gate 合规检查器判定证据充分性

---

## 2. 数据模型

### EvidenceRecord

```typescript
interface EvidenceRecord {
  evidence_type: string;      // 证据类型
  source_role: string;        // 来源角色
  task_id: string;            // 关联任务 ID
  command: string;            // 执行命令
  result_summary: string;     // 结果摘要
  attachments: string[];      // 附件路径
  timestamp: string;          // ISO 8601 时间戳
}
```

---

## 3. 证据类型清单

| 证据类型 | 所属 Phase | 收集角色 | 要求 |
|----------|-----------|----------|------|
| failing_test | Phase 5 | @Backend / @Fullstack-Coder | 关键新功能必须有 RED 阶段测试记录 |
| passing_test | Phase 5 | @Backend / @Fullstack-Coder | 关键新功能必须有 GREEN 阶段测试记录 |
| refactor_evidence | Phase 5 | @Backend / @Fullstack-Coder | 关键新功能必须有重构记录 |
| verification_commands | Phase 6-9 | @Code-Reviewer / @Final-Reviewer | 可执行的验证命令及输出 |
| review_feedback | Phase 6 | @Code-Reviewer | 代码审查反馈记录 |
| deploy_smoke_test | Phase 10 | @DevOps | 部署后冒烟测试通过记录 |
| build_verification | Phase 10 | @DevOps | 构建验证通过记录 |

---

## 4. 存储位置

- 证据注册表：`artifacts/evidence/initial-evidence.json`
- 单类证据：`artifacts/evidence/{evidence-type}.json`

---

## 5. 接口

### 收集证据

```typescript
function collectEvidence(record: EvidenceRecord): void
```

### 查询证据充分性

```typescript
function checkSufficiency(phase: string): { sufficient: boolean; missing: string[] }
```

### 获取证据摘要

```typescript
function getEvidenceSummary(evidenceType: string): string
```

---

## 6. 铁律

1. Phase 5 完成前必须至少有 failing_test + passing_test 证据
2. Phase 6 完成前必须至少有 verification_commands + review_feedback 证据
3. 终审放行前所有证据类型必须齐全
4. 证据必须为当场验证产出，禁止引用历史结果
5. 证据状态变更必须同步更新黑板区块十-B
