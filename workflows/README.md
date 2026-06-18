# Loop Agent · Workflows 目录

> **版本**：v1.0
> **生效日期**：2026-06-15
> **对齐**：Trae Solo 工程实现指南 第二章

---

## 目录结构

```text
workflows/
├── prd-to-production.json           # 主蓝图（总入口，向后兼容）
├── README.md                        # 本文件
├── phases/                          # 10 相位独立 JSON
│   ├── 01-INIT.json
│   ├── 02-REQUIREMENTS.json
│   ├── 03-DESIGN.json
│   ├── 04-ARCHITECTURE.json
│   ├── 05-DEVELOPMENT.json
│   ├── 06-QUALITY_GATES.json
│   ├── 07-KNOWLEDGE.json
│   ├── 08-DOCUMENTATION.json
│   ├── 09-FINAL_REVIEW.json
│   └── 10-DEPLOY.json
├── gates/                           # 4 道门禁独立 JSON
│   ├── gate1-code-review.json
│   ├── gate2-performance.json
│   ├── gate3-testing.json
│   └── gate4-final.json
└── schemas/                         # JSON Schema（待补充）
    ├── blackboard.schema.json
    ├── task-input.schema.json
    └── task-output.schema.json
```

---

## 渐进式设计

**双层结构**：
- `prd-to-production.json`（主蓝图）保留作为总入口（向后兼容）
- `phases/*.json` + `gates/*.json` 提供细粒度复用

**加载逻辑**：

```yaml
load_priority:
  1: prd-to-production.json          # 总入口（向后兼容）
  2: phases/*.json                   # 细粒度（执行时按需加载）
  3: gates/*.json                    # 门禁（按 phase 触发加载）
```

---

## 主蓝图引用

`prd-to-production.json` 顶部添加以下引用段：

```json
{
  "phase_references": {
    "INIT": "./phases/01-INIT.json",
    "REQUIREMENTS": "./phases/02-REQUIREMENTS.json",
    "DESIGN": "./phases/03-DESIGN.json",
    "ARCHITECTURE": "./phases/04-ARCHITECTURE.json",
    "DEVELOPMENT": "./phases/05-DEVELOPMENT.json",
    "QUALITY_GATES": "./phases/06-QUALITY_GATES.json",
    "KNOWLEDGE": "./phases/07-KNOWLEDGE.json",
    "DOCUMENTATION": "./phases/08-DOCUMENTATION.json",
    "FINAL_REVIEW": "./phases/09-FINAL_REVIEW.json",
    "DEPLOY": "./phases/10-DEPLOY.json"
  },
  "gate_references": {
    "GATE_1": "./gates/gate1-code-review.json",
    "GATE_2": "./gates/gate2-performance.json",
    "GATE_3": "./gates/gate3-testing.json",
    "GATE_4": "./gates/gate4-final.json"
  }
}
```

---

## 状态机命名（与 Trae Solo 对齐）

| 旧（v1.0 baseline） | 新（v1.1 trae-solo-aligned） |
|---------------------|------------------------------|
| PHASE_0 | **INIT** |
| PHASE_1 | **REQUIREMENTS** |
| PHASE_2 | **DESIGN** |
| PHASE_3 | **ARCHITECTURE** |
| PHASE_4 | **DEVELOPMENT** |
| PHASE_5 | **QUALITY_GATES** |
| PHASE_6 | **KNOWLEDGE** |
| PHASE_7 | **DOCUMENTATION** |
| PHASE_8 | **FINAL_REVIEW** |
| PHASE_9 | **DEPLOY** |
| (无) | **DONE** |

---

## 版本演进

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v1.0 | 2026-06-15 | 初始版本：1 个主蓝图 |
| v1.1 | 2026-06-15 | 拆分 phases/ + gates/ + 语义化命名 |

---

**【Loop Agent Workflows v1.1 · 双层结构 · 10 相位 + 4 门禁】**
