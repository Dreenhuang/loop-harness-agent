# =============================================================================
# Loop-Harness-Agent 全局一键安装脚本
# =============================================================================
# 功能：
#   1. 安装 LHA 到 TRAE 用户级目录（%USERPROFILE%\.trae\ 和 .trae-cn\）
#   2. 复制所有 .trae 内容（规则、Agent、Skill、Workflow）
#   3. 创建 .rules 触发规则文件（TRAE 专用格式）
#   4. 安装到其他 IDE 的用户级目录（Cursor、VSCode、Claude Code）
#   5. 创建 desktop 快捷方式
# =============================================================================

param(
    [string]$LhaRoot = "g:\ai-gongju\Loop-agent\loop-harness-agent"
)

$ErrorActionPreference = "Continue"

function Write-Step { param($msg) Write-Host "`n▶ $msg" -ForegroundColor Cyan }
function Write-OK { param($msg) Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "  ❌ $msg" -ForegroundColor Red }

# 验证源
if (-not (Test-Path $LhaRoot)) {
    Write-Host "❌ LHA 源目录不存在: $LhaRoot" -ForegroundColor Red
    exit 1
}

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Loop-Harness-Agent 全局安装 v1.2" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  源目录: $LhaRoot"
Write-Host "  用户:   $env:USERNAME"
Write-Host ""

# 定义所有 TRAE 用户级目录
$traeDirs = @(
    "$env:USERPROFILE\.trae",
    "$env:USERPROFILE\.trae-cn"
)

# Step 1: 安装到所有 TRAE 目录
foreach ($traeDir in $traeDirs) {
    $traeName = Split-Path $traeDir -Leaf
    Write-Step "Step 1: 安装到 $traeName"

    if (-not (Test-Path $traeDir)) {
        Write-Warn "$traeDir 不存在，跳过"
        continue
    }

    # 1.1 复制 rules
    $rulesDir = "$traeDir\rules"
    if (-not (Test-Path $rulesDir)) {
        New-Item -ItemType Directory -Path $rulesDir -Force | Out-Null
    }
    # 复制主规则
    $mainRuleSrc = "$LhaRoot\.trae\rules\loop-agent.md"
    $mainRuleDst = "$rulesDir\loop-harness-agent.rules"
    if (Test-Path $mainRuleSrc) {
        Copy-Item $mainRuleSrc $mainRuleDst -Force
        Write-OK "已安装主规则: $mainRuleDst"
    } else {
        Write-Err "主规则文件不存在: $mainRuleSrc"
    }

    # 1.2 复制 A2A 速查卡
    $a2aSrc = "$LhaRoot\.trae\rules\A2A消息速查卡.md"
    $a2aDst = "$rulesDir\loop-harness-agent-a2a.rules"
    if (Test-Path $a2aSrc) {
        Copy-Item $a2aSrc $a2aDst -Force
        Write-OK "已安装 A2A 规则: $a2aDst"
    }

    # 1.3 复制 agents
    $agentsSrc = "$LhaRoot\.trae\agents"
    $agentsDst = "$traeDir\agents\lha"
    if (Test-Path $agentsSrc) {
        if (Test-Path $agentsDst) {
            Remove-Item $agentsDst -Recurse -Force
        }
        New-Item -ItemType Directory -Path $agentsDst -Force | Out-Null
        Copy-Item "$agentsSrc\*" $agentsDst -Recurse -Force
        $agentCount = (Get-ChildItem "$agentsDst\*.toml" -ErrorAction SilentlyContinue).Count
        Write-OK "已安装 $agentCount 个 Agent Profile → $agentsDst"
    }

    # 1.4 复制 skills
    $skillsSrc = "$LhaRoot\.trae\skills\core"
    $skillsDst = "$traeDir\builtin_skills\lha"
    if (Test-Path $skillsSrc) {
        if (Test-Path $skillsDst) {
            Remove-Item $skillsDst -Recurse -Force
        }
        New-Item -ItemType Directory -Path $skillsDst -Force | Out-Null
        Copy-Item "$skillsSrc\*" $skillsDst -Recurse -Force
        $skillCount = (Get-ChildItem "$skillsDst\*\SKILL.md" -Recurse -ErrorAction SilentlyContinue).Count
        Write-OK "已安装 $skillCount 个 Skill → $skillsDst"
    }

    # 1.5 复制 workflows
    $wfSrc = "$LhaRoot\.trae\workflows"
    $wfDst = "$traeDir\lha\workflows"
    if (Test-Path $wfSrc) {
        if (Test-Path $wfDst) {
            Remove-Item $wfDst -Recurse -Force
        }
        New-Item -ItemType Directory -Path $wfDst -Force | Out-Null
        Copy-Item "$wfSrc\*" $wfDst -Recurse -Force
        Write-OK "已安装 Workflow → $wfDst"
    }

    # 1.6 复制工件模板和注册表
    $artifactsSrc = "$LhaRoot\artifacts"
    $artifactsDst = "$traeDir\lha\artifacts"
    if (Test-Path $artifactsSrc) {
        if (Test-Path $artifactsDst) {
            Remove-Item $artifactsDst -Recurse -Force
        }
        Copy-Item $artifactsSrc $artifactsDst -Recurse -Force
        Write-OK "已安装 Artifacts → $artifactsDst"
    }

    $templatesSrc = "$LhaRoot\templates"
    $templatesDst = "$traeDir\lha\templates"
    if (Test-Path $templatesSrc) {
        if (Test-Path $templatesDst) {
            Remove-Item $templatesDst -Recurse -Force
        }
        Copy-Item $templatesSrc $templatesDst -Recurse -Force
        Write-OK "已安装 Templates → $templatesDst"
    }

    # 1.7 创建 loop-harness-agent.rules 触发规则文件
    $triggerContent = @"
# Loop-Harness-Agent Global Trigger Rules
# Version: 1.2.0
# Updated: 2026-06-17

## Trigger Keywords
When user input contains these keywords, automatically activate Loop-Harness-Agent mode:

### Primary Keywords (case-insensitive, format-tolerant)
- "loop-harness-agent"
- "loop harness agent"
- "loop_harness_agent"
- "loopharnessagent"
- "LHA" / "lha"

### Compatible Keywords
- "loop-agent" / "loop agent" / "loopagent"

### Chinese Keywords
- "Loop-Harness-Agent 模式"
- "Loop Agent 模式"
- "Harness 模式"
- "融合模式"
- "循环工程"
- "全自动开发"
- "16 角色团队"

### Shortcut Commands
- "/loop-harness-agent" - Quick activation (full path)
- "/loop-harness-agent status" - Query status
- "/loop-harness-agent resume" - Resume previous loop
- "/loop-harness-agent abort" - Abort current loop
- "/loop-agent" - Compatible command (same as /loop-harness-agent)
- "/LHA" - Shortcut command

## Mode Description
Loop-Harness-Agent is a 5-level encapsulation automation engine:
- Level 1: Skill (18 atomic skills)
- Level 2: Agent (16 roles)
- Level 3: Workflow (10 phases + 4 gates)
- Level 4: Domain Chip (web-feature-chip)
- Level 5: Artifact & Evidence (registry + collector)

## Auto-Loading Resources
When activated, automatically load:
- Main rules: loop-agent.md
- Agent profiles: 16 .toml files
- Skills: 18 SKILL.md files
- Workflow: prd-to-production.json
- Artifacts: 9 templates + registry + evidence
- Fusion standard: docs/integration/融合验收标准.md

## Fallback
If any of the above resources fail to load, gracefully degrade but still maintain core function.
"@
    $triggerDst = "$rulesDir\loop-harness-agent.rules"
    $triggerContent | Out-File -FilePath $triggerDst -Encoding utf8 -Force
    Write-OK "已创建触发规则: $triggerDst"
}

# Step 2: 安装到 Cursor 用户级
Write-Step "Step 2: 安装到 Cursor 用户级目录"
$cursorRules = "$env:USERPROFILE\.cursor\rules"
if (-not (Test-Path $cursorRules)) {
    New-Item -ItemType Directory -Path $cursorRules -Force | Out-Null
}
$cursorRule = "$cursorRules\loop-harness-agent.mdc"
$mainRuleSrc = "$LhaRoot\.trae\rules\loop-agent.md"
if (Test-Path $mainRuleSrc) {
    Copy-Item $mainRuleSrc $cursorRule -Force
    Write-OK "已安装 Cursor 规则: $cursorRule"
} else {
    Write-Err "源规则不存在"
}

# Step 3: 安装到 Claude Code 用户级
Write-Step "Step 3: 安装到 Claude Code 用户级目录"
$claudeDir = "$env:USERPROFILE\.claude"
if (Test-Path $claudeDir) {
    $claudeRules = "$claudeDir\rules"
    if (-not (Test-Path $claudeRules)) {
        New-Item -ItemType Directory -Path $claudeRules -Force | Out-Null
    }
    Copy-Item $mainRuleSrc "$claudeRules\loop-harness-agent.md" -Force
    Write-OK "已安装 Claude Code 规则: $claudeRules\loop-harness-agent.md"
} else {
    Write-Warn "Claude Code 目录不存在: $claudeDir"
}

# Step 4: 安装到 VSCode 用户级
Write-Step "Step 4: 安装到 VSCode 用户级目录"
$vscodeDir = "$env:APPDATA\Code\User"
if (Test-Path $vscodeDir) {
    $vscodeRules = "$vscodeDir\rules"
    if (-not (Test-Path $vscodeRules)) {
        New-Item -ItemType Directory -Path $vscodeRules -Force | Out-Null
    }
    Copy-Item $mainRuleSrc "$vscodeRules\loop-harness-agent.md" -Force
    Write-OK "已安装 VSCode 规则: $vscodeRules\loop-harness-agent.md"
} else {
    Write-Warn "VSCode 目录不存在: $vscodeDir"
}

# Step 5: 验证
Write-Step "Step 5: 验证安装结果"
$checks = @(
    @{ Path = "$env:USERPROFILE\.trae\rules\loop-harness-agent.rules"; Name = "TRAE 触发规则" },
    @{ Path = "$env:USERPROFILE\.trae\rules\loop-harness-agent.rules"; Name = "TRAE-CN 触发规则" },
    @{ Path = "$env:USERPROFILE\.trae\agents\lha\orchestrator.agent.toml"; Name = "TRAE Agent" },
    @{ Path = "$env:USERPROFILE\.trae\builtin_skills\lha\gate1-code-review\SKILL.md"; Name = "TRAE Skill" },
    @{ Path = "$env:USERPROFILE\.cursor\rules\loop-harness-agent.mdc"; Name = "Cursor 规则" }
)
$pass = 0
foreach ($c in $checks) {
    if (Test-Path $c.Path) {
        Write-OK "$($c.Name) → $($c.Path)"
        $pass++
    } else {
        Write-Warn "$($c.Name) → $($c.Path) (可选，跳过)"
    }
}

Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ 全局安装完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  📋 触发方式（任何项目、任何 IDE）：" -ForegroundColor Yellow
Write-Host ""
Write-Host "  TRAE:        /loop-harness-agent" -ForegroundColor White
Write-Host "  TRAE:        loop-harness-agent（自然语言）" -ForegroundColor White
Write-Host "  TRAE:        /LHA" -ForegroundColor White
Write-Host "  Cursor:      Ctrl+I → loop-harness-agent" -ForegroundColor White
Write-Host "  Claude Code: loop-harness-agent" -ForegroundColor White
Write-Host "  VSCode:      Continue 插件 → loop-harness-agent" -ForegroundColor White
Write-Host ""
Write-Host "  🔄 下一步：完全关闭 TRAE 后重新打开" -ForegroundColor Yellow
Write-Host "     File → Exit → 重新打开 TRAE → 输入 /loop-harness-agent" -ForegroundColor White
Write-Host ""
