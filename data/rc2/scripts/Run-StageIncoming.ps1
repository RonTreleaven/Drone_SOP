<#
.SYNOPSIS
    Stage the newest INCOMING KMZ into a mission role folder and archive the source file.

.DESCRIPTION
    Wrapper for Step5B_StageFromIncoming.ps1 with -ArchiveIncoming pre-set.

    This script is the first step in the Safe User Sequence. It scans the INCOMING
    folder for the most recently delivered KMZ flight-plan file, copies it into the
    chosen mission role folder (Mission_A, Mission_B, or Mission_C), and then moves
    the source file to ARCHIVE so it cannot be staged a second time by accident.

    Run this step whenever a new KMZ has been delivered to the INCOMING folder and
    you are ready to assign it to a specific mission role.

.PARAMETER Role
    The mission role to stage the KMZ into: Mission_A, Mission_B, or Mission_C.
    If omitted you will be prompted to enter a value interactively.

.EXAMPLE
    & "./data/rc2/scripts/Run-StageIncoming.ps1" -Role Mission_B

.EXAMPLE
    & "./data/rc2/scripts/Run-StageIncoming.ps1"
    # Interactive prompt — enter the role when asked.

.NOTES
    Safe User Sequence: Step 1 of 4
    Underlying script : Step5B_StageFromIncoming.ps1
    Flags applied     : -ArchiveIncoming
#>

param(
  [ValidateSet('Mission_A','Mission_B','Mission_C')]
  [string]$Role
)

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Run-StageIncoming  [Safe Sequence: Step 1]" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What this does:"
Write-Host "  1. Finds the newest KMZ in your INCOMING folder."
Write-Host "  2. Copies it into the chosen mission role folder."
Write-Host "  3. Moves the source file to ARCHIVE (prevents re-staging)."
Write-Host ""

if (-not $Role) {
  Write-Host "Which role should receive this KMZ?" -ForegroundColor Yellow
  Write-Host "  Options: Mission_A  /  Mission_B  /  Mission_C"
  $Role = (Read-Host "  Role").Trim()
  if ($Role -notin @('Mission_A', 'Mission_B', 'Mission_C')) {
    Write-Host ""
    Write-Host "[BLOCKED] '$Role' is not a valid role. Must be Mission_A, Mission_B, or Mission_C." -ForegroundColor Red
    exit 1
  }
}

Write-Host ""
Write-Host "[INFO] Target role : $Role" -ForegroundColor Green
Write-Host "[INFO] ArchiveIncoming is enabled - source KMZ will be moved to ARCHIVE after staging." -ForegroundColor Green
Write-Host ""

$step5BPath = Join-Path $PSScriptRoot 'Step5B_StageFromIncoming.ps1'
& $step5BPath -Role $Role -ArchiveIncoming
