# =============================================================================
# Loop-Harness-Agent 诊断+修复脚本
# =============================================================================
# 用法：在项目根目录执行
#   powershell -ExecutionPolicy Bypass -File diagnose-lha.ps1
#   或带参数指定项目
#   powershell -ExecutionPolicy Bypass -File diagnose-lha.ps1 -ProjectDir "D:\my-project"
# =============================================================================

param(
    [string]$ProjectDir = $PWD,
    [string]$LhaRoot = "g:\ai-gongju\Loop-agent\loop-harness-agent"
)

$ErrorActionPreference = "Continue"

function Write-Step { param($msg) Write-Host "`n▶ $msg" -ForegroundColor Cyan }
function Write-OK { param($msg) Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "  ❌ $msg" -ForegroundColor Red }
function Write-Fix { param($msg) Write-Host "  🔧 $msg" -ForegroundColor Magenta }

$fixesApplied = @()

Push-Location $ProjectDir

try {
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Loop-Harness-Agent 诊断+修复工具 v1.2" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  项目目录: $ProjectDir"
    Write-Host "  LHA 源:   $LhaRoot"

    # 诊断 1: LHA 源是否存在
    Write-Step "诊断 1/8: LHA 源目录"
    if (Test-Path $LhaRoot) {
        Write-OK "LHA 源目录存在"
    } else {
        Write-Err "LHA 源目录不存在: $LhaRoot"
        Write-Fix "请先运行: git clone https://github.com/Dreenhuang/loop-harness-agent.git $LhaRoot"
        exit 1
    }

    # 诊断 2: 项目 .trae 目录
    Write-Step "诊断 2/8: 项目 .trae 目录"
    if (Test-Path .\.trae) {
        $trae = Get-Item .\.trae
        if ($trae.LinkType -eq "Junction" -or $trae.LinkType -eq "SymbolicLink") {
            Write-Warn ".trae 是软链接 → $($trae.Target)"
            if (Test-Path $trae.Target) {
                Write-OK "链接目标有效"
            } else {
                Write-Err "链接目标不存在: $($trae.Target)"
                Write-Fix "重新创建软链接"
                Remove-Item .\.trae -Force -Recurse
                New-Item -ItemType Junction -Path .\.trae -Target $LhaRoot\.trae | Out-Null
                $fixesApplied += "重建 .trae 软链接"
                Write-OK "已修复"
            }
        } else {
            Write-OK ".trae 是真实目录"
        }
    } else {
        Write-Err ".trae 目录不存在"
        Write-Fix "创建 .trae 软链接"
        New-Item -ItemType Junction -Path .\.trae -Target $LhaRoot\.trae | Out-Null
        $fixesApplied += "创建 .trae 软链接"
        Write-OK "已修复"
    }

    # 诊断 3: 主规则文件
    Write-Step "诊断 3/8: 主规则文件"
    $mainRule = ".\.trae\rules\loop-agent.md"
    if (Test-Path $mainRule) {
        $content = Get-Content $mainRule -Head 3
        if ($content -match "Loop-Harness-Agent") {
            Write-OK "规则文件内容正确"
        } else {
            Write-Warn "规则文件存在但内容可能不对"
            Write-Host "  当前内容前 3 行："
            $content | ForEach-Object { Write-Host "    $_" }
        }
    } else {
        Write-Err "主规则文件不存在: $mainRule"
    }

    # 诊断 4: Agent Profile
    Write-Step "诊断 4/8: Agent Profile"
    $agents = Get-ChildItem ".\.trae\agents\*.agent.toml" -ErrorAction SilentlyContinue
    if ($agents) {
        Write-OK "发现 $($agents.Count) 个 Agent Profile"
    } else {
        Write-Err "Agent Profile 缺失"
        Write-Fix "检查 .trae\agents 目录"
    }

    # 诊断 5: Skill 库
    Write-Step "诊断 5/8: Skill 库"
    $skills = Get-ChildItem ".\.trae\skills\core\*\SKILL.md" -Recurse -ErrorAction SilentlyContinue
    if ($skills) {
        Write-OK "发现 $($skills.Count) 个 Skill"
    } else {
        Write-Err "Skill 库缺失"
    }

    # 诊断 6: templates
    Write-Step "诊断 6/8: 工件模板"
    $templates = Get-ChildItem ".\templates\*.md" -ErrorAction SilentlyContinue
    if ($templates.Count -ge 9) {
        Write-OK "工件模板 $($templates.Count) 个"
    } else {
        if ($templates.Count -gt 0) {
            Write-Warn "工件模板只有 $($templates.Count) 个（应有 9 个）"
        } else {
            Write-Err "工件模板缺失"
            Write-Fix "创建 templates 软链接"
            if (Test-Path "$LhaRoot\templates") {
                if (Test-Path .\templates) { Remove-Item .\templates -Force -Recurse }
                New-Item -ItemType Junction -Path .\templates -Target "$LhaRoot\templates" | Out-Null
                $fixesApplied += "创建 templates 软链接"
                Write-OK "已修复"
            }
        }
    }

    # 诊断 7: artifacts
    Write-Step "诊断 7/8: 工件注册表 + 证据收集器"
    if ((Test-Path ".\artifacts\registry") -and (Test-Path ".\artifacts\evidence")) {
        Write-OK "artifacts 完整"
    } else {
        Write-Err "artifacts 目录缺失"
        Write-Fix "创建 artifacts 软链接"
        if (Test-Path "$LhaRoot\artifacts") {
            if (Test-Path .\artifacts) { Remove-Item .\artifacts -Force -Recurse }
            New-Item -ItemType Junction -Path .\artifacts -Target "$LhaRoot\artifacts" | Out-Null
            $fixesApplied += "创建 artifacts 软链接"
            Write-OK "已修复"
        }
    }

    # 诊断 8: 检查 .trae 在 git 中是否被忽略
    Write-Step "诊断 8/8: Git 忽略检查"
    if (Test-Path .\.gitignore) {
        $gitignore = Get-Content .\.gitignore
        $traeIgnored = $gitignore | Where-Object { $_ -match "^\.trae" -or $_ -match "/\.trae" }
        if ($traeIgnored) {
            Write-Warn ".trae 在 .gitignore 中: $($traeIgnored -join ', ')"
            Write-Fix "TRAE 工作正常，但不应提交到 Git"
        } else {
            Write-OK ".trae 未被 gitignore"
        }
    } else {
        Write-OK "项目无 .gitignore"
    }

    # 输出结果
    Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  诊断完成" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

    if ($fixesApplied.Count -gt 0) {
        Write-Host "`n  🔧 已自动修复：" -ForegroundColor Magenta
        $fixesApplied | ForEach-Object { Write-Host "     - $_" }
    } else {
        Write-Host "`n  ✅ 未发现需要修复的问题" -ForegroundColor Green
    }

    Write-Host "`n  下一步操作：" -ForegroundColor Yellow
    Write-Host "  1. 完全关闭 TRAE IDE（File → Exit）"
    Write-Host "  2. 重新打开项目"
    Write-Host "  3. 等待 5-10 秒（TRAE 扫描 .trae 目录）"
    Write-Host "  4. 在 AI 对话框输入: /loop-harness-agent"
    Write-Host "  5. 如果还是不行，尝试: loop-harness-agent（无斜杠）"
    Write-Host "  6. 或自然语言: 用 Loop-Harness-Agent 模式开发"
    Write-Host ""
}
finally {
    Pop-Location
}
