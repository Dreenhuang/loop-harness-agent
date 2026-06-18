# Loop Agent · 跨项目使用指南

> **版本**: v1.2
> **生效日期**: 2026-06-15
> **核心目标**: 在任何新项目中 5 分钟内启动 Loop Agent 模式

## 一、标准启动流程（5 分钟）

### 1.1 最简流程（3 步）

```bash
# Step 1: 进入新项目
cd D:\my-new-project

# Step 2: 一键安装（30 秒）
G:\ai-gongju\Loop-agent\init-loop-agent.bat

# Step 3: 触发 Loop Agent
# 在 Trae IDE 中说："用 Loop Agent 模式开发"
```

### 1.2 完整流程（5 步 + PRD）

```text
【Step 1: 准备】1 分钟
  cd D:\my-new-project

【Step 2: 安装】30 秒
  G:\ai-gongju\Loop-agent\init-loop-agent.bat
  → 自动复制 .trae/ workflows/ config/ mcp/ scripts/
  → 自动创建 blackboard/ 项目进度记录.md

【Step 3: 写 PRD】2 分钟
  编辑 blackboard\input\prd.md
  或直接用对话告诉 AI 你的需求

【Step 4: 触发】10 秒
  /loop-agent
  或 "用 Loop Agent 模式开发"

【Step 5: @Orchestrator 接管】自动
  → 加载 18 Skills + 16 Agents
  → 按 10 相位 + 4 门禁执行
  → 持续监控到完成
```

## 二、典型跨项目场景

### 场景 1：从零开始 Web 项目

```bash
mkdir my-saas && cd my-saas
G:\ai-gongju\Loop-agent\init-loop-agent.bat
# 写 PRD
# 触发："用 Loop Agent 模式开发，做一个 SaaS 后台"
```

### 场景 2：在已有项目加 Loop Agent

```bash
cd D:\existing-react-app
G:\ai-gongju\Loop-agent\init-loop-agent.bat
# 在 README 中追加"本项目使用 Loop Agent 模式"
# 触发："用 Loop Agent 模式重构用户模块"
```

### 场景 3：多项目同时使用

```bash
for dir in project1 project2 project3; do
  cd $dir
  G:\ai-gongju\Loop-agent\init-loop-agent.bat
  cd ..
done
```

### 场景 4：团队成员共享 Loop Agent

```text
A 在主仓库提交 .trae/ workflows/ config/ mcp/ scripts/
B clone 项目后，init-loop-agent.bat 自动可用
C D 同样
→ 全团队使用同一份 Loop Agent 配置
```

## 三、Trae 全局 Skill 模式

### 3.1 全局 Skill 已就位

```text
位置: C:\Users\Administrator\AppData\Roaming\Trae\User\skills\loop-agent-system\SKILL.md
状态: ✅ 已注册
效果: 所有 Trae 项目自动生效
```

### 3.2 在任意项目直接说

```text
"用 Loop Agent 模式开发"
→ Trae 加载全局 Skill
→ 自动读取当前项目的 项目进度记录.md（如有）
→ 自动加载 .trae/ 资产
→ 启动 Loop
```

### 3.3 不需要 .trae/ 也可以用？

**答**: 可以，但功能受限。

| 功能 | 有 .trae/ | 无 .trae/ |
|------|-----------|-----------|
| Loop 触发 | ✅ | ✅ |
| 16 Agent Profile | ✅ | ❌（用默认） |
| 18 Skills | ✅ | ⚠️ 基础 4 个 |
| 4 Workflows | ✅ | ⚠️ 简化版 |
| MCP 工具链 | ✅ | ❌ |
| 黑板模板 | ✅ | ✅ 自动建 |
| 项目类型感知 | ✅ | ⚠️ 默认 web |

**建议**: 跨项目使用仍推荐运行 init-loop-agent.bat 一次。

## 四、跨项目使用的 5 个最佳实践

### 4.1 ✅ 推荐做法

1. **首次进入项目必跑 init 脚本**（30 秒节省 5 小时）
2. **PRD 写到 blackboard/input/ 而不是 docs/**（基底介导）
3. **每次 Loop 完成检查 blackboard/**（状态可追溯）
4. **失败案例记录到 blackboard/failure-cases/**（团队知识）
5. **不修改 Loop Agent 源文件**（通过项目级 .trae/ 覆盖）

### 4.2 ❌ 避免做法

1. ❌ 直接复制 .trae/ 文件到项目（用 init 脚本）
2. ❌ 修改源 Loop Agent 文件（破坏可升级性）
3. ❌ 跨项目共享 decision_log.json（项目隔离）
4. ❌ 在 init 脚本外手动改路径（破坏可移植性）
5. ❌ 跳过 blackboard 初始化（黑板是核心）

## 五、跨项目升级 Loop Agent

### 5.1 一键升级

```bash
# Loop-agent 仓库更新后，在项目内运行
G:\ai-gongju\Loop-agent\init-loop-agent.bat /upgrade
```

### 5.2 手动升级

```text
1. git pull g:\ai-gongju\Loop-agent
2. 在项目目录运行 init-loop-agent.bat
3. 对比 .trae/ 文件变化
4. 合并自定义修改（如有）
```

## 六、故障排查

| 症状 | 原因 | 修复 |
|------|------|------|
| "找不到 loop-agent.md" | init 脚本未运行 | 重跑 init |
| "/loop-agent 命令无响应" | Trae 全局 Skill 未注册 | 重新注册 `loop-agent-system` |
| "黑板格式错误" | 项目进度记录.md 损坏 | 从 blackboard/templates/ 重新复制 |
| "Agent Profile 加载失败" | .trae/agents/ 不完整 | 重新跑 init |
| "路径冲突" | 项目已有同名目录 | 手动合并 |

## 七、卸载 Loop Agent

```bash
# 删除 Loop Agent 在项目中产生的所有文件
rmdir /S /Q .trae
rmdir /S /Q workflows
rmdir /S /Q config
rmdir /S /Q mcp
rmdir /S /Q scripts
rmdir /S /Q blackboard
del /Q trae.toml
del /Q 项目进度记录.md
```

**注意**: Trae 全局 Skill 不删，保留供下次使用。

---

**【跨项目使用指南 v1.2 · 5 分钟启动 · 一键安装器 · 95% 可移植性】**
