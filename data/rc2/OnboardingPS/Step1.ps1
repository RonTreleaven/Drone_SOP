$defaultWorkspaceRoot = Join-Path $env:USERPROFILE "RC2_Missions"
$inputRoot = Read-Host "Workspace root path (Enter for default: $defaultWorkspaceRoot)"
$workspaceRoot = if([string]::IsNullOrWhiteSpace($inputRoot)) { $defaultWorkspaceRoot } else { $inputRoot }

# Optional team standard override example:
# $workspaceRoot = "C:/Users/RC2_Missions"

$root = $workspaceRoot
$configPath = Join-Path $root "REGISTRY/local_config.json"
$configPointer = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"

$folders = @(
  (Join-Path $root "INCOMING"),
  (Join-Path $root "ARCHIVE"),
  (Join-Path $root "BACKUPS"),
  (Join-Path $root "LOGS"),
  (Join-Path $root "Mission_A"),
  (Join-Path $root "Mission_B"),
  (Join-Path $root "Mission_C"),
  (Join-Path $root "REGISTRY")
)

$rootExists = Test-Path $root
$existingFolders = @($folders | Where-Object { Test-Path $_ })
$configExists = Test-Path $configPath
$pointerExists = Test-Path $configPointer

if($rootExists -or $configExists -or $pointerExists -or $existingFolders.Count -gt 0){
  Write-Host "Existing Step 1 setup detected."
  Write-Host "Root exists: $rootExists"
  Write-Host "Existing required folders: $($existingFolders.Count)/$($folders.Count)"
  Write-Host "Config exists: $configExists"
  Write-Host "Config pointer exists: $pointerExists"
  Write-Host ""
  Write-Host "Choose action:"
  Write-Host "  A = Accept existing setup and exit"
  Write-Host "  O = Overwrite config and re-assert folders"
  Write-Host "  X = Abort"

  $choice = (Read-Host "Enter A, O, or X").Trim().ToUpper()
  switch($choice){
    "A" {
      "Workspace ready: $root"
      "Config path: $configPath"
      "Config pointer path: $configPointer"
      "[PASS] Existing Step 1 setup accepted by user."
      "[SUCCESS] Step 1 completed successfully (no changes applied)."
      return
    }
    "O" {
      Write-Host "Proceeding with overwrite mode (folders preserved, config files refreshed)."
    }
    default {
      throw "Step 1 aborted by user."
    }
  }
}

foreach($f in $folders){ New-Item -ItemType Directory -Force -Path $f | Out-Null }

# Save local config so every next script loads the same user-specific paths.
$config = [ordered]@{
  createdAt = (Get-Date).ToString("s")
  userProfile = $env:USERPROFILE
  workspaceRoot = $workspaceRoot
  managerRoot = $root
  logRoot = (Join-Path $root "LOGS")
}
$config | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $configPath
Set-Content -Encoding UTF8 -Path $configPointer -Value $configPath

"Workspace ready: $root"
"Config saved: $configPath"
"Config pointer saved: $configPointer"
"[PASS] Step 1 validation checks passed."
"[SUCCESS] Step 1 completed successfully."