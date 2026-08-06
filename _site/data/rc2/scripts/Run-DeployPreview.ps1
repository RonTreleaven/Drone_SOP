<#
.SYNOPSIS
    Preview the deployment plan for a mission role� no files are transferred.

.DESCRIPTION
    Wrapper for Step6.ps1 with -DryRun pre-set.

    This script is the third step in the Safe User Sequence (preview pass). It
    reads the staged role KMZ package and the UUID slot mapping, then prints a
    full deployment plan showing exactly which files would be copied to which
    RC2 UUID slot folders — without writing, moving, or deleting anything.

    Use this step immediately after a clean health check to verify the intended
    deployment before committing any changes to the RC2 controller.

    Nothing is changed on disk or on the RC2 during a dry run.

.PARAMETER Role
    The mission role to preview: Mission_A, Mission_B, or Mission_C.
    If omitted you will be prompted to enter a value interactively.

.EXAMPLE
    & "./data/rc2/scripts/Run-DeployPreview.ps1" -Role Mission_B

.EXAMPLE
    & "./data/rc2/scripts/Run-DeployPreview.ps1"
    # Interactive prompt — enter the role when asked.

.NOTES
    Safe User Sequence: Step 3 of 4 (DryRun preview — no writes)
    Underlying script : Step6.ps1
    Flags applied     : -DryRun
    Next step         : Run-Deploy.ps1  (actual transfer with confirmation gate)
#>

param(
  [ValidateSet('Mission_A','Mission_B','Mission_C')]
  [string]$Role
)

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Run-DeployPreview  [Safe Sequence: Step 3]" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What this does:"
Write-Host "  Shows the full deployment plan for the chosen role."
Write-Host "  Displays which KMZ files would be copied to which RC2 UUID slot folders."
Write-Host "  NO files are transferred, created, moved, or deleted."
Write-Host ""

if (-not $Role) {
  Write-Host "Which role do you want to preview?" -ForegroundColor Yellow
  Write-Host "  Options: Mission_A  /  Mission_B  /  Mission_C"
  $Role = (Read-Host "  Role").Trim()
  if ($Role -notin @('Mission_A', 'Mission_B', 'Mission_C')) {
    Write-Host ""
    Write-Host "[BLOCKED] '$Role' is not a valid role. Must be Mission_A, Mission_B, or Mission_C." -ForegroundColor Red
    exit 1
  }
}

Write-Host ""
Write-Host "[INFO] Previewing deployment for role : $Role  (DryRun : no files will be transferred)" -ForegroundColor Green
Write-Host ""

& "$PSScriptRoot\Step6.ps1" -Roles $Role -DryRun
