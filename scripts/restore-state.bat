@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM Loop Agent · 状态恢复脚本
REM 用途：从指定快照恢复 Blackboard
REM 用法：restore-state.bat [snapshot_id]
REM 编码：GBK / ANSI
REM ============================================================

title Loop Agent - Restore State

echo.
echo ============================================================
echo   Loop Agent - 状态恢复 v1.0
echo ============================================================
echo.

set "TARGET_DIR=%CD%"
set "BLACKBOARD_DIR=%TARGET_DIR%\blackboard"
set "SNAPSHOT_BASE=%BLACKBOARD_DIR%\.snapshots"

REM 1. 列出所有可用快照
if not exist "%SNAPSHOT_BASE%" (
    echo ❌ 快照目录不存在
    pause
    exit /b 1
)

echo [可用快照]
echo.

set "IDX=0"
for /d %%d in ("%SNAPSHOT_BASE%\*") do (
    set /a IDX+=1
    echo   [!IDX!] %%~nxd
)

echo.
echo ============================================================
echo.

REM 2. 获取快照 ID
set "SNAPSHOT_ID=%~1"

if "%SNAPSHOT_ID%"=="" (
    set /p "SNAPSHOT_ID=请输入要恢复的快照 ID（或 Ctrl+C 取消）: "
)

set "SNAPSHOT_DIR=%SNAPSHOT_BASE%\%SNAPSHOT_ID%"

if not exist "%SNAPSHOT_DIR%" (
    echo ❌ 快照不存在：%SNAPSHOT_ID%
    pause
    exit /b 1
)

REM 3. 备份当前状态
echo [1/4] 备份当前状态...
call "%TARGET_DIR%\scripts\snapshot-state.bat" 2>nul
echo       ✅ 当前状态已备份

REM 4. 清空黑板
echo [2/4] 清空黑板（保留 input 目录）...
if exist "%BLACKBOARD_DIR%\state.json" del /Q "%BLACKBOARD_DIR%\state.json"
if exist "%BLACKBOARD_DIR%\a2a" rd /S /Q "%BLACKBOARD_DIR%\a2a"
if exist "%BLACKBOARD_DIR%\logs" rd /S /Q "%BLACKBOARD_DIR%\logs"
if exist "%BLACKBOARD_DIR%\requirements" rd /S /Q "%BLACKBOARD_DIR%\requirements"
if exist "%BLACKBOARD_DIR%\design" rd /S /Q "%BLACKBOARD_DIR%\design"
if exist "%BLACKBOARD_DIR%\architecture" rd /S /Q "%BLACKBOARD_DIR%\architecture"
if exist "%BLACKBOARD_DIR%\code" rd /S /Q "%BLACKBOARD_DIR%\code"
if exist "%BLACKBOARD_DIR%\quality" rd /S /Q "%BLACKBOARD_DIR%\quality"
if exist "%BLACKBOARD_DIR%\knowledge" rd /S /Q "%BLACKBOARD_DIR%\knowledge"

echo       ✅ 黑板已清空（保留 input/ 和 .snapshots/）

REM 5. 恢复快照
echo [3/4] 恢复快照...
xcopy /E /I /Y /Q "%SNAPSHOT_DIR%\*" "%BLACKBOARD_DIR%\" >nul 2>&1
echo       ✅ 快照内容已恢复

REM 6. 验证
echo [4/4] 验证恢复...
if exist "%BLACKBOARD_DIR%\state.json" (
    echo       ✅ state.json 已恢复
) else (
    echo       ❌ state.json 恢复失败
)

echo.
echo ============================================================
echo   ✅ 状态恢复完成：%SNAPSHOT_ID%
echo ============================================================
echo.
echo 接下来请：
echo   1. 检查 项目进度记录.md 内容
echo   2. 在 Trae 中触发：/loop-agent resume
echo.
pause
