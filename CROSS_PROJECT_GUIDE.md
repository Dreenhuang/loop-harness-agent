# 跨项目跨 IDE 使用指南

> **Loop-Harness-Agent v1.2 多场景适配方案**

---

## 一、3 大使用场景

| 场景 | 适用人群 | 推荐方式 |
|------|----------|----------|
| **本地其他项目** | 已有项目想用 LHA | 复制或软链接 `.trae` |
| **其他 IDE 集成** | 用 VSCode/Cursor/JetBrains | IDE 规则文件软链接 |
| **跨电脑同步** | 多设备开发 | Git 拉取或云盘同步 |

---

## 二、场景 A：本地其他项目使用

### A1：复制方式（最简单）

```bash
# 在目标项目根目录
cp -r "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae" "./.trae"
cp -r "g:\ai-gongju\Loop-agent\loop-harness-agent\templates" "./templates"
cp -r "g:\ai-gongju\Loop-agent\loop-harness-agent\artifacts" "./artifacts"
cp -r "g:\ai-gongju\Loop-agent\loop-harness-agent\domain-chips" "./domain-chips"
cp "g:\ai-gongju\Loop-agent\loop-harness-agent\CLAUDE.md" "./CLAUDE.md"
```

**优点**：项目自包含，团队成员无需额外配置  
**缺点**：占空间（约 2MB），更新需手动同步

### A2：符号链接方式（推荐，省空间）

```powershell
# PowerShell 方式（不需要管理员）
New-Item -ItemType Junction -Path "D:\my-project\.trae" -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae"
New-Item -ItemType Junction -Path "D:\my-project\templates" -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\templates"
New-Item -ItemType Junction -Path "D:\my-project\artifacts" -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\artifacts"
New-Item -ItemType Junction -Path "D:\my-project\domain-chips" -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\domain-chips"
```

**优点**：一处更新，所有项目生效；不占空间  
**缺点**：依赖源目录存在；跨盘符需用 Junction 而非 SymbolicLink

### A3：一键集成脚本（最省心）

```powershell
# 在 loop-harness-agent 目录中
cd g:\ai-gongju\Loop-agent\loop-harness-agent
powershell -ExecutionPolicy Bypass -File scripts\setup-lha.ps1 -ProjectDir "D:\my-project" -Mode symlink
```

参数说明：
- `-Mode full`：完全复制（占空间但独立）
- `-Mode symlink`：符号链接（推荐）
- `-Mode minimal`：仅复制规则
- `-IncludeMcp`：额外集成 MCP Server

---

## 三、场景 B：其他 IDE 集成

### B1：Cursor IDE

```bash
# 软链接方式
New-Item -ItemType SymbolicLink -Path "D:\my-project\.cursorrules" -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae\rules\loop-agent.md"
```

**触发**：`Ctrl+I` → 输入 `loop-harness-agent` 或 `LHA`

### B2：VSCode + Continue / Cline / Cody

创建 `.vscode/rules/lha.md`（内容来自 `.trae/rules/loop-agent.md`）：

```powershell
# 创建目录
New-Item -ItemType Directory -Path "D:\my-project\.vscode\rules" -Force

# 软链接（需要管理员或同盘符）
New-Item -ItemType SymbolicLink -Path "D:\my-project\.vscode\rules\lha.md" -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae\rules\loop-agent.md"
```

**配置 Continue（`.continue/config.json`）**：

```json
{
  "rules": [
    {
      "name": "Loop-Harness-Agent",
      "rule": ".vscode/rules/lha.md"
    }
  ]
}
```

**触发**：`Ctrl+L` → 输入 `loop-harness-agent`

### B3：JetBrains（IntelliJ IDEA / WebStorm / PyCharm）

创建 `.idea/ai-assistant-prompt.xml`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project-prompt>
  <rule source="$PROJECT_DIR$/.trae/rules/loop-agent.md" name="Loop-Harness-Agent" />
  <description>Loop-Harness-Agent v1.2</description>
</project-prompt>
```

**触发**：AI Assistant → 输入 `loop-harness-agent`

### B4：Windsurf（Codeium）

```powershell
New-Item -ItemType SymbolicLink -Path "D:\my-project\.windsurfrules" -Target "g:\ai-gongju\Loop-agent\loop-harness-agent\.trae\rules\loop-agent.md"
```

**触发**：直接说 `loop-harness-agent`

### B5：通用 IDE 规则对照表

| IDE | 规则文件位置 | 触发方式 |
|-----|--------------|----------|
| Trae | `.trae/rules/loop-agent.md` | `/loop-harness-agent` |
| Cursor | `.cursorrules` | `Ctrl+I` |
| VSCode + Continue | `.vscode/rules/lha.md` | `Ctrl+L` |
| VSCode + Cline | `.clinerules` | `Ctrl+Shift+P` → Cline |
| JetBrains | `.idea/ai-assistant-prompt.xml` | AI Assistant |
| Windsurf | `.windsurfrules` | 自然语言 |
| Claude Code | `CLAUDE.md` | 自然语言 |
| Aider | `CONVENTIONS.md` | `/run` |

---

## 四、场景 C：跨电脑同步

### C1：Git 仓库同步（推荐）

每台电脑：
```bash
git clone https://github.com/Dreenhuang/loop-harness-agent.git
# 或更新
cd loop-harness-agent && git pull
```

### C2：U盘/移动硬盘

```powershell
# 源电脑
Compress-Archive -Path "g:\ai-gongju\Loop-agent\loop-harness-agent" -DestinationPath "D:\share\lha-v1.2.zip"

# 目标电脑
Expand-Archive -Path "E:\share\lha-v1.2.zip" -DestinationPath "D:\tools\"
```

### C3：云盘同步（OneDrive / iCloud / 坚果云）

```powershell
# 把 loop-harness-agent 移到云盘
Move-Item "g:\ai-gongju\Loop-agent\loop-harness-agent" "C:\Users\Administrator\OneDrive\lha"

# 任何项目软链接到云盘目录
New-Item -ItemType Junction -Path "D:\my-project\.trae" -Target "C:\Users\Administrator\OneDrive\lha\.trae"
```

**优点**：自动同步多设备  
**缺点**：依赖云盘可用性

### C4：局域网共享

```powershell
# 源电脑共享
net share lha="g:\ai-gongju\Loop-agent\loop-harness-agent" /grant:everyone,read

# 目标电脑映射
net use Z: \\<源电脑IP>\lha

# 软链接
New-Item -ItemType Junction -Path "D:\my-project\.trae" -Target "Z:\.trae"
```

---

## 五、典型配置示例

### 示例 1：VSCode + Continue 启动 LHA

**项目结构**：
```
D:\my-todo-app\
├── .vscode/
│   └── rules/lha.md      → 软链接到 LHA 主规则
├── .trae/                 → 软链接到 LHA 完整目录
├── src/
└── package.json
```

**操作**：
1. VSCode 打开 `D:\my-todo-app`
2. `Ctrl+L` 打开 Continue
3. 输入 `loop-harness-agent`
4. 看到："🚀 Loop-Harness-Agent v1.2 已激活"
5. 提供 PRD 开始开发

### 示例 2：Cursor 启动 LHA

```
D:\ecommerce-site\
├── .cursorrules           → 软链接
├── .trae/                 → 软链接
└── src/
```

**操作**：
1. Cursor 打开项目
2. `Ctrl+I`
3. 输入 `用 loop-harness-agent 开发电商网站`

### 示例 3：IntelliJ IDEA 启动 LHA

```
D:\spring-boot-app\
├── .idea/
│   └── ai-assistant-prompt.xml
├── .trae/                 → 软链接
└── src/main/java/
```

**操作**：
1. IDEA 打开项目
2. AI Assistant → New Chat
3. 输入 `loop-harness-agent`

---

## 六、权限问题处理

### 软链接失败（跨盘符）

**错误**：`New-Item : Cannot create symbolic link...`

**原因**：Windows 跨盘符符号链接需要管理员权限或开发者模式

**解决方案**：

```powershell
# 方案 1：使用 Junction（无需管理员）
New-Item -ItemType Junction -Path "D:\my-project\.trae" -Target "G:\lha\.trae"

# 方案 2：开启开发者模式
# 设置 → 更新和安全 → 开发者模式 → 开

# 方案 3：使用复制代替软链接
Copy-Item "G:\lha\.trae" "D:\my-project\.trae" -Recurse
```

### 软链接循环引用

**症状**：删除源文件后软链接失效

**解决方案**：
```powershell
# 查看软链接目标
Get-Item "D:\my-project\.trae" | Select-Object Target

# 重新指向正确位置
New-Item -ItemType Junction -Path "D:\my-project\.trae" -Target "G:\lha\.trae" -Force
```

---

## 七、最佳实践

### 1. 团队协作

- ✅ 团队统一在项目根目录的 `.trae/`（提交到 Git）
- ❌ 不要用软链接到个人电脑路径

### 2. 个人多项目

- ✅ 用 `setup-lha.ps1 -Mode symlink` 一键集成
- ✅ LHA 主仓库单独放，定期 `git pull` 更新

### 3. 跨电脑开发

- ✅ 主力机用 Git 克隆
- ✅ 临时电脑用云盘或 U 盘

### 4. IDE 选择

- **Cursor 用户**：推荐用 `.cursorrules`（最成熟）
- **VSCode 用户**：推荐 Continue 插件 + `.vscode/rules/lha.md`
- **JetBrains 用户**：用 AI Assistant + `.idea/ai-assistant-prompt.xml`
- **Trae IDE 用户**：原生支持 `/loop-harness-agent`（最完整）

---

## 八、跨平台说明

### Windows（当前）

```powershell
New-Item -ItemType Junction -Path "D:\project\.trae" -Target "G:\lha\.trae"
```

### macOS / Linux

```bash
ln -s /path/to/lha/.trae /path/to/project/.trae
```

### 跨平台兼容脚本

```bash
# scripts/setup-lha.sh
#!/bin/bash
PROJECT_DIR=$1
LHA_ROOT=${2:-"$HOME/lha"}

[ -z "$PROJECT_DIR" ] && { echo "用法: $0 <project-dir> [lha-root]"; exit 1; }

cd "$PROJECT_DIR" || exit 1

[ ! -L .trae ] && ln -s "$LHA_ROOT/.trae" .trae
[ ! -L templates ] && ln -s "$LHA_ROOT/templates" .templates
[ ! -L artifacts ] && ln -s "$LHA_ROOT/artifacts" .artifacts

[ ! -L .cursorrules ] && ln -s ".trae/rules/loop-agent.md" .cursorrules
[ ! -L .windsurfrules ] && ln -s ".trae/rules/loop-agent.md" .windsurfrules
[ ! -L .vscode/rules/lha.md ] && {
  mkdir -p .vscode/rules
  ln -s "../../.trae/rules/loop-agent.md" .vscode/rules/lha.md
}

echo "✅ 集成完成"
```

---

**【Loop-Harness-Agent v1.2 · 全场景适配就绪】**
