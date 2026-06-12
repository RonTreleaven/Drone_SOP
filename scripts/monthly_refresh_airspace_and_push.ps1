param(
    [string]$RemoteName = "origin",
    [string]$BranchName = "main",
    [switch]$SkipPush,
    [switch]$SkipRefresh
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$reportDir = "data/airspace/reports"
if (-not (Test-Path $reportDir)) {
    New-Item -Path $reportDir -ItemType Directory -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $reportDir ("monthly_refresh_push_" + $stamp + ".log")

function Write-Log {
    param([string]$Message)
    $line = "$((Get-Date).ToString('s')) $Message"
    $line | Tee-Object -FilePath $logPath -Append
}

Write-Log "Refresh-and-push run started."
Write-Log "Repo root: $repoRoot"

if (-not $SkipRefresh) {
    $refreshScript = Join-Path $PSScriptRoot "monthly_refresh_airspace.ps1"
    if (-not (Test-Path $refreshScript)) {
        throw "Refresh script not found at: $refreshScript"
    }

    Write-Log "Running refresh script: $refreshScript"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $refreshScript 2>&1 | Tee-Object -FilePath $logPath -Append
    Write-Log "Refresh script completed."
}
else {
    Write-Log "SkipRefresh set; refresh step skipped."
}

$insideRepo = (git rev-parse --is-inside-work-tree 2>$null)
if ($LASTEXITCODE -ne 0 -or $insideRepo -ne "true") {
    throw "Current directory is not a git repository."
}

$pathsToStage = @(
    "data/airspace/_sources/canadian_airspace.air",
    "data/airspace/_sources/airports.csv",
    "data/airspace/_sources/ca_asp.geojson",
    "data/airspace/_sources/ca_apt.geojson",
    "data/airspace/_sources/dah*.pdf",
    "data/airspace/_derived/dah_gold_airspace.metadata.json",
    "data/airspace/_derived/dah_special_zones.geojson",
    "data/airspace/dah_gold_airspace.geojson",
    "data/canadian_airspace.geojson",
    "data/airspace/reports/monthly_refresh_*.log",
    "data/airspace/reports/dah*_moa_adiz_*.txt",
    "data/airspace/reports/dah*_moa_adiz_*.csv"
)

Write-Log "Staging refreshed airspace artifacts."
git add -- $pathsToStage
if ($LASTEXITCODE -ne 0) {
    throw "git add failed."
}

$stagedDiff = git diff --cached --name-only
if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect staged changes."
}

if (-not $stagedDiff) {
    Write-Log "No staged changes detected; nothing to commit."
    Write-Log "Refresh-and-push run completed with no git changes."
    exit 0
}

Write-Log "Staged files:"
$stagedDiff | Tee-Object -FilePath $logPath -Append

$msg = "chore(airspace): automated refresh $((Get-Date).ToString('yyyy-MM-dd HH:mm'))"
Write-Log "Creating commit: $msg"
git commit -m $msg 2>&1 | Tee-Object -FilePath $logPath -Append
if ($LASTEXITCODE -ne 0) {
    throw "git commit failed."
}

if ($SkipPush) {
    Write-Log "SkipPush set; commit created but push skipped."
    Write-Log "Refresh-and-push run completed."
    exit 0
}

Write-Log "Pushing to $RemoteName/$BranchName"
git push $RemoteName $BranchName 2>&1 | Tee-Object -FilePath $logPath -Append
if ($LASTEXITCODE -ne 0) {
    throw "git push failed. Ensure local credentials are configured for unattended pushes."
}

Write-Log "Push completed successfully."
Write-Log "Refresh-and-push run completed."