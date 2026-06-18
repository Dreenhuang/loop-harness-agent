# Loop Agent 系统 - 安装与使用清单 v1.0

> **生成日期**：2026-06-15
> **系统版本**：Loop Agent v1.0

---

## ✅ 已完成（系统构建）

### 主仓库（g:\ai-gongju\Loop-agent\）

```text
g:\ai-gongju\Loop-agent\
├── README.md                                    ← 系统总说明
├── INSTALL.md                                   ← 本文件
├── .gitignore
├── .trae/
│   ├── rules/
│   │   ├── loop-agent.md                        ← 主入口规则 ⭐
│   │   └── A2A消息速查卡.md                      ← A2A 协议
│   ├── commands/
│   │   └── loop-agent.toml                      ← 斜杠命令配置
│   ├── skills/core/                              ← 第 1 层（10 个 Skill）
│   │   ├── gate1-code-review/SKILL.md           ← 门禁 1：代码质量
│   │   ├── gate2-performance/SKILL.md           ← 门禁 2：性能
│   │   ├── gate3-testing/SKILL.md               ← 门禁 3：全栈测试
│   │   ├── gate4-final/SKILL.md                 ← 门禁 4：终审
│   │   ├── budget-track/SKILL.md                ← 原子：预算
│   │   ├── progress-detect/SKILL.md             ← 原子：无进展检测
│   │   ├── state-snapshot/SKILL.md              ← 原子：快照
│   │   ├── bug-triaging/SKILL.md                ← 原子：Bug 分级
│   │   ├── orchestrate-map-reduce/SKILL.md      ← 原子：高阶编排
│   │   └── knowledge-extract/SKILL.md           ← 原子：知识沉淀
│   ├── agents/                                   ← 第 2 层（16 个 Profile）
│   │   ├── orchestrator.agent.toml              ⭐
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
│   └── workflows/
│       └── prd-to-production.json               ← 第 3 层 Workflow 蓝图
├── blackboard/
│   └── templates/
│       └── 项目进度记录.md                        ← 黑板模板（12 区块）
├── domain-chips/                                 ← 第 4 层 Domain Chip
│   └── web-feature-chip/
│       ├── chip.json                            ← 芯片元数据
│       └── README.md
└── loop-agent-system/
    └── Loop-Agent启动器.bat                     ← Windows 启动器
```

**统计**：
- 文件总数：约 35 个核心文件
- Skill 数：10 个
- Agent Profile 数：16 个
- Workflow 蓝图：1 个（10 相位）
- Domain Chip：1 个（带 Autoloop）
- 总代码行数：约 5000+ 行

### Trae 全局（双份存储）

```text
C:\Users\Administrator\AppData\Roaming\Trae\User\skills\loop-agent-system\SKILL.md
```

**已注册为 Trae 全局 Skill**（YAML frontmatter 格式，含 name/description/color/emoji/vibe/tools）。

---

## 🚀 立即使用

### 方式 1：在 Trae 中触发

打开 Trae IDE，说：

```text
# 自然语言触发（推荐）
"用 Loop Agent 模式开发"
"启动 Loop Agent"
"按 Loop Engineering 流程做"

# 或斜杠命令
/loop-agent
/loop-agent status
/loop-agent resume
```

### 方式 2：在新项目中使用

```bash
# Step 1: 复制 Loop Agent 资产
xcopy /E /I "g:\ai-gongju\Loop-agent\.trae" "<你的项目>\.trae"
xcopy /E /I "g:\ai-gongju\Loop-agent\blackboard" "<你的项目>\blackboard"
xcopy /E /I "g:\ai-gongju\Loop-agent\domain-chips" "<你的项目>\domain-chips"

# Step 2: 初始化黑板
copy "g:\ai-gongju\Loop-agent\blackboard\templates\项目进度记录.md" "<你的项目>\项目进度记录.md"

# Step 3: 在 Trae 中触发
/loop-agent
```

### 方式 3：双份存储已就位

由于 loop-agent-system Skill 已注册到 Trae 全局 `User\skills\`，**所有项目自动生效**。无需任何额外配置。

---

## 📋 16 角色速查（@调用）

| @角色 | 职责 |
|-------|------|
| `@Orchestrator` | 总控调度、任务分派、状态管理 |
| `@Product-Manager` | 产品规划、业务决策、需求优先级 |
| `@Requirements` | PRD 编写、需求基线、验收标准 |
| `@UX-Researcher` | 交互流程、用户旅程、原型 |
| `@UI-Designer` | 视觉设计、组件库、Design Token |
| `@Architect` | 架构设计、技术选型、接口规范 |
| `@Backend` | 后端开发、API、数据库 |
| `@Fullstack-Coder` | 前端开发、页面、组件 |
| `@Bug-Defect-Repairer` | Bug 定位修复、故障应急 |
| `@Code-Reviewer` | 代码审查（Gate 1） |
| `@Professional-Performance` | 性能压测（Gate 2） |
| `@全栈测试员` | 全栈测试（Gate 3） |
| `@Knowledge-Curator` | 知识沉淀、6 段式教程 |
| `@Documenter` | 全文档归档 |
| `@Final-Reviewer` | 终审、Gate 4 |
| `@DevOps` | 部署、CI/CD、监控 |

---

## 🎯 4 道门禁

| 门禁 | 角色 | 通过条件 | 不通过处理 |
|------|------|----------|------------|
| **Gate 1** | @Code-Reviewer | 0 Blocker + 0 Major | → @Bug-Defect-Repairer → 回 Phase 5 |
| **Gate 2** | @Professional-Performance | P95 ≤ 300ms + 错误率 ≤ 0.1% | 同上 |
| **Gate 3** | @全栈测试员 | P0=0 + P1=0 + P2≤3 | 同上 |
| **Gate 4** | @Final-Reviewer | 风险等级 ≤ LOW | 回到对应 Phase |

---

## 🔧 3 道硬刹车

1. **max_iterations = 200**（全局）
2. **max_budget_usd = 100**（全局）
3. **no_progress_detection = 3**（连续 3 轮无进展即停）

---

## 📂 与 A2A-Agent 集成

| A2A-Agent 资源 | Loop Agent 复用方式 |
|----------------|---------------------|
| `c:\Users\Administrator\Documents\A2A-Agent\trae-skills\core\a2a-orchestrator.skill.md` | Loop Agent 的 @Orchestrator |
| `trae-skills\core\a2a-requirements.skill.md` | Loop Agent 的 @Requirements |
| `trae-skills\extended\a2a-architect.skill.md` | Loop Agent 的 @Architect |
| `trae-skills\extended\a2a-*.skill.md` | Loop Agent 的 14 角色 |
| `A2A消息速查卡.md` | 完全继承 |
| `全局规则_v2.1_黑板增强版.md` | 完全继承（黑板+A2A） |

**Loop Agent 是 A2A-Agent 的超集**：14 角色 → 16 角色（增加 @Product-Manager + @Knowledge-Curator），增加 Loop Engineering 层（10 相位 + 4 门禁 + 3 硬刹车）。

---

## ✨ 下次使用流程

1. **打开 Trae IDE**
2. **说**："用 Loop Agent 模式开发"（或 `/loop-agent`）
3. **AI 自动**：
   - 加载 loop-agent-system Skill（已注册到 Trae 全局）
   - 读取 `项目进度记录.md`（如不存在则提示初始化）
   - 加载 4 级封装资产
   - 切换到 @Orchestrator 视角
4. **你提供 PRD**
5. **AI 跑全流程**（10 相位 + 4 门禁）
6. **交付**：生产代码 + 完整文档 + 质量报告

---

## 🆘 故障排查

| 问题 | 解决方案 |
|------|----------|
| AI 没识别"Loop Agent 模式"关键词 | 改用 `/loop-agent` 斜杠命令 |
| 黑板文件没自动初始化 | 手动运行 `Loop-Agent启动器.bat` |
| 某个 Agent Profile 加载失败 | 检查 `.trae\agents\*.agent.toml` 文件格式 |
| 门禁不通过 | 查看 `.blackboard\reviews\` 报告 + 通知 @Bug-Defect-Repairer |
| 预算耗尽 | 查看 `项目进度记录.md` 区块二（状态快照） |

---

## 📊 系统就绪度自检

| 检查项 | 状态 |
|--------|------|
| ✅ 主入口规则（loop-agent.md） | 就位 |
| ✅ A2A 协议（5 消息 + Topic 命名） | 就位 |
| ✅ Skill 层（10 个） | 就位 |
| ✅ Agent Profile 层（16 个） | 就位 |
| ✅ Workflow Blueprint（10 相位） | 就位 |
| ✅ Domain Chip（web-feature-chip + Autoloop） | 就位 |
| ✅ 黑板模板（12 区块） | 就位 |
| ✅ Trae 全局 Skill 注册 | 就位 |
| ✅ Windows 启动器 | 就位 |
| ✅ README + INSTALL 文档 | 就位 |

**系统状态**：✅ **完全就绪，可立即使用**

---

**【Loop Agent v1.0 · 4 级封装 · 16 角色 · 10 相位 · 双份存储生效中】**

> 安装者：基于 Agent Loop Engineering 蓝皮书 + 用户项目需求
> 验证方式：在 Trae 中说"用 Loop Agent 模式开发"或输入 `/loop-agent`
