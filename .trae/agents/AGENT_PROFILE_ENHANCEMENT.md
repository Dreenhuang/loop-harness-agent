# Agent Profile 增强规范（Trae Solo 对齐版）

> **版本**：v1.1
> **生效日期**：2026-06-15
> **对齐**：Trae Solo 工程实现指南 第四章

---

## 适用范围

本规范适用于 `.trae/agents/*.agent.toml` 中**全部 16 个 Agent Profile**。

---

## 5 个核心 Agent 已完成增强

| Agent | 状态 |
|-------|------|
| `@Orchestrator` | ✅ 已增强 |
| `@Backend` | ✅ 已增强 |
| `@Code-Reviewer` | ✅ 已增强（只读权限） |
| `@Final-Reviewer` | ✅ 已增强（只读权限） |
| `@DevOps` | ✅ 已增强（唯一全权限） |

## 其他 11 个 Agent 待 v1.2 增强

如需立即增强，参考以下模板（以 `@UX-Researcher` 为例）。

---

## 增强模板（以只读角色为例）

```toml
[system]
isolation = "process"            # Trae Solo 必需
stateless = true
worktree = false
max_turns = <N>
ralph_mode = true
reset_context_each_turn = true
max_context_turns = 1

[constraints]
max_input_tokens = 6000          # Trae Solo 风格
max_output_tokens = 3000
timeout = "300s"
max_retries = 3

[blackboard]
read_paths = [
  "blackboard/state.json",
  "blackboard/requirements/",
  "<本角色需要的其他路径>"
]
write_paths = [
  "<本角色写入路径>"
]
forbidden_paths = [
  "<禁止访问的路径>"
]

[mcp]
filesystem = "read_write"        # 或 "read_only"（门禁角色）
git = "none"                     # 或 "read_write"（开发角色）
shell = "none"                   # 或 "read_write"
testing = "none"                 # 或 "read_write"
```

---

## 角色权限矩阵（速查）

| 角色类型 | filesystem | git | shell | testing |
|----------|-----------|-----|-------|---------|
| **决策/业务层**（PM/Requirements/UX/UI） | read_write | none | none | none |
| **技术层**（Architect/Backend/Frontend/Bug） | read_write | read_write | read_write | read_write |
| **质量门禁层**（Code-Reviewer/Performance/Tester/Final-Reviewer） | **read_only** | none | 不定 | read |
| **知识层**（Knowledge-Curator） | read_write | none | none | none |
| **交付层**（Documenter/DevOps） | read_write | read_write | read_write | read_write |

---

## v1.2 待办

- [ ] @Product-Manager 加 [blackboard]
- [ ] @Requirements 加 [blackboard]
- [ ] @UX-Researcher 加 [blackboard]
- [ ] @UI-Designer 加 [blackboard]
- [ ] @Architect 加 [blackboard]
- [ ] @Fullstack-Coder 加 [blackboard]
- [ ] @Bug-Defect-Repairer 加 [blackboard]
- [ ] @Professional-Performance 加 [blackboard]
- [ ] @全栈测试员 加 [blackboard]
- [ ] @Knowledge-Curator 加 [blackboard]
- [ ] @Documenter 加 [blackboard]

---

**【Agent Profile 增强规范 v1.1 · 5/16 完成】**
