# Skill: unattended-mode 无人值守执行模式

> **Skill ID**: `unattended-mode`
> **所属层级**: 第 1 层 - Skill 层（核心调度类）
> **调用方**: @Orchestrator（Loop Agent 启动时）
> **调用时机**: 用户明确进入 LOOP agent 模式 + 设置长时间任务
> **核心承诺**: **不中断、不暂停、完整执行、自动决策、事后报告**

---

## 一、用途与定位

**无人值守模式是 Loop Agent 的"夜间作业"能力**。典型场景：用户晚上 11 点设定所有任务，去睡觉，第二天早上 8 点看到完整交付物。

**核心设计原则**：
1. **不中断原则**：除非触发"用户确认边界"，否则 AI 自主决策
2. **最小影响原则**：异常时优先回滚而非中断
3. **完整执行原则**：宁可慢也要完成，不留半成品
4. **可审计原则**：所有自动决策都有记录

---

## 二、触发条件

```text
触发关键词（自然语言）：
- "用 Loop Agent 模式开发，今晚做完"
- "进入无人值守模式"
- "今晚完成，明天早上给我结果"
- "Auto Mode"
- "set it and forget it"
- "通宵跑"
- "/unattended"
- "/auto-overnight"

触发关键词（斜杠命令）：
- /unattended
- /auto-overnight
- /loop-agent unattended
```

---

## 三、自动决策 vs 用户确认边界

### 3.1 ✅ AI 自动决策（不暂停）

| 类别 | 具体操作 | 决策依据 |
|------|----------|----------|
| **文件操作** | 创建/修改/删除临时文件（.tmp/.cache/.log/node_modules） | 临时文件可重建 |
|  | 选择文件路径（自动选最优） | 按 Trae Solo 目录约定 |
|  | 文件命名（按 snake_case/kebab-case） | 项目规范 |
|  | 创建/删除/重组目录 | 临时性操作 |
| **资源分配** | Token 预算内自动选择 API | budget-track Skill |
|  | CPU/内存限制 | 配置文件 |
|  | 并行度调节 | 3-7 Agent 规则 |
| **非关键参数** | 超时时间（默认 300s 内） | 项目 SLA |
|  | 重试次数（≤ 3） | global_guardrails |
|  | 日志级别（debug/info/warn） | 调试需要 |
|  | 端口分配（从池中选空闲） | 全局规则端口池 |
|  | 缓存策略 | optimization 配置 |
| **错误恢复** | 单次失败自动重试（≤ 3 次） | maker_checker_separation |
|  | 回滚到上一个 snapshot | state-snapshot Skill |
|  | 应用知识库匹配方案 | knowledge-extract |
|  | 触发 Bug-Defect-Repairer | 角色协作 |
| **Bug 修复** | 自动选择修复方案（从候选中） | orchestrate-map-reduce |
|  | 写根因分析报告 | Maker-Checker 分离 |
|  | 自动应用预防措施 | knowledge-extract |
| **代码生成** | 函数命名、类结构 | 项目约定 |
|  | 单元测试用例生成 | coverage ≥ 80% |
|  | API endpoint 命名 | RESTful 规范 |
|  | 数据库表结构 | DDD 范式 |
| **文档生成** | README/CHANGELOG 内容 | 模板驱动 |
|  | 注释风格 | 项目规范 |
|  | 截图/图表 | 自动生成 |

### 3.2 ❌ 必须用户确认（暂停并报告）

| 类别 | 具体场景 | 阈值 | 报告内容 |
|------|----------|------|----------|
| **架构变更** | 更换技术栈（Vue → React） | 跨语言/跨框架 | 影响范围 + 迁移成本 |
|  | 重写核心模块 | > 30% 模块改动 | 新架构 + 兼容性分析 |
|  | 数据库迁移（关系型 → NoSQL） | 跨数据库类型 | 数据迁移方案 |
| **核心功能** | 修改 PRD 范围 | > 20% 功能点变更 | 变更清单 + 影响 |
|  | 删除已实现功能 | 任何 | 业务影响评估 |
|  | 添加 PRD 未提及功能 | 任何 | 必要性论证 |
| **资源超阈** | Token 预算超 50% | > 150% 预估 | 节省方案 |
|  | 迭代次数超 5 倍预估 | > 500% | 卡点分析 |
|  | 时间超 5 倍预估 | > 500% | 阻塞点 |
| **安全/合规** | 涉及用户隐私 | 任何 | 合规检查 |
|  | 涉及支付/金融 | 任何 | 安全审计 |
|  | 涉及数据删除 | 任何 | 影响范围 |
| **不可逆操作** | 生产环境部署 | 任何 | 部署清单 + 回滚方案 |
|  | 数据库 DROP/DELETE | 任何 | 影响数据量 |
|  | 强制 push | 任何 | 影响分支 |
|  | 密钥上传 | 任何 | 泄露风险 |
| **时间计划** | 任务延期 > 3 天 | 任何 | 原因 + 调整方案 |
|  | 里程碑大幅调整 | 任何 | 新时间线 |
| **异常无法恢复** | 连续 3 次同一错误 | 3 轮 | 错误堆栈 + 已知方案 |
|  | 知识库无匹配方案 | 任何 | 故障报告 + 人工建议 |
|  | Snapshot 恢复失败 | 任何 | 损坏诊断 |

### 3.3 决策矩阵（决策树）

```
执行中遇到决策点
    ↓
属于 3.1 列表（自动决策）？
    ├─ 是 → AI 自动决策
    │     ↓
    │     记录到 decision_log.json
    │     ↓
    │     继续执行
    │
    └─ 否 → 属于 3.2 列表（需用户确认）？
          ├─ 是 → 暂停并报告
          │     ↓
          │     写入 pending_decision.json
          │     ↓
          │     输出 5W1H 报告
          │     ↓
          │     在 unattended_mode = false 时 → 等待用户
          │     在 unattended_mode = true + 阈值内 → 自动应用"最小影响"方案
          │
          └─ 否 → 未明确归类（边缘情况）
                ↓
                启用"最小影响原则"
                ↓
                选项 1：选择改动最小的方案
                选项 2：跳过该步骤
                选项 3：回滚到 snapshot
                ↓
                记录 + 继续
                ↓
                任务完成后向用户报告
```

---

## 四、决策记录 Schema

### 4.0 防循环机制（v1.1.1 修复 V-011）

> **背景**：自动决策可能因状态机问题陷入死循环（如每个 tick 重复添加同一条记录）。

```yaml
# decision_log 防循环机制
loop_protection:
  enabled: true
  
  # 指纹去重：相同 fingerprint 的决策不重复记录
  fingerprint_fields:
    - "category"
    - "decision"
    - "context.task_id"
    - "context.operation"
  
  # 同类决策合并窗口
  merge_window_seconds: 60
  
  # 单类决策上限（超过则升级为异常）
  per_category_max_count: 50
  
  # 写入前检查
  pre_write_check:
    - "检查 fingerprint 是否已存在（最近 100 条内）"
    - "如存在，更新 count + last_seen，不新增条目"
    - "如不存在，新增条目"
  
  # 循环检测（如 10 条相同 fingerprint 连续触发）
  loop_detection:
    threshold: 10
    on_detected:
      - "记录异常到 decision_log.loop_alerts"
      - "触发 ESCAPE：跳过该决策类型 5 分钟"
      - "通知 @Orchestrator"
```

### 4.1 decision_log.json 格式

```json
{
  "$schema": "decision_log.schema.json",
  "version": "1.0",
  "loop_agent_version": "v1.1",
  "session": {
    "id": "session-2026-06-15-2300",
    "mode": "unattended",
    "started_at": "2026-06-15T23:00:00Z",
    "user_present": false,
    "max_duration_hours": 9
  },
  "decisions": [
    {
      "id": "DEC-001",
      "timestamp": "2026-06-15T23:15:32Z",
      "type": "auto",
      "category": "file_operation",
      "context": {
        "task_id": "T5-BE-1",
        "agent": "@Backend",
        "operation": "create_temp_file",
        "description": "创建 .cache/api-schema.json 缓存 OpenAPI 解析结果"
      },
      "decision": "CREATE",
      "rationale": "临时缓存文件，可重建，加快下次解析速度 30%",
      "result": "SUCCESS",
      "impact": "low",
      "reversible": true,
      "rollback_path": "rm .cache/api-schema.json"
    },
    {
      "id": "DEC-002",
      "timestamp": "2026-06-15T23:42:18Z",
      "type": "auto",
      "category": "bug_fix",
      "context": {
        "task_id": "BUG-2026-06-15-001",
        "agent": "@Bug-Defect-Repairer",
        "candidates": [
          "加 Redis 缓存",
          "优化 SQL + 加复合索引",
          "分库分表"
        ]
      },
      "decision": "candidates[1] (优化 SQL + 加复合索引)",
      "rationale": "治本方案；治标方案会引入一致性风险；分库分表过度设计",
      "result": "SUCCESS",
      "impact": "medium",
      "reversible": true,
      "rollback_path": "git revert HEAD",
      "p95_improvement_ms": 180
    }
  ],
  "pending_decisions": [
    {
      "id": "DEC-PENDING-001",
      "timestamp": "2026-06-16T02:15:00Z",
      "type": "user_required",
      "category": "time_adjustment",
      "context": "Phase 5 开发比预估时间超 3 倍（2h → 6h）",
      "options": [
        "继续执行到天亮（可能完成）",
        "降级 Phase 5 范围（牺牲非核心功能）",
        "暂停等待用户"
      ],
      "default_in_unattended": "option_1",
      "applied_action": "继续执行到天亮"
    }
  ],
  "summary": {
    "total_decisions": 12,
    "auto": 11,
    "user_required": 1,
    "success_rate": 0.917,
    "reversible_count": 12,
    "irreversible_count": 0
  }
}
```

### 4.2 pending_decision.json 格式

```json
{
  "id": "DEC-PENDING-001",
  "timestamp": "2026-06-16T02:15:00Z",
  "type": "user_required",
  "severity": "high",
  "category": "time_adjustment",
  "context": {
    "what_happened": "Phase 5 开发从预估 2h 跑到现在 6h",
    "why": "@Backend 遇到 2 个 P0 Bug 修复 + 1 个性能瓶颈",
    "expected_remaining_hours": 4
  },
  "options": [
    {
      "id": "option_1",
      "name": "继续执行到天亮",
      "risk": "可能凌晨 5 点前完成，睡眠时间充足",
      "reversible": true
    },
    {
      "id": "option_2",
      "name": "降级 Phase 5 范围",
      "risk": "牺牲 2 个非核心功能，但能保证天亮前完成",
      "reversible": true
    },
    {
      "id": "option_3",
      "name": "暂停并保存状态",
      "risk": "用户需早起处理，睡眠被打断",
      "reversible": true
    }
  ],
  "default_in_unattended": "option_1",
  "applied_action": "option_1",
  "user_acknowledged": false,
  "acknowledged_at": null
}
```

---

## 五、异常处理（"最小影响"原则）

### 5.1 异常处理矩阵

| 异常级别 | 触发条件 | 处理方式 | 是否暂停 |
|----------|----------|----------|----------|
| **L1 轻微** | 单次失败 | 自动重试（≤ 3 次） | ❌ |
| **L2 一般** | 连续失败 + 知识库有方案 | 应用方案 | ❌ |
| **L3 严重** | 无已知方案 | 跳过 + 记录 + 报告 | ❌ |
| **L4 致命** | 阻塞流程（连续 3 次同错） | 自动应用"最小影响"方案 | ❌（除非超出阈值） |
| **L5 不可逆** | 涉及生产/数据/安全 | 暂停并报告 | ✅ |
| **L6 用户边界** | 3.2 列表命中 | 暂停并报告 | ✅ |

### 5.2 "最小影响"原则决策树

```
异常发生
    ↓
是否可重试（≤ 3 次）？
    ├─ 是 → 重试
    │
    └─ 否 → 知识库有方案？
          ├─ 是 → 应用方案
          │
          └─ 否 → 是否有"最小影响"降级方案？
                ├─ 是 → 应用降级
                │     例：跳过非核心功能 / 用 mock 替代 / 留 TODO + 警告
                │     ↓
                │     记录 + 继续
                │
                └─ 否 → 暂停并报告
                      ↓
                      写入 pending_decision.json
                      ↓
                      输出 5W1H 报告
                      ↓
                      在 unattended_mode = true 时：
                        应用最安全的默认方案
                        记录 + 继续
                        任务完成后向用户报告
```

---

## 六、时间预算与检查点

### 6.1 时间预算管理

```yaml
unattended_time_budget:
  max_duration_hours: 9              # 用户设定（默认 9 小时睡觉场景）
  checkpoint_interval_minutes: 30     # 每 30 分钟保存 snapshot
  max_pending_decisions: 5           # 最多累积 5 个待确认决策
  auto_resolve_after_minutes: 60     # 待确认超过 60 分钟自动应用默认方案
  
  # 时间预警
  warnings:
    - 80% time used → 输出进度报告（不暂停）
    - 95% time used → 输出紧迫进度（不暂停）
    - 100% time used → 强制保存状态 + 输出报告
```

### 6.2 检查点策略

```yaml
checkpoints:
  frequency: "every 30 minutes"
  auto_snapshot: true
  retention: 100
  
  # 早晨交付报告
  morning_report:
    enabled: true
    content:
      - "完成的 Phase"
      - "累计自动决策数"
      - "待用户确认决策"
      - "未解决问题"
      - "完整交付物清单"
```

---

## 七、6 条运行规则（铁律）

```
┌──────────────────────────────────────────────────────────────┐
│ Loop Agent 无人值守模式 · 6 条铁律                            │
│                                                              │
│  1. 不中断原则：除非命中"用户确认边界"，不暂停               │
│  2. 最小影响原则：异常时优先回滚或降级，不破坏现有状态         │
│  3. 完整执行原则：宁可慢也要完成，不留半成品                   │
│  4. 决策可审计：所有自动决策记录到 decision_log.json          │
│  5. 时间有预算：明确 max_duration，到点强制保存并报告          │
│  6. 早晨有报告：用户醒来看到完整的"夜间作业报告"               │
└──────────────────────────────────────────────────────────────┘
```

---

## 八、夜间作业标准流程（用户视角）

```text
【23:00 用户操作】
你：用 Loop Agent 模式开发，今晚完成明天早上给我结果
PRD：docs/todo-prd.md
时间预算：8 小时
必做：登录/列表/详情/提交/单元测试/部署
可选：消息推送/统计/导出

【23:00-23:05 AI 启动】
✅ Loop Agent 模式 v1.1 激活
✅ 无人值守模式启用
✅ 时间预算 8 小时
✅ 主蓝图加载
✅ 快照 CP-000 保存
✅ Orchestrator 接管

【23:05-07:00 AI 执行（你睡觉中）】
Phase 1 需求基线（30 min）    [自动] ✅
Phase 2 交互设计（40 min）    [自动] ✅
Phase 3 视觉设计（30 min）    [自动] ✅
Phase 4 技术架构（30 min）    [自动] ✅
Phase 5 并行开发（3 h）      [自动] ✅
Phase 6 质量门禁（1.5 h）    [自动] ✅
Phase 7 知识沉淀（10 min）   [自动] ✅
Phase 8 文档生成（10 min）   [自动] ✅
Phase 9 最终终审（20 min）    [自动] ✅
Phase 10 部署（30 min）      [需确认]

中途 3 个自动决策：
- DEC-001: 创建 .cache 临时文件
- DEC-002: 选择 SQL 优化方案
- DEC-003: 跳过 P3 UI 优化

【07:00 你醒来】
📊 夜间作业报告：
  ✅ 已完成：9/10 Phase
  ⚠️ 待确认：1（部署到生产环境）
  ❌ 未完成：0
  📁 交付物：docs/、src/、测试报告、部署包
  💰 消耗：$45 / 预算 $100
  ⏱️ 实际用时：7.5 小时

请确认是否部署到生产环境（默认操作：等待你手动确认）
```

---

## 九、调用方式

### 9.1 在主入口中引用

```yaml
# loop-agent.md 触发逻辑
on_loop_agent_triggered:
  detect_unattended_intent:
    keywords: ["今晚", "明天早上", "通宵", "无人值守", "auto", "overnight"]
  if_detected:
    activate_skill: unattended-mode
    set_time_budget: <hours>
    start_execution: true
```

### 9.2 Orchestrator 调用

```javascript
// 伪代码
if (unattended_mode_enabled) {
  await skillRunner.execute('unattended-mode', {
    max_duration_hours: user_input.max_duration || 9,
    checkpoint_interval_minutes: 30,
    auto_resolve_pending_after: 60,
    strict_user_boundary: user_input.strict_boundary ?? true
  });
}
```

---

## 十、停止条件

```yaml
stop_conditions:
  normal_complete:
    - "all_phases_done"
    - "all_gates_passed"
    - "final_review == GO"
    
  hard_brakes:
    - "max_duration_hours_reached"
    - "max_budget_usd_reached"
    - "max_pending_decisions_reached (5)"
    - "user_boundary_hit"

after_stop:
  - "保存最终 snapshot"
  - "输出夜间作业报告"
  - "decision_log.json 归档"
  - "等待用户确认（如有 pending_decision）"
```

---

## 十一、与现有 Skills 集成

| Skill | 集成方式 |
|-------|----------|
| **state-snapshot** | 每 30 分钟 + 每 Phase 完成 |
| **budget-track** | 持续监控 Token 消耗 |
| **progress-detect** | 检测卡点 + 自动降级 |
| **bug-triaging** | 自动分级 + 自动分派 |
| **knowledge-extract** | 经验自动沉淀 |
| **orchestrate-map-reduce** | 多解法自动收敛 |

---

**【unattended-mode · Loop Agent v1.1 · 夜间作业能力 · 6 条铁律生效中】**
