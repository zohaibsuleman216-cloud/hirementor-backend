$env:PYTHONPATH = Split-Path -Parent $MyInvocation.MyCommand.Path

# Load SERVER_HOST from .env if available
$envFile = Join-Path -Path $env:PYTHONPATH -ChildPath ".env"
$hostAddr = "127.0.0.1"
if (Test-Path -LiteralPath $envFile) {
    $line = Get-Content -LiteralPath $envFile | Select-String "^SERVER_HOST=" | ForEach-Object { $_ -replace "^SERVER_HOST=", "" } | Select-Object -First 1
    if ($line) { $hostAddr = $line.Trim() }
}

$port = 8000
Write-Host "Starting SPB Backend Server..." -ForegroundColor Green
Write-Host "API Docs: http://${hostAddr}:${port}/docs" -ForegroundColor Cyan
Write-Host ""
python -m uvicorn main:app --host $hostAddr --port $port --reload
