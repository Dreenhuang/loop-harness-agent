# Skill: Gate1 代码质量审查门禁

> **Skill ID**: `gate1-code-review`
> **所属层级**: 第 1 层 - Skill 层（门禁类）
> **调用方**: @Code-Reviewer / @Orchestrator
> **调用时机**: Phase 5（并行开发）完成后
> **严格度**: ⭐⭐⭐⭐⭐（最高，不允许放宽）
> **铁律**: 任何 Blocker 不通过 → 强制回到 Phase 5 修复

---

## 一、用途与定位

**Gate 1 是 Loop Agent 4 道门禁中的第一道**，由 @Code-Reviewer 独立角色执行（Maker-Checker 分离）。

**核心职责**：
- 对 Phase 5 输出的前后端代码进行全维度审查
- 严格判定 Blocker 级别问题
- 输出结构化 CR 报告
- 触发 Bug 修复回路（如有 Blocker）

**与 A2A Agent 关系**：
- 接收 topic: `task.code.review` / `gate.code.review.request`
- 完成后发送 topic: `gate.code.review.passed` 或 `gate.code.review.failed`
- 输出节点: `Gate` 类型

---

## 二、调用方式

```text
@Code-Reviewer 请调用 gate1-code-review Skill，对以下代码进行审查：
- 后端代码路径：src/backend/
- 前端代码路径：src/frontend/
- 配置文件：package.json, .env.example
- 输出报告路径：.blackboard/reviews/review_<taskId>.json
```

---

## 三、检查标准（必须 100% 满足才算通过）

### 3.1 Blocker 级别（任一不通过 → 整体不通过）

| # | 检查项 | 阈值 | 检测方法 |
|---|--------|------|----------|
| B1 | 编译/构建错误 | 0 Error | `bun run build` 必须 0 错误 |
| B2 | 安全漏洞（Critical/High） | 0 个 | 手动审计 + ESLint security 插件 |
| B3 | SQL 注入风险 | 0 处 | 检查所有数据库操作使用参数化查询 |
| B4 | XSS 风险 | 0 处 | 检查所有 v-html / innerHTML / dangerouslySetInnerHTML |
| B5 | 硬编码密钥/凭证 | 0 处 | 扫描所有 .env、配置文件、源代码 |
| B6 | TypeScript 严格模式错误 | 0 个 | `tsc --noEmit` 必须 0 错误 |
| B7 | 测试套件运行 | 100% 通过 | `bun test` 必须 0 failure |

### 3.2 Major 级别（不通过 → 警告但可继续）

| # | 检查项 | 阈值 | 检测方法 |
|---|--------|------|----------|
| M1 | 单元测试覆盖率 | ≥ 80% | `bun test --coverage` |
| M2 | 代码重复率 | ≤ 3% | jscpd / 人工抽检 |
| M3 | 圈复杂度 | ≤ 10/函数 | ESLint complexity 规则 |
| M4 | 函数行数 | ≤ 50 行/函数 | ESLint max-lines-per-function |
| M5 | 文件行数 | ≤ 300 行/文件 | ESLint max-lines |
| M6 | 依赖漏洞（Moderate） | 0 个 | `bun audit` |

### 3.3 Minor 级别（仅记录，不阻断）

| # | 检查项 | 阈值 |
|---|--------|------|
| m1 | 命名规范 | 100% 符合项目约定 |
| m2 | 注释覆盖率 | ≥ 30%（公开 API） |
| m3 | 格式化 | 100% 通过 prettier |

---

## 四、执行流程（5 步）

```
【第 1 步】收集审查范围
    ├─ 接收 @Orchestrator 派发的代码路径清单
    ├─ 收集所有 git diff（对比上一 Phase 的输出）
    └─ 加载项目代码规范（.eslintrc / tsconfig.json）

【第 2 步】执行自动化检查
    ├─ bun run build        # 编译检查（B1, B6）
    ├─ bun test             # 测试运行（B7）
    ├─ bun test --coverage  # 覆盖率（M1）
    └─ bun audit            # 依赖漏洞（M6）

【第 3 步】执行人工/AI 审查
    ├─ B2-B5 安全审计（必须逐文件检查）
    ├─ M2-M5 复杂度与重复（ESLint + 人工抽检）
    └─ m1-m3 规范与注释

【第 4 步】生成审查报告
    └─ 写入 .blackboard/reviews/review_<taskId>.json

【第 5 步】发送 A2A 消息
    ├─ 全部 Blocker 通过 → [RESP] gate.code.review.passed
    └─ 有 Blocker → [ERR] gate.code.review.failed（含问题清单）
```

---

## 五、输出契约（Schema）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Gate 1 Code Review Report",
  "type": "object",
  "required": ["taskId", "passed", "blockerCount", "summary", "issues"],
  "properties": {
    "taskId": { "type": "string" },
    "passed": { "type": "boolean", "description": "true=通过, false=不通过" },
    "blockerCount": { "type": "integer", "minimum": 0 },
    "majorCount": { "type": "integer", "minimum": 0 },
    "minorCount": { "type": "integer", "minimum": 0 },
    "summary": { "type": "string", "description": "人类可读摘要" },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["severity", "file", "line", "rule", "message"],
        "properties": {
          "severity": { "enum": ["BLOCKER", "MAJOR", "MINOR"] },
          "file": { "type": "string" },
          "line": { "type": "integer" },
          "rule": { "type": "string", "description": "规则编号 B1-M6-m3" },
          "message": { "type": "string" },
          "fix_suggestion": { "type": "string" }
        }
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "test_coverage": { "type": "number" },
        "duplication_rate": { "type": "number" },
        "avg_complexity": { "type": "number" },
        "build_time_ms": { "type": "integer" }
      }
    },
    "next_actions": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

### 5.1 通过示例

```json
{
  "taskId": "cr-2026-06-15-001",
  "passed": true,
  "projectType": "web",  # v1.1.1 修复 V-007: 添加项目类型
  "blockerCount": 0,
  "majorCount": 0,
  "minorCount": 2,
  "summary": "代码审查通过：0 Blocker，0 Major，2 Minor（建议优化）。可进入 Gate 2 性能门禁。",
  "issues": [
    {
      "severity": "MINOR",
      "file": "src/utils/format.ts",
      "line": 23,
      "rule": "m1",
      "message": "函数命名建议更语义化",
      "fix_suggestion": "rename 'fmt' to 'formatDate'"
    }
  ],
  "metrics": {
    "test_coverage": 87.3,
    "duplication_rate": 1.2,
    "avg_complexity": 4.5,
    "build_time_ms": 12450
  },
  "next_actions": ["@Orchestrator 触发 Gate 2 性能门禁"]
}
```

### 5.2 不通过示例

```json
{
  "taskId": "cr-2026-06-15-001",
  "passed": false,
  "blockerCount": 2,
  "majorCount": 1,
  "minorCount": 0,
  "summary": "代码审查不通过：2 个 Blocker（SQL 注入 + 硬编码密钥），必须修复后重审。",
  "issues": [
    {
      "severity": "BLOCKER",
      "file": "src/backend/api/users.ts",
      "line": 42,
      "rule": "B3",
      "message": "SQL 注入风险：用户输入直接拼接到 SQL 字符串",
      "fix_suggestion": "使用参数化查询：db.query('SELECT * FROM users WHERE id = $1', [userId])"
    },
    {
      "severity": "BLOCKER",
      "file": "src/backend/config/auth.ts",
      "line": 8,
      "rule": "B5",
      "message": "硬编码 JWT_SECRET",
      "fix_suggestion": "改用 process.env.JWT_SECRET，从 .env 读取"
    }
  ],
  "metrics": { "test_coverage": 65.2 },
  "next_actions": [
    "@Bug-Defect-Repairer 修复 2 个 Blocker",
    "修复完成后 @Code-Reviewer 重新审查"
  ]
}
```

---

## 六、停止条件

```yaml
stop_condition: |
  is_done = (
    自动化检查全部执行完成
    AND
    review_report_written_to_blackboard == true
    AND
    a2a_message_sent == true
  )

max_attempts: 3
timeout_seconds: 600
```

---

## 七、与 Loop Agent 系统的集成

| 集成点 | 说明 |
|--------|------|
| **Phase 6 触发** | Phase 5 完成后 @Orchestrator 自动触发 |
| **失败回路** | Blocker → @Bug-Defect-Repairer → 回到 Phase 5 |
| **预算消耗** | 单次审查约 2-5 USD Token |
| **黑板写入** | `.blackboard/reviews/review_<taskId>.json` |
| **知识图谱** | 新增 `Gate-CR-<taskId>` 节点 |
| **A2A 消息** | 通过 / 不通过 都必须发 A2A 消息 |

---

## 八、Maker-Checker 分离铁律

> **禁止** @Backend / @Fullstack-Coder 自行验证自己的代码。
>
> 即使 @Code-Reviewer 是 AI 模型，也必须：
> - 独立视角（不同 prompt / 不同 temperature）
> - 不同指令集（审查者 vs 编码者）
> - 严禁放水（"看起来不错" 不算通过）

## 融合验收检查（v1.1 新增）

> **对齐标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md` 第 4、7 节

### 证据链检查（强制）

审查通过前必须验证以下证据：

| 证据类型 | 要求 | 验证方式 |
|----------|------|----------|
| failing_test | 关键新功能必须有失败测试记录 | 检查测试文件中是否有 RED 阶段测试 |
| passing_test | 关键新功能必须有通过测试记录 | 检查测试文件中是否有 GREEN 阶段测试 |
| verification_commands | 必须提供可执行的验证命令 | 检查是否提供 `npm test` / `bun test` 等命令及输出 |

**铁律**：缺少上述任一证据时，Gate 1 不得放行。

### Fresh Evidence 规则（强制）

- 任何"已通过""已完成"声明必须有**当场验证证据**
- 禁止引用历史验证结果作为当前通过依据
- 验证命令必须在审查时重新执行并记录输出

### No Soft Claims 规则（强制）

- 禁止"看起来不错""应该没问题"等软性判断
- 每项检查结论必须为 ✅ PASS 或 ❌ FAIL，不接受 ⚠️ MAYBE
- FAIL 项必须附带具体问题描述和修复建议

### 工件完整性检查

Gate 1 通过前必须确认以下工件存在：
- [ ] DEV-PLAN.md 已创建
- [ ] 源代码目录结构清晰
- [ ] 测试文件已创建

### 合规判定逻辑

```
IF blocker_count > 0 → GATE FAIL
IF evidence_missing → GATE FAIL
IF soft_claims_detected → GATE FAIL
IF artifacts_incomplete → GATE FAIL
ELSE → GATE PASS
```

---

**【Gate 1 代码质量门禁 · Loop Agent v1.1 · 融合验收补强 · 生效中】**
