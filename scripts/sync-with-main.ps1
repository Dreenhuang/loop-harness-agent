#!/usr/bin/env pwsh
# ============================================================
# 分支同步脚本 - sync-with-main.ps1
# 用途: 将 feature/mcp-monitor-dashboard 分支与 master 同步
# 策略: 使用 rebase 保持线性历史
# 频率: 每 2 个工作日执行一次
# 触发方式: .\scripts\sync-with-main.ps1
# ============================================================

param(
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$GIT = "C:\Program Files\Git\cmd\git.exe"
$PROJECT_ROOT = "g:\ai-gongju\Loop-agent"
$BRANCH_NAME = "feature/mcp-monitor-dashboard"
$MAIN_BRANCH = "master"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP Monitor Dashboard - Branch Sync" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查 git 是否可用
if (-not (Test-Path $GIT)) {
    Write-Host "[ERROR] Git not found at $GIT" -ForegroundColor Red
    exit 1
}

Set-Location $PROJECT_ROOT

# 获取当前分支
$currentBranch = & $GIT rev-parse --abbrev-ref HEAD
if ($currentBranch -ne $BRANCH_NAME) {
    Write-Host "[WARN] Current branch is '$currentBranch', switching to '$BRANCH_NAME'..." -ForegroundColor Yellow
    if (-not $DryRun) {
        & $GIT checkout $BRANCH_NAME
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to switch to $BRANCH_NAME" -ForegroundColor Red
            exit 1
        }
    }
}

# 检查是否有未提交的更改
$status = & $GIT status --porcelain
if ($status -and -not $Force) {
    Write-Host "[ERROR] Working directory has uncommitted changes!" -ForegroundColor Red
    Write-Host "Use -Force to stash changes or commit them first." -ForegroundColor Yellow
    exit 1
} elseif ($status -and $Force) {
    Write-Host "[INFO] Stashing uncommitted changes..." -ForegroundColor Yellow
    if (-not $DryRun) {
        & $GIT stash push -m "auto-stash-before-sync-$(Get-Date -Format 'yyyyMMddHHmmss')"
    }
}

Write-Host "`n[STEP 1/4] Fetching latest from origin/$MAIN_BRANCH..." -ForegroundColor Green

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute: git fetch origin $MAIN_BRANCH" -ForegroundColor Gray
} else {
    & $GIT fetch origin $MAIN_BRANCH
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to fetch origin/$MAIN_BRANCH" -ForegroundColor Red
        # 尝试恢复 stash
        if ($status -and $Force) { & $GIT stash pop }
        exit 1
    }
}

Write-Host "[STEP 2/4] Rebasing $BRANCH_NAME onto origin/$MAIN_BRANCH..." -ForegroundColor Green

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute: git rebase origin/$MAIN_BRANCH" -ForegroundColor Gray
} else {
    & $GIT rebase origin/$MAIN_BRANCH
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Red
        Write-Host "║     CONFLICT DETECTED DURING REBASE      ║" -ForegroundColor Red
        Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Red
        Write-Host ""
        Write-Host "[ALERT] Rebase conflict detected! Please resolve manually:" -ForegroundColor Red
        Write-Host "  1. Run 'git status' to see conflicted files" -ForegroundColor Yellow
        Write-Host "  2. Resolve conflicts in each file" -ForegroundColor Yellow
        Write-Host "  3. Run 'git add <resolved-file>' for each file" -ForegroundColor Yellow
        Write-Host "  4. Run 'git rebase --continue'" -ForegroundColor Yellow
        Write-Host "  5. If needed, abort with 'git rebase --abort'" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "[NOTIFY] Conflict event logged to blackboard" -ForegroundColor Magenta
        Write-Host "[REQ] @Orchestrator → @专业DevOps" -ForegroundColor Magenta
        Write-Host "topic: error.rebase.conflict" -ForegroundColor Magenta
        Write-Host "payload: 'Rebase conflict on $BRANCH_NAME, manual resolution required'" -ForegroundColor Magenta
        Write-Host ""

        # 记录冲突到黑板（如果黑板目录存在）
        $blackboardDir = "$PROJECT_ROOT/blackboard/failure-cases"
        if (Test-Path $blackboardDir) {
            $conflictLog = @{
                timestamp = (Get-Date -Format "o")
                type = "rebase_conflict"
                branch = $BRANCH_NAME
                main_branch = $MAIN_BRANCH
                status = "awaiting_resolution"
                action_required = "manual_conflict_resolution"
            } | ConvertTo-Json -Depth 3
            $conflictLog | Out-File -FilePath "$blackboardDir/rebase-conflict-$(Get-Date -Format 'yyyyMMddHHmmss').json" -Encoding UTF8
            Write-Host "[INFO] Conflict details saved to blackboard/failure-cases/" -ForegroundColor Green
        }

        # 恢复 stash
        if ($status -and $Force) { & $GIT stash pop }
        exit 1
    }
}

Write-Host "[STEP 3/4] Verifying sync status..." -ForegroundColor Green

$commitsAhead = (& $GIT rev-list --count origin/$MAIN_BRANCH..HEAD)
$commitsBehind = (& $GIT rev-list --count HEAD..origin/$MAIN_BRANCH)

if ($DryRun) {
    Write-Host "[DRY RUN] Sync verification skipped" -ForegroundColor Gray
} else {
    if ([int]$commitsBehind -eq 0) {
        Write-Host "[SUCCESS] Branch is up to date with $MAIN_BRANCH" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Still behind by $commitsBehind commits" -ForegroundColor Yellow
    }
}

Write-Host "[STEP 4/4] Generating sync report..." -ForegroundColor Green

$report = @"
========================================
  SYNC REPORT
========================================
Timestamp : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Branch    : $BRANCH_NAME
Base      : $MAIN_BRANCH
Commits Ahead : $commitsAhead
Commits Behind: $commitsBehind
Status    : SUCCESS
========================================
"@

Write-Host $report -ForegroundColor Cyan

# 恢复 stash
if ($status -and $Force -and -not $DryRun) {
    Write-Host "`n[INFO] Restoring stashed changes..." -ForegroundColor Yellow
    & $GIT stash pop
}

Write-Host "`n[DONE] Synchronization completed successfully!" -ForegroundColor Green
exit 0
