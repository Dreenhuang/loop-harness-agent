# Skill: Gate4 最终终审门禁

> **Skill ID**: `gate4-final`
> **所属层级**: 第 1 层 - Skill 层（门禁类·最高级）
> **调用方**: @Final-Reviewer / @Orchestrator
> **调用时机**: Phase 8（文档生成）完成后
> **严格度**: ⭐⭐⭐⭐⭐（最高·上线最后一道闸门）
> **铁律**: 风险等级 > LOW → 禁止上线

---

## 一、用途与定位

**Gate 4 是 Loop Agent 4 道门禁中的最后一道**，由 @Final-Reviewer 独立执行。

**核心职责**：
- 对全流程所有产出做综合核验
- 全局风险评估
- 上线最终决策（Go / No-Go）
- 输出终审报告

---

## 二、终审检查清单（12 项必查）

### 2.1 质量门禁（4 项）（v1.1.1 修复 V-008：项目类型感知）

**根据 projectType 自动跳过不适用的检查项**：

- [ ] Gate 1（代码审查）已通过
- [ ] Gate 2（性能）已通过
- [ ] Gate 3（测试）已通过
- [ ] 无未关闭的 P0/P1 Bug

### 2.2 文档完整性（4 项）

- [ ] PRD / 需求文档齐全
- [ ] 架构设计文档齐全
- [ ] API 接口文档齐全
- [ ] 部署运维文档齐全

### 2.3 上线准备（4 项）

- [ ] 回滚方案已准备且演练通过
- [ ] 监控告警已配置
- [ ] 备份恢复方案已验证
- [ ] 发布计划已制定（含灰度策略）

### 2.4 业务确认（额外项）

- [ ] @Product-Manager 已确认验收
- [ ] @Knowledge-Curator 已完成知识沉淀
- [ ] @DevOps 已就绪
- [ ] 风险等级评估为 LOW

---

## 三、风险评估矩阵

| 风险等级 | 定义 | 决策 |
|----------|------|------|
| **LOW** | 所有指标达标，无重大隐患 | ✅ Go |
| **MEDIUM** | 1-2 个非核心指标接近阈值 | ⚠️ Conditional Go（需人工确认） |
| **HIGH** | 多个指标超标 / 存在未解决风险 | ❌ No-Go（回到对应 Phase 修复） |
| **CRITICAL** | 数据丢失风险 / 安全漏洞未修复 | 🛑 Stop（立即停止流程） |

---

## 四、调用方式

```text
@Final-Reviewer 请调用 gate4-final Skill，对项目进行最终终审：
- 项目名称：xxx
- 当前阶段：Phase 8 完成
- 报告输出：.blackboard/final_review/review_final_<taskId>.json
```

---

## 五、执行流程（6 步）

```
【第 1 步】收集所有交付物
    ├─ 读取 项目进度记录.md
    ├─ 收集所有门禁报告（reviews/performance/test_reports）
    ├─ 收集所有文档（docs/）
    └─ 收集部署计划（DevOps 输出）

【第 2 步】逐项核验 12 项清单
    └─ 不通过项 → 记录到 issues

【第 3 步】执行风险评估
    ├─ 列出所有潜在风险
    ├─ 评估每个风险的影响 + 概率
    └─ 计算综合风险等级

【第 4 步】业务确认
    └─ @Product-Manager 确认验收

【第 5 步】生成终审报告
    └─ 写入 .blackboard/final_review/review_final_<taskId>.json

【第 6 步】发送 A2A 消息
    ├─ Go → [RESP] gate.final.passed（@DevOps 可启动部署）
    ├─ Conditional → [NOTIFY] gate.final.conditional（需人工确认）
    └─ No-Go / Stop → [ERR] gate.final.failed
```

---

## 六、输出契约（Schema）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Gate 4 Final Review Report",
  "type": "object",
  "required": ["taskId", "decision", "riskLevel", "checklist", "summary"],
  "properties": {
    "taskId": { "type": "string" },
    "projectType": { "enum": ["web", "cli", "library", "mobile", "desktop", "backend-api"], "description": "v1.1.1 修复 V-008: 项目类型" },
    "decision": { "enum": ["GO", "CONDITIONAL_GO", "NO_GO", "STOP"] },
    "riskLevel": { "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"] },
    "checklist": {
      "type": "object",
      "properties": {
        "gate1_passed": { "type": "boolean" },
        "gate2_passed": { "type": "boolean" },
        "gate3_passed": { "type": "boolean" },
        "prd_documented": { "type": "boolean" },
        "architecture_documented": { "type": "boolean" },
        "api_documented": { "type": "boolean" },
        "deploy_documented": { "type": "boolean" },
        "rollback_tested": { "type": "boolean" },
        "monitoring_configured": { "type": "boolean" },
        "backup_verified": { "type": "boolean" },
        "release_plan_approved": { "type": "boolean" },
        "pm_accepted": { "type": "boolean" }
      }
    },
    "risks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "level": { "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"] },
          "impact": { "type": "string" },
          "probability": { "type": "string" },
          "mitigation": { "type": "string" }
        }
      }
    },
    "unresolvedIssues": {
      "type": "array",
      "items": { "type": "string" }
    },
    "summary": { "type": "string" },
    "next_actions": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

---

## 七、上线决策树

```
Gate 4 评估
    ↓
风险等级 = ?
    ├─ LOW → decision: GO → @DevOps 启动部署
    ├─ MEDIUM → decision: CONDITIONAL_GO
    │       ↓
    │   人工确认是否接受风险？
    │       ├─ Yes → @DevOps 启动部署（带额外监控）
    │       └─ No → decision: NO_GO → 回到对应 Phase 修复
    ├─ HIGH → decision: NO_GO → 回到对应 Phase 修复
    └─ CRITICAL → decision: STOP → 立即停止，人工介入
```

---

## 八、停止条件

```yaml
stop_condition: |
  is_done = (
    all_12_checklist_items_evaluated == true
    AND
    risk_level_assigned == true
    AND
    final_report_written == true
    AND
    a2a_message_sent == true
  )

max_attempts: 1  # 终审不重试
timeout_seconds: 1800
```

---

## 九、与 Loop Agent 系统的集成

| 集成点 | 说明 |
|--------|------|
| **Phase 9 触发** | Phase 8 完成后 @Orchestrator 触发 |
| **预算消耗** | 约 3-5 USD Token |
| **黑板写入** | `.blackboard/final_review/review_final_<taskId>.json` |
| **A2A 消息** | `gate.final.passed/conditional/failed` |
| **下游触发** | GO → @DevOps 启动 Phase 10 部署 |

---

## 十、上线后必须做

Gate 4 通过后，@DevOps 启动部署，仍需监控以下指标：

```yaml
post_deploy_monitoring:
  duration: "发布后 24 小时"
  metrics:
    - 错误率 ≤ 0.1%
    - P95 响应时间 ≤ 300ms
    - 业务核心指标正常
    - 无 P0/P1 用户反馈
  rollback_trigger: 任一指标连续 5 分钟异常
```

## 融合验收检查（v1.1 新增）

> **对齐标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md` 第 9、10 节

### 强制工件完整性检查

终审放行前，以下工件必须全部为 ✅ COMPLETED：

| 工件名称 | 所属 Phase | 检查方式 |
|----------|-----------|----------|
| Product-Spec.md | Phase 1 | 文件存在且非空 |
| Design-Brief.md | Phase 2-3 | 文件存在且非空 |
| UI-Design.md | Phase 3 | 文件存在且非空 |
| Component-Library.md | Phase 3 | 文件存在且非空 |
| Architecture.md | Phase 4 | 文件存在且非空 |
| API-Spec.md | Phase 4 | 文件存在且非空 |
| DEV-PLAN.md | Phase 5 | 文件存在且非空 |
| Quality-Check-Report.md | Phase 6 | 文件存在且非空 |
| Test-Report.md | Phase 6 | 文件存在且非空 |
| Code-Review-Report.md | Phase 6 | 文件存在且非空 |
| UX-Review-Report.md | Phase 6 | 文件存在且非空 |
| Release-Notes.md | Phase 10 前 | 文件存在且非空 |

**铁律**：上表任一工件缺失，终审不得放行。

### 证据充分性检查

| 证据类型 | 要求 |
|----------|------|
| failing_test | Phase 5 产出，至少 1 条 |
| passing_test | Phase 5 产出，至少 1 条 |
| verification_commands | Phase 6-9 产出，至少 1 条可执行命令 |
| review_feedback | Phase 6 产出，代码审查反馈记录 |
| deploy_smoke_test | Phase 10 产出，冒烟测试通过记录 |

**铁律**：上表任一证据缺失，终审不得放行。

### 一票否决项检查

出现以下任一情况，终审立即阻断：

1. ❌ 无法稳定生成完整工件链
2. ❌ Gate 可被绕过或存在无证据放行
3. ❌ 无法在失败后基于黑板恢复执行
4. ❌ 输出仍停留在 demo 级，却宣称满足生产级交付
5. ❌ Token 消耗明显失控且无法收敛
6. ❌ 无人值守模式下出现长时间空转、重复执行或伪完成

### 部署前提完备性检查

- [ ] 部署脚本/说明已提供
- [ ] 环境变量清单已提供
- [ ] 回滚策略已说明
- [ ] 冒烟测试已通过
- [ ] 不存在"仅在本地可运行"的状态

### 合规判定逻辑

```
IF artifacts_incomplete → VETO (一票否决)
IF evidence_insufficient → VETO (一票否决)
IF gate_bypass_detected → VETO (一票否决)
IF demo_disguised_as_production → VETO (一票否决)
IF recovery_impossible → VETO (一票否决)
IF token_out_of_control → VETO (一票否决)
IF unattended_hollow_loop → VETO (一票否决)
IF deploy_prerequisites_missing → GATE FAIL (非一票否决，需修复)
ELSE → GATE PASS
```

---

**【Gate 4 最终终审门禁 · Loop Agent v1.1 · 融合验收补强 · 生效中】**
