param(
    [switch]$Merge
)

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Split-Path -Parent $Here

Write-Host "Advanced RPAS ingest root: $Repo"

$Scripts = @(
    Join-Path $Here "batch1\Merge_Batch1.py",
    Join-Path $Here "batch2\Merge_Batch2.py"
)

foreach ($Script in $Scripts) {
    if ($Merge) {
        python $Script
    } else {
        python $Script --dry-run
    }
}
