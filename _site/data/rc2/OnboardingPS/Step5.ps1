function Invoke-RC2MissionDeploy {
  param(
    [Parameter(Mandatory=$true)][ValidateSet('Mission_B','Mission_A','Mission_C')] [string]$Role,
    [Parameter(Mandatory=$true)] [string]$SourceKmz,
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
  $rolesPath = Join-Path $root "REGISTRY/uuid_roles.json"
  if(-not (Test-Path $rolesPath)){ throw "Missing roles file: $rolesPath" }
  if(-not (Test-Path $SourceKmz)){ throw "Source KMZ not found: $SourceKmz" }

  $roles = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $uuid = $roles.$Role
  if(-not $uuid -or $uuid -notmatch '^[0-9A-F-]{36}$'){ throw "Invalid UUID for role $Role" }

  $slotDir = "$root/$Role"
  New-Item -ItemType Directory -Force -Path $slotDir | Out-Null

  $normalized = Join-Path $slotDir ("$uuid.kmz")
  Copy-Item -Path $SourceKmz -Destination $normalized -Force

  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $backupDir = "$root/BACKUPS/$Role/$stamp"
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
  Copy-Item -Path $normalized -Destination (Join-Path $backupDir "$uuid.predeploy.kmz") -Force

  if($PruneRoleFolder){
    $archiveDir = Join-Path $root ("ARCHIVE/{0}/cleanup_{1}" -f $Role, $stamp)
    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

    $extras = Get-ChildItem -Path $slotDir -File -Filter *.kmz |
      Where-Object { $_.Name -ne ("$uuid.kmz") }

    foreach($extra in $extras){
      Move-Item -Path $extra.FullName -Destination (Join-Path $archiveDir $extra.Name) -Force
    }

    "Role folder cleanup archived $($extras.Count) extra KMZ file(s): $archiveDir"
  }

  "Prepared local deploy package: $normalized"
  "Pre-deploy backup created: $backupDir"
}

function Invoke-RC2RoleFolderCleanup {
  param(
    [Parameter(Mandatory=$true)][ValidateSet('Mission_B','Mission_A','Mission_C')] [string]$Role
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
  $rolesPath = Join-Path $root "REGISTRY/uuid_roles.json"
  if(-not (Test-Path $rolesPath)){ throw "Missing roles file: $rolesPath" }

  $roles = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $uuid = $roles.$Role
  if(-not $uuid -or $uuid -notmatch '^[0-9A-F-]{36}$'){ throw "Invalid UUID for role $Role" }

  $slotDir = Join-Path $root $Role
  New-Item -ItemType Directory -Force -Path $slotDir | Out-Null

  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $archiveDir = Join-Path $root ("ARCHIVE/{0}/cleanup_{1}" -f $Role, $stamp)
  New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

  $extras = Get-ChildItem -Path $slotDir -File -Filter *.kmz |
    Where-Object { $_.Name -ne ("$uuid.kmz") }

  foreach($extra in $extras){
    Move-Item -Path $extra.FullName -Destination (Join-Path $archiveDir $extra.Name) -Force
  }

  "Kept active role package: $($uuid).kmz"
  "Archived $($extras.Count) extra KMZ file(s): $archiveDir"
}

function Move-RC2IncomingToArchive {
  param(
    [Parameter(Mandatory=$true)] [string]$SourceKmz,
    [ValidateSet('Mission_B','Mission_A','Mission_C','UNASSIGNED')] [string]$Role = 'UNASSIGNED'
  )

  $configPointer = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
  if(-not (Test-Path $configPointer)){
    throw "CONFIG_POINTER_NOT_FOUND. Run Step 1 first."
  }

  $configPath = (Get-Content $configPointer -Raw).Trim()
  if(-not (Test-Path $configPath)){
    throw "CONFIG_NOT_FOUND. Run Step 1 again to regenerate local_config.json."
  }

  if(-not (Test-Path $SourceKmz)){
    throw "Source KMZ not found: $SourceKmz"
  }

  $config = Get-Content $configPath -Raw | ConvertFrom-Json
  $root = $config.managerRoot
  $incomingDir = (Join-Path $root "INCOMING").TrimEnd('\\')
  $sourceFull = (Resolve-Path $SourceKmz).Path

  if(-not $sourceFull.StartsWith($incomingDir, [System.StringComparison]::OrdinalIgnoreCase)){
    throw "Source is not inside INCOMING: $sourceFull"
  }

  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $archiveDir = Join-Path $root ("ARCHIVE/INCOMING_PROCESSED/{0}_{1}" -f $stamp, $Role)
  New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

  $fileName = Split-Path $sourceFull -Leaf
  $dest = Join-Path $archiveDir $fileName
  Move-Item -Path $sourceFull -Destination $dest -Force

  "Archived INCOMING file: $sourceFull"
  "Archive destination: $dest"
}

function Initialize-RC2MissionSlotSeed {
  param(
    [Parameter(Mandatory=$true)][ValidateSet('Mission_B','Mission_A','Mission_C')] [string]$Role,
    [Parameter(Mandatory=$true)] [string]$SourceKmz,
    [switch]$Force
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
  $rolesPath = Join-Path $root "REGISTRY/uuid_roles.json"
  if(-not (Test-Path $rolesPath)){ throw "Missing roles file: $rolesPath" }
  if(-not (Test-Path $SourceKmz)){ throw "Source KMZ not found: $SourceKmz" }

  $roles = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $uuid = $roles.$Role
  if(-not $uuid -or $uuid -notmatch '^[0-9A-F-]{36}$'){ throw "Invalid UUID for role $Role" }

  $slotDir = Join-Path $root $Role
  New-Item -ItemType Directory -Force -Path $slotDir | Out-Null
  $slotTarget = Join-Path $slotDir ("$uuid.kmz")

  if((Test-Path $slotTarget) -and -not $Force){
    throw "Target already exists for ${Role}: $slotTarget. Use -Force to replace intentionally."
  }

  Copy-Item -Path $SourceKmz -Destination $slotTarget -Force

  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $backupDir = Join-Path $root "BACKUPS/$Role/$stamp"
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
  Copy-Item -Path $slotTarget -Destination (Join-Path $backupDir "$uuid.seed.kmz") -Force

  "Seeded package for ${Role}: $slotTarget"
  "Seed backup created: $backupDir"
}

"[PASS] Step 5 function loaded successfully."
"[SUCCESS] Invoke-RC2MissionDeploy is ready to use."
"[INFO] Initialize-RC2MissionSlotSeed is available to seed Mission_A, Mission_B, or Mission_C."
"[INFO] Invoke-RC2RoleFolderCleanup is available to archive extra role-folder KMZ files."
"[INFO] Move-RC2IncomingToArchive is available to archive processed INCOMING files."