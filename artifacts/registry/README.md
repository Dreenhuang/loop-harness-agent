# Artifact Registry

> 工件注册表目录，用于追踪所有强制工件的状态

## 用途

- 记录每个 Phase 产出的强制工件路径、状态、版本和责任人
- 供 Gate 合规检查器读取工件完整性
- 供 @Orchestrator 调度时判断前置工件是否就绪

## 数据格式

每个工件记录为 JSON 文件，命名格式：`{artifact-name}.json`

```json
{
  "artifact_name": "DEV-PLAN.md",
  "artifact_path": "docs/DEV-PLAN.md",
  "owner_role": "@Backend",
  "phase": "Phase 5",
  "status": "PENDING",
  "version": "1.0.0",
  "updated_at": "2026-06-16T00:00:00Z"
}
```

## 状态流转

PENDING → IN_PROGRESS → COMPLETED
                      → MISSING
