<#
.SYNOPSIS
    Run a full system health check against the RC2 mission registry.

.DESCRIPTION
    Wrapper for Step9_HealthCheck.ps1 with -CheckRC2 and -FailOnWarning pre-set.

    This script is the second step in the Safe User Sequence. It validates the
    current state of the mission management system across four areas:

    1. UUID Role Mapping   - confirms Mission_A/B/C each have a valid UUID in
                               uuid_roles.json with correct format.
    2. Inventory Alignment - checks that each UUID exists in uuid_inventory.csv
                               with no orphan or missing entries.
    3. Staged KMZ Files   - verifies that a staged KMZ package is present for
                               each role folder before deployment.
    4. RC2 Live Slot Check - connects to the RC2 controller via MTP and confirms
                               that the on-device waypoint slot folders match the
                               expected UUIDs from the registry.

    If any check produces a WARNING or ERROR the script exits with a non-zero code.
    Run this step after staging and before deploying to confirm the system is clean.

.EXAMPLE
    & "./data/rc2/scripts/Run-HealthCheck.ps1"

.NOTES
    Safe User Sequence: Step 2 of 4
    Underlying script : Step9_HealthCheck.ps1
    Flags applied     : -CheckRC2  -FailOnWarning
    Prerequisite      : RC2 controller must be powered on and connected via USB.
#>

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Run-HealthCheck    [Safe Sequence: Step 2]" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What this checks:"
Write-Host "  1. UUID role mapping     (uuid_roles.json format and completeness)"
Write-Host "  2. Inventory alignment   (uuid_inventory.csv vs registry)"
Write-Host "  3. Staged KMZ files      (each role folder has a package ready)"
Write-Host "  4. RC2 live slot state   (on-device UUIDs match registry - RC2 must be connected)"
Write-Host ""
Write-Host "[INFO] Flags: -CheckRC2  -FailOnWarning - any WARNING or ERROR will block deployment." -ForegroundColor Green
Write-Host ""
Write-Host "Ensure the RC2 controller is powered on and connected via USB before continuing." -ForegroundColor Yellow
Write-Host ""

& "$PSScriptRoot\Step9_HealthCheck.ps1" -CheckRC2 -FailOnWarning
