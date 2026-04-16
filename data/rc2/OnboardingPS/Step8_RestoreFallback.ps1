param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('Mission_B','Mission_A','Mission_C')]
  [string]$TargetRole,

  [string]$SourceFallbackKmz
)

$configPointer = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
if(-not (Test-Path $configPointer)){
  throw "CONFIG_POINTER_NOT_FOUND. Run Step 1 first."
}

$configPath = (Get-Content $configPointer -Raw).Trim()
if(-not (Test-Path $configPath)){
  throw "CONFIG_NOT_FOUND. Run Step 1 again to regenerate local_config.json."
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$root = $config.managerRoot
$logRoot = if($config.logRoot){ $config.logRoot } else { Join-Path $root "LOGS" }
$rolesPath = Join-Path $root "REGISTRY/uuid_roles.json"
if(-not (Test-Path $rolesPath)){
  throw "UUID_ROLES_NOT_FOUND. Run Step 4 first."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logRoot "step8_restore_fallback_$stamp.log"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Write-StepLog {
  param([string]$Level, [string]$Message)
  $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  $entry | Add-Content -Path $logFile -Encoding UTF8
  Write-Host $entry
}

try {
  Write-StepLog INFO "Step 8 started. Preparing fallback restore workflow."

  $roles = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $missionCUuid = $roles.Mission_C
  if(-not $missionCUuid -or $missionCUuid -notmatch '^[0-9A-F-]{36}$'){
    throw "Invalid Mission_C UUID in uuid_roles.json"
  }

  if([string]::IsNullOrWhiteSpace($SourceFallbackKmz)){
    $SourceFallbackKmz = Join-Path $root ("Mission_C/{0}.kmz" -f $missionCUuid)
  }

  if(-not (Test-Path $SourceFallbackKmz)){
    throw "Fallback source KMZ not found: $SourceFallbackKmz"
  }

  $step5Path = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "Step5.ps1"
  if(-not (Test-Path $step5Path)){
    throw "Step5.ps1 not found beside this script: $step5Path"
  }

  . $step5Path

  if(-not (Get-Command Invoke-RC2MissionDeploy -ErrorAction SilentlyContinue)){
    throw "Invoke-RC2MissionDeploy is not available. Step5.ps1 did not load correctly."
  }

  Write-StepLog INFO "Restoring fallback mission to slot: $TargetRole"
  Write-StepLog INFO "Fallback source file: $SourceFallbackKmz"

  Invoke-RC2MissionDeploy -Role $TargetRole -SourceKmz $SourceFallbackKmz

  Write-StepLog INFO "Step 8 completed successfully."
  Write-Host "Log file: $logFile"
  Write-Host "[PASS] Step 8 validation checks passed."
  Write-Host "[SUCCESS] Step 8 completed successfully."
  Write-Host "[COMPLETE] Fallback mission restored to slot: $TargetRole"
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 8 failed. See log: $logFile"
  throw
}