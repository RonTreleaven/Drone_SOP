<#
.SYNOPSIS
    Deploy staged KMZ packages to RC2 UUID slot folders with an interactive confirmation gate.

.DESCRIPTION
    Wrapper for Step6.ps1 with -PromptBeforeCopy pre-set.

    This script is the fourth and final step in the Safe User Sequence (live transfer).
    It reads the staged role KMZ package and the UUID slot mapping, then presents the
    full deployment plan and asks you to type YES before any file is written to the RC2.

    Files are copied to the RC2 controller via MTP only after you confirm.
    If you type anything other than YES the transfer is cancelled and no changes are made.

    Prerequisites before running this step:
      - Run-StageIncoming.ps1 completed successfully (KMZ staged to role folder).
      - Run-HealthCheck.ps1 exited with code 0 (all checks passed).
      - Run-DeployPreview.ps1 reviewed and the plan looks correct.
      - RC2 controller is powered on and connected via USB.

.PARAMETER Role
    The mission role to deploy: Mission_A, Mission_B, or Mission_C.
    If omitted you will be prompted to enter a value interactively.

.EXAMPLE
    & "./data/rc2/scripts/Run-Deploy.ps1" -Role Mission_B

.EXAMPLE
    & "./data/rc2/scripts/Run-Deploy.ps1"
    # Interactive prompt — enter the role when asked.

.NOTES
    Safe User Sequence: Step 4 of 4 (live transfer with confirmation gate)
    Underlying script : Step6.ps1
    Flags applied     : -PromptBeforeCopy
    Exit code 0       : Transfer completed successfully.
    Exit code non-zero: Transfer cancelled or an error occurred — no partial writes.
#>

param(
  [ValidateSet('Mission_A','Mission_B','Mission_C')]
  [string]$Role
)

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Run-Deploy         [Safe Sequence: Step 4]" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What this does:"
Write-Host "  Copies the staged KMZ package to the matching RC2 UUID slot folders via MTP."
Write-Host "  You will be shown the deployment plan and asked to type YES before any file"
Write-Host "  is written.  Typing anything else cancels the transfer cleanly."
Write-Host ""
Write-Host "Prerequisites:" -ForegroundColor Yellow
Write-Host "  - Run-StageIncoming.ps1    completed (role folder has a staged KMZ)"
Write-Host "  - Run-HealthCheck.ps1      passed    (all checks exit code 0)"
Write-Host "  - Run-DeployPreview.ps1    reviewed  (deployment plan looks correct)"
Write-Host "  - RC2 controller powered on and connected via USB"
Write-Host ""

if (-not $Role) {
  Write-Host "Which role do you want to deploy?" -ForegroundColor Yellow
  Write-Host "  Options: Mission_A  /  Mission_B  /  Mission_C"
  $Role = (Read-Host "  Role").Trim()
  if ($Role -notin @('Mission_A', 'Mission_B', 'Mission_C')) {
    Write-Host ""
    Write-Host "[BLOCKED] '$Role' is not a valid role. Must be Mission_A, Mission_B, or Mission_C." -ForegroundColor Red
    exit 1
  }
}

Write-Host ""
Write-Host "[INFO] Deploying role : $Role  (you will be prompted to confirm before any file is transferred)" -ForegroundColor Green
Write-Host ""

& "$PSScriptRoot\Step6.ps1" -Roles $Role -PromptBeforeCopy
