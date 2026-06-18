# Skill: Gate2 性能门禁

> **Skill ID**: `gate2-performance`
> **所属层级**: 第 1 层 - Skill 层（门禁类）
> **调用方**: @Professional-Performance / @Orchestrator
> **调用时机**: Gate 1 通过后
> **严格度**: ⭐⭐⭐⭐⭐（最高）
> **铁律**: SLA 指标未达标 → 触发性能调优回路

---

## 一、用途与定位

**Gate 2 是 Loop Agent 4 道门禁中的第二道**，由 @Professional-Performance 独立执行。

**核心职责**：
- 对 Gate 1 通过后的系统进行全链路压测
- 验证性能 SLA（响应时间、并发、错误率、吞吐量）
- 输出压测报告
- 触发性能调优回路（如未达 SLA）

---

## 二、性能 SLA 指标（强制标准）

### 2.1 API 响应时间

| 指标 | 阈值 | 测量方式 |
|------|------|----------|
| **P50** | ≤ 100ms | 压测 5 分钟取中位数 |
| **P95** | ≤ 300ms | 压测 5 分钟取 95 分位 |
| **P99** | ≤ 500ms | 压测 5 分钟取 99 分位 |

### 2.2 页面加载时间

| 指标 | 阈值 | 测量方式 |
|------|------|----------|
| **FCP（First Contentful Paint）** | ≤ 1s | Lighthouse |
| **LCP（Largest Contentful Paint）** | ≤ 2s | Lighthouse |
| **TTI（Time to Interactive）** | ≤ 3s | Lighthouse |

### 2.3 并发与吞吐量

| 指标 | 阈值 |
|------|------|
| **并发用户数** | ≥ 1000 并发无错误 |
| **吞吐量** | ≥ 1000 TPS |
| **错误率** | ≤ 0.1% |

### 2.4 资源使用

| 指标 | 阈值 |
|------|------|
| **CPU 使用率** | ≤ 70%（压测期间均值） |
| **内存使用率** | ≤ 80%（无泄漏） |
| **数据库慢查询** | 0 个（> 1s） |

---

## 三、调用方式

```text
@Professional-Performance 请调用 gate2-performance Skill，对以下系统进行压测：
- 系统入口：https://staging.example.com
- 压测场景：登录 + 列表 + 详情 + 提交
- 报告输出：.blackboard/performance/perf_<taskId>.json
```

---

## 四、执行流程（6 步）

```
【第 1 步】环境准备
    ├─ 确认 staging 环境已部署
    ├─ 准备压测数据（10000+ 用户/订单）
    └─ 配置监控（Grafana / Prometheus）

【第 2 步】冒烟测试
    ├─ 10 并发跑 1 分钟
    ├─ 确认无 5xx 错误
    └─ 确认 P99 < 500ms

【第 3 步】阶梯加压
    ├─ 100 → 500 → 1000 并发
    ├─ 每阶段持续 5 分钟
    └─ 记录 P50/P95/P99 + 错误率

【第 4 步】峰值测试
    ├─ 1500 并发持续 10 分钟
    ├─ 监控资源使用
    └─ 检测是否有泄漏

【第 5 步】生成压测报告
    └─ 写入 .blackboard/performance/perf_<taskId>.json

【第 6 步】发送 A2A 消息
    ├─ 全部 SLA 达标 → [RESP] gate.performance.passed
    └─ 有指标超标 → [ERR] gate.performance.failed
```

---

## 五、输出契约（Schema）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Gate 2 Performance Report",
  "type": "object",
  "required": ["taskId", "passed", "slaMetrics", "issues"],
  "properties": {
    "taskId": { "type": "string" },
    "passed": { "type": "boolean" },
    "slaMetrics": {
      "type": "object",
      "properties": {
        "api_response_ms": {
          "p50": { "type": "number" },
          "p95": { "type": "number" },
          "p99": { "type": "number" }
        },
        "page_load_ms": {
          "fcp": { "type": "number" },
          "lcp": { "type": "number" },
          "tti": { "type": "number" }
        },
        "concurrent_users_passed": { "type": "integer" },
        "throughput_tps": { "type": "number" },
        "error_rate": { "type": "number" }
      }
    },
    "resourceUsage": {
      "cpu_avg": { "type": "number" },
      "memory_avg": { "type": "number" },
      "db_slow_queries": { "type": "integer" }
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "metric": { "type": "string" },
          "expected": { "type": "number" },
          "actual": { "type": "number" },
          "severity": { "enum": ["BLOCKER", "MAJOR"] },
          "bottleneck": { "type": "string" },
          "optimization_suggestion": { "type": "string" }
        }
      }
    },
    "summary": { "type": "string" }
  }
}
```

---

## 六、停止条件

```yaml
stop_condition: |
  is_done = (
    smoke_test_passed == true
    AND
    pressure_test_completed == true
    AND
    performance_report_written == true
    AND
    a2a_message_sent == true
  )

max_attempts: 3
timeout_seconds: 1800  # 30 分钟
```

---

## 七、性能调优回路

当性能未达 SLA 时：

```
Gate 2 不通过
    ↓
@Orchestrator 接收 [ERR] gate.performance.failed
    ↓
判断瓶颈类型：
    ├─ API 慢 → @Backend 优化（缓存、查询、算法）
    ├─ 页面慢 → @Fullstack-Coder 优化（懒加载、CDN、压缩）
    └─ 资源高 → @DevOps 优化（扩容、配置调优）
    ↓
@Bug-Defect-Repairer 跟踪修复进度
    ↓
修复完成 → 重新触发 Gate 2
    ↓
通过 → 进入 Gate 3
```

---

## 八、与 Loop Agent 系统的集成

| 集成点 | 说明 |
|--------|------|
| **Phase 6 触发** | Gate 1 通过后 @Orchestrator 自动触发 |
| **预算消耗** | 单次压测约 5-10 USD Token |
| **黑板写入** | `.blackboard/performance/perf_<taskId>.json` |
| **A2A 消息** | `gate.performance.passed/failed` |
| **依赖工具** | k6 / wrk / Lighthouse / Apache Bench |

## 融合验收检查（v1.1 新增）

> **对齐标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md` 第 4、6 节

### 证据真实性验证（强制）

| 检查项 | 要求 |
|--------|------|
| 压测数据来源 | 必须来自真实压测工具执行结果，禁止手动构造 |
| SLA 指标可复现 | 必须提供压测命令和参数，可独立复现 |
| 性能报告完整性 | 必须包含 P50/P95/P99/错误率/并发数 |

### Token 效率检查

- 性能测试过程是否产生不必要的全量扫描
- 测试报告是否采用摘要格式而非全量日志
- 是否存在重复执行已通过检查的情况

### 生产级 vs Demo 级判定

| 判定维度 | 生产级 | Demo 级 |
|----------|--------|---------|
| 并发用户数 | ≥ 预期生产负载 | 仅单用户测试 |
| 持续时间 | ≥ 5 分钟稳定 | 仅秒级验证 |
| 数据量 | 生产级数据量 | 仅少量样本 |

**铁律**：性能测试结果为 Demo 级时，不得标记为生产级交付。

### 合规判定逻辑

```
IF sla_not_met → GATE FAIL
IF evidence_not_verifiable → GATE FAIL
IF demo_disguised_as_production → GATE FAIL (一票否决)
ELSE → GATE PASS
```

---

**【Gate 2 性能门禁 · Loop Agent v1.1 · 融合验收补强 · 生效中】**
