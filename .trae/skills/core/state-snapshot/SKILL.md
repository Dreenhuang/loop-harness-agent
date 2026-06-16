# Skill: state-snapshot 状态快照

> **Skill ID**: `state-snapshot`
> **所属层级**: 第 1 层 - Skill 层（原子能力）
> **调用方**: @Orchestrator
> **调用时机**: 每个 Phase 完成 / 任务失败 / 紧急停止

---

## 一、用途

将 Loop Agent 当前完整状态保存为快照，支持断点续跑和崩溃恢复。

---

## 二、快照内容

```yaml
snapshot:
  id: "CP-2026-06-15-005"
  created_at: "2026-06-15T14:23:45Z"
  phase: "DEV"
  overall_progress: 50
  
  blackboard:
    state_file: "项目进度记录.md"
    knowledge_graph_hash: "sha256:xxx"
    a2a_messages_count: 234
    
  workflow:
    completed_phases: [0, 1, 2, 3, 4, 5]
    current_phase: 6
    ready_tasks: ["cr-001", "perf-001", "test-001"]
    blocked_tasks: []
    
  budget:
    used_usd: 45.3
    iterations: 87
    
  artifacts:
    code: "src/"
    docs: "docs/"
    reports: ".blackboard/"
```

---

## 三、调用方式

```text
@Orchestrator 调用 state-snapshot Skill：
- 触发原因: phase_completed
- 触发 phase: DEV
```

---

## 四、快照存储

```text
.blackboard/snapshots/
├── CP-2026-06-15-000.json   # 启动
├── CP-2026-06-15-001.json   # Phase 0 完成
├── CP-2026-06-15-002.json   # Phase 1 完成
└── ...

最近 10 个快照保留，更早的归档到 .blackboard/snapshots/archive/
```

---

## 五、恢复方式

```text
@Orchestrator 调用 state-snapshot 恢复：
- snapshot_id: CP-2026-06-15-005
- 恢复模式: RESUME（从该快照继续）
```

---

## 六、保留策略

| 快照类型 | 保留时长 |
|----------|----------|
| 启动快照 | 永久 |
| Phase 完成快照 | 永久 |
| 任务失败快照 | 保留 30 天 |
| 紧急停止快照 | 保留 30 天 |

---

**【state-snapshot · Loop Agent v1.0】**
