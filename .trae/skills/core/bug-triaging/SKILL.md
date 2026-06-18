# Skill: bug-triaging Bug 分级与分派

> **Skill ID**: `bug-triaging`
> **所属层级**: 第 1 层 - Skill 层（原子能力）
> **调用方**: @Bug-Defect-Repairer / @全栈测试员
> **调用时机**: Bug 发现后立即调用

---

## 一、用途

对 Bug 进行标准化分级，决定修复优先级、修复时长、负责人分派。

---

## 二、Bug 分级标准

| 等级 | 严重程度 | 修复 SLA | 影响范围 | 分派对象 |
|------|----------|----------|----------|----------|
| **P0** | 致命 | 立即（4h 内） | 阻塞核心功能 / 数据丢失 / 安全漏洞 | @Bug-Defect-Repairer 主修 + @Architect 评审 |
| **P1** | 严重 | 24h 内 | 影响主流程但有 workaround | @Bug-Defect-Repairer |
| **P2** | 一般 | 一周内 | 不影响核心流程的小问题 | 排期修复 |
| **P3** | 轻微 | 下个版本 | UI 文字、优化建议 | 标记但不修复 |

---

## 三、Bug 严重度评分矩阵

```yaml
severity_score:
  impact:
    blocker: 5      # 阻塞核心功能
    major: 4        # 主流程受影响
    moderate: 3     # 边缘功能
    minor: 2        # UI/UX
    cosmetic: 1     # 文字/排版
    
  frequency:
    always: 5       # 100% 复现
    often: 4        # 50%+ 复现
    sometimes: 3    # 10-50% 复现
    rare: 2         # < 10% 复现
    once: 1         # 单次
    
  score_formula: "impact * frequency"
  
  mapping:
    score >= 20: P0
    12 <= score < 20: P1
    6 <= score < 12: P2
    score < 6: P3
```

---

## 四、调用方式

```text
调用 bug-triaging Skill：
- Bug 标题: "登录接口在 1000 并发下返回 500"
- 复现步骤: ["Step 1", "Step 2"]
- 期望: "登录成功"
- 实际: "返回 500 Internal Server Error"
- 影响: "100% 用户无法登录"
- 复现率: "100%"
```

---

## 五、输出

```json
{
  "bug_id": "BUG-2026-06-15-001",
  "level": "P0",
  "score": 25,
  "sla_hours": 4,
  "assigned_to": "@Bug-Defect-Repairer",
  "review_by": "@Architect",
  "blackboard_path": ".blackboard/bugs/BUG-2026-06-15-001.json",
  "auto_actions": [
    "立即通知 @Orchestrator",
    "暂停 Phase 5 后续任务",
    "触发 @Bug-Defect-Repairer 应急响应"
  ]
}
```

---

## 六、P0 Bug 应急流程

```
P0 Bug 出现
    ↓
bug-triaging 标记 P0
    ↓
@Orchestrator 立即响应：
    ├─ 暂停当前 Phase 所有新任务
    ├─ 分派 @Bug-Defect-Repairer 修复
    ├─ @Architect 同步评审
    └─ 通知 @Product-Manager
    ↓
@Bug-Defect-Repairer 修复（4h SLA）
    ↓
修复完成 → @全栈测试员 回归测试
    ↓
通过 → 恢复 Phase 5 流程
未通过 → 升级为 P0-CRITICAL，立即停止 Loop
```

---

**【bug-triaging · Loop Agent v1.0】**
