$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$output = Join-Path (Get-Location) ('Loop-Agent-v1.1-trae-solo-aligned_' + $timestamp + '.zip')
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Get-Location).Path,
    $output,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)
$info = Get-Item $output
Write-Host ('PACKAGED: ' + $info.FullName)
Write-Host ('SIZE: ' + [math]::Round($info.Length / 1MB, 2) + ' MB')
