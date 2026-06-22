# 兼容 PowerShell 5.1 / 7+ 跨版本；推荐 7.2+ 享受最佳体验
<#
.SYNOPSIS
  Phase B · Worktree 真实模式端到端验证脚本

.DESCRIPTION
  验证 Loop Agent v1.2 worktree 隔离模式的关键行为：
  1. worker 真实创建并清理 worktree
  2. git worktree 本身提供文件隔离（主分支不受污染）
  3. 并发 3 agent 互不干扰
  4. Loud Failure 三连 + 降级
  5. .worktrees/ 被 .gitignore 忽略
  6. max_concurrent_worktrees=7 配置正确
  7. dry-run 模式不创建真实 worktree

  执行：
    powershell -ExecutionPolicy Bypass -File scripts/verify-worktree-e2e.ps1
#>

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
$ProjectRoot = Split-Path -Parent $PSScriptRoot | Resolve-Path | Select-Object -ExpandProperty Path
$GitExe = "C:\Program Files\Git\bin\git.exe"
$BunExe = (Get-Command bun.exe -ErrorAction SilentlyContinue)?.Source
if (-not $BunExe) {
    $BunExe = Join-Path $env:USERPROFILE ".bun\bin\bun.exe"
}
if (-not (Test-Path $BunExe)) {
    $BunExe = "bun"
}

$TasksDir = Join-Path $ProjectRoot "blackboard" "tasks"
$WorktreesDir = Join-Path $ProjectRoot ".worktrees"
$EvidenceDir = Join-Path $ProjectRoot "blackboard" "evidence"
$WorkerScript = Join-Path $ProjectRoot "loop-agent-engine" "agent-worker.ts"

New-Item -ItemType Directory -Force -Path $TasksDir | Out-Null
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
function Run-Git {
    param([string]$Arguments, [string]$Cwd = $ProjectRoot)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $GitExe
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $Cwd
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    $out = $proc.StandardOutput.ReadToEnd()
    $err = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    return @{
        ExitCode = $proc.ExitCode
        StdOut = $out
        StdErr = $err
    }
}

function Get-WorktreeList {
    $r = Run-Git "worktree list --porcelain"
    return $r.StdOut
}

function WorktreeExists {
    param([string]$Name)
    $list = Get-WorktreeList
    return $list -match [regex]::Escape(".worktrees\$Name") -or $list -match [regex]::Escape("/$Name")
}

function New-TestTask {
    param([string]$TaskId, [string]$AgentType)
    $task = @{
        id = $TaskId
        agentType = $AgentType
        phase = "DEVELOPMENT"
        status = "RUNNING"
        worktree = $true
        outputPath = "output.md"
        inputPaths = @()
        acceptanceCriteria = @{}
    }
    $task | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $TasksDir "$TaskId.json") -Encoding UTF8
}

function Remove-TestTask {
    param([string]$TaskId)
    $p = Join-Path $TasksDir "$TaskId.json"
    if (Test-Path $p) { Remove-Item $p -Force }
}

function Invoke-Worker {
    param([string]$TaskId, [hashtable]$ExtraEnv = @{})
    foreach ($k in $ExtraEnv.Keys) {
        Set-Item -Path "env:$k" -Value $ExtraEnv[$k]
    }
    try {
        & $BunExe run $WorkerScript $TaskId 2>&1
    } finally {
        foreach ($k in $ExtraEnv.Keys) {
            Remove-Item -Path "env:$k" -ErrorAction SilentlyContinue
        }
    }
}

function Invoke-WorkerAsync {
    param([string]$TaskId, [hashtable]$ExtraEnv = @{})
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $BunExe
    $psi.Arguments = "run `"$WorkerScript`" $TaskId"
    $psi.WorkingDirectory = $ProjectRoot
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    foreach ($k in $ExtraEnv.Keys) {
        $psi.Environment[$k] = $ExtraEnv[$k]
    }
    $proc = [System.Diagnostics.Process]::Start($psi)
    return $proc
}

function Wait-ForWorktree {
    param([string]$Name, [int]$TimeoutMs = 8000)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt $TimeoutMs) {
        if (WorktreeExists $Name) { return $true }
        Start-Sleep -Milliseconds 100
    }
    return $false
}

function Wait-ForProcess {
    param([System.Diagnostics.Process]$Proc, [int]$TimeoutMs = 5000)
    if ($null -eq $Proc) { return $true }
    return $Proc.WaitForExit($TimeoutMs)
}

function Cleanup-AllWorktrees {
    # 1) git worktree remove --force 所有 .worktrees/ 下的
    $listText = (Get-WorktreeList).Trim()
    $lines = $listText -split "`n"
    foreach ($line in $lines) {
        if ($line.StartsWith("worktree ")) {
            $wtPath = $line.Substring(9).Trim()
            if ($wtPath -like "*.worktrees*" -and (Test-Path $wtPath)) {
                Run-Git "worktree remove --force `"$wtPath`"" | Out-Null
            }
        }
    }
    # 2) prune（清理 .git/worktrees 引用）
    Run-Git "worktree prune" | Out-Null
    # 3) 物理删除 .worktrees 目录残留
    if (Test-Path $WorktreesDir) {
        Get-ChildItem $WorktreesDir -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    # 4) 删除所有 wt-* 测试分支（包括上次失败残留的）
    $branchesResult = (Run-Git "branch --list `"wt-*`"" -Cwd $ProjectRoot).StdOut
    Write-Host "  [Cleanup] 检测到 wt-* 分支列表:`n$branchesResult"
    foreach ($br in ($branchesResult -split "`n")) {
        $name = $br.Trim() -replace '^\*\s*', '' -replace '^\s+', ''
        if ($name -and $name -ne '' -and $name -like "wt-*") {
            $delResult = Run-Git "branch -D `"$name`"" -Cwd $ProjectRoot
            Write-Host "  [Cleanup] 删除分支 $name : exit=$($delResult.ExitCode)"
        }
    }
    # 5) prune 一次
    Run-Git "worktree prune" | Out-Null
}

# ---------------------------------------------------------------------------
# 场景执行器
# ---------------------------------------------------------------------------
$Results = [ordered]@{}

function Write-ScenarioHeader {
    param([int]$N, [string]$Title)
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "[SCENARIO-$N] $Title" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

# ---------------------------------------------------------------------------
# 场景 1：单任务真实 worktree 创建与清理
# ---------------------------------------------------------------------------
$taskId = "test-e2e-single"
Write-ScenarioHeader 1 "单任务真实 worktree 创建与清理"
try {
    Cleanup-AllWorktrees
    Remove-TestTask $taskId
    New-TestTask $taskId "backend"

    $proc = Invoke-WorkerAsync $taskId @{}  # 真实模式：不设置 DRY_RUN
    $found = Wait-ForWorktree "wt-backend-$taskId" 3000
    if (-not $found) {
        throw "worker 未在 3 秒内创建 worktree wt-backend-$taskId"
    }
    Write-Host "  worktree wt-backend-$taskId 已出现 ✓"

    # 在 worktree 内写隔离测试文件（利用 sleep 窗口）
    $wtPath = Join-Path $WorktreesDir "wt-backend-$taskId"
    "isolation-test" | Set-Content -Path (Join-Path $wtPath "isolation-test.txt") -Encoding UTF8
    Write-Host "  已在 worktree 内写入 isolation-test.txt ✓"

    # 等待 worker 完成
    if (-not (Wait-ForProcess $proc 5000)) {
        $proc.Kill()
        throw "worker 未在 5 秒内结束"
    }
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    Write-Host "  worker stdout:`n$stdout"
    if ($stderr) { Write-Host "  worker stderr:`n$stderr" -ForegroundColor Yellow }

    # 等待 worker 进程完全退出（worktree remove 的 git 子进程可能还在执行）
    Start-Sleep -Milliseconds 1500

    # 验证清理
    if (WorktreeExists "wt-backend-$taskId") {
        # 二次等待 + prune
        Start-Sleep -Milliseconds 1500
        Run-Git "worktree prune" | Out-Null
        if (WorktreeExists "wt-backend-$taskId") {
            throw "worktree 未被清理"
        }
    }
    Write-Host "  worktree 已清理 ✓"

    # 验证任务状态
    $task = Get-Content (Join-Path $TasksDir "$taskId.json") | ConvertFrom-Json
    if ($task.status -ne "DONE") {
        throw "任务状态不是 DONE: $($task.status)"
    }
    Write-Host "  任务状态=DONE ✓"

    $Results["SCENARIO-1"] = "PASS"
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $Results["SCENARIO-1"] = "FAIL: $_"
} finally {
    Cleanup-AllWorktrees
    Remove-TestTask $taskId
}

# ---------------------------------------------------------------------------
# 场景 2：worktree 文件隔离（主分支不受污染）
# ---------------------------------------------------------------------------
Write-ScenarioHeader 2 "worktree 文件隔离验证"
$wtIso = "wt-isolation-test"
try {
    Cleanup-AllWorktrees
    $r = Run-Git "worktree add -b $wtIso .worktrees\$wtIso HEAD"
    if ($r.ExitCode -ne 0) { throw "worktree add 失败: $($r.StdErr)" }

    $wtPath = Join-Path $WorktreesDir $wtIso
    "only-in-worktree" | Set-Content -Path (Join-Path $wtPath "isolation-test.txt") -Encoding UTF8

    if (-not (Test-Path (Join-Path $wtPath "isolation-test.txt"))) {
        throw "worktree 内文件未写入"
    }
    Write-Host "  worktree 内 isolation-test.txt 存在 ✓"

    if (Test-Path (Join-Path $ProjectRoot "isolation-test.txt")) {
        throw "主分支被污染：isolation-test.txt 出现在项目根"
    }
    Write-Host "  主分支未出现 isolation-test.txt ✓"

    $Results["SCENARIO-2"] = "PASS"
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $Results["SCENARIO-2"] = "FAIL: $_"
} finally {
    Run-Git "worktree remove --force .worktrees\$wtIso" | Out-Null
    if (Test-Path (Join-Path $ProjectRoot "isolation-test.txt")) {
        Remove-Item (Join-Path $ProjectRoot "isolation-test.txt") -Force
    }
    Cleanup-AllWorktrees
}

# ---------------------------------------------------------------------------
# 场景 3：并发 3 agent 无互踩
# ---------------------------------------------------------------------------
Write-ScenarioHeader 3 "并发 3 agent 无互踩"
$agents = @(
    @{ id = "test-e2e-backend"; type = "backend" },
    @{ id = "test-e2e-frontend"; type = "frontend" },
    @{ id = "test-e2e-bugfix"; type = "bug_defect_repairer" }
)
try {
    Cleanup-AllWorktrees
    $procs = @()
    foreach ($a in $agents) {
        Remove-TestTask $a.id
        New-TestTask $a.id $a.type
        $procs += Invoke-WorkerAsync $a.id @{}
    }

    # 等待所有 worktree 出现
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $allFound = $false
    while ($sw.ElapsedMilliseconds -lt 12000 -and -not $allFound) {
        $allFound = $true
        foreach ($a in $agents) {
            if (-not (WorktreeExists "wt-$($a.type)-$($a.id)")) {
                $allFound = $false
                break
            }
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $allFound) { throw "并发 worktree 未在 5 秒内全部出现" }
    Write-Host "  3 个 worktree 同时存在 ✓"

    # 验证互不污染：每个 worktree 只写自己的 marker
    foreach ($a in $agents) {
        $wtPath = Join-Path $WorktreesDir "wt-$($a.type)-$($a.id)"
        $marker = "concurrent-$($a.type).txt"
        "marker-for-$($a.type)" | Set-Content -Path (Join-Path $wtPath $marker) -Encoding UTF8
    }
    foreach ($a in $agents) {
        $wtPath = Join-Path $WorktreesDir "wt-$($a.type)-$($a.id)"
        $ownMarker = "concurrent-$($a.type).txt"
        if (-not (Test-Path (Join-Path $wtPath $ownMarker))) {
            throw "$($a.type) worktree 缺少自己的 marker"
        }
        foreach ($other in $agents) {
            if ($other.type -eq $a.type) { continue }
            $otherMarker = "concurrent-$($other.type).txt"
            if (Test-Path (Join-Path $wtPath $otherMarker)) {
                throw "$($a.type) worktree 被 $($other.type) 污染"
            }
        }
    }
    Write-Host "  3 个 worktree 无交叉污染 ✓"

    # 等待所有 worker 完成
    foreach ($proc in $procs) {
        if (-not (Wait-ForProcess $proc 8000)) {
            $proc.Kill()
            throw "worker 未在 8 秒内结束"
        }
    }

    # 等 worker 进程完全退出（worktree remove 的 git 子进程可能还在执行）
    Start-Sleep -Milliseconds 2000

    # 验证清理
    $notCleaned = @()
    foreach ($a in $agents) {
        if (WorktreeExists "wt-$($a.type)-$($a.id)") {
            $notCleaned += $a.type
        }
    }
    if ($notCleaned.Count -gt 0) {
        # 二次等待 + prune 重试
        Start-Sleep -Milliseconds 2000
        Run-Git "worktree prune" | Out-Null
        $stillNotCleaned = @()
        foreach ($a in $agents) {
            if (WorktreeExists "wt-$($a.type)-$($a.id)") {
                $stillNotCleaned += $a.type
            }
        }
        if ($stillNotCleaned.Count -gt 0) {
            throw "$($stillNotCleaned -join ',') worktree 未被清理"
        }
    }
    Write-Host "  3 个 worktree 均已清理 ✓"

    $Results["SCENARIO-3"] = "PASS"
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $Results["SCENARIO-3"] = "FAIL: $_"
} finally {
    foreach ($a in $agents) { Remove-TestTask $a.id }
    Cleanup-AllWorktrees
}

# ---------------------------------------------------------------------------
# 场景 4：Loud Failure 回退
# ---------------------------------------------------------------------------
Write-ScenarioHeader 4 "Loud Failure 回退验证"
$taskId = "test-e2e-loudfail"
try {
    Cleanup-AllWorktrees
    Remove-TestTask $taskId
    New-TestTask $taskId "backend"

    # 预创建同名目录，让 git worktree add 失败
    $wtPath = Join-Path $WorktreesDir "wt-backend-$taskId"
    New-Item -ItemType Directory -Force -Path $wtPath | Out-Null
    "block" | Set-Content -Path (Join-Path $wtPath "block.txt") -Encoding UTF8

    $output = Invoke-Worker $taskId @{}
    $outStr = $output -join "`n"
    Write-Host "  worker output:`n$outStr"

    if ($outStr -notmatch "\[Worker\]\[LOUD FAILURE\]") {
        throw "未输出 LOUD FAILURE 标记"
    }
    Write-Host "  LOUD FAILURE 三连输出 ✓"

    # 验证任务仍写回 DONE（降级到 non-worktree 模式继续）
    $task = Get-Content (Join-Path $TasksDir "$taskId.json") | ConvertFrom-Json
    if ($task.status -ne "DONE") {
        throw "降级后任务未写回 DONE: $($task.status)"
    }
    Write-Host "  降级后任务仍完成 ✓"

    $Results["SCENARIO-4"] = "PASS"
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $Results["SCENARIO-4"] = "FAIL: $_"
} finally {
    Remove-TestTask $taskId
    Cleanup-AllWorktrees
}

# ---------------------------------------------------------------------------
# 场景 5：.gitignore 验证
# ---------------------------------------------------------------------------
Write-ScenarioHeader 5 ".gitignore 验证"
try {
    Cleanup-AllWorktrees
    # 创建一个临时 worktree
    $r = Run-Git "worktree add -b wt-gitignore-test .worktrees\wt-gitignore-test HEAD"
    if ($r.ExitCode -ne 0) { throw "worktree add 失败: $($r.StdErr)" }

    # 在 worktree 内创建文件
    "ignore-me" | Set-Content -Path (Join-Path $WorktreesDir "wt-gitignore-test" "ignored.txt") -Encoding UTF8

    $status = (Run-Git "status --short").StdOut
    if ($status -match "\.worktrees") {
        throw ".worktrees 出现在 git status 中，说明未被 .gitignore 忽略"
    }
    Write-Host "  .worktrees/ 未出现在 git status ✓"

    $Results["SCENARIO-5"] = "PASS"
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $Results["SCENARIO-5"] = "FAIL: $_"
} finally {
    Run-Git "worktree remove --force .worktrees\wt-gitignore-test" | Out-Null
    Cleanup-AllWorktrees
}

# ---------------------------------------------------------------------------
# 场景 6：max_concurrent_worktrees=7
# ---------------------------------------------------------------------------
Write-ScenarioHeader 6 "max_concurrent_worktrees=7 配置验证"
try {
    $cfgPath = Join-Path $ProjectRoot "mcp" "git.mcp.json"
    $cfg = Get-Content $cfgPath | ConvertFrom-Json -Depth 10
    $max = $cfg.worktree_strategy.max_concurrent_worktrees
    if ($max -ne 7) {
        throw "max_concurrent_worktrees = $max，期望 7"
    }
    Write-Host "  max_concurrent_worktrees = 7 ✓"

    $Results["SCENARIO-6"] = "PASS"
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $Results["SCENARIO-6"] = "FAIL: $_"
}

# ---------------------------------------------------------------------------
# 场景 7：dry-run 模式无副作用
# ---------------------------------------------------------------------------
Write-ScenarioHeader 7 "dry-run 模式无副作用"
$taskId = "test-e2e-dryrun"
try {
    Cleanup-AllWorktrees
    Remove-TestTask $taskId
    New-TestTask $taskId "backend"

    $before = Get-WorktreeList
    $output = Invoke-Worker $taskId @{ "LOOP_AGENT_WORKTREE_DRY_RUN" = "1" }
    $outStr = $output -join "`n"
    Write-Host "  worker output:`n$outStr"

    if ($outStr -notmatch "\[Worker\]\[DRY-RUN\] would: git worktree add") {
        throw "dry-run 未打印计划命令"
    }
    Write-Host "  dry-run 输出计划命令 ✓"

    $after = Get-WorktreeList
    if ($before -ne $after) {
        throw "dry-run 模式真实创建了 worktree"
    }
    Write-Host "  dry-run 未改变 git worktree list ✓"

    # 任务仍完成
    $task = Get-Content (Join-Path $TasksDir "$taskId.json") | ConvertFrom-Json
    if ($task.status -ne "DONE") {
        throw "dry-run 任务未写回 DONE"
    }
    Write-Host "  dry-run 任务完成 ✓"

    $Results["SCENARIO-7"] = "PASS"
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $Results["SCENARIO-7"] = "FAIL: $_"
} finally {
    Remove-TestTask $taskId
    Cleanup-AllWorktrees
}

# ---------------------------------------------------------------------------
# 最终清理与汇总
# ---------------------------------------------------------------------------
Cleanup-AllWorktrees

$finalList = Get-WorktreeList
Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "最终 git worktree 状态：" -ForegroundColor Green
Write-Host $finalList
Write-Host "============================================================" -ForegroundColor Green

$passCount = ($Results.Values | Where-Object { $_ -eq "PASS" }).Count
$failCount = $Results.Count - $passCount

Write-Host "`n汇总结果：" -ForegroundColor Green
foreach ($k in $Results.Keys) {
    $v = $Results[$k]
    $color = if ($v -eq "PASS") { "Green" } else { "Red" }
    Write-Host "  $k : $v" -ForegroundColor $color
}
Write-Host "`n总计: $passCount / $($Results.Count) 通过" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

# 输出交付报告
$report = @"
# Phase B 交付报告 · Worktree 端到端验证

> **Agent**: @DevOps-Deployment-Engineer
> **Phase**: Phase B
> **日期**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> **总结果**: $passCount / $($Results.Count) 通过

## 一、脚本交付
- 路径: scripts/verify-worktree-e2e.ps1
- 场景数: $($Results.Count)

## 二、执行结果

| # | 场景 | 结果 |
|---|------|------|
"@
foreach ($k in $Results.Keys) {
    $num = $k.Split("-")[1]
    $title = switch ($num) {
        "1" { "单任务真实 worktree 创建与清理" }
        "2" { "worktree 文件隔离验证" }
        "3" { "并发 3 agent 无互踩" }
        "4" { "Loud Failure 回退验证" }
        "5" { ".gitignore 验证" }
        "6" { "max_concurrent_worktrees=7 配置验证" }
        "7" { "dry-run 模式无副作用" }
        default { "场景 $num" }
    }
    $report += "| $num | $title | $($Results[$k]) |`n"
}

$report += @"

## 三、最终 git worktree 状态

```text
$finalList
```

## 四、Phase C 交接确认
- $(if ($failCount -eq 0) { "✅ 全部通过，可进入 Phase C（@Final-Reviewer Gate 4 一票否决项验证）" } else { "❌ 存在失败场景，需先回 Phase A 修复后再重跑 Phase B" })
"@

$reportPath = Join-Path $EvidenceDir "phase-b-delivery.md"
$report | Set-Content -Path $reportPath -Encoding UTF8
Write-Host "`n报告已写入: $reportPath" -ForegroundColor Cyan

exit $(if ($failCount -eq 0) { 0 } else { 1 })
