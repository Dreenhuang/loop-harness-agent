# Skill: Gate3 全栈测试门禁

> **Skill ID**: `gate3-testing`
> **所属层级**: 第 1 层 - Skill 层（门禁类）
> **调用方**: @全栈测试员 / @Orchestrator
> **调用时机**: Gate 2 通过后
> **严格度**: ⭐⭐⭐⭐⭐（最高）
> **铁律**: P0/P1 Bug = 0 才能通过

---

## 一、用途与定位

**Gate 3 是 Loop Agent 4 道门禁中的第三道**，由 @全栈测试员 独立执行。

**核心职责**：
- 对系统进行全维度测试（功能/接口/安全/可用性）
- 严格判定 Bug 等级（P0/P1/P2/P3）
- 输出测试报告
- 触发 Bug 修复回路

---

## 二、测试维度（5 大维度全覆盖）

### 2.1 功能测试

- ✅ 100% 核心业务流程覆盖
- ✅ 所有 P0 需求点验证
- ✅ 边界条件测试（空值、极限值、异常输入）
- ✅ 用户场景模拟（happy path + 异常 path）

### 2.2 接口测试

- ✅ 100% API 覆盖（所有 endpoint）
- ✅ 正常请求 + 异常请求
- ✅ 参数校验（类型、范围、必填）
- ✅ 错误码正确性
- ✅ 幂等性测试

### 2.3 安全测试

- ✅ SQL 注入防护
- ✅ XSS 防护
- ✅ CSRF 防护
- ✅ 权限控制（水平越权 + 垂直越权）
- ✅ 敏感数据加密
- ✅ 登录爆破防护

### 2.4 可用性测试

- ✅ 跨浏览器（Chrome / Firefox / Safari / Edge）
- ✅ 跨设备（Desktop / Tablet / Mobile）
- ✅ 响应式布局
- ✅ WCAG 2.1 AA 级无障碍
- ✅ 错误提示友好性

### 2.5 兼容性测试

- ✅ 主流操作系统（Windows / macOS / Linux）
- ✅ 主流浏览器最新 2 个版本
- ✅ 网络环境（弱网 / 断网 / 切换）

---

## 三、Bug 分级标准

| 等级 | 定义 | 处理 | 通过条件 |
|------|------|------|----------|
| **P0** | 阻塞核心功能 / 数据丢失 / 安全漏洞 | 立即修复 | 必须 0 个 |
| **P1** | 影响主流程但有 workaround | 24h 内修复 | 必须 0 个 |
| **P2** | 不影响核心流程的小问题 | 排期修复 | ≤ 3 个 |
| **P3** | UI 文字、建议性优化 | 可选 | 无限制 |

---

## 调用方式

```text
@全栈测试员 请调用 gate3-testing Skill，对系统进行全面测试：
- 测试入口：https://staging.example.com
- 测试用例：docs/test-cases/
- 报告输出：.blackboard/test_reports/report_<taskId>.json
```

## 强制自动化执行（v1.1.1 修复 V-009）

> **背景**：之前 @全栈测试员 可能手动构造测试报告，违反 Maker-Checker 分离。

**强制流程**：

```
1. 调用 testing MCP（`mcp/testing.mcp.json`）执行实际测试
2. 收集真实测试输出（stdout/stderr/coverage）
3. 按本 Skill 的输出 Schema 生成报告
4. 写黑板：`blackboard/test_reports/test-report-<taskId>.json`
5. 禁止手动构造测试结果
```

**禁止行为**：
- ❌ 禁止跳过失败的测试
- ❌ 禁止伪造测试覆盖率
- ❌ 禁止在未跑测试的情况下生成报告
- ❌ 禁止修改测试结果以通过门禁

**触发命令**（@全栈测试员 必读）：

```bash
# 单元测试
bun test --coverage 2>&1 | tee test-output.log

# 集成测试
bun test tests/integration 2>&1 | tee integration-output.log

# E2E 测试
playwright test 2>&1 | tee e2e-output.log

# 生成报告（基于真实输出）
python -c "
import json, re
# 解析真实测试输出
# 生成符合本 Skill Schema 的报告
report = parse_real_test_output(...)
write_to_blackboard('blackboard/test_reports/', report)
"
```

---

## 五、执行流程（7 步）

```
【第 1 步】加载测试用例
    ├─ 从 docs/test-cases/ 加载功能用例
    ├─ 从 docs/api-spec/ 自动生成接口用例
    └─ 自动生成安全 + 兼容性用例

【第 2 步】执行功能测试
    ├─ 跑通所有 P0 场景
    └─ 记录所有 Bug

【第 3 步】执行接口测试
    ├─ 100% API 覆盖
    ├─ 异常场景
    └─ 性能基线

【第 4 步】执行安全扫描
    ├─ OWASP Top 10 检查
    ├─ 依赖漏洞扫描
    └─ 渗透测试

【第 5 步】执行兼容性测试
    ├─ 浏览器矩阵
    └─ 设备矩阵

【第 6 步】生成测试报告
    └─ 写入 .blackboard/test_reports/report_<taskId>.json

【第 7 步】发送 A2A 消息
    ├─ P0/P1 = 0 → [RESP] gate.testing.passed
    └─ 有 P0/P1 → [ERR] gate.testing.failed
```

---

## 六、输出契约（Schema）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Gate 3 Test Report",
  "type": "object",
  "required": ["taskId", "passed", "bugSummary", "coverage", "issues"],
  "properties": {
    "taskId": { "type": "string" },
    "passed": { "type": "boolean" },
    "bugSummary": {
      "type": "object",
      "properties": {
        "p0": { "type": "integer", "minimum": 0 },
        "p1": { "type": "integer", "minimum": 0 },
        "p2": { "type": "integer", "minimum": 0 },
        "p3": { "type": "integer", "minimum": 0 }
      }
    },
    "coverage": {
      "type": "object",
      "properties": {
        "core_business_flow": { "type": "number", "minimum": 0, "maximum": 100 },
        "api_coverage": { "type": "number", "minimum": 0, "maximum": 100 },
        "browser_coverage": { "type": "number", "minimum": 0, "maximum": 100 },
        "device_coverage": { "type": "number", "minimum": 0, "maximum": 100 }
      }
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "level": { "enum": ["P0", "P1", "P2", "P3"] },
          "title": { "type": "string" },
          "description": { "type": "string" },
          "reproduction_steps": { "type": "array", "items": { "type": "string" } },
          "expected": { "type": "string" },
          "actual": { "type": "string" },
          "screenshots": { "type": "array", "items": { "type": "string" } },
          "severity_reason": { "type": "string" },
          "suggested_fix": { "type": "string" }
        }
      }
    },
    "testCasesExecuted": { "type": "integer" },
    "testCasesPassed": { "type": "integer" },
    "testCasesFailed": { "type": "integer" },
    "summary": { "type": "string" }
  }
}
```

---

## 七、停止条件

```yaml
stop_condition: |
  is_done = (
    all_test_dimensions_executed == true
    AND
    test_report_written == true
    AND
    a2a_message_sent == true
  )

  passed = (
    p0_count == 0
    AND
    p1_count == 0
    AND
    p2_count <= 3
    AND
    core_business_coverage == 100
    AND
    api_coverage == 100
  )

max_attempts: 3
timeout_seconds: 3600  # 1 小时
```

---

## 八、Bug 修复回路

```
Gate 3 不通过（有 P0/P1 Bug）
    ↓
@Orchestrator 接收 [ERR] gate.testing.failed + Bug 清单
    ↓
@Bug-Defect-Repairer 接收 Bug 工单
    ↓
按 P0 → P1 → P2 顺序修复
    ↓
修复完成 → @全栈测试员 回归测试
    ↓
P0/P1 清零 → 重新触发 Gate 3
    ↓
通过 → 进入 Gate 4
```

---

## 九、与 Loop Agent 系统的集成

| 集成点 | 说明 |
|--------|------|
| **Phase 6 触发** | Gate 2 通过后自动触发 |
| **预算消耗** | 约 5-15 USD Token（取决于测试规模） |
| **黑板写入** | `.blackboard/test_reports/report_<taskId>.json` |
| **Bug 工单** | 写入 `.blackboard/bugs/bug_<id>.json` |
| **A2A 消息** | `gate.testing.passed/failed` |
| **依赖工具** | Playwright / Jest / Postman / OWASP ZAP |

## 融合验收检查（v1.1 新增）

> **对齐标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md` 第 4、7 节

### TDD 证据链检查（强制）

| 证据类型 | 要求 | 验证方式 |
|----------|------|----------|
| failing_test | 关键新功能必须有 RED 阶段测试记录 | 检查 git log 或测试文件中是否有先写测试后写实现的证据 |
| passing_test | 关键新功能必须有 GREEN 阶段测试记录 | 检查测试运行输出 |
| refactor_evidence | 关键新功能必须有重构记录或等效证明 | 检查 git log 中的 refactor 提交 |

### TDD 覆盖率要求

- 新功能代码 TDD 执行率 ≥ 80%
- TDD 执行率 = 有 TDD 证据的功能数 / 总功能数
- 低于 80% 时 Gate 3 不得放行

### 证据充分性检查

- 测试报告必须包含：测试用例数、通过数、失败数、跳过数
- 安全测试必须包含：SQL 注入、XSS、CSRF 基础检查
- API 测试覆盖率必须 ≥ 80%

### 合规判定逻辑

```
IF p0 > 0 → GATE FAIL
IF p1 > 0 → GATE FAIL
IF tdd_coverage < 80% → GATE FAIL
IF evidence_insufficient → GATE FAIL
ELSE → GATE PASS
```

---

**【Gate 3 全栈测试门禁 · Loop Agent v1.1 · 融合验收补强 · 生效中】**
