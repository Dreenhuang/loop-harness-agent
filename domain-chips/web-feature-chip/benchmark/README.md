# Domain Chip Benchmark

> 评估基准目录，存储 Web Feature 开发质量的评估集和评分标准

## 评估指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| code_quality_score | ≥ 80 | 代码质量评分 |
| test_coverage_percent | ≥ 80 | 测试覆盖率 |
| performance_p95_ms | ≤ 300 | P95 响应时间 |
| security_score | ≥ 90 | 安全评分 |
| ux_quality_score | ≥ 75 | UX 质量评分 |

## 融合验收扩展指标（v1.1 新增）

| 指标 | 目标值 | 说明 |
|------|--------|------|
| artifact_completion_rate | ≥ 95% | 工件完成率 |
| evidence_coverage_rate | ≥ 90% | 证据覆盖率 |
| tdd_execution_rate | ≥ 80% | TDD 执行率 |
| review_closure_rate | ≥ 95% | 审查闭环完成率 |

## 自进化循环

1. 标准化工作流：Loop 形状稳定才能改进
2. 评估基准：定义可度量的成功标准
3. 变异探索：在 Skills / Workflow / Prompts 上做小范围变异
4. 评分对比：基于 benchmark 对比新旧版本
5. 优胜劣汰：赢了保留，输了回滚
