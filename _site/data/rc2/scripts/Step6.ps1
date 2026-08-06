param(
  [ValidateSet('Mission_B','Mission_A','Mission_C')]
  [string[]]$Roles,
  [switch]$SkipMissionC,
  [switch]$IncludeMissionC,
  [switch]$DryRun,
  [switch]$PromptBeforeCopy,
  [int]$InterCopyDelaySeconds = 2
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
$logFile = Join-Path $logRoot "step6_copy_to_rc2_$stamp.log"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Write-StepLog {
  param([string]$Level, [string]$Message)
  $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  $entry | Add-Content -Path $logFile -Encoding UTF8
  Write-Host $entry
}

function Get-MtpChildFolder {
  param($folder, [string]$name)
  if(-not $folder){ return $null }
  foreach($x in $folder.Items()){
    if($x.Name -eq $name){ return $x.GetFolder() }
  }
  return $null
}

function Test-MtpFileExists {
  param($folder, [string]$fileName)
  if(-not $folder){ return $false }
  foreach($x in $folder.Items()){
    if(-not $x.IsFolder -and $x.Name -eq $fileName){
      return $true
    }
  }
  return $false
}

function Get-MtpFileItem {
  param($folder, [string]$fileName)
  if(-not $folder){ return $null }
  foreach($x in $folder.Items()){
    if(-not $x.IsFolder -and $x.Name -eq $fileName){
      return $x
    }
  }
  return $null
}

function Wait-ForMtpFileAbsent {
  param($folder, [string]$fileName, [int]$TimeoutSeconds = 20)
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while((Get-Date) -lt $deadline){
    if(-not (Test-MtpFileExists -folder $folder -fileName $fileName)){
      return $true
    }
    Start-Sleep -Milliseconds 300
  }
  return (-not (Test-MtpFileExists -folder $folder -fileName $fileName))
}

function Wait-ForMtpFile {
  param($folder, [string]$fileName, [int]$TimeoutSeconds = 20)
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while((Get-Date) -lt $deadline){
    if(Test-MtpFileExists -folder $folder -fileName $fileName){
      return $true
    }
    Start-Sleep -Milliseconds 300
  }
  return (Test-MtpFileExists -folder $folder -fileName $fileName)
}

try {
  Write-StepLog INFO "Step 6 started. Preparing mission-slot RC2 copy operation."

  if($Roles -and ($SkipMissionC -or $IncludeMissionC)){
    throw "PARAMETER_CONFLICT. Use either -Roles or -SkipMissionC/-IncludeMissionC, not both."
  }

  if($SkipMissionC -and $IncludeMissionC){
    throw "PARAMETER_CONFLICT. Use either -SkipMissionC or -IncludeMissionC, not both."
  }

  $roleMap = Get-Content $rolesPath -Raw | ConvertFrom-Json
  if($Roles){
    $roleOrder = @()
    foreach($r in $Roles){
      if($r -notin $roleOrder){
        $roleOrder += $r
      }
    }
    Write-StepLog INFO "Explicit role selection requested (-Roles): $($roleOrder -join ', ')"
  }
  else {
    $roleOrder = @("Mission_C", "Mission_B", "Mission_A")
    Write-StepLog INFO "Default timestamp strategy: copying oldest-intended role first (Mission_C -> Mission_B -> Mission_A)."
    if($SkipMissionC){
      $roleOrder = @("Mission_B", "Mission_A")
      Write-StepLog INFO "Mission_C copy skipped for this run by request (-SkipMissionC)."
      Write-Host "[INFO] With Mission_C skipped, timestamp order becomes Mission_B then Mission_A."
    }
    elseif($IncludeMissionC){
      Write-StepLog INFO "-IncludeMissionC specified; Mission_C is already included by default."
    }
  }

  Write-StepLog INFO "Roles selected for copy: $($roleOrder -join ', ')"

  $deployPlan = @()
  foreach($role in $roleOrder){
    $uuid = $roleMap.$role
    if(-not $uuid -or $uuid -notmatch '^[0-9A-F-]{36}$'){
      throw "Invalid UUID for role $role in uuid_roles.json"
    }

    $localFile = Join-Path $root ("{0}/{1}.kmz" -f $role, $uuid)
    if(-not (Test-Path $localFile)){
      throw "Missing staged KMZ for ${role}: $localFile. Run Step 5 deploy prep first."
    }

    $deployPlan += [PSCustomObject]@{
      Role = $role
      UUID = $uuid
      LocalFile = $localFile
      TargetName = "$uuid.kmz"
    }
  }

  Write-StepLog INFO "Deploy plan validated: $($deployPlan.Count) role(s)."

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
    throw "DJI RC 2 not found. Connect RC2 by USB, unlock controller, set USB mode to File Transfer (MTP), then retry Step 6."
  }
  Write-StepLog INFO "RC2 device detected: $($rc.Name)"

  $waypoint = $rc.GetFolder()
  $waypoint = Get-MtpChildFolder $waypoint 'Internal shared storage'
  $waypoint = Get-MtpChildFolder $waypoint 'Android'
  $waypoint = Get-MtpChildFolder $waypoint 'data'
  $waypoint = Get-MtpChildFolder $waypoint 'dji.go.v5'
  $waypoint = Get-MtpChildFolder $waypoint 'files'
  $waypoint = Get-MtpChildFolder $waypoint 'waypoint'

  if(-not $waypoint){
    throw "Waypoint folder not found on RC2. Confirm RC2 mission storage exists, then retry Step 6."
  }
  Write-StepLog INFO "Waypoint folder located on RC2."

  $slotFolders = @{}
  foreach($slot in $waypoint.Items()){
    if($slot.IsFolder -and $slot.Name -match '^[0-9A-F-]{36}$'){
      $slotFolders[$slot.Name.ToUpper()] = $slot.GetFolder()
    }
  }

  if($InterCopyDelaySeconds -lt 0){
    throw "INVALID_DELAY. -InterCopyDelaySeconds must be 0 or greater."
  }

  $copyIndex = 0
  foreach($item in $deployPlan){
    $copyIndex++
    $slotFolder = $slotFolders[$item.UUID.ToUpper()]
    if(-not $slotFolder){
      throw "RC2 slot folder not found for $($item.Role) UUID: $($item.UUID)"
    }

    if($DryRun){
      Write-StepLog INFO "[DRYRUN] $($item.Role) would copy $($item.LocalFile) -> RC2 slot $($item.UUID) as $($item.TargetName)"
      continue
    }

    if($PromptBeforeCopy){
      Write-Host ""
      Write-Host "[PROMPT] Type YES to deploy role(s): $($roleOrder -join ', ')" -ForegroundColor Yellow
      $confirm = (Read-Host "Confirm deploy").Trim()
      if($confirm -ne 'YES'){
        Write-StepLog WARN "Deployment cancelled by user at confirmation prompt."
        Write-Host "[CANCELLED] No files were copied to RC2."
        return
      }
      Write-StepLog INFO "User confirmed deployment (YES)."
      $PromptBeforeCopy = $false
    }

    $srcDir = Split-Path $item.LocalFile -Parent
    $srcName = Split-Path $item.LocalFile -Leaf
    $srcNs = $shell.Namespace($srcDir)
    if(-not $srcNs){ throw "Unable to open source folder: $srcDir" }
    $srcItem = $srcNs.ParseName($srcName)
    if(-not $srcItem){ throw "Unable to resolve source item: $($item.LocalFile)" }

    if(Test-MtpFileExists -folder $slotFolder -fileName $item.TargetName){
      Write-StepLog INFO "Existing RC2 file found for role $($item.Role); removing $($item.TargetName) before copy."
      $existing = Get-MtpFileItem -folder $slotFolder -fileName $item.TargetName
      if(-not $existing){
        throw "Failed to resolve existing RC2 file item for removal: $($item.TargetName)"
      }

      $existing.InvokeVerb('delete')
      if(-not (Wait-ForMtpFileAbsent -folder $slotFolder -fileName $item.TargetName -TimeoutSeconds 20)){
        throw "Timed out waiting for RC2 file deletion before copy: $($item.TargetName)"
      }
      Write-StepLog INFO "Existing RC2 file removed: $($item.TargetName)"
    }

    Write-StepLog INFO "Copying $($item.Role) -> RC2 slot $($item.UUID) as $($item.TargetName)"
    # Option 16 keeps copy non-interactive for replace/yes-to-all behavior.
    $slotFolder.CopyHere($srcItem, 16)

    if(-not (Wait-ForMtpFile -folder $slotFolder -fileName $item.TargetName -TimeoutSeconds 25)){
      throw "Timed out waiting for RC2 file after copy: $($item.TargetName) in slot $($item.UUID)"
    }

    Write-StepLog INFO "RC2 copy confirmed for role $($item.Role)."

    if((-not $DryRun) -and ($copyIndex -lt $deployPlan.Count) -and ($InterCopyDelaySeconds -gt 0)){
      Write-StepLog INFO "Applying inter-copy delay of $InterCopyDelaySeconds second(s) to stabilize RC2 date-sort ordering."
      Start-Sleep -Seconds $InterCopyDelaySeconds
    }
  }

  if($DryRun){
    Write-StepLog INFO "Step 6 DryRun completed. No files were copied."
    Write-Host "Log file: $logFile"
    Write-Host "[PASS] Step 6 DryRun validation checks passed."
    Write-Host "[COMPLETE] DryRun only; RC2 was not modified."
    return
  }

  Write-StepLog INFO "Step 6 completed successfully."
  Write-Host "Log file: $logFile"
  Write-Host "[PASS] Step 6 validation checks passed."
  Write-Host "[SUCCESS] Step 6 completed successfully."
  Write-Host "[COMPLETE] RC2 slot copies applied for mission slots: $($roleOrder -join ', ')"
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 6 failed. See log: $logFile"
  throw
}
