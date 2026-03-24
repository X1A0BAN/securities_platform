# 用途：供定时任务调用，执行每日股票数据增量同步并把输出写入日志。
param()

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$syncScript = Join-Path $PSScriptRoot "run_daily_sync.py"
$logDir = Join-Path $projectRoot "logs"
$logFile = Join-Path $logDir "daily_sync.log"

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found: $pythonExe"
}

if (-not (Test-Path $syncScript)) {
    throw "Sync script not found: $syncScript"
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null

Push-Location $projectRoot
try {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "[$timestamp] Starting daily sync job."

    & $pythonExe $syncScript *>> $logFile

    if ($LASTEXITCODE -ne 0) {
        throw "Daily sync job failed with exit code $LASTEXITCODE."
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "[$timestamp] Daily sync job completed successfully."
}
finally {
    Pop-Location
}
