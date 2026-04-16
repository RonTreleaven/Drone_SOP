param(
  [ValidateSet('Mission_B','Mission_A','Mission_C')]
  [string]$Role = 'Mission_B',
  [string]$SourceKmz,
  [switch]$ArchiveIncoming,
  [switch]$PruneRoleFolder
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
$incomingDir = Join-Path $root "INCOMING"

function Get-KmzCount {
  param([string]$Path)
  if(-not (Test-Path $Path)){ return 0 }
  return @(Get-ChildItem -Path $Path -File -Filter *.kmz -ErrorAction SilentlyContinue).Count
}

if([string]::IsNullOrWhiteSpace($SourceKmz)){
  if(-not (Test-Path $incomingDir)){
    Write-Host "[BLOCKED] INCOMING folder not found: $incomingDir"
    return
  }

  $latest = Get-ChildItem -Path $incomingDir -File -Filter *.kmz |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

  if(-not $latest){
    $missionACount = Get-KmzCount -Path (Join-Path $root "Mission_A")
    $missionBCount = Get-KmzCount -Path (Join-Path $root "Mission_B")
    $missionCCount = Get-KmzCount -Path (Join-Path $root "Mission_C")
    Write-Host "[INFO] No .kmz files found in INCOMING: $incomingDir"
    Write-Host "[INFO] Current role-folder KMZ counts -> Mission_A: $missionACount, Mission_B: $missionBCount, Mission_C: $missionCCount"
    Write-Host "[BLOCKED] Nothing to stage. Export a mission KMZ to INCOMING and rerun Step5B."
    return
  }

  $SourceKmz = $latest.FullName
}

if(-not (Test-Path $SourceKmz)){
  Write-Host "[BLOCKED] Source KMZ not found: $SourceKmz"
  return
}

$step5Path = Join-Path $PSScriptRoot "Step5.ps1"
if(-not (Test-Path $step5Path)){
  throw "STEP5_NOT_FOUND: $step5Path"
}

. $step5Path

Write-Host "[INFO] Step5B using source: $SourceKmz"
Write-Host "[INFO] Step5B target role: $Role"

if($PruneRoleFolder){
  Invoke-RC2MissionDeploy -Role $Role -SourceKmz $SourceKmz -PruneRoleFolder
}
else {
  Invoke-RC2MissionDeploy -Role $Role -SourceKmz $SourceKmz
}

if($ArchiveIncoming){
  try {
    Move-RC2IncomingToArchive -SourceKmz $SourceKmz -Role $Role
  }
  catch {
    Write-Host "[WARN] ArchiveIncoming skipped: $($_.Exception.Message)"
  }
}

Write-Host "[SUCCESS] Step5B staging completed for role: $Role"
