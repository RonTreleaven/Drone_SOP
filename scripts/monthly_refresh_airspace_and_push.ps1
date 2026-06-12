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
    if ($LASTEXITCODE -ne 0) {
        throw "Refresh script failed with exit code $LASTEXITCODE."
    }
    Write-Log "Refresh script completed."
}
else {
    Write-Log "SkipRefresh set; refresh step skipped."
}

$insideRepo = (git rev-parse --is-inside-work-tree 2>$null)
if ($LASTEXITCODE -ne 0 -or $insideRepo -ne "true") {
    throw "Current directory is not a git repository."
}

$corePathsToStage = @(
    "data/airspace/_sources/canadian_airspace.air",
    "data/airspace/_sources/airports.csv",
    "data/airspace/_sources/ca_asp.geojson",
    "data/airspace/_sources/ca_apt.geojson",
    "data/airspace/_sources/dah*.pdf",
    "data/airspace/_derived/dah_gold_airspace.metadata.json",
    "data/airspace/_derived/dah_special_zones.geojson",
    "data/airspace/dah_gold_airspace.geojson",
    "data/canadian_airspace.geojson"
)

$logPathsToStage = @(
    "data/airspace/reports/monthly_refresh_[0-9]*.log",
    "data/airspace/reports/dah*_moa_adiz_*.txt",
    "data/airspace/reports/dah*_moa_adiz_*.csv"
)

Write-Log "Staging core refreshed airspace artifacts."
$coreStageFiles = @()
foreach ($pattern in $corePathsToStage) {
    $coreStageFiles += Get-ChildItem -Path $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        $_.FullName
    }
}

if ($coreStageFiles.Count -gt 0) {
    git add -- $coreStageFiles
    if ($LASTEXITCODE -ne 0) {
        throw "git add failed."
    }
}

$coreStagedDiff = git diff --cached --name-only
if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect staged core changes."
}

if (-not $coreStagedDiff) {
    Write-Log "No core data changes detected; skipping commit to avoid log-only churn."
    Write-Log "Refresh-and-push run completed with no core git changes."
    exit 0
}

Write-Log "Core changes detected; staging refresh logs for traceability."
$logStageFiles = @()
foreach ($pattern in $logPathsToStage) {
    $logStageFiles += Get-ChildItem -Path $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
        $_.FullName
    }
}

if ($logStageFiles.Count -gt 0) {
    git add -- $logStageFiles
    if ($LASTEXITCODE -ne 0) {
        throw "git add for log artifacts failed."
    }
}

# Do not stage the currently written push log; it is still being appended.
git restore --staged -- $logPath 2>$null

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
$nativeErrPref = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$pushOutput = & git push $RemoteName $BranchName 2>&1
$pushExit = $LASTEXITCODE
$ErrorActionPreference = $nativeErrPref
if ($pushOutput) {
    $pushOutput | Tee-Object -FilePath $logPath -Append
}
if ($pushExit -ne 0) {
    Write-Log "git push returned non-zero exit code: $pushExit"

    $nativeErrPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $fetchOutput = & git fetch $RemoteName $BranchName --quiet 2>&1
    $ErrorActionPreference = $nativeErrPref
    if ($fetchOutput) {
        $fetchOutput | Tee-Object -FilePath $logPath -Append
    }
    $localHead = (git rev-parse HEAD).Trim()
    $remoteHead = (git rev-parse "$RemoteName/$BranchName").Trim()

    if ($localHead -eq $remoteHead) {
        Write-Log "Remote is already at local HEAD despite non-zero push exit; continuing as success."
    }
    else {
        throw "git push failed and remote is not at local HEAD. Ensure local credentials are configured for unattended pushes."
    }
}

Write-Log "Push completed successfully."
Write-Log "Refresh-and-push run completed."
exit 0