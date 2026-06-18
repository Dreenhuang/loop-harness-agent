# 清理 + 重新打包
$zipFiles = Get-ChildItem -Path (Get-Location) -Filter "*.zip"
foreach ($zip in $zipFiles) {
    Write-Host "Removing old zip: $($zip.Name)"
    Remove-Item $zip.FullName -Force
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outputName = "Loop-Agent-v1.1-trae-solo-aligned_${timestamp}.zip"
$outputPath = Join-Path (Get-Location) $outputName
$sourcePath = (Get-Location).Path

Write-Host "Source: $sourcePath"
Write-Host "Output: $outputPath"
Write-Host "Compressing..."

# 使用 ZipArchive 方式（更稳定）
Add-Type -AssemblyName System.IO.Compression.FileSystem
$compression = [System.IO.Compression.CompressionLevel]::Optimal

# 统计文件数
$files = Get-ChildItem -Path $sourcePath -Recurse -File | Where-Object {
    $_.DirectoryName -notmatch '\\(\.git|node_modules|dist|build|\.vscode|\.idea)\b' -and
    $_.Name -notmatch '\.(log|bat)$' -and
    $_.Name -ne 'taskkill_err.txt' -and
    $_.Name -ne 'taskkill_out.txt'
}
Write-Host "File count to include: $($files.Count)"

# 创建 ZIP
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $sourcePath,
    $outputPath,
    $compression,
    $false
)

# 验证
if (Test-Path $outputPath) {
    $info = Get-Item $outputPath
    Write-Host ""
    Write-Host "==========================================="
    Write-Host "PACKAGE COMPLETE"
    Write-Host "==========================================="
    Write-Host ("File: " + $info.FullName)
    Write-Host ("Size: " + [math]::Round($info.Length / 1MB, 2) + " MB")
    Write-Host ("Created: " + $info.LastWriteTime)

    # 列出 ZIP 内容统计
    Add-Type -AssemblyName System.IO.Compression.FileStream
    $zip = [System.IO.Compression.ZipFile]::OpenRead($outputPath)
    Write-Host ("Entries in zip: " + $zip.Entries.Count)
    $zip.Dispose()
} else {
    Write-Host "ERROR: ZIP file not created"
    exit 1
}
