$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$pythonExe = "C:/Program Files/Python312/python.exe"
$sourceDir = "data/airspace/_sources"
$reportDir = "data/airspace/reports"

if (-not (Test-Path $sourceDir)) {
  New-Item -Path $sourceDir -ItemType Directory -Force | Out-Null
}
if (-not (Test-Path $reportDir)) {
  New-Item -Path $reportDir -ItemType Directory -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $reportDir ("monthly_refresh_" + $stamp + ".log")

$cmd = @(
  "scripts/refresh_airspace_data.py",
  "--download-openair",
  "--require-web-openair",
  "--download-airports-csv",
  "--discover-latest-dah-url",
  "--download-dah-pdf",
  "--extract-dah-special-zones"
)

$caAspUrl = $env:OPENAIP_CA_ASP_URL
$caAptUrl = $env:OPENAIP_CA_APT_URL
if ($caAspUrl) {
  $cmd += @("--download-ca-sources", "--require-web-ca-asp", "--ca-asp-url", $caAspUrl)
  if ($caAptUrl) {
    $cmd += @("--ca-apt-url", $caAptUrl)
  }
}

"Monthly refresh started: $(Get-Date -Format s)" | Tee-Object -FilePath $logPath
"Working directory: $repoRoot" | Tee-Object -FilePath $logPath -Append
"Command: $pythonExe $($cmd -join ' ')" | Tee-Object -FilePath $logPath -Append

try {
  & $pythonExe @cmd 2>&1 | Tee-Object -FilePath $logPath -Append
  "Monthly refresh completed successfully." | Tee-Object -FilePath $logPath -Append
  exit 0
}
catch {
  "Monthly refresh failed: $($_.Exception.Message)" | Tee-Object -FilePath $logPath -Append
  exit 1
}
