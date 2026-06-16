@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM Loop Agent · Blackboard 初始化脚本
REM 用途：创建黑板目录结构 + 复制模板 + 初始化 state.json
REM 编码：GBK / ANSI（防止 Windows 乱码）
REM ============================================================

title Loop Agent - Blackboard Init

echo.
echo ============================================================
echo   Loop Agent - Blackboard 初始化 v1.0
echo ============================================================
echo.

set "TARGET_DIR=%CD%"
set "BLACKBOARD_DIR=%TARGET_DIR%\blackboard"

REM 1. 创建黑板目录结构
echo [1/6] 创建黑板目录结构...

if not exist "%BLACKBOARD_DIR%" mkdir "%BLACKBOARD_DIR%"
if not exist "%BLACKBOARD_DIR%\input" mkdir "%BLACKBOARD_DIR%\input"
if not exist "%BLACKBOARD_DIR%\output" mkdir "%BLACKBOARD_DIR%\output"
if not exist "%BLACKBOARD_DIR%\.snapshots" mkdir "%BLACKBOARD_DIR%\.snapshots"
if not exist "%BLACKBOARD_DIR%\logs" mkdir "%BLACKBOARD_DIR%\logs"
if not exist "%BLACKBOARD_DIR%\a2a" mkdir "%BLACKBOARD_DIR%\a2a"
if not exist "%BLACKBOARD_DIR%\requirements" mkdir "%BLACKBOARD_DIR%\requirements"
if not exist "%BLACKBOARD_DIR%\design" mkdir "%BLACKBOARD_DIR%\design"
if not exist "%BLACKBOARD_DIR%\architecture" mkdir "%BLACKBOARD_DIR%\architecture"
if not exist "%BLACKBOARD_DIR%\code" mkdir "%BLACKBOARD_DIR%\code"
if not exist "%BLACKBOARD_DIR%\quality" mkdir "%BLACKBOARD_DIR%\quality"
if not exist "%BLACKBOARD_DIR%\knowledge" mkdir "%BLACKBOARD_DIR%\knowledge"
if not exist "%BLACKBOARD_DIR%\docs" mkdir "%BLACKBOARD_DIR%\docs"
if not exist "%BLACKBOARD_DIR%\prd" mkdir "%BLACKBOARD_DIR%\prd"
if not exist "%BLACKBOARD_DIR%\ux" mkdir "%BLACKBOARD_DIR%\ux"
if not exist "%BLACKBOARD_DIR%\ui" mkdir "%BLACKBOARD_DIR%\ui"
if not exist "%BLACKBOARD_DIR%\test_reports" mkdir "%BLACKBOARD_DIR%\test_reports"
if not exist "%BLACKBOARD_DIR%\performance" mkdir "%BLACKBOARD_DIR%\performance"
if not exist "%BLACKBOARD_DIR%\reviews" mkdir "%BLACKBOARD_DIR%\reviews"
if not exist "%BLACKBOARD_DIR%\final_review" mkdir "%BLACKBOARD_DIR%\final_review"
if not exist "%BLACKBOARD_DIR%\bugs" mkdir "%BLACKBOARD_DIR%\bugs"

echo       ✅ 黑板目录已创建（22 个子目录）

REM 2. 复制黑板模板
echo [2/6] 复制黑板模板...

set "TEMPLATE_PATH=%USERPROFILE%\ai-gongju\Loop-agent\blackboard\templates\项目进度记录.md"

if exist "%TEMPLATE_PATH%" (
    copy "%TEMPLATE_PATH%" "%TARGET_DIR%\项目进度记录.md" >nul
    echo       ✅ 黑板已复制到项目根
) else (
    if exist "%TARGET_DIR%\.trae\blackboard\templates\项目进度记录.md" (
        copy "%TARGET_DIR%\.trae\blackboard\templates\项目进度记录.md" "%TARGET_DIR%\项目进度记录.md" >nul
        echo       ✅ 黑板已复制（备选路径）
    ) else (
        echo       ⚠️ 模板未找到，请手动创建项目进度记录.md
    )
)

REM 3. 初始化 state.json
echo [3/6] 初始化 state.json...

(
echo {
echo   "phase": "INIT",
echo   "projectName": "%~1",
echo   "tasks": {},
echo   "dependencies": {},
echo   "budget": {
echo     "maxCost": 100.0,
echo     "currentCost": 0.0,
echo     "maxIterations": 200,
echo     "currentIteration": 0,
echo     "maxAttemptsPerTask": 3,
echo     "noProgressThreshold": 3,
echo     "noProgressCount": 0
echo   },
echo   "qualityGates": {
echo     "codeReview": "NOT_STARTED",
echo     "performance": "NOT_STARTED",
echo     "testing": "NOT_STARTED",
echo     "final": "NOT_STARTED"
echo   },
echo   "startedAt": "%date% %time%",
echo   "updatedAt": "%date% %time%"
echo }
) > "%BLACKBOARD_DIR%\state.json"

echo       ✅ state.json 已创建

REM 4. 初始化 A2A 消息文件
echo [4/6] 初始化 A2A 消息文件...
echo. > "%BLACKBOARD_DIR%\a2a\messages.jsonl"
echo {} > "%BLACKBOARD_DIR%\a2a\topic_index.json"
echo. > "%BLACKBOARD_DIR%\a2a\dead_letter.jsonl"
echo       ✅ A2A 消息日志就绪

REM 5. 初始化知识索引
echo [5/6] 初始化知识索引...

(
echo {
echo   "version": "1.0",
echo   "createdAt": "%date%",
echo   "entries": []
echo }
) > "%BLACKBOARD_DIR%\knowledge_index.json"

echo       ✅ 知识索引已创建

REM 6. 创建 PRD 入口占位文件
echo [6/6] 创建 PRD 入口...

(
echo # PRD 输入区
echo.
echo 请将 PRD 文档放到本目录下，命名为 prd.md。
echo.
echo ## 使用方式
echo.
echo 1. 复制 PRD 模板：cp blackboard/templates/prd-template.md blackboard/input/prd.md
echo 2. 填写 PRD 内容
echo 3. 触发 Loop Agent：/loop-agent 或 "用 Loop Agent 模式开发"
echo.
echo ## 模板说明
echo.
echo PRD 模板位于：blackboard/templates/prd-template.md
) > "%BLACKBOARD_DIR%\input\README.md"

echo       ✅ PRD 入口就绪

echo.
echo ============================================================
echo   ✅ Blackboard 初始化完成
echo ============================================================
echo.
echo 接下来请：
echo   1. 将 PRD 文件放到：%BLACKBOARD_DIR%\input\prd.md
echo   2. 在 Trae 中触发：/loop-agent
echo.
pause
