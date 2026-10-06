param(
    [switch]$NoPush
)

# Pulls latest, refreshes jobs data (no reset), then commits and pushes ONLY the data/jobs* files.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$dataFiles = @("data/jobs.db", "data/jobs.json", "data/jobs_review.csv", "data/jobs_review_latest.csv")

function Invoke-Git {
    & git @args
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') failed with exit code $LASTEXITCODE" }
}

# Start from the latest remote jobs.db so the local run builds on the GitHub Actions data.
Invoke-Git pull --rebase --autostash

& (Join-Path $root "UpdateJobsBoard.cmd") --sources "jobbank,simplyhired,talent,jobs_bear,greenhouse,lever"
if ($LASTEXITCODE -ne 0) { throw "UpdateJobsBoard.cmd failed with exit code $LASTEXITCODE" }

Invoke-Git add -- $dataFiles
& git diff --cached --quiet -- $dataFiles
if ($LASTEXITCODE -eq 0) {
    Write-Host "No job data changes to commit."
    exit 0
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm 'UTC'")
Invoke-Git commit -m "Auto-update drone jobs (local) $stamp" -- $dataFiles

if ($NoPush) {
    Write-Host "Committed locally; skipping push (-NoPush)."
    exit 0
}

try {
    Invoke-Git pull --rebase --autostash
    Invoke-Git push
} catch {
    & git rebase --abort 2>$null
    throw
}
Write-Host "Jobs data pushed to GitHub."
