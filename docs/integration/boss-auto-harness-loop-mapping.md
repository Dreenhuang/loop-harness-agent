# Boss-auto-harness × Loop Agent Phase/Step 映射表

> **版本**：v1.0
> **日期**：2026-06-16
> **用途**：定义 Loop Agent 10 Phase 与 boss-auto-harness 11 Step 的映射关系

---

## 1. 映射总览

| Loop Agent Phase | boss-auto-harness Step | 融合方式 | 强制 Skill | 强制工件 |
|---|---|---|---|---|
| Phase 0 初始化 | Step 0 前置准备 | 加载资产后增加 Harness 规则注册 | pre-flight-check | - |
| Phase 1 需求基线 | Step 1 需求收集 | 强制引入 brainstorming 与 Product-Spec.md 约束 | brainstorming, product-spec-builder | Product-Spec.md |
| Phase 2 交互设计 | Step 2 + Step 3 | 在 UX 阶段引入 Design Brief 工件 | web-design-guidelines | Design-Brief.md |
| Phase 3 视觉设计 | Step 3 + Step 4 | 将组件库和状态规范纳入交付要求 | ui-designer, interaction-designer | UI-Design.md, Component-Library.md |
| Phase 4 技术架构 | Step 5 前半段 | 架构结果同步为开发计划输入 | - | Architecture.md, API-Spec.md |
| Phase 5 并行开发 | Step 5 + Step 6 | 引入微任务、TDD、子代理执行和 worktree 隔离 | writing-plans, test-driven-development, subagent-driven-development, using-git-worktrees | DEV-PLAN.md |
| Gate 1 前后 | Step 7 + Step 9 | 把验证前置与代码审查闭环融合进 Gate 1 | verification-before-completion, quality-gate, requesting-code-review, receiving-code-review | Quality-Check-Report.md, Code-Review-Report.md |
| Gate 2/3 | Step 8 + Step 10 | 用测试与 UX 审查增强现有门禁质量解释力 | test-driven-development | Test-Report.md, UX-Review-Report.md |
| Phase 7/8/9 | Step 11 + 全程文档 | 在知识沉淀、文档归档、终审中追加 Harness 工件校验 | verification-before-completion, knowledge-extract | Release-Notes.md |

---

## 2. 详细映射规则

### Phase 1 → Step 1：需求收集

**融合策略**：在 @Requirements 执行 PRD 编写前，强制执行苏格拉底式需求澄清。

- 触发条件：Phase 1 启动
- 强制 Skill：brainstorming（一次一问，探索 2-3 个替代方案）
- 强制工件：Product-Spec.md
- 证据要求：需求澄清问答记录
- 不通过处理：缺少 Product-Spec.md 时 Phase 1 不得完成

### Phase 5 → Step 5 + Step 6：开发阶段

**融合策略**：在编码前强制形成微任务级计划，编码中强制 TDD 闭环。

- 触发条件：Phase 5 启动
- 强制 Skill：
  - writing-plans（微任务分解，2-5 分钟粒度）
  - test-driven-development（RED-GREEN-REFACTOR 闭环）
  - subagent-driven-development（复杂任务自动启用子代理）
  - using-git-worktrees（每个 Phase 在独立 worktree 中开发）
- 强制工件：DEV-PLAN.md
- 证据要求：failing_test + passing_test + refactor_evidence
- 不通过处理：缺少 DEV-PLAN.md 或 TDD 证据时 Phase 5 不得完成

### Gate 1 → Step 7 + Step 9：验证与审查

**融合策略**：完成前验证 + 代码审查闭环融合进 Gate 1。

- 触发条件：Phase 5 完成
- 强制 Skill：
  - verification-before-completion（任何完成声明前必须有当场验证证据）
  - quality-gate（5 项检查必须全部通过）
  - requesting-code-review / receiving-code-review（审查反馈逐项闭环）
- 证据要求：verification_commands + review_feedback
- 不通过处理：→ @Bug-Defect-Repairer → 回到 Phase 5

---

## 3. Harness 执行协议注入流程

```
@Orchestrator 识别 Phase →
  HarnessPolicyEngine.generateProtocol() →
    生成 {phase, required_skills, required_artifacts, evidence_requirements} →
      协议随 A2A 消息派发给目标 Agent →
        Agent 执行时遵守协议约束 →
          工件写入 Artifact Registry →
            证据写入 Evidence Collector →
              Gate 读取进行合规校验
```

---

## 4. 可裁剪策略

| 项目类型 | 启用级别 | 裁剪规则 |
|----------|----------|----------|
| Web 全栈 | 严格模式 | 全部 Step + 全部工件 + 全部证据 |
| 纯后端 API | 标准模式 | 跳过 Step 2-4（UI 设计），用 API 协议替代 |
| Bug 修复 | 轻量模式 | 仅 Step 6-7 + 修复证据 + 验证命令 |
| 基础设施 | 标准模式 | Step 2-4 替换为架构契约设计 |

---

## 5. 与融合验收标准的对应

本文档定义的映射关系是融合验收标准中"流程收敛目标"和"严格按预设逻辑执行"的技术实现基础。所有 Phase/Step 映射、强制 Skill、强制工件和证据要求都可在 `prd-to-production.json` 的 `harness_discipline` 字段中找到对应配置。
