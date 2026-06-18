# Loop Agent · 配置文件目录

> **版本**：v1.0
> **生效日期**：2026-06-15
> **对齐**：Trae Solo 工程实现指南 第二章

---

## 配置文件清单

| 文件 | 用途 | 引用方 |
|------|------|--------|
| **budget.yaml** | 预算配置（全局/Phase/Task/Agent Token） | Orchestrator / budget-track Skill |
| **quality.yaml** | 质量门禁标准（4 道门禁阈值） | 4 个 Gate Skill / 门禁角色 |
| **agents.yaml** | 16 角色清单 + Profile 映射 | Orchestrator / Trae 加载 |
| **knowledge.yaml** | 知识库配置（分类/索引/匹配/模板） | @Knowledge-Curator / knowledge-extract |

---

## 与 trae.toml 的关系

`trae.toml` 是 Trae IDE 直接识别的主配置（项目模式/MCP/路由）。

`config/*.yaml` 是 Loop Agent 系统内部的细分配置（预算/质量/角色/知识）。

**Trae 加载顺序**：

```
trae.toml
    ↓
config/agents.yaml  →  加载 16 角色 Profile
    ↓
config/budget.yaml  →  加载预算约束
    ↓
config/quality.yaml  →  加载质量门禁阈值
    ↓
config/knowledge.yaml  →  加载知识库配置
```

---

## 版本演进

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v1.0 | 2026-06-15 | 初始版本：4 个 yaml（budget/quality/agents/knowledge） |

---

**【Loop Agent Config v1.0 · 4 个 yaml 就绪】**
