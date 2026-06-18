@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM Loop Agent 启动器 v1.0
REM 功能：智能检测 + 加载资产 + 启动 Loop Agent
REM 编码：GBK / ANSI（防止 Windows 乱码）
REM ============================================================

title Loop Agent 启动器 v1.0

echo.
echo ============================================================
echo   Loop Agent 模式启动器 v1.0
echo   基于 Agent Loop Engineering + 16 角色 AGENT TEAM
echo ============================================================
echo.

REM 1. 检测当前目录
set "TARGET_DIR=%CD%"
echo [1/5] 当前目录：%TARGET_DIR%

REM 2. 检测黑板
if exist "%TARGET_DIR%\项目进度记录.md" (
    echo [2/5] ✅ 检测到黑板文件：项目进度记录.md
    set "BLACKBOARD_STATUS=EXISTS"
) else (
    echo [2/5] ⚠️ 未检测到黑板文件，准备初始化...
    set "BLACKBOARD_STATUS=MISSING"
)

REM 3. 检测 Loop Agent 资产
if exist "%TARGET_DIR%\.trae\rules\loop-agent.md" (
    echo [3/5] ✅ Loop Agent 资产已就位
) else (
    echo [3/5] ❌ Loop Agent 资产未找到
    echo       请先在 Trae 中加载 Loop Agent 规则
    pause
    exit /b 1
)

REM 4. 检测 .trae 子目录
echo.
echo [4/5] 检查 4 级封装资产：
set "MISSING=0"

if not exist "%TARGET_DIR%\.trae\skills" (
    echo       ❌ .trae\skills 缺失
    set "MISSING=1"
) else (
    echo       ✅ .trae\skills
)

if not exist "%TARGET_DIR%\.trae\agents" (
    echo       ❌ .trae\agents 缺失
    set "MISSING=1"
) else (
    echo       ✅ .trae\agents
)

if not exist "%TARGET_DIR%\.trae\workflows" (
    echo       ❌ .trae\workflows 缺失
    set "MISSING=1"
) else (
    echo       ✅ .trae\workflows
)

if not exist "%TARGET_DIR%\domain-chips" (
    echo       ❌ domain-chips 缺失
    set "MISSING=1"
) else (
    echo       ✅ domain-chips
)

if !MISSING! == 1 (
    echo.
    echo ⚠️ 部分资产缺失，Loop Agent 模式仍可工作，但建议补齐
)

REM 5. 初始化（如果需要）
if "%BLACKBOARD_STATUS%"=="MISSING" (
    echo.
    echo [5/5] 初始化黑板...
    copy "%TARGET_DIR%\.trae\rules\loop-agent.md" nul >nul 2>&1
    
    REM 从模板复制
    if exist "%USERPROFILE%\ai-gongju\Loop-agent\blackboard\templates\项目进度记录.md" (
        copy "%USERPROFILE%\ai-gongju\Loop-agent\blackboard\templates\项目进度记录.md" "%TARGET_DIR%\项目进度记录.md" >nul
        echo       ✅ 黑板已初始化
    ) else (
        echo       ⚠️ 黑板模板未找到，请手动创建
    )
) else (
    echo [5/5] 黑板已存在，跳过初始化
)

echo.
echo ============================================================
echo   Loop Agent 系统就绪
echo ============================================================
echo.
echo 接下来请在 Trae 中：
echo   1. 输入 /loop-agent 启动
echo   2. 或说"用 Loop Agent 模式开发"
echo.
echo 详细使用说明请看 README.md
echo.
pause
