param(
  [switch]$CheckRC2,
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
$logFile = Join-Path $logRoot "step10_slot_summary_$stamp.log"

function Write-StepLog {
  param([string]$Level, [string]$Message)
  $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  $entry | Add-Content -Path $logFile -Encoding UTF8
  Write-Host $entry
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

function Get-Rc2WaypointFolder {
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
    throw "Waypoint folder not found on RC2."
  }

  return $f
}

function Read-KmzWpmlMetadata {
  param([string]$KmzPath)

  if(-not (Test-Path $KmzPath)){
    return $null
  }

  $tempRoot = Join-Path $env:TEMP ("slotsummary_{0}" -f [guid]::NewGuid().ToString('N'))
  $zipPath = Join-Path $tempRoot "src.zip"
  $extractDir = Join-Path $tempRoot "extract"
  New-Item -ItemType Directory -Force -Path $extractDir | Out-Null

  try {
    Copy-Item $KmzPath $zipPath -Force
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $templatePath = Join-Path $extractDir "wpmz/template.kml"
    $waylinesPath = Join-Path $extractDir "wpmz/waylines.wpml"

    [xml]$template = Get-Content $templatePath -Raw
    $nameNode = $template.kml.Document.SelectSingleNode("*[local-name()='name']")
    $createMs = [string]$template.kml.Document.createTime
    $updateMs = [string]$template.kml.Document.updateTime

    $createTimeLocal = $null
    $updateTimeLocal = $null

    if($createMs -match '^\d+$'){
      $createTimeLocal = [DateTimeOffset]::FromUnixTimeMilliseconds([Int64]$createMs).ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss')
    }
    if($updateMs -match '^\d+$'){
      $updateTimeLocal = [DateTimeOffset]::FromUnixTimeMilliseconds([Int64]$updateMs).ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss')
    }

    $templateHash = if(Test-Path $templatePath){ (Get-FileHash $templatePath -Algorithm SHA256).Hash } else { $null }
    $waylinesHash = if(Test-Path $waylinesPath){ (Get-FileHash $waylinesPath -Algorithm SHA256).Hash } else { $null }

    return [ordered]@{
      kmlName = if($nameNode){ $nameNode.InnerText } else { '' }
      createTimeMs = $createMs
      updateTimeMs = $updateMs
      createTimeLocal = $createTimeLocal
      updateTimeLocal = $updateTimeLocal
      templateHashSha256 = $templateHash
      waylinesHashSha256 = $waylinesHash
    }
  }
  finally {
    if(Test-Path $tempRoot){ Remove-Item $tempRoot -Recurse -Force }
  }
}

try {
  Write-StepLog INFO "Step 10 started. Building role/UUID/KMZ slot summary."

  $rolesPath = Join-Path $root "REGISTRY/uuid_roles.json"
  if(-not (Test-Path $rolesPath)){
    throw "UUID_ROLES_NOT_FOUND. Run Step 4 first."
  }

  $rolesRaw = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $roleNames = @('Mission_A','Mission_B','Mission_C')

  $rc2Waypoint = $null
  $rc2Lookup = @{}
  if($CheckRC2){
    $rc2Waypoint = Get-Rc2WaypointFolder
    foreach($slot in $rc2Waypoint.Items()){
      if($slot.IsFolder -and (Is-UuidLike $slot.Name)){
        $rc2Lookup[$slot.Name.ToUpper()] = $slot.GetFolder()
      }
    }
    Write-StepLog INFO "RC2 slot folders discovered: $($rc2Lookup.Keys.Count)"
  }

  $entries = @()
  foreach($role in $roleNames){
    $uuid = ([string]$rolesRaw.$role).Trim().ToUpper()
    $kmzPath = Join-Path $root ("{0}/{1}.kmz" -f $role, $uuid)

    $exists = Test-Path $kmzPath
    $kmzHash = $null
    $kmzSize = $null
    $kmzLastWrite = $null
    $wpmlMeta = $null

    if($exists){
      $fi = Get-Item $kmzPath
      $kmzHash = (Get-FileHash $kmzPath -Algorithm SHA256).Hash
      $kmzSize = $fi.Length
      $kmzLastWrite = $fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
      $wpmlMeta = Read-KmzWpmlMetadata -KmzPath $kmzPath
    }

    $rc2SlotExists = $null
    $rc2ExpectedFileName = $null
    $rc2ExpectedFilePresent = $null

    if($CheckRC2){
      $rc2ExpectedFileName = if(Is-UuidLike $uuid){ "$uuid.kmz" } else { $null }
      if(Is-UuidLike $uuid -and $rc2Lookup.ContainsKey($uuid)){
        $rc2SlotExists = $true
        $slotFolder = $rc2Lookup[$uuid]
        $present = $false
        foreach($item in $slotFolder.Items()){
          if(-not $item.IsFolder -and $item.Name -eq $rc2ExpectedFileName){
            $present = $true
            break
          }
        }
        $rc2ExpectedFilePresent = $present
      }
      else {
        $rc2SlotExists = $false
        $rc2ExpectedFilePresent = $false
      }
    }

    $entries += [ordered]@{
      role = $role
      uuid = $uuid
      stagedKmzPath = $kmzPath
      stagedKmzExists = $exists
      stagedKmzSizeBytes = $kmzSize
      stagedKmzLastWriteLocal = $kmzLastWrite
      stagedKmzSha256 = $kmzHash
      wpml = $wpmlMeta
      rc2 = if($CheckRC2){
        [ordered]@{
          slotFolderExists = $rc2SlotExists
          expectedFileName = $rc2ExpectedFileName
          expectedFilePresent = $rc2ExpectedFilePresent
        }
      } else { $null }
    }
  }

  $report = [ordered]@{
    schemaVersion = '1.0.0'
    reportType = 'rc2-slot-summary'
    generatedAt = (Get-Date).ToString('s')
    generatedBy = 'Step10_SlotSummary.ps1'
    managerRoot = $root
    inputs = [ordered]@{
      rolesPath = $rolesPath
      checkRC2 = [bool]$CheckRC2
    }
    entries = $entries
  }

  $summaryDir = Join-Path $root "REGISTRY/summary"
  New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null
  if([string]::IsNullOrWhiteSpace($OutputPath)){
    $OutputPath = Join-Path $summaryDir "step10_slot_summary_$stamp.json"
  }

  $report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $OutputPath
  Write-StepLog INFO "Slot summary report written: $OutputPath"

  Write-Host ""
  Write-Host "Slot Summary"
  Write-Host "Report file: $OutputPath"
  Write-Host "Log file: $logFile"
  Write-Host ""

  $display = $entries | ForEach-Object {
    [PSCustomObject]@{
      Role = $_.role
      UUID = $_.uuid
      StagedKmz = $_.stagedKmzExists
      LastWrite = $_.stagedKmzLastWriteLocal
      CreateTime = if($_.wpml){ $_.wpml.createTimeLocal } else { '' }
      WaylinesHash = if($_.wpml){ $_.wpml.waylinesHashSha256.Substring(0,12) } else { '' }
      RC2Slot = if($CheckRC2){ $_.rc2.slotFolderExists } else { $null }
      RC2File = if($CheckRC2){ $_.rc2.expectedFilePresent } else { $null }
    }
  }

  $display | Format-Table -AutoSize

  Write-Host ""
  Write-Host "[SUCCESS] Step 10 slot summary complete."
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 10 failed. See log: $logFile"
  throw
}
