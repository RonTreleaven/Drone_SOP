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
$logDir = if($config.logRoot) { $config.logRoot } else { Join-Path $root "LOGS" }
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ("step2_detect_rc2_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

function Write-StepLog {
  param(
    [string]$Level,
    [string]$Message
  )
  $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  Add-Content -Path $logFile -Value $line
  Write-Host $line
}

function Get-MtpChildFolder {
  param($folder, [string]$name)
  if(-not $folder){ return $null }
  foreach($x in $folder.Items()){
    if($x.Name -eq $name){ return $x.GetFolder() }
  }
  return $null
}

try {
  Write-StepLog INFO "Step 2 started. Looking for DJI RC 2 device in This PC."

  $s = New-Object -ComObject Shell.Application
  $pc = $s.Namespace('shell:MyComputerFolder')
  $rc = $null
  foreach($i in $pc.Items()){
    if($i.Name -like '*DJI RC 2*'){
      $rc = $i
      break
    }
  }

  if(-not $rc){
    throw "DJI RC 2 was not found. Connect RC2 by USB, unlock the controller, set USB mode to File Transfer (MTP), then run Step 2 again."
  }
  Write-StepLog INFO "RC2 device detected: $($rc.Name)"

  $f = $rc.GetFolder()
  $f = Get-MtpChildFolder $f 'Internal shared storage'
  $f = Get-MtpChildFolder $f 'Android'
  $f = Get-MtpChildFolder $f 'data'
  $f = Get-MtpChildFolder $f 'dji.go.v5'
  $f = Get-MtpChildFolder $f 'files'
  $f = Get-MtpChildFolder $f 'waypoint'

  if(-not $f){
    throw "Waypoint folder not found on RC2. Go outdoors, connect the aircraft, confirm the Home Point, save at least one waypoint mission in DJI Fly, reconnect RC2, then retry Step 2."
  }

  $slots = @()
  foreach($it in $f.Items()){
    if($it.IsFolder -and $it.Name -match '^[0-9A-F-]{36}$'){
      $slots += $it.Name
    }
  }

  $slots = $slots | Sort-Object
  if(($slots | Measure-Object).Count -eq 0){
    Write-StepLog WARN "No UUID slots found. Connect aircraft outdoors, confirm Home Point, then create and save at least one waypoint mission in DJI Fly first."
  } else {
    Write-StepLog INFO ("Found {0} UUID slot(s)." -f (($slots | Measure-Object).Count))
  }

  foreach($slot in $slots){
    Write-StepLog INFO "UUID slot: $slot"
  }

  Write-StepLog INFO "Step 2 completed successfully."
  Write-Host "Log file: $logFile"
  Write-Host "[PASS] Step 2 validation checks passed."
  Write-Host "[SUCCESS] Step 2 completed successfully."
  $slots
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "Step 2 failed. See log: $logFile"
  throw
}