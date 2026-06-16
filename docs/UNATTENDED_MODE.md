# Loop Agent · 无人值守执行模式（Unattended Mode）

> **版本**：v1.1
> **生效日期**：2026-06-15
> **Skill ID**: `unattended-mode`
> **核心承诺**：晚上设定任务 → 睡觉 → 第二天早上看到完整项目，绝对不中断

---

## 一、为什么需要无人值守模式

### 1.1 现实场景

```text
【23:00 用户】
"用 Loop Agent 模式开发，今晚做完，明天早上给我结果"
"PRD 在 docs/todo-prd.md，时间预算 8 小时"
"必做：登录/列表/详情/提交/部署"
"可选：消息推送/统计/导出"

【用户去睡觉】

【07:00 用户醒来】
✅ 打开电脑看交付物
```

**传统 Loop Agent 的问题**：
- ❌ 遇到架构变更 → 暂停 → 用户被叫醒
- ❌ 遇到 Token 超限 → 暂停 → 用户被叫醒
- ❌ 遇到 Bug 修复方案选择 → 暂停 → 用户被叫醒
- ❌ 累计暂停 5 次 → 用户无法睡觉

**无人值守模式解决的问题**：
- ✅ 自动决策常规操作（90% 场景）
- ✅ 仅在"用户确认边界"暂停（< 5% 场景）
- ✅ 异常时自动应用"最小影响"方案
- ✅ 早晨自动输出"夜间作业报告"

---

## 二、6 条铁律

| # | 铁律 | 说明 |
|---|------|------|
| 1 | **不中断原则** | 除非命中"用户确认边界"，不暂停 |
| 2 | **最小影响原则** | 异常时优先回滚或降级，不破坏现有状态 |
| 3 | **完整执行原则** | 宁可慢也要完成，不留半成品 |
| 4 | **决策可审计** | 所有自动决策记录到 `decision_log.json` |
| 5 | **时间有预算** | 明确 max_duration，到点强制保存并报告 |
| 6 | **早晨有报告** | 用户醒来看到完整的"夜间作业报告" |

---

## 三、自动决策 vs 用户确认边界

### 3.1 ✅ AI 自动决策（90% 场景）

#### 文件操作
- 创建/修改/删除临时文件（.tmp/.cache/.log/node_modules）
- 自动选择文件路径
- 文件命名（snake_case/kebab-case）
- 创建/删除/重组目录

#### 资源分配
- Token 预算内自动选择 API
- CPU/内存限制调整
- 并行度调节（3-7 Agent 规则）
- 端口分配（从池中选空闲）

#### 非关键参数
- 超时时间（默认 300s 内）
- 重试次数（≤ 3）
- 日志级别
- 缓存策略

#### 错误恢复
- 单次失败自动重试（≤ 3 次）
- 回滚到上一个 snapshot
- 应用知识库匹配方案
- 触发 Bug-Defect-Repairer

#### Bug 修复
- 自动选择修复方案（候选中）
- 写根因分析报告
- 自动应用预防措施

#### 代码生成
- 函数命名、类结构
- 单元测试用例生成
- API endpoint 命名
- 数据库表结构

#### 文档生成
- README/CHANGELOG 内容
- 注释风格
- 截图/图表

### 3.2 ❌ 必须用户确认（< 5% 场景）

| 类别 | 场景 | 阈值 |
|------|------|------|
| **架构变更** | 更换技术栈 | 跨语言/跨框架 |
|  | 重写核心模块 | > 30% 模块改动 |
|  | 数据库迁移 | 跨数据库类型 |
| **核心功能** | 修改 PRD 范围 | > 20% 功能点变更 |
|  | 删除已实现功能 | 任何 |
| **资源超阈** | Token 预算超 50% | > 150% 预估 |
|  | 迭代次数超 5 倍 | > 500% 预估 |
|  | 时间超 5 倍 | > 500% 预估 |
| **安全/合规** | 涉及用户隐私 | 任何 |
|  | 涉及支付/金融 | 任何 |
| **不可逆操作** | 生产环境部署 | 任何 |
|  | 数据库 DROP/DELETE | 任何 |
|  | 强制 push | 任何 |
| **时间计划** | 任务延期 > 3 天 | 任何 |
|  | 里程碑大幅调整 | 任何 |
| **异常无法恢复** | 连续 3 次同错 | 3 轮 |
|  | 知识库无方案 | 任何 |
|  | Snapshot 恢复失败 | 任何 |

### 3.3 决策矩阵（决策树）

```
执行中遇到决策点
    ↓
属于自动决策列表？
    ├─ 是 → AI 自动决策
    │     ↓
    │     记录到 decision_log.json
    │     ↓
    │     继续执行
    │
    └─ 否 → 属于用户确认列表？
          ├─ 是 → 暂停并报告（unattended 模式下应用默认方案）
          │
          └─ 否 → 启用"最小影响"原则
                ↓
                选项：选择改动最小 / 跳过 / 回滚
                ↓
                记录 + 继续
                ↓
                任务完成后向用户报告
```

---

## 四、决策记录格式

### 4.1 decision_log.json

存储路径：`blackboard/decision_log.json`

```json
{
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
        "operation": "create_temp_file"
      },
      "decision": "CREATE .cache/api-schema.json",
      "rationale": "临时缓存文件，可重建，加快解析速度 30%",
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
        "candidates": ["加 Redis 缓存", "优化 SQL", "分库分表"]
      },
      "decision": "优化 SQL + 加复合索引",
      "rationale": "治本方案；无一致性风险；避免过度设计",
      "result": "SUCCESS",
      "impact": "medium",
      "reversible": true,
      "rollback_path": "git revert HEAD",
      "metrics": {
        "p95_improvement_ms": 180
      }
    }
  ],
  "pending_decisions": [],
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

### 4.2 pending_decision.json

存储路径：`blackboard/pending_decision.json`

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
    { "id": "option_1", "name": "继续执行到天亮", "risk": "可能凌晨 5 点前完成" },
    { "id": "option_2", "name": "降级 Phase 5 范围", "risk": "牺牲 2 个非核心功能" },
    { "id": "option_3", "name": "暂停并保存状态", "risk": "用户需早起处理" }
  ],
  "default_in_unattended": "option_1",
  "applied_action": "option_1",
  "user_acknowledged": false
}
```

---

## 五、异常处理（"最小影响"原则）

### 5.1 异常处理矩阵

| 异常级别 | 触发条件 | 处理方式 | 暂停？ |
|----------|----------|----------|--------|
| **L1 轻微** | 单次失败 | 自动重试 ≤ 3 | ❌ |
| **L2 一般** | 连续失败 + 知识库有方案 | 应用方案 | ❌ |
| **L3 严重** | 无已知方案 | 跳过 + 记录 + 报告 | ❌ |
| **L4 致命** | 阻塞流程（连续 3 次同错） | 应用"最小影响"方案 | ❌ |
| **L5 不可逆** | 涉及生产/数据/安全 | 暂停并报告 | ✅ |
| **L6 用户边界** | 3.2 列表命中 | 暂停并报告（unattended 模式应用默认） | ⚠️ |

### 5.2 "最小影响"原则决策树

```
异常发生
    ↓
可重试（≤ 3 次）？
    ├─ 是 → 重试
    │
    └─ 否 → 知识库有方案？
          ├─ 是 → 应用方案
          │
          └─ 否 → 是否有降级方案？
                ├─ 是 → 应用降级
                │     例：跳过非核心 / mock 替代 / TODO + 警告
                │     ↓
                │     记录 + 继续
                │
                └─ 否 → 暂停并报告
                      ↓
                      写入 pending_decision.json
                      ↓
                      输出 5W1H 报告
                      ↓
                      unattended 模式：应用最安全默认
                      任务完成后向用户报告
```

---

## 六、时间预算与检查点

### 6.1 时间预算管理

```yaml
unattended_time_budget:
  max_duration_hours: 9              # 用户设定（默认 9h 睡觉）
  checkpoint_interval_minutes: 30     # 每 30 分钟 snapshot
  max_pending_decisions: 5           # 最多累积 5 个待确认
  auto_resolve_after_minutes: 60     # 待确认超过 60 分钟自动应用默认
  
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

## 八、夜间作业标准流程

```text
【23:00 用户】
你：用 Loop Agent 模式开发，今晚完成明天早上给我结果
PRD：docs/todo-prd.md
时间预算：8 小时
必做：登录/列表/详情/提交/部署
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
```

---

## 九、触发关键词

### 9.1 自然语言触发

```text
- "用 Loop Agent 模式开发，今晚做完"
- "进入无人值守模式"
- "今晚完成，明天早上给我结果"
- "Auto Mode"
- "set it and forget it"
- "通宵跑"
- "/unattended"
- "/auto-overnight"
```

### 9.2 斜杠命令

```text
/unattended                    # 启用无人值守模式
/auto-overnight                # 启用通宵模式
/loop-agent unattended         # 组合：Loop Agent + 无人值守
```

### 9.3 Orchestrator 集成

```javascript
// 在 Orchestrator 启动时检测
if (detectUnattendedIntent(input)) {
  await skillRunner.execute('unattended-mode', {
    max_duration_hours: extractMaxDuration(input) || 9,
    checkpoint_interval_minutes: 30,
    auto_resolve_pending_after: 60,
    strict_user_boundary: true
  });
}
```

---

## 十、与其他 Skills 集成

| Skill | 集成方式 |
|-------|----------|
| **state-snapshot** | 每 30 分钟 + 每 Phase 完成 |
| **budget-track** | 持续监控 Token 消耗 |
| **progress-detect** | 检测卡点 + 自动降级 |
| **bug-triaging** | 自动分级 + 自动分派 |
| **knowledge-extract** | 经验自动沉淀 |
| **orchestrate-map-reduce** | 多解法自动收敛 |

---

## 十一、版本演进

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v1.0 | 2026-06-15 | 初始版本：6 铁律 + 决策矩阵 + decision_log + 夜间作业流程 |

---

**【unattended-mode · Loop Agent v1.1 · 6 条铁律 · 夜间作业能力】**
