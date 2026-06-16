# TRAE 找不到 /loop-harness-agent 解决方案

> **常见 5 大原因 + 完整修复方案**

---

## 🚨 最常见原因（90% 情况）

**问题**：TRAE 找不到 `/loop-harness-agent` 命令

**原因**：规则文件不在 TRAE 识别的标准位置

---

## 一、立即修复（1 分钟搞定）

### 步骤 1：在 TRAE 终端中 cd 到你的新项目

```
cd D:\你的新项目路径
```

### 步骤 2：执行一键修复脚本

```powershell
powershell -ExecutionPolicy Bypass -File "g:\ai-gongju\Loop-agent\loop-harness-agent\scripts\diagnose-lha.ps1"
```

### 步骤 3：重启 TRAE

1. **完全关闭** TRAE（File → Exit）
2. 重新打开项目
3. 等待 5-10 秒
4. 在 AI 对话框输入 `/loop-harness-agent`

---

## 二、5 大原因详细诊断

### 原因 1：`.trae` 目录不在项目根目录（最常见）

**症状**：TRAE 完全没有响应 `/loop-harness-agent`

**验证**：
```powershell
# 在项目根目录执行
Test-Path .\.trae\rules\loop-agent.md
# 必须返回 True
```

**修复**：
```powershell
# 一键脚本
powershell -ExecutionPolicy Bypass -File "g:\ai-gongju\Loop-agent\loop-harness-agent\scripts\setup-lha.ps1" -ProjectDir "$PWD" -Mode symlink
```

### 原因 2：软链接失效

**症状**：`.trae` 在但文件访问不到

**验证**：
```powershell
Get-Item .\.trae | Format-List Name, LinkType, Target
```

**修复**：
```powershell
# 删除失效链接
Remove-Item .\.trae -Force

# 重新创建
New-Item -ItemType Junction -Path .\.trae -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae"
```

### 原因 3：TRAE 没重新加载规则

**症状**：文件存在但命令不识别

**修复**：
1. File → Exit（完全退出，不是关窗口）
2. 重新打开项目
3. 等待 5-10 秒（TRAE 扫描规则文件）
4. 测试触发

### 原因 4：触发位置错误

**错误位置**：
- ❌ PowerShell 终端
- ❌ VSCode 终端
- ❌ 任何 IDE 终端

**正确位置**：
- ✅ TRAE AI 对话框（顶部输入区，发送消息的位置）

### 原因 5：TRAE 规则作用域不对

**TRAE 规则识别优先级**：
1. 项目级 `.trae/rules/` ✅ 最高优先级
2. 用户级 `~/.trae/rules/` ⚠️ 备用
3. 全局规则（系统提供）

**修复**：确保使用项目级 `.trae/rules/loop-agent.md`

---

## 三、手动检查清单

请在项目根目录逐项检查：

```powershell
# ✅ 1. .trae 目录存在
Test-Path .\.trae

# ✅ 2. rules 子目录存在
Test-Path .\.trae\rules

# ✅ 3. loop-agent.md 存在
Test-Path .\.trae\rules\loop-agent.md

# ✅ 4. agents 目录存在
Test-Path .\.trae\agents

# ✅ 5. 至少 16 个 Agent Profile
(Get-ChildItem .\.trae\agents\*.toml).Count -ge 16

# ✅ 6. 至少 18 个 Skill
(Get-ChildItem .\.trae\skills\core\*\SKILL.md -Recurse).Count -ge 18

# ✅ 7. workflows 目录存在
Test-Path .\.trae\workflows

# ✅ 8. prd-to-production.json 存在
Test-Path .\.trae\workflows\prd-to-production.json
```

如果任何一项是 False，按一键脚本修复。

---

## 四、TRAE 内部检查

### 4.1：查看 TRAE 是否识别了规则

在 TRAE AI 对话框输入：

```
你识别到 .trae 目录了吗？请列出当前项目的所有规则文件。
```

预期响应：
```
是的，我识别到以下规则文件：
- .trae/rules/loop-agent.md
- .trae/rules/A2A消息速查卡.md
- .trae/agents/orchestrator.agent.toml
...
```

如果没识别，按步骤 3 重启。

### 4.2：测试触发

在 AI 对话框输入：

```
测试 trigger: /loop-harness-agent
```

或自然语言：
```
loop-harness-agent 是什么模式？
```

### 4.3：查看 TRAE 日志

如果还是不工作：

1. TRAE → Help → Toggle Developer Tools
2. Console 标签
3. 查找错误信息（搜索 "loop-agent" 或 "rules"）
4. 把错误信息反馈给开发者

---

## 五、终极解决方案

如果所有方法都不行，**最简单粗暴的方式**：

### 5.1：完全复制到项目（不推荐，但最稳）

```powershell
# 复制整个 LHA 目录到项目
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae" "D:\你的项目\"
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\templates" "D:\你的项目\"
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\artifacts" "D:\你的项目\"
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\domain-chips" "D:\你的项目\"
```

**优点**：100% 能用，不依赖软链接  
**缺点**：占空间（~2MB）

### 5.2：放到 TRAE 用户级目录

如果项目级不工作，可以放到全局：

```powershell
# TRAE 用户级目录
$userTraeDir = "$env:USERPROFILE\.trae"

# 创建（如果不存在）
New-Item -ItemType Directory -Path "$userTraeDir\rules" -Force

# 复制规则
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae\rules\*" "$userTraeDir\rules\" -Recurse -Force

# 复制 Agent
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae\agents" "$userTraeDir\agents" -Recurse -Force

# 复制 Skill
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae\skills" "$userTraeDir\skills" -Recurse -Force

# 复制 Workflow
Copy-Item "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae\workflows" "$userTraeDir\workflows" -Recurse -Force

Write-Host "✅ LHA 已安装到用户级目录"
Write-Host "请重启 TRAE 后测试"
```

**优点**：所有项目自动可用  
**缺点**：每个项目都加载，资源占用稍高

---

## 六、常见问题 FAQ

### Q1：执行脚本后 TRAE 还是找不到

**A**：
1. 确认你重启了 TRAE（File → Exit，不是关窗口）
2. 确认 `.trae` 在项目根目录，不在子目录
3. 在 TRAE 对话框输入 `loop-harness-agent`（无斜杠）

### Q2：规则文件太大怎么办？

**A**：TRAE 默认会读取 `.trae/rules/` 下所有 .md 文件。如果太大，移除非必要规则：

```powershell
# 仅保留核心规则
Remove-Item .\.trae\rules\*.md -Exclude "loop-agent.md"
```

### Q3：能否团队共享一个 LHA？

**A**：可以。用 Git 仓库或共享文件夹：

```bash
# 团队 Git
git clone https://github.com/Dreenhuang/loop-harness-agent.git
cd loop-harness-agent
# 软链接到团队项目
```

### Q4：能否同时使用多个 LHA 版本？

**A**：可以。修改软链接目标即可：

```powershell
# v1.2 → v1.3
New-Item -ItemType Junction -Path .\.trae -Target "g:\lha-v1.3\.trae" -Force
```

### Q5：TRAE 启动慢了很多？

**A**：软链接指向的 LHA 包含 18 个 Skill + 16 个 Agent + JSON 等。TRAE 启动会扫描所有。可移除不必要内容：

```powershell
# 最小化：仅保留核心
Remove-Item .\.trae\skills\core\* -Recurse -Force -Exclude "gate1-code-review","gate2-performance","gate3-testing","gate4-final"
```

---

## 七、获取帮助

如果以上都不能解决：

1. **运行诊断脚本**（自动检查并修复）：
   ```powershell
   powershell -ExecutionPolicy Bypass -File "g:\ai-gongju\Loop-agent\loop-harness-agent\scripts\diagnose-lha.ps1"
   ```

2. **查看 GitHub Issues**：
   https://github.com/Dreenhuang/loop-harness-agent/issues

3. **提交新 Issue** 时附上：
   - TRAE 版本
   - 项目路径
   - `dir .\.trae /s` 输出
   - TRAE Console 错误信息

---

**【Loop-Harness-Agent v1.2 · TRAE 集成就绪】**
