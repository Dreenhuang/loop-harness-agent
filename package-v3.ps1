# 清理旧 ZIP
Get-ChildItem -Path (Get-Location) -Filter "*.zip" | Remove-Item -Force

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outputName = "Loop-Agent-v1.1-trae-solo-aligned_${timestamp}.zip"
$outputPath = Join-Path (Get-Location) $outputName

# 用 Compress-Archive（更现代，处理文件占用更好）
$sourcePath = (Get-Location).Path
$tempSource = Join-Path $env:TEMP "Loop-Agent-source-temp"
if (Test-Path $tempSource) { Remove-Item $tempSource -Recurse -Force }

# 复制到临时目录（避免源文件被占用）
Write-Host "Copying to temp: $tempSource"
Copy-Item -Path $sourcePath -Destination $tempSource -Recurse -Force

# 清理临时目录中的 zip 和 .bat（可选）
Get-ChildItem -Path $tempSource -Filter "*.zip" -Recurse | Remove-Item -Force
Get-ChildItem -Path $tempSource -Filter "*.ps1" -Recurse | Remove-Item -Force

# 创建 ZIP
Write-Host "Compressing..."
Compress-Archive -Path "$tempSource\*" -DestinationPath $outputPath -CompressionLevel Optimal

# 清理临时
Remove-Item $tempSource -Recurse -Force

# 验证
$info = Get-Item $outputPath
Write-Host ""
Write-Host "==========================================="
Write-Host "PACKAGE COMPLETE"
Write-Host "==========================================="
Write-Host ("File: " + $info.FullName)
Write-Host ("Size: " + [math]::Round($info.Length / 1MB, 2) + " MB")
