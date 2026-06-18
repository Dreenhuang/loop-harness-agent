# Loop Agent 自动化开发系统 v1.0

> **基于**：Agent Loop Engineering + Harness Engineering + 16 大角色 AGENT TEAM
> **封装层级**：4 级分层封装（Skill → Agent Profile → Workflow Blueprint → Domain Chip）
> **协同系统**：黑板（项目进度记录.md）+ A2A 消息协议
> **核心承诺**：说"用 Loop Agent 模式开发"，系统自动按 PRD→生产 流水线 全流程跑完

---

## 一、系统速览

### 1.1 核心能力

| 能力 | 说明 |
|------|------|
| **触发方式** | 自然语言（"用 Loop Agent 模式开发"）+ 斜杠命令（`/loop-agent`） |
| **16 角色协作** | 调度层/决策层/业务层/技术层/质量层/知识层/交付层 完整覆盖 |
| **4 道门禁** | 代码审查 → 性能压测 → 全栈测试 → 最终终审 |
| **10 相位流程** | 初始化 → 需求 → 设计 → 架构 → 开发 → 质量 → 知识 → 文档 → 终审 → 部署 |
| **黑板+A2A** | 文件级状态共享 + 5 种消息类型 + 4 种依赖关系 |
| **3 道硬刹车** | 预算上限 + 迭代上限 + 无进展检测 |
| **自进化（Autoloop）** | Benchmark 驱动 + 变异探索 + 优胜劣汰 |

### 1.2 适用与不适用

| ✅ 适用 | ❌ 不适用 |
|----------|------------|
| Web 功能开发 | 纯 UI 探索无明确需求 |
| 前后端分离项目 | 一句话需求（无 PRD） |
| 有明确验收标准 | 需要人工审美判断的设计 |
| 团队 4+ 人协作 | 单人超小型项目 |
| 有可复用 Skill 库 | 完全陌生的技术栈 |
| **🌙 夜间无人值守作业**（v1.1 新增） | 强实时交互任务 |

---

## 🌙 无人值守模式（v1.1 新增）

> **核心承诺**：晚上设定任务 → 睡觉 → 早晨看到完整项目。**绝对不中断**。

### 6 条铁律

1. **不中断原则**：除非命中"用户确认边界"，不暂停
2. **最小影响原则**：异常时优先回滚或降级
3. **完整执行原则**：宁可慢也要完成，不留半成品
4. **决策可审计**：所有自动决策记录到 `decision_log.json`
5. **时间有预算**：到点强制保存并报告
6. **早晨有报告**：用户醒来看到完整的"夜间作业报告"

### 触发关键词

```text
"用 Loop Agent 模式开发，今晚完成明天早上给我结果"
"进入无人值守模式" / "通宵跑" / "Auto Mode"
/unattended  / /auto-overnight
"时间预算 X 小时"
```

### 典型场景

```text
【23:00 用户】
"用 Loop Agent 模式开发，今晚完成明天早上给我结果。
 PRD：docs/todo-prd.md，时间预算 8 小时"

【07:00 用户醒来】
✅ 9/10 Phase 完成
✅ 12 次自动决策（11 成功）
📊 早晨报告自动输出
```

详细规范见 `docs/UNATTENDED_MODE.md` + `docs/night-task-template.md`。

---

## 二、4 级封装架构

### 2.1 资产全景

```text
g:\ai-gongju\Loop-agent\
├── README.md                                    ← 你正在看
├── .trae/
│   ├── rules/
│   │   ├── loop-agent.md                        ← 主入口规则 ⭐
│   │   └── A2A消息速查卡.md                      ← A2A 协议
│   ├── skills/                                   ← 第 1 层：原子能力
│   │   └── core/
│   │       ├── gate1-code-review/SKILL.md       ← 门禁 1
│   │       ├── gate2-performance/SKILL.md       ← 门禁 2
│   │       ├── gate3-testing/SKILL.md           ← 门禁 3
│   │       ├── gate4-final/SKILL.md             ← 门禁 4
│   │       ├── budget-track/SKILL.md            ← 原子：预算
│   │       ├── progress-detect/SKILL.md         ← 原子：无进展
│   │       ├── state-snapshot/SKILL.md          ← 原子：快照
│   │       ├── bug-triaging/SKILL.md            ← 原子：Bug 分级
│   │       ├── orchestrate-map-reduce/SKILL.md  ← 原子：高阶编排
│   │       └── knowledge-extract/SKILL.md       ← 原子：知识沉淀
│   ├── agents/                                   ← 第 2 层：单角色循环单元
│   │   ├── orchestrator.agent.toml
│   │   ├── product-manager.agent.toml
│   │   ├── requirements.agent.toml
│   │   ├── ux-researcher.agent.toml
│   │   ├── ui-designer.agent.toml
│   │   ├── architect.agent.toml
│   │   ├── backend.agent.toml
│   │   ├── fullstack-coder.agent.toml
│   │   ├── bug-defect-repairer.agent.toml
│   │   ├── code-reviewer.agent.toml
│   │   ├── professional-performance.agent.toml
│   │   ├── tester.agent.toml
│   │   ├── knowledge-curator.agent.toml
│   │   ├── documenter.agent.toml
│   │   ├── final-reviewer.agent.toml
│   │   └── devops.agent.toml
│   └── workflows/                                ← 第 3 层：编排蓝图
│       └── prd-to-production.json               ← 10 相位 + 4 门禁
├── blackboard/
│   └── templates/
│       └── 项目进度记录.md                        ← 黑板模板
├── domain-chips/                                 ← 第 4 层：领域黑盒芯片
│   └── web-feature-chip/
│       ├── chip.json                            ← 芯片元数据
│       └── README.md
└── loop-agent-system/
    └── Loop-Agent启动器.bat                     ← Windows 启动器
```

### 2.2 4 层职责划分

| 层级 | 定位 | 状态 | 复用粒度 |
|------|------|------|----------|
| **Skill** | 可复用的能力资产包 | 无状态 | 原子能力级 |
| **Agent Profile** | 单角色循环单元（含内部 Loop + 绑定 Skills） | 可有状态 | 角色级 |
| **Workflow Blueprint** | 多角色编排蓝图 | 有状态 | 流程级 |
| **Domain Chip** | 领域黑盒（含全部上层 + 知识库 + Benchmark + Autoloop） | 有状态 | 领域级 |

---

## 三、快速上手（5 步）

### Step 1：复制 Loop Agent 到你的项目

```bash
# 方式 A：完整复制
xcopy /E /I "g:\ai-gongju\Loop-agent\.trae" "你的项目\.trae"
xcopy /E /I "g:\ai-gongju\Loop-agent\blackboard" "你的项目\blackboard"
xcopy /E /I "g:\ai-gongju\Loop-agent\domain-chips" "你的项目\domain-chips"

# 方式 B：仅复制核心规则 + 资产链接
xcopy "g:\ai-gongju\Loop-agent\.trae\rules\loop-agent.md" "你的项目\.trae\rules\"
```

### Step 2：初始化黑板

```bash
# 把黑板模板复制到项目根
copy "g:\ai-gongju\Loop-agent\blackboard\templates\项目进度记录.md" "你的项目\项目进度记录.md"

# 或运行启动器
"g:\ai-gongju\Loop-agent\loop-agent-system\Loop-Agent启动器.bat"
```

### Step 3：在 Trae 中加载规则

把 `.trae/rules/loop-agent.md` 完整复制到：
- **Trae 全局 Custom Rules**（推荐，一次配置所有项目生效）
- 或每个项目的 `.trae/rules/`

### Step 4：触发 Loop Agent

在 Trae 中说：

```text
# 方式 1：自然语言
用 Loop Agent 模式开发

# 方式 2：斜杠命令
/loop-agent
```

### Step 5：提供 PRD

触发后，AI 会输出：

```text
✅ Loop Agent 模式已激活
✅ 黑板已加载（项目进度记录.md）
✅ 4 级封装资产已加载
✅ @Orchestrator 已就位

请提供 PRD 文档路径或粘贴 PRD 内容：
```

---

## 四、典型工作流示例

### 4.1 场景：开发一个 Todo App

```text
# 步骤 1：触发
你：用 Loop Agent 模式开发

# AI 输出
✅ Loop Agent 模式已激活
✅ @Orchestrator 启动
请提供 PRD。

# 步骤 2：提供 PRD
你：PRD 路径：docs/todo-prd.md

# AI 自动执行（10 相位）
# PHASE 0：加载资产 + 建黑板
# PHASE 1：@Product-Manager + @Requirements 产出 PRD
# PHASE 2：@UX-Researcher 产出交互流程
# PHASE 3：@UI-Designer 产出设计稿
# PHASE 4：@Architect 产出架构
# PHASE 5：@Backend + @Fullstack-Coder 并行编码
# PHASE 6：3 道门禁（CR/Performance/Testing）
# PHASE 7：@Knowledge-Curator 沉淀经验
# PHASE 8：@Documenter 生成文档
# PHASE 9：@Final-Reviewer 终审（Gate 4）
# PHASE 10：@DevOps 部署上线
```

### 4.2 场景：修复一个 Bug

```text
# 触发
你：用 Loop Agent 修复 src/api/users.ts:42 的 SQL 注入 Bug

# AI 执行
1. @全栈测试员 复现 Bug → bug-triaging 分级为 P0
2. @Bug-Defect-Repairer 修复（含回归测试）
3. gate1-code-review 自检
4. @Knowledge-Curator 沉淀 6 段式教程
5. 黑板更新
```

### 4.3 场景：性能优化

```text
# 触发
你：用 Loop Agent 模式优化 /api/users 接口的 P95 响应时间

# AI 执行
1. @Professional-Performance 压测，定位瓶颈
2. orchestrate-map-reduce：3 个 Agent 各提方案
3. @Backend 应用最优方案
4. 重新压测验证
5. @Knowledge-Curator 沉淀
```

---

## 五、核心铁律（违反任一 → Loop 失败）

| # | 铁律 | 违反后果 |
|---|------|----------|
| 1 | **Maker-Checker 分离** | 自我验证的输出永远不可信 |
| 2 | **基底介导通信** | 协调者上下文膨胀 → 单 Agent 瓶颈 |
| 3 | **三道硬刹车** | 无限循环 + 账单爆炸 |
| 4 | **先定义 Done** | 永动机 |
| 5 | **Worktree 隔离** | 协作灾难 |
| 6 | **Skill 资产化** | 重复劳动无复利 |
| 7 | **Loud Failure** | 静默替代 = 系统性崩溃 |

---

## 六、与现有系统集成

| 现有系统 | 集成方式 |
|----------|----------|
| **A2A-Agent demo** (`c:\Users\Administrator\Documents\A2A-Agent`) | 14 角色 Skill → 扩展为 16 角色；A2A 协议完全复用 |
| **黑板模式 v2.1** (`全局规则_v2.1_黑板增强版.md`) | 完整继承 |
| **问题解决经验文档管理规则** | @Knowledge-Curator 按 6 段式模板输出 |
| **GitHub & Gitee 密钥配置** | @DevOps 部署时读取 |
| **Agent Team 14 大角色** | 扩展为 16 角色 |

---

## 七、版本演进

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v1.0 | 2026-06-15 | 初始版本：4 级封装 + 16 角色 + 10 相位 + 黑板+A2A 集成 |

---

## 八、反馈与改进

- **反馈命令**：`/loop-agent feedback <问题>`
- **紧急停止**：`/loop-agent abort`
- **查询进度**：`/loop-agent status`
- **接续开发**：`/loop-agent resume`

---

## 九、一句话总结

> **Loop Agent = 4 级封装 + 16 角色 + 10 相位 + 黑板+A2A。**
> **说"用 Loop Agent 模式开发"，系统自动跑完 PRD→生产全流程。**
> **一次开发，到处复用，越用越聪明。**

---

**【Loop Agent v1.0 · 16 角色 · 10 相位 · 4 层封装 · 生效中】**

> 设计者：基于 Agent Loop Engineering 蓝皮书 + 用户项目需求
> 维护：自动演进（Autoloop）
