param(
  [string]$ScanFolder,
  [switch]$Force,
  [switch]$SkipMissionC
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
$scanRoot = Join-Path $root "REGISTRY/slot_scan"

if(-not (Test-Path $rolesPath)){
  throw "UUID_ROLES_NOT_FOUND. Run Step 4 first."
}
if(-not (Test-Path $scanRoot)){
  throw "SLOT_SCAN_ROOT_NOT_FOUND: $scanRoot. Run Step 3 first."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logRoot "step5a_seed_slots_$stamp.log"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Write-StepLog {
  param([string]$Level, [string]$Message)
  $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  $entry | Add-Content -Path $logFile -Encoding UTF8
  Write-Host $entry
}

try {
  Write-StepLog INFO "Step 5A started. Preparing automatic slot seeding."

  if([string]::IsNullOrWhiteSpace($ScanFolder)){
    $latest = Get-ChildItem -Path $scanRoot -Directory |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1

    if(-not $latest){
      throw "No slot scan folders found under $scanRoot. Run Step 3 first."
    }

    $ScanFolder = $latest.FullName
    Write-StepLog INFO "No scan folder passed. Using latest: $ScanFolder"
  }
  else {
    if(-not [System.IO.Path]::IsPathRooted($ScanFolder)){
      $ScanFolder = Join-Path $scanRoot $ScanFolder
    }
    Write-StepLog INFO "Using provided scan folder: $ScanFolder"
  }

  if(-not (Test-Path $ScanFolder)){
    throw "SCAN_FOLDER_NOT_FOUND: $ScanFolder"
  }

  $roles = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $roleOrder = @("Mission_A", "Mission_B")
  if(-not $SkipMissionC){
    $roleOrder += "Mission_C"
  }

  $step5Path = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "Step5.ps1"
  if(-not (Test-Path $step5Path)){
    throw "Step5.ps1 not found beside this script: $step5Path"
  }

  . $step5Path
  if(-not (Get-Command Initialize-RC2MissionSlotSeed -ErrorAction SilentlyContinue)){
    throw "Initialize-RC2MissionSlotSeed is not available. Step5.ps1 did not load correctly."
  }

  foreach($role in $roleOrder){
    $uuid = $roles.$role
    if(-not $uuid -or $uuid -notmatch '^[0-9A-F-]{36}$'){
      throw "Invalid UUID for $role in uuid_roles.json"
    }

    $sourceKmz = Join-Path $ScanFolder ("{0}.kmz" -f $uuid)
    if(-not (Test-Path $sourceKmz)){
      throw "Source KMZ not found for ${role}: $sourceKmz"
    }

    Write-StepLog INFO "Seeding $role from $sourceKmz"

    if($Force){
      Initialize-RC2MissionSlotSeed -Role $role -SourceKmz $sourceKmz -Force | ForEach-Object {
        Write-StepLog INFO $_
      }
    }
    else {
      Initialize-RC2MissionSlotSeed -Role $role -SourceKmz $sourceKmz | ForEach-Object {
        Write-StepLog INFO $_
      }
    }
  }

  Write-StepLog INFO "Step 5A completed successfully."
  Write-Host "Log file: $logFile"
  Write-Host "[PASS] Step 5A validation checks passed."
  Write-Host "[SUCCESS] Step 5A completed successfully."
  if($SkipMissionC){
    Write-Host "[COMPLETE] Seeded roles: Mission_A, Mission_B"
  }
  else {
    Write-Host "[COMPLETE] Seeded roles: Mission_A, Mission_B, Mission_C"
  }
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 5A failed. See log: $logFile"
  throw
}
