# Artifact Registry 规范

> **版本**：v1.0
> **日期**：2026-06-16
> **用途**：定义工件注册表的数据模型、接口和操作规范

---

## 1. 概述

Artifact Registry 是融合验收体系中追踪强制工件状态的核心组件。它负责：

- 记录每个 Phase 产出的强制工件路径、状态、版本和责任人
- 供 Gate 合规检查器读取工件完整性
- 供 @Orchestrator 调度时判断前置工件是否就绪
- 供 @Documenter 归档时确认文档资产齐全

---

## 2. 数据模型

### ArtifactRecord

```typescript
interface ArtifactRecord {
  artifact_name: string;      // 工件名称（如 "DEV-PLAN.md"）
  artifact_path: string;      // 工件文件路径（相对于项目根目录）
  owner_role: string;         // 责任角色（如 "@Backend"）
  phase: string;              // 所属 Phase（如 "Phase 5"）
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "MISSING";
  version: string;            // 语义化版本号
  updated_at: string;         // ISO 8601 时间戳
}
```

### 状态流转

```
PENDING → IN_PROGRESS → COMPLETED
                      → MISSING（文件不存在或内容为空）
```

---

## 3. 强制工件清单

| 工件名称 | 所属 Phase | 责任角色 | 模板路径 |
|----------|-----------|----------|----------|
| Product-Spec.md | Phase 1 | @Requirements | templates/Product-Spec.md |
| Design-Brief.md | Phase 2-3 | @UX-Researcher | templates/Design-Brief.md |
| UI-Design.md | Phase 3 | @UI-Designer | templates/UI-Design.md |
| Component-Library.md | Phase 3 | @UI-Designer | templates/Component-Library.md |
| Architecture.md | Phase 4 | @Architect | - |
| API-Spec.md | Phase 4 | @Architect | - |
| DEV-PLAN.md | Phase 5 | @Backend | templates/DEV-PLAN.md |
| Quality-Check-Report.md | Phase 6 | @Code-Reviewer | templates/Quality-Check-Report.md |
| Test-Report.md | Phase 6 | @全栈测试员 | - |
| Code-Review-Report.md | Phase 6 | @Code-Reviewer | templates/Code-Review-Report.md |
| UX-Review-Report.md | Phase 6 | @UX-Researcher | templates/UX-Review-Report.md |
| Release-Notes.md | Phase 10 前 | @DevOps | templates/Release-Notes.md |

---

## 4. 存储位置

- 注册表文件：`artifacts/registry/initial-registry.json`
- 单工件记录：`artifacts/registry/{artifact-name}.json`
- 工件模板：`templates/{artifact-name}.md`

---

## 5. 接口

### 注册工件

```typescript
function registerArtifact(record: ArtifactRecord): void
```

### 更新工件状态

```typescript
function updateArtifactStatus(name: string, status: ArtifactRecord["status"]): void
```

### 查询工件完整性

```typescript
function checkCompleteness(phase: string): { complete: boolean; missing: string[] }
```

---

## 6. 铁律

1. 终审放行前，所有强制工件状态必须为 COMPLETED
2. 工件状态变更必须同步更新黑板区块十-A
3. 缺少工件时 Gate 不得放行，不得用占位符替代
