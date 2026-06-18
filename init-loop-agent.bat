@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM Loop Agent v1.2 · 一键安装器
REM ============================================================
REM 用途: 把 Loop Agent 系统安装到任意新项目
REM 用法: init-loop-agent.bat
REM 兼容: Windows 10+ / PowerShell 5+
REM ============================================================

title Loop Agent Installer v1.2

echo.
echo ============================================================
echo   Loop Agent v1.2 · 一键安装器
echo   "Stop being the thing in the loop."
echo ============================================================
echo.

REM 1. 检查当前目录
set "TARGET_DIR=%CD%"
set "SOURCE_DIR=%~dp0"
if "%SOURCE_DIR:~-1%"=="\" set "SOURCE_DIR=%SOURCE_DIR:~0,-1%"

echo [INFO] 源目录: %SOURCE_DIR%
echo [INFO] 目标目录: %TARGET_DIR%
echo.

REM 2. 检查是否在 Loop-agent 源目录运行
if /I "%TARGET_DIR%"=="%SOURCE_DIR%" (
    echo [ERROR] 不能在 Loop-agent 源目录运行本脚本
    echo [HINT] 请先 cd 到你的新项目目录
    pause
    exit /b 1
)

REM 3. 检查必要文件
if not exist "%SOURCE_DIR%\.trae\rules\loop-agent.md" (
    echo [ERROR] 源目录缺少 .trae/rules/loop-agent.md
    echo [HINT] 请确认脚本位于 Loop-agent 仓库根目录
    pause
    exit /b 1
)

echo [STEP 1/8] 复制 .trae/ 配置目录...
if not exist "%TARGET_DIR%\.trae" mkdir "%TARGET_DIR%\.trae"
xcopy /E /I /Y /Q "%SOURCE_DIR%\.trae\rules" "%TARGET_DIR%\.trae\rules" >nul 2>&1
xcopy /E /I /Y /Q "%SOURCE_DIR%\.trae\commands" "%TARGET_DIR%\.trae\commands" >nul 2>&1
xcopy /E /I /Y /Q "%SOURCE_DIR%\.trae\skills" "%TARGET_DIR%\.trae\skills" >nul 2>&1
xcopy /E /I /Y /Q "%SOURCE_DIR%\.trae\agents" "%TARGET_DIR%\.trae\agents" >nul 2>&1
xcopy /E /I /Y /Q "%SOURCE_DIR%\.trae\workflows" "%TARGET_DIR%\.trae\workflows" >nul 2>&1
echo   [OK] .trae/ 已复制

echo [STEP 2/8] 复制 workflows/ 工作流...
if not exist "%TARGET_DIR%\workflows" mkdir "%TARGET_DIR%\workflows"
xcopy /E /I /Y /Q "%SOURCE_DIR%\workflows" "%TARGET_DIR%\workflows" >nul 2>&1
echo   [OK] workflows/ 已复制

echo [STEP 3/8] 复制 config/ 配置...
if not exist "%TARGET_DIR%\config" mkdir "%TARGET_DIR%\config"
xcopy /E /I /Y /Q "%SOURCE_DIR%\config" "%TARGET_DIR%\config" >nul 2>&1
echo   [OK] config/ 已复制

echo [STEP 4/8] 复制 mcp/ 工具链...
if not exist "%TARGET_DIR%\mcp" mkdir "%TARGET_DIR%\mcp"
xcopy /E /I /Y /Q "%SOURCE_DIR%\mcp" "%TARGET_DIR%\mcp" >nul 2>&1
echo   [OK] mcp/ 已复制

echo [STEP 5/8] 复制 scripts/ 脚本...
if not exist "%TARGET_DIR%\scripts" mkdir "%TARGET_DIR%\scripts"
xcopy /E /I /Y /Q "%SOURCE_DIR%\scripts" "%TARGET_DIR%\scripts" >nul 2>&1
echo   [OK] scripts/ 已复制

echo [STEP 6/8] 复制 trae.toml + docs/...
if exist "%SOURCE_DIR%\trae.toml" (
    copy /Y "%SOURCE_DIR%\trae.toml" "%TARGET_DIR%\trae.toml" >nul 2>&1
    echo   [OK] trae.toml 已复制
)
if not exist "%TARGET_DIR%\docs" mkdir "%TARGET_DIR%\docs"
xcopy /E /I /Y /Q "%SOURCE_DIR%\docs" "%TARGET_DIR%\docs" >nul 2>&1
echo   [OK] docs/ 已复制

echo [STEP 7/8] 创建 blackboard/ 黑板目录...
if not exist "%TARGET_DIR%\blackboard" mkdir "%TARGET_DIR%\blackboard"
if not exist "%TARGET_DIR%\blackboard\input" mkdir "%TARGET_DIR%\blackboard\input"
if not exist "%TARGET_DIR%\blackboard\templates" mkdir "%TARGET_DIR%\blackboard\templates"
if not exist "%TARGET_DIR%\blackboard\output" mkdir "%TARGET_DIR%\blackboard\output"
if not exist "%TARGET_DIR%\blackboard\.snapshots" mkdir "%TARGET_DIR%\blackboard\.snapshots"
if not exist "%TARGET_DIR%\blackboard\failure-cases" mkdir "%TARGET_DIR%\blackboard\failure-cases"
if exist "%SOURCE_DIR%\blackboard\templates\项目进度记录.md" (
    copy /Y "%SOURCE_DIR%\blackboard\templates\项目进度记录.md" "%TARGET_DIR%\项目进度记录.md" >nul 2>&1
    echo   [OK] 项目进度记录.md 已创建
)
if exist "%SOURCE_DIR%\blackboard\failure-cases\README.md" (
    copy /Y "%SOURCE_DIR%\blackboard\failure-cases\README.md" "%TARGET_DIR%\blackboard\failure-cases\README.md" >nul 2>&1
)
echo   [OK] blackboard/ 目录已创建

echo [STEP 8/8] 创建 PRD 入口提示...
if not exist "%TARGET_DIR%\blackboard\input\README.md" (
    echo # PRD 入口 > "%TARGET_DIR%\blackboard\input\README.md"
    echo. >> "%TARGET_DIR%\blackboard\input\README.md"
    echo 请把 PRD 写到这里或同名 prd.md。 >> "%TARGET_DIR%\blackboard\input\README.md"
    echo. >> "%TARGET_DIR%\blackboard\input\README.md"
    echo 然后在 Trae 中说：/loop-agent >> "%TARGET_DIR%\blackboard\input\README.md"
)
echo   [OK] PRD 入口已就位

echo.
echo ============================================================
echo   ✅ Loop Agent v1.2 安装完成！
echo ============================================================
echo.
echo [文件统计]
dir /S /B "%TARGET_DIR%\.trae" 2>nul | find /C "\" > "%TEMP%\count1.txt"
set /p COUNT1=<"%TEMP%\count1.txt"
echo   .trae/        : !COUNT1! 个文件

dir /S /B "%TARGET_DIR%\blackboard" 2>nul | find /C "\" > "%TEMP%\count2.txt"
set /p COUNT2=<"%TEMP%\count2.txt"
echo   blackboard/   : !COUNT2! 个文件

dir /S /B "%TARGET_DIR%\workflows" 2>nul | find /C "\" > "%TEMP%\count3.txt"
set /p COUNT3=<"%TEMP%\count3.txt"
echo   workflows/    : !COUNT3! 个文件

echo.
echo [下一步]
echo   1. 编辑 blackboard/input/prd.md 写入需求
echo   2. 在 Trae 中说：用 Loop Agent 模式开发
echo   3. 或输入 /loop-agent
echo.
echo [文档]
echo   - docs/QUICKSTART.md        5 分钟启动指南
echo   - docs/PORTABILITY_REPORT.md 可移植性说明
echo   - docs/CROSS_PROJECT_GUIDE.md 跨项目使用
echo   - docs/UNATTENDED_MODE.md   无人值守模式
echo.
echo [卸载]
echo   直接删除 .trae/ workflows/ config/ mcp/ scripts/ docs/ blackboard/ 项目进度记录.md trae.toml
echo.
pause
endlocal
