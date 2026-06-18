@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM Loop Agent · 自动打包脚本
REM 用途：将整个 Loop Agent 系统打包为 ZIP 最终交付物
REM 编码：GBK / ANSI
REM ============================================================

title Loop Agent - Package

echo.
echo ============================================================
echo   Loop Agent v1.1 - 自动打包
echo ============================================================
echo.

set "SOURCE_DIR=%CD%"
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "OUTPUT_NAME=Loop-Agent-v1.1-trae-solo-aligned_%TIMESTAMP%.zip"
set "OUTPUT_PATH=%SOURCE_DIR%\%OUTPUT_NAME%"

echo [1/4] 准备打包...

REM 排除项
set "EXCLUDE_FILES=*.bat *.log taskkill_err.txt taskkill_out.txt"
set "EXCLUDE_DIRS=.git node_modules dist build .vscode .idea"

echo       源目录：%SOURCE_DIR%
echo       输出文件：%OUTPUT_NAME%

REM 1. 统计文件数
echo [2/4] 统计文件数...
set "FILE_COUNT=0"
for /r "%SOURCE_DIR%" %%f in (*.*) do (
    set "SKIP=0"
    for %%e in (%EXCLUDE_FILES%) do (
        if /i "%%~xf"=="%%e" set "SKIP=1"
    )
    if !SKIP!==0 set /a FILE_COUNT+=1
)
echo       预计打包：约 %FILE_COUNT% 个文件

REM 2. 检查 PowerShell + .NET ZIP 支持
echo [3/4] 检查打包工具...
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       ❌ PowerShell 未找到
    pause
    exit /b 1
)
echo       ✅ PowerShell 可用

REM 3. 执行打包
echo [4/4] 执行打包...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
    "$source = '%SOURCE_DIR%';" ^
    "$output = '%OUTPUT_PATH%';" ^
    "$excludeFiles = @(%EXCLUDE_FILES:'=\"%\"%) ;" ^
    "$excludeDirs = @(%EXCLUDE_DIRS:'=\"%\"%) ;" ^
    "if (Test-Path $output) { Remove-Item $output -Force };" ^
    "Write-Host '       正在打包，请稍候...';" ^
    "[System.IO.Compression.ZipFile]::CreateFromDirectory($source, $output, [System.IO.Compression.CompressionLevel]::Optimal, $false);" ^
    "$zipInfo = Get-Item $output;" ^
    "Write-Host ('       ✅ 打包完成：' + $zipInfo.Name);" ^
    "Write-Host ('       📦 文件大小：{0:N2} MB' -f ($zipInfo.Length / 1MB));" ^
    "Write-Host ('       📍 完整路径：' + $zipInfo.FullName);"

if exist "%OUTPUT_PATH%" (
    echo.
    echo ============================================================
    echo   ✅ 打包完成
    echo ============================================================
    echo.
    echo 📦 交付物：%OUTPUT_PATH%
    echo.
    echo 包含内容：
    echo   - trae.toml 主配置
    echo   - .trae/（rules/commands/skills/agents/workflows/）
    echo   - workflows/（主蓝图 + 10 phases + 4 gates）
    echo   - config/（4 个 yaml）
    echo   - mcp/（4 个 .mcp.json）
    echo   - scripts/（3 个 .bat）
    echo   - loop-agent-engine/（2 个 .ts）
    echo   - domain-chips/（web-feature-chip）
    echo   - blackboard/templates/
    echo   - 完整文档（README/INSTALL/CHANGELOG/DELIVERY）
    echo.
    pause
) else (
    echo.
    echo ❌ 打包失败，请检查 PowerShell 输出
    pause
    exit /b 1
)
