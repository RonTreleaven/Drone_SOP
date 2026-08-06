param(
  [switch]$CheckRC2,
  [switch]$FailOnWarning,
  [string]$OutputPath
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
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logRoot "step9_healthcheck_$stamp.log"

function Write-StepLog {
  param([string]$Level, [string]$Message)
  $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  $entry | Add-Content -Path $logFile -Encoding UTF8
  Write-Host $entry
}

function Add-Check {
  param(
    [Parameter(Mandatory=$true)][string]$Code,
    [Parameter(Mandatory=$true)][ValidateSet('OK','WARN','FAIL')] [string]$Status,
    [Parameter(Mandatory=$true)][string]$Role,
    [Parameter(Mandatory=$true)][string]$Message,
    [hashtable]$Evidence,
    [string]$RecommendedAction = ''
  )

  $severity = if($Status -eq 'FAIL'){ 'ERROR' } elseif($Status -eq 'WARN'){ 'WARN' } else { 'INFO' }
  $script:checks += [PSCustomObject]@{
    code = $Code
    status = $Status
    severity = $severity
    role = $Role
    message = $Message
    evidence = if($Evidence){ $Evidence } else { @{} }
    recommendedAction = $RecommendedAction
  }
}

function Is-UuidLike {
  param([string]$Value)
  return [regex]::IsMatch(([string]$Value).ToUpper(), '^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$')
}

function Get-MtpChildFolder {
  param($folder, [string]$name)
  if(-not $folder){ return $null }
  foreach($x in $folder.Items()){
    if($x.Name -eq $name){ return $x.GetFolder() }
  }
  return $null
}

function Get-Rc2WaypointUuidFolders {
  $shell = New-Object -ComObject Shell.Application
  $pc = $shell.Namespace('shell:MyComputerFolder')
  $rc = $null
  foreach($i in $pc.Items()){
    if($i.Name -like '*DJI RC 2*'){
      $rc = $i
      break
    }
  }
  if(-not $rc){
    throw "DJI RC 2 not found. Connect RC2 by USB, unlock controller, set USB mode to File Transfer (MTP), then retry."
  }

  $f = $rc.GetFolder()
  $f = Get-MtpChildFolder $f 'Internal shared storage'
  $f = Get-MtpChildFolder $f 'Android'
  $f = Get-MtpChildFolder $f 'data'
  $f = Get-MtpChildFolder $f 'dji.go.v5'
  $f = Get-MtpChildFolder $f 'files'
  $f = Get-MtpChildFolder $f 'waypoint'

  if(-not $f){
    throw "Waypoint folder not found on RC2. Confirm waypoint missions exist in DJI Fly, then retry."
  }

  $set = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach($slot in $f.Items()){
    if($slot.IsFolder -and (Is-UuidLike $slot.Name)){
      [void]$set.Add($slot.Name.ToUpper())
    }
  }
  return $set
}

$script:checks = @()

try {
  Write-StepLog INFO "Step 9 started. Running RC2 mission slot health check."

  $registryDir = Join-Path $root "REGISTRY"
  $rolesPath = Join-Path $registryDir "uuid_roles.json"
  $inventoryPath = Join-Path $registryDir "uuid_inventory.csv"

  if(-not (Test-Path $rolesPath)){
    throw "UUID_ROLES_NOT_FOUND. Run Step 4 first."
  }

  $rolesRaw = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $roleNames = @('Mission_A','Mission_B','Mission_C')
  $roleUuidMap = @{}

  foreach($role in $roleNames){
    $uuid = ([string]$rolesRaw.$role).Trim().ToUpper()
    $roleUuidMap[$role] = $uuid
    if(-not (Is-UuidLike $uuid)){
      Add-Check -Code 'INVALID' -Status 'FAIL' -Role $role -Message "Role $role has invalid UUID in uuid_roles.json." -Evidence @{ uuid = $uuid; rolesPath = $rolesPath } -RecommendedAction "Run Step 4 and assign a valid UUID for $role."
      Write-StepLog ERROR "INVALID: $role UUID is not valid: $uuid"
    } else {
      Add-Check -Code 'OK_ROLE_UUID_FORMAT' -Status 'OK' -Role $role -Message "Role $role UUID format is valid." -Evidence @{ uuid = $uuid }
      Write-StepLog INFO "Role UUID format valid: $role -> $uuid"
    }
  }

  # Duplicate detection in role map.
  $uuidGroups = $roleUuidMap.GetEnumerator() |
    Where-Object { Is-UuidLike $_.Value } |
    Group-Object -Property Value

  foreach($g in $uuidGroups){
    if($g.Count -gt 1){
      $dupRoles = @($g.Group | ForEach-Object { $_.Key })
      foreach($dupRole in $dupRoles){
        Add-Check -Code 'DUPLICATE' -Status 'FAIL' -Role $dupRole -Message "Duplicate UUID assigned across roles: $($g.Name)." -Evidence @{ uuid = $g.Name; roles = $dupRoles } -RecommendedAction "Run Step 4 and assign unique UUID values per role."
      }
      Write-StepLog ERROR "DUPLICATE UUID detected: $($g.Name) used by $($dupRoles -join ', ')"
    }
  }

  # Inventory checks.
  $inventoryUuidSet = New-Object 'System.Collections.Generic.HashSet[string]'
  if(Test-Path $inventoryPath){
    $inventoryRows = Import-Csv $inventoryPath
    foreach($row in $inventoryRows){
      $invUuid = ([string]$row.UUID).Trim().ToUpper()
      if(Is-UuidLike $invUuid){ [void]$inventoryUuidSet.Add($invUuid) }
    }
    Write-StepLog INFO "Loaded inventory UUID count: $($inventoryUuidSet.Count)"
  } else {
    Add-Check -Code 'MISSING_INVENTORY' -Status 'WARN' -Role 'GLOBAL' -Message "uuid_inventory.csv not found." -Evidence @{ inventoryPath = $inventoryPath } -RecommendedAction "Run Step 3 to refresh inventory before health check."
    Write-StepLog WARN "Inventory file missing: $inventoryPath"
  }

  foreach($role in $roleNames){
    $uuid = $roleUuidMap[$role]
    if(-not (Is-UuidLike $uuid)){ continue }

    if($inventoryUuidSet.Count -gt 0){
      if($inventoryUuidSet.Contains($uuid)){
        Add-Check -Code 'OK_INVENTORY_MATCH' -Status 'OK' -Role $role -Message "$role UUID is present in uuid_inventory.csv." -Evidence @{ uuid = $uuid; inventoryPath = $inventoryPath }
      } else {
        Add-Check -Code 'DRIFT' -Status 'WARN' -Role $role -Message "$role UUID is not present in current inventory." -Evidence @{ uuid = $uuid; inventoryPath = $inventoryPath } -RecommendedAction "Run Step 3 and Step 4 to refresh role mapping, then re-run health check."
        Write-StepLog WARN "DRIFT: $role UUID missing from inventory: $uuid"
      }
    }

    $expectedLocal = Join-Path $root ("{0}/{1}.kmz" -f $role, $uuid)
    if(Test-Path $expectedLocal){
      Add-Check -Code 'OK_LOCAL_STAGE' -Status 'OK' -Role $role -Message "Expected staged package exists for $role." -Evidence @{ expectedPath = $expectedLocal }
    } else {
      Add-Check -Code 'MISSING' -Status 'FAIL' -Role $role -Message "Expected staged package is missing for $role." -Evidence @{ expectedPath = $expectedLocal } -RecommendedAction "Run Step5B_StageFromIncoming.ps1 -Role $role to stage a package."
      Write-StepLog ERROR "MISSING staged file: $expectedLocal"
    }
  }

  # Optional live RC2 slot folder check.
  $rc2Checked = $false
  if($CheckRC2){
    try {
      $rc2Checked = $true
      $rc2SlotSet = Get-Rc2WaypointUuidFolders
      Write-StepLog INFO "RC2 slot folder count discovered: $($rc2SlotSet.Count)"

      foreach($role in $roleNames){
        $uuid = $roleUuidMap[$role]
        if(-not (Is-UuidLike $uuid)){ continue }

        if($rc2SlotSet.Contains($uuid)){
          Add-Check -Code 'OK_RC2_SLOT' -Status 'OK' -Role $role -Message "RC2 slot folder exists for mapped UUID." -Evidence @{ uuid = $uuid }
        } else {
          Add-Check -Code 'MISSING' -Status 'FAIL' -Role $role -Message "RC2 slot folder missing for mapped UUID." -Evidence @{ uuid = $uuid } -RecommendedAction "Rescan RC2 (Step 2/3), verify role map (Step 4), and recreate missions if UUID slot no longer exists."
          Write-StepLog ERROR "RC2 slot folder missing for $role UUID: $uuid"
        }
      }
    }
    catch {
      Add-Check -Code 'RC2_CHECK_FAILED' -Status 'WARN' -Role 'GLOBAL' -Message "RC2 live check failed: $($_.Exception.Message)" -Evidence @{} -RecommendedAction "Reconnect/unlock RC2 and rerun with -CheckRC2."
      Write-StepLog WARN "RC2 live check skipped due to error: $($_.Exception.Message)"
    }
  }

  $failCount = @($script:checks | Where-Object { $_.status -eq 'FAIL' }).Count
  $warnCount = @($script:checks | Where-Object { $_.status -eq 'WARN' }).Count
  $okCount = @($script:checks | Where-Object { $_.status -eq 'OK' }).Count

  $overallStatus = if($failCount -gt 0){ 'FAILED' } elseif($warnCount -gt 0){ 'BLOCKED' } else { 'COMPLETE' }

  $report = [ordered]@{
    schemaVersion = '1.0.0'
    reportType = 'rc2-health-check'
    generatedAt = (Get-Date).ToString('s')
    generatedBy = 'Step9_HealthCheck.ps1'
    managerRoot = $root
    inputs = [ordered]@{
      rolesPath = $rolesPath
      inventoryPath = $inventoryPath
      rc2LiveCheckRequested = [bool]$CheckRC2
      rc2LiveCheckAttempted = [bool]$rc2Checked
    }
    summary = [ordered]@{
      overallStatus = $overallStatus
      okCount = $okCount
      warnCount = $warnCount
      failCount = $failCount
    }
    checks = $script:checks
  }

  $healthDir = Join-Path $registryDir 'health'
  New-Item -ItemType Directory -Force -Path $healthDir | Out-Null
  if([string]::IsNullOrWhiteSpace($OutputPath)){
    $OutputPath = Join-Path $healthDir "step9_healthcheck_$stamp.json"
  }

  $report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $OutputPath
  Write-StepLog INFO "Health report written: $OutputPath"

  Write-Host ""
  Write-Host "Health Check Summary"
  Write-Host "Overall: $overallStatus"
  Write-Host "OK: $okCount  WARN: $warnCount  FAIL: $failCount"
  Write-Host "Log file: $logFile"
  Write-Host "Report file: $OutputPath"

  $display = $script:checks |
    Select-Object role, code, status, message
  $display | Format-Table -AutoSize

  if($failCount -gt 0){
    Write-Host "[FAILED] Step 9 health check found blocking failures."
    exit 2
  }
  if($FailOnWarning -and $warnCount -gt 0){
    Write-Host "[BLOCKED] Step 9 health check found warnings and -FailOnWarning was set."
    exit 3
  }

  if($warnCount -gt 0){
    Write-Host "[BLOCKED] Step 9 health check completed with warnings."
  } else {
    Write-Host "[SUCCESS] Step 9 health check completed with no warnings or failures."
  }
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 9 failed unexpectedly. See log: $logFile"
  throw
}