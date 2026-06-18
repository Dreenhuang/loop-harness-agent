@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM Loop Agent · 状态快照脚本
REM 用途：保存当前 Blackboard 完整状态到快照目录
REM 编码：GBK / ANSI
REM ============================================================

title Loop Agent - Snapshot State

echo.
echo ============================================================
echo   Loop Agent - 状态快照 v1.0
echo ============================================================
echo.

set "TARGET_DIR=%CD%"
set "BLACKBOARD_DIR=%TARGET_DIR%\blackboard"
set "SNAPSHOT_BASE=%BLACKBOARD_DIR%\.snapshots"

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value 2^>nul') do set "DATETIME=%%a"
set "TIMESTAMP=%DATETIME:~0,8%_%DATETIME:~8,6%"
set "SNAPSHOT_DIR=%SNAPSHOT_BASE%\%TIMESTAMP%"

REM 1. 检查黑板是否存在
if not exist "%BLACKBOARD_DIR%" (
    echo ❌ Blackboard 不存在，请先运行 init-blackboard.bat
    pause
    exit /b 1
)

REM 2. 创建快照目录
echo [1/4] 创建快照目录：%SNAPSHOT_DIR%
mkdir "%SNAPSHOT_DIR%" 2>nul

REM 3. 全量复制
echo [2/4] 复制黑板完整内容...
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\state.json" "%SNAPSHOT_DIR%\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\a2a" "%SNAPSHOT_DIR%\a2a\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\logs" "%SNAPSHOT_DIR%\logs\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\knowledge_index.json" "%SNAPSHOT_DIR%\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\requirements" "%SNAPSHOT_DIR%\requirements\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\design" "%SNAPSHOT_DIR%\design\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\architecture" "%SNAPSHOT_DIR%\architecture\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\code" "%SNAPSHOT_DIR%\code\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\quality" "%SNAPSHOT_DIR%\quality\" >nul 2>&1
xcopy /E /I /Y /Q "%BLACKBOARD_DIR%\knowledge" "%SNAPSHOT_DIR%\knowledge\" >nul 2>&1

echo       ✅ 黑板内容已复制

REM 4. 生成快照元数据
echo [3/4] 生成快照元数据...

(
echo {
echo   "snapshot_id": "%TIMESTAMP%",
echo   "created_at": "%date% %time%",
echo   "type": "manual",
echo   "trigger": "snapshot-state.bat",
echo   "size_mb": 0,
echo   "files_count": 0
echo }
) > "%SNAPSHOT_DIR%\.snapshot-meta.json"

echo       ✅ 快照元数据已生成

REM 5. 清理旧快照（保留最近 100 个）
echo [4/4] 清理旧快照（保留最近 100 个）...

set "COUNT=0"
for /d %%d in ("%SNAPSHOT_BASE%\*") do set /a COUNT+=1

echo       当前快照数：%COUNT%

REM 注：PowerShell 实现更高效
powershell -Command "$dirs = Get-ChildItem -Path '%SNAPSHOT_BASE%' -Directory | Sort-Object LastWriteTime -Descending; if ($dirs.Count -gt 100) { $dirs[100..($dirs.Count-1)] | Remove-Item -Recurse -Force; Write-Host '       ✅ 已清理多余快照' } else { Write-Host '       ✅ 无需清理' }" 2>nul

echo.
echo ============================================================
echo   ✅ 快照已保存：%SNAPSHOT_DIR%
echo ============================================================
echo.
echo 查看所有快照：
echo   dir "%SNAPSHOT_BASE%"
echo.
pause
