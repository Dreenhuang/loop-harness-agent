# =============================================================================
# Loop-Harness-Agent 跨项目跨 IDE 一键集成脚本
# =============================================================================
# 用法：
#   .\setup-lha.ps1 -ProjectDir "D:\my-project" -LhaRoot "g:\ai-gongju\Loop-agent\loop-harness-agent"
#   .\setup-lha.ps1 -ProjectDir "D:\my-project" -Mode "minimal"  # 仅复制规则
# =============================================================================

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,

    [string]$LhaRoot = "g:\ai-gongju\Loop-agent\loop-harness-agent",

    [ValidateSet("full", "minimal", "symlink")]
    [string]$Mode = "symlink",

    [switch]$IncludeMcp
)

$ErrorActionPreference = "Stop"

# 颜色输出
function Write-Step { param($msg) Write-Host "`n▶ $msg" -ForegroundColor Cyan }
function Write-OK { param($msg) Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "  ❌ $msg" -ForegroundColor Red }

# 验证源目录
Write-Step "验证 LHA 源目录"
if (-not (Test-Path $LhaRoot)) {
    Write-Err "LHA 源目录不存在: $LhaRoot"
    exit 1
}
Write-OK "源目录: $LhaRoot"

# 验证目标项目
if (-not (Test-Path $ProjectDir)) {
    Write-Warn "目标项目不存在，创建: $ProjectDir"
    New-Item -ItemType Directory -Path $ProjectDir -Force | Out-Null
}
Write-OK "目标项目: $ProjectDir"

# 切换到项目目录
Push-Location $ProjectDir

try {
    # Step 1: 集成 .trae 目录
    Write-Step "Step 1: 集成 .trae 目录（规则+Agent+Skill+Workflow）"
    $traeTarget = ".\.trae"
    if (Test-Path $traeTarget) {
        Write-Warn ".trae 已存在，跳过"
    } else {
        switch ($Mode) {
            "full" {
                Copy-Item "$LhaRoot\.trae" $traeTarget -Recurse -Force
                Write-OK "已复制 .trae"
            }
            "minimal" {
                New-Item -ItemType Directory -Path "$traeTarget\rules" -Force | Out-Null
                Copy-Item "$LhaRoot\.trae\rules\*" "$traeTarget\rules\" -Recurse -Force
                Write-OK "已复制 .trae\rules（最小化）"
            }
            "symlink" {
                if (-not (Test-Path $traeTarget)) {
                    New-Item -ItemType Junction -Path $traeTarget -Target "$LhaRoot\.trae" | Out-Null
                    Write-OK "已创建符号链接 .trae → $LhaRoot\.trae"
                }
            }
        }
    }

    # Step 2: 集成 templates
    Write-Step "Step 2: 集成 templates（9 个工件模板）"
    if ($Mode -ne "minimal") {
        $templatesTarget = ".\templates"
        if (Test-Path $templatesTarget) {
            Write-Warn "templates 已存在，跳过"
        } else {
            switch ($Mode) {
                "full" {
                    Copy-Item "$LhaRoot\templates" $templatesTarget -Recurse -Force
                    Write-OK "已复制 templates"
                }
                "symlink" {
                    New-Item -ItemType Junction -Path $templatesTarget -Target "$LhaRoot\templates" | Out-Null
                    Write-OK "已创建符号链接 templates"
                }
            }
        }
    }

    # Step 3: 集成 artifacts
    Write-Step "Step 3: 集成 artifacts（工件注册表 + 证据收集器）"
    if ($Mode -ne "minimal") {
        $artifactsTarget = ".\artifacts"
        if (Test-Path $artifactsTarget) {
            Write-Warn "artifacts 已存在，跳过"
        } else {
            switch ($Mode) {
                "full" {
                    Copy-Item "$LhaRoot\artifacts" $artifactsTarget -Recurse -Force
                    Write-OK "已复制 artifacts"
                }
                "symlink" {
                    New-Item -ItemType Junction -Path $artifactsTarget -Target "$LhaRoot\artifacts" | Out-Null
                    Write-OK "已创建符号链接 artifacts"
                }
            }
        }
    }

    # Step 4: 集成 domain-chips
    Write-Step "Step 4: 集成 domain-chips（领域芯片）"
    if ($Mode -ne "minimal") {
        $chipsTarget = ".\domain-chips"
        if (Test-Path $chipsTarget) {
            Write-Warn "domain-chips 已存在，跳过"
        } else {
            switch ($Mode) {
                "full" {
                    Copy-Item "$LhaRoot\domain-chips" $chipsTarget -Recurse -Force
                    Write-OK "已复制 domain-chips"
                }
                "symlink" {
                    New-Item -ItemType Junction -Path $chipsTarget -Target "$LhaRoot\domain-chips" | Out-Null
                    Write-OK "已创建符号链接 domain-chips"
                }
            }
        }
    }

    # Step 5: 集成 MCP Server（可选）
    if ($IncludeMcp) {
        Write-Step "Step 5: 集成 MCP Server"
        $mcpTarget = ".\loop-agent-mcp"
        if (Test-Path $mcpTarget) {
            Write-Warn "loop-agent-mcp 已存在，跳过"
        } else {
            Copy-Item "$LhaRoot\loop-agent-mcp" $mcpTarget -Recurse -Force
            Write-OK "已复制 loop-agent-mcp"
            Write-Warn "记得运行: cd loop-agent-mcp && bun install"
        }
    }

    # Step 6: 创建 IDE 规则软链接
    Write-Step "Step 6: 创建 IDE 规则软链接"

    # Cursor
    $cursorLink = ".\.cursorrules"
    if (Test-Path $cursorLink) {
        Write-Warn ".cursorrules 已存在"
    } else {
        $cursorTarget = ".\.trae\rules\loop-agent.md"
        if (Test-Path $cursorTarget) {
            New-Item -ItemType SymbolicLink -Path $cursorLink -Target $cursorTarget | Out-Null
            Write-OK "已创建 .cursorrules → $cursorTarget"
        }
    }

    # Windsurf
    $windsurfLink = ".\.windsurfrules"
    if (Test-Path $windsurfLink) {
        Write-Warn ".windsurfrules 已存在"
    } else {
        $windsurfTarget = ".\.trae\rules\loop-agent.md"
        if (Test-Path $windsurfTarget) {
            New-Item -ItemType SymbolicLink -Path $windsurfLink -Target $windsurfTarget | Out-Null
            Write-OK "已创建 .windsurfrules → $windsurfTarget"
        }
    }

    # VSCode
    $vscodeLinkDir = ".\.vscode\rules"
    if (-not (Test-Path $vscodeLinkDir)) {
        New-Item -ItemType Directory -Path $vscodeLinkDir -Force | Out-Null
    }
    $vscodeLink = ".\.vscode\rules\lha.md"
    if (Test-Path $vscodeLink) {
        Write-Warn ".vscode/rules/lha.md 已存在"
    } else {
        $vscodeTarget = "..\..\.trae\rules\loop-agent.md"
        if (Test-Path $vscodeTarget) {
            New-Item -ItemType SymbolicLink -Path $vscodeLink -Target $vscodeTarget | Out-Null
            Write-OK "已创建 .vscode/rules/lha.md → $vscodeTarget"
        }
    }

    # JetBrains
    $ideaDir = ".\.idea"
    if (-not (Test-Path $ideaDir)) {
        New-Item -ItemType Directory -Path $ideaDir -Force | Out-Null
    }
    $ideaFile = ".\.idea\ai-assistant-prompt.xml"
    if (Test-Path $ideaFile) {
        Write-Warn ".idea/ai-assistant-prompt.xml 已存在"
    } else {
        @"
<?xml version="1.0" encoding="UTF-8"?>
<project-prompt>
  <rule source="`$PROJECT_DIR`$/.trae/rules/loop-agent.md" name="Loop-Harness-Agent" />
  <description>Loop-Harness-Agent v1.2 - 5级封装 + 16角色 + 18 Skill</description>
</project-prompt>
"@ | Out-File -FilePath $ideaFile -Encoding utf8
        Write-OK "已创建 .idea/ai-assistant-prompt.xml"
    }

    # Step 7: 复制 CLAUDE.md
    Write-Step "Step 7: 复制 CLAUDE.md（Claude Code 规则）"
    $claudeTarget = ".\CLAUDE.md"
    if (Test-Path $claudeTarget) {
        Write-Warn "CLAUDE.md 已存在，跳过"
    } else {
        Copy-Item "$LhaRoot\CLAUDE.md" $claudeTarget -Force
        Write-OK "已复制 CLAUDE.md"
    }

    # Step 8: 验证
    Write-Step "Step 8: 验证集成结果"
    $checks = @(
        @{ Path = ".\.trae\rules\loop-agent.md"; Name = "LHA 主规则" },
        @{ Path = ".\.trae\agents"; Name = "Agent Profiles" },
        @{ Path = ".\.trae\skills\core"; Name = "Skill 库" },
        @{ Path = ".\.cursorrules"; Name = "Cursor 规则" },
        @{ Path = ".\.vscode\rules\lha.md"; Name = "VSCode 规则" },
        @{ Path = ".\.idea\ai-assistant-prompt.xml"; Name = "JetBrains 规则" }
    )
    if ($Mode -ne "minimal") {
        $checks += @(
            @{ Path = ".\templates"; Name = "工件模板" },
            @{ Path = ".\artifacts"; Name = "工件注册表" },
            @{ Path = ".\domain-chips"; Name = "领域芯片" }
        )
    }
    $pass = 0
    foreach ($c in $checks) {
        if (Test-Path $c.Path) {
            Write-OK "$($c.Name) → $($c.Path)"
            $pass++
        } else {
            Write-Err "$($c.Name) → $($c.Path) 缺失"
        }
    }
    Write-Host "`n通过: $pass / $($checks.Count)" -ForegroundColor $(if ($pass -eq $checks.Count) { "Green" } else { "Yellow" })

    # 输出使用说明
    Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  集成完成！触发方式：" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Cursor:   `"/loop-harness-agent`" 或自然语言 `"LHA`""
    Write-Host "  VSCode:   Continue / Cline 中输入 `"/loop-harness-agent`""
    Write-Host "  Windsurf: `"/loop-harness-agent`" 或自然语言"
    Write-Host "  JetBrains: AI Assistant 中输入 `"/loop-harness-agent`""
    Write-Host "  Trae:    `"/loop-harness-agent`" 或 `"/loop-agent`""
    Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Cyan
}
finally {
    Pop-Location
}
