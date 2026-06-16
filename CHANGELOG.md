# 更新日志

> **Loop-Harness-Agent 版本变更记录**

---

## [1.2.0] - 2026-06-17

### 🎉 重大变更

- **正式命名**：Loop Agent 升级为 **Loop-Harness-Agent**（Loop Agent × Boss-auto-harness 融合模式）
- **架构升级**：从 4 级封装升级为 **5 级封装**（新增 Artifact & Evidence 地基层）
- **触发机制**：新增 `/loop-harness-agent` 斜杠命令，兼容旧 `/loop-agent` 命令
- **容错识别**：触发词支持大小写不敏感、连字符/空格/下划线混用、简写 LHA

### ✨ 新增

- **9 个工件模板**（在 `templates/` 下）：
  - Product-Spec.md（产品规格）
  - Design-Brief.md（设计规范）
  - UI-Design.md（UI 设计）
  - Component-Library.md（组件库）
  - DEV-PLAN.md（开发计划）
  - Quality-Check-Report.md（质量检查报告）
  - Code-Review-Report.md（代码审查报告）
  - UX-Review-Report.md（UX 审查报告）
  - Release-Notes.md（发布说明）

- **artifacts 目录结构**（地基层）：
  - `artifacts/registry/` - 工件注册表
  - `artifacts/evidence/` - 证据收集器

- **domain-chips 扩展**：
  - `knowledge/` - 知识库
  - `benchmark/eval-set.json` - 评估集

- **融合验收集成文档**（在 `docs/integration/` 下）：
  - 融合验收标准.md
  - boss-auto-harness-loop-mapping.md（Phase/Step 映射表）
  - artifact-registry-spec.md（工件注册表规范）
  - evidence-collector-spec.md（证据收集器规范）

- **分发文档**：
  - README.md（中文主入口）
  - INSTALL.md（安装指南）
  - EXAMPLES.md（使用示例）
  - CHANGELOG.md（更新日志）

### 🔧 增强

- **orchestrator.ts**：
  - 新增 `HarnessPolicyEngine` 类（10 Phase 协议映射）
  - 新增 `GateComplianceChecker` 类（Gate 1 + Gate 4 合规检查）
  - 新增 5 个类型定义（HarnessProtocol、ArtifactRecord、EvidenceRecord 等）
  - `spawnAgents` 方法注入 Harness 协议生成逻辑

- **4 道门禁 Skill 融合验收补强**：
  - `gate1-code-review`：证据链检查 + Fresh Evidence 规则 + No Soft Claims
  - `gate2-performance`：证据真实性验证 + 生产级 vs Demo 级判定
  - `gate3-testing`：TDD 证据链 + TDD 覆盖率要求（≥80%）
  - `gate4-final`：12 项强制工件 + 5 类证据 + 6 项一票否决

- **Agent Profile**：
  - 16 个 .toml 全部增加 `fallback_mode` 字段
  - documenter.agent.toml 增加 `artifact_registry_sync` 字段

- **Skill 补强**：
  - `knowledge-extract`：新增融合经验沉淀模板（5 类偏离分类 + 6 段式扩展）
  - `progress-detect`：新增 4 级恢复机制（重试→回退→降级→人工确认）

### 🐛 修复

- 修复 `04-ARCHITECTURE.json` 含非法 JSON 注释导致解析失败

### 📊 统计

| 指标 | 数值 |
|------|------|
| Agent Profile | 16 个 |
| Skill | 18 个 |
| Workflow Phase JSON | 10 个 |
| Workflow Gate JSON | 4 个 |
| 工件模板 | 9 个 |
| 文档 | 12+ |
| 总代码行数 | ~20,000 |

---

## [1.1.0] - 2026-06-16

### ✨ 新增

- 融合 Boss-auto-harness 验收标准
- 新增闭环、证据、Token 治理与防偏离规则
- A2A 速查卡 v1.1：新增融合验收类 Topic（8 个）
- 16 角色 Agent Profile（含 harness_discipline 字段）

---

## [1.0.0] - 2026-06-15

### ✨ 初始发布

- 4 级封装（Skill → Agent → Workflow → Domain Chip）
- 16 角色 + 10 相位 + 黑板+A2A 集成
- 18 个原子 Skill
- Loop Agent 主入口规则

---

## 版本规范

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

---

**【Loop-Harness-Agent · 持续演进中】**
