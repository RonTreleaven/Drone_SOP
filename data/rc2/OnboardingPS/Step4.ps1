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
$logRoot = $config.logRoot
$inventoryPath = Join-Path $root "REGISTRY/uuid_inventory.csv"
$registryPath = Join-Path $root "REGISTRY/uuid_roles.json"

if(-not (Test-Path $inventoryPath)){
  throw "UUID_INVENTORY_NOT_FOUND. Run Step 3 first."
}

$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logRoot "step4_assign_roles_$stamp.log"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Write-StepLog {
  param([string]$Level, [string]$Message)
  $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  $entry | Add-Content -Path $logFile -Encoding UTF8
  Write-Host $entry
}

function Read-RoleUuid {
  param(
    [Parameter(Mandatory=$true)][string]$Role,
    [Parameter(Mandatory=$true)][string[]]$AllowedUuids,
    [string[]]$AlreadyUsed = @()
  )

  while($true){
    $value = (Read-Host "Enter UUID for $Role").Trim().ToUpper()

    if($value -notmatch '^[0-9A-F-]{36}$'){
      Write-Host "Invalid UUID format. Paste the full UUID exactly as shown above."
      continue
    }
    if($value -notin $AllowedUuids){
      Write-Host "UUID not found in the inventory list above."
      continue
    }
    if($value -in $AlreadyUsed){
      Write-Host "That UUID is already assigned to another role. Choose a different one."
      continue
    }

    return $value
  }
}

try {
  Write-StepLog INFO "Step 4 started. Loading uuid_inventory.csv."

  $inventory = Import-Csv $inventoryPath |
    Sort-Object FileLastWriteLocal -Descending

  if(($inventory | Measure-Object).Count -lt 3){
    throw "At least 3 UUIDs are required for Mission_A, Mission_B, and Mission_C. Run Step 3 again after creating more missions."
  }

  Write-StepLog INFO ("Loaded {0} UUID entries from inventory." -f (($inventory | Measure-Object).Count))
  Write-Host ""
  Write-Host "Available UUIDs (newest first, by local file date):"
  $inventory | Format-Table UUID, FileLastWriteLocal, CreateTimeLocal, Author -AutoSize
  Write-Host ""
  Write-Host "Recommended: choose Mission_A for operational use, Mission_B for validation, and Mission_C as the third active slot."
  Write-Host ""

  $allowedUuids = @($inventory.UUID | ForEach-Object { $_.ToUpper() })

  $missionAUuid = Read-RoleUuid -Role Mission_A -AllowedUuids $allowedUuids
  Write-StepLog INFO "Selected Mission_A UUID: $missionAUuid"

  $missionBUuid = Read-RoleUuid -Role Mission_B -AllowedUuids $allowedUuids -AlreadyUsed @($missionAUuid)
  Write-StepLog INFO "Selected Mission_B UUID: $missionBUuid"

  $missionCUuid = Read-RoleUuid -Role Mission_C -AllowedUuids $allowedUuids -AlreadyUsed @($missionAUuid, $missionBUuid)
  Write-StepLog INFO "Selected Mission_C UUID: $missionCUuid"

  $roles = [ordered]@{
    updatedAt = (Get-Date).ToString('s')
    Mission_A = $missionAUuid
    Mission_B = $missionBUuid
    Mission_C = $missionCUuid
    notes = 'Mission_C is a normal working slot. Save any mission you care about before overwriting a slot.'
  }

  $roles | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $registryPath
  Write-StepLog INFO "uuid_roles.json written: $registryPath"
  Write-StepLog INFO "Step 4 completed successfully."
  Write-Host ""
  Write-Host "Log file: $logFile"
  Write-Host "[PASS] Step 4 validation checks passed."
  Write-Host "[SUCCESS] Step 4 completed successfully."
  Write-Host "[COMPLETE] Step 4: UUID roles saved."
  Write-Host ""
  Get-Content $registryPath
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 4 failed."
  Write-Host "Step 4 failed. See log: $logFile"
  throw
}