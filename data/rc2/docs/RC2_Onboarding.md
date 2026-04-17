# RC2_Onboarding

## What This Is
This guide helps a drone pilot set up a safe DJI RC2 UUID workflow on Windows.  Apple IOS does not support MTP protocol. Android devices do support MTP, but these procedures currently work on Windows, using native PowerShell, which for Windows 10/11+ versions.  

## Use these procedures to:

- Discover DJI RC2 UUID slots, connected to PC with controller turned on.
- Assign Mission A, Mission B, and Mission C slots to DJI UUID indexes, in order to upload your  mission.kmz package and exported from Gcode Tools. 
- Deploy DJI UUID mission packages as .kmz into matching RC2 slots safely.  

Standard mission package extension in this SOP: `.kmz`


## Alternate Manual approach.

There are many good YouTube videos, in which to do similar hacks of pre-planning a flight path, or orbits that Gcode currently has tested.



## Profile Files In /RC2_Missions/REGISTRY

Use of these profile export names are saved as:
- `DroneSOP_user.json` (My Profile)
- `DroneSOP_Adv.json` (Mission Automation / Advanced Profile)

Recommended save target:
- `RC2_Missions/REGISTRY/`

If `REGISTRY/local_config.json` has `"workspaceRoot": "C:\\Users\\<username>\\RC2_Missions"` (example), verify both files are present under that root's `REGISTRY` folder after creation of your User/Advanced profiles on this website.



## Beginner Mode vs Quick Mode

- Beginner Mode: step-by-step with explanation.
- Quick Mode: short command sequence once your setup is stable.



## Core Safety Rules

1. Keep local mission files organized so slot assignments stay clear and easy to refresh.
2. Create, inventory, and assign three distinct RC2 UUID slots to Mission A, Mission B, and Mission C before staging or copying mission files.
3. Keep timestamped backups before each slot change.
4. Keep a local UUID map file so slot roles never become guesswork.

* { see /Registry/slot_scan/yyyymmdd_hhmmss/***.kmz }

## Slot Strategy (Mission A / Mission B / Mission C)

Use 3 existing RC2 UUID slots and keep them stable:
- Mission A: mission used for primary operations.
- Mission B: staging and validation slot.  
- Mission C: fully functional third slot you can load and use like the others.

Rename policy (depends on slot mode):
- Local archive filenames can be descriptive (example: `Bridge_Inspection_v4.kmz`).
- RC2 deployed filename should be normalized to `<UUID>.kmz` for the slot target.

## Prerequisites
- Windows PC
- USB cable connected DJI RC2 (MTP visible in This PC)
- PowerShell 5.1+
- Ability to create and save 3 simple waypoint missions in DJI Fly on the RC2
  

  Your Windows PC to RC2 Controller 

  > DJI RC 2\Internal shared storage\Android\data\dji.go.v5\files\waypoint\*.kmz



## Before You Start

Before creating the first 3 RC2 waypoint missions, the user should establish a valid map context in DJI Fly.

This document used the DJI Mini Pro 4 and an RC2 controller with screen for testing.  Adding models that will be tested with these methods.

Mavic 4 Pro, Air 3S, Mini Pro 5?



## Beginner Readiness Tracker

Use this checklist before moving into the scripted steps.

- [x] RC2 is charged and powered on.
- [x] Aircraft battery is installed and aircraft powers on.
- [x] RC2 is connected to the aircraft.
- [x] RC2 and aircraft were taken outdoors for GNSS lock.
- [x] DJI Fly Camera View opens correctly.
- [x] Home Point was updated or confirmed.
- [x] The map centers on the real operating area.
- [x] Three simple waypoint missions were created and saved in DJI Fly.
- [x] The RC2 was then connected to the PC by USB.
- [x] The RC2 is unlocked and visible in Windows.
- [x] USB mode is set to File Transfer (MTP) if prompted.

Use this status language in the document and in future scripts:
- `READY`: user completed the checkpoint successfully.
- `BLOCKED`: user cannot continue until a prerequisite is fixed.
- `FAILED`: the script ran but hit an error.
- `COMPLETE`: the step finished successfully.


Recommended self-training style, use gates:

- If any checklist item is not complete, stop and fix it before running the next PowerShell step.
  

Preferred method:
1. Take the RC2 and aircraft outdoors.
2. Power on the RC2 and aircraft and connect to the aircraft.
3. Open DJI Fly and enter Camera View.
4. Wait for GNSS position to stabilize. 
5. Update or confirm the Home Point.
6. Confirm the map now centers on the your surrounding operating area.  * you can do this without, but the maps are small and being familiar with how to create/modify missions is a good skill to practice, if designing automated flight patterns.
7. You must "Create" and save 3 simple waypoint missions.  
   (user may want to delete any stored missions with the RC2 controller and Waypoint UI process.  You need to create 3 new slots, that we will map to Mission A, Mission B, Mission C)

Why this matters:
- The first 3 saved waypoint missions create the UUID slot structure used later in this workflow.
- Those 3 saved missions give you the three UUID-backed RC2 slots you will inventory and assign to Mission A, Mission B, and Mission C.
- Without a valid Home Point or usable map position, creating that first mission is awkward and error-prone.

What new users should know:
- DJI Fly does not usually expose a simple "set arbitrary user location" control for manual latitude/longitude entry as a controller location override. You have to manipulate a small world map, multiple times to match your location.  
- In practice, the most reliable way to center the map is to connect the aircraft and let DJI Fly use aircraft GNSS and the updated Home Point.
- A user may still be able to manually pan/search the map, but that is a fallback, not the preferred beginner workflow.

Beginner checkpoint:
- Do not continue to Step 2 until <u>3 waypoint missions</u> have been saved in DJI Fly.
- If the map is still showing the whole world, go back outdoors, reconnect aircraft, confirm GNSS and Home Point, then retry.
  

## Logging Standard For Future Scripts
Every future PowerShell step script should follow the same simple pattern:

1. Start a timestamped log file in the user's `LOGS` folder.
2. Record the step number and script name.
3. Log each major checkpoint as `INFO`, `WARN`, or `ERROR`.
4. Print a plain-language next action when blocked.
5. End with a final state of `COMPLETE`, `BLOCKED`, or `FAILED`.

Recommended checkpoints to log for each script:
- User environment loaded.
- Required config file found.
- Required device or folder found.
- Main action started.
- Main action completed.
- Output file written.
- Final status.

Recommended beginner-facing output style:
- `INFO: Step 2 started.`
- `INFO: RC2 detected.`
- `WARN: Fewer than 3 UUID slots found yet.`
- `BLOCKED: Save 3 waypoint missions in DJI Fly, then rerun Step 2.`
- `COMPLETE: Step 2 finished. Log saved to ...`

## 1) First-Run Setup (User-Specific Workspace)
Run this once. It detects the current user home directory and creates a unique workspace.

Primary script for Step 1:
- `Dev\RC2 UUID PowerShell\Step1.ps1`

First-time install note:
- If you renamed or deleted an older `RC2_Missions` folder but still have `rc2_missions_config_path.txt` in your Windows profile, Step 1 may detect an existing setup.
- In that case, choose `O` to refresh config files and re-assert the folder structure for the new root.
- Choose `A` only if the detected root and config are already correct and you want no changes.

Step 1 objective:
- Create the user's local `RC2_Missions` workspace.
- Create the required working folders.
- Save the config file and config pointer for later scripts.

Step 1 is `READY` when:
- The user has PowerShell open.
- The user knows whether to accept the default path or enter a custom path.

Step 1 is `COMPLETE` when:
- The `RC2_Missions` root folder exists.
- The `INCOMING`, `ARCHIVE`, `BACKUPS`, `LOGS`, `Mission_A`, `Mission_B`, `Mission_C`, and `REGISTRY` folders exist.
- `local_config.json` exists in `REGISTRY`.
- `rc2_missions_config_path.txt` exists in the user profile.

Step 1 is `BLOCKED` if:
- PowerShell cannot create folders in the selected path.
- The config file cannot be written.
- The config pointer cannot be written.

Step 1 expected user-facing result:
- `Workspace ready: ...`
- `Config saved: ...`
- `Config pointer saved: ...`
- `[PASS] Step 1 validation checks passed.`
- `[SUCCESS] Step 1 completed successfully.`

```powershell
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
```

What each folder is for:
- `INCOMING`: new exports to be processed.
- `Mission_B`: files prepared for testing and validation.
- `Mission_A`: files prepared for production deployment.
- `Mission_C`: files prepared for the third active mission slot.
- `BACKUPS`: local timestamped backup snapshots created during staging or seeding.
- `LOGS`: step-by-step run logs and error logs.
- `REGISTRY`: UUID role mapping, inventory CSV files, slot-scan exports, audit logs, and saved pilot profile JSON files.
- `ARCHIVE`: historical mission packages.

Profile note:
- `index.html` supports two modes:
  1. Standard profile mode: saves locally in browser storage and export/import JSON only.
  2. Mission Automation Profile mode (optional): requires a valid `RC2_Missions` root and writes a personalized profile JSON into `REGISTRY/profile/`.
- If Mission Automation Profile is enabled but required RC2 folders are missing, profile save shows an error and stays open until Step 1 folder setup is complete.

## Current Function Linkage (Web To PowerShell)

Mission Automation Manager linkage:
- Load UUID Roles reads REGISTRY/uuid_roles.json and fills Mission A/B/C UUID slot fields.
- Supports selecting either RC2_Missions root or REGISTRY directly.
- Loaded role map is cached in dsop.uuidRolesRegistry.v1 for downstream GGCode checks.

GGCode linkage:
- Default GGCode Export Slot resolves from dsop.missionAutomationProfile.v1 defaultExportSlot.
- Profile Slot mode UUID resolves from rc2UuidMissionA/B/C in the same profile state.
- KMZ export preflight checks selected Profile Slot UUID against dsop.uuidRolesRegistry.v1.
- On mismatch, export is blocked and user is directed to reload UUID roles in MAM.

PowerShell linkage:
- Step5B_StageFromIncoming uses newest INCOMING .kmz when source is not specified.
- Step5 Invoke-RC2MissionDeploy normalizes role package filename to <UUID>.kmz using REGISTRY/uuid_roles.json.
- Step6 copies staged role packages to RC2 waypoint UUID folders and verifies copy completion.

Health-check intent (next enhancement):
- Compare dsop.uuidRolesRegistry.v1, local REGISTRY/uuid_roles.json, and current RC2 slot inventory.
- Report per role as OK, MISSING, DRIFT, DUPLICATE, or INVALID before Step6.

Step 9 health-check script (current):
- Dev/RC2 UUID PowerShell/Step9_HealthCheck.ps1
- Schema: Dev/RC2 UUID PowerShell/Step9_HealthCheck.report.schema.json

Recommended pre-Step6 operator sequence:

```powershell
# 1) Stage newest INCOMING package to Mission_B
./data/rc2/scripts/Step5B_StageFromIncoming.ps1 -Role Mission_B -ArchiveIncoming

# 2) Run health check (local + RC2)
./data/rc2/scripts/Step9_HealthCheck.ps1 -CheckRC2 -FailOnWarning

# 3) Copy only validated slot
./data/rc2/scripts/Step6.ps1 -Roles Mission_B
```

## 2) Discover RC2 Waypoint UUID Slots
Connect RC2 and run:

Step 2 objective:
- Confirm the local config from Step 1 is valid.
- Confirm the RC2 is connected and visible to Windows.
- Confirm the DJI waypoint folder exists.
- Enumerate UUID slot folders and log the result.

Step 2 depends on Step 1:
- Do not run Step 2 until Step 1 is `COMPLETE`.

Step 2 is `READY` when:
- The Beginner Readiness Tracker is complete.
- The RC2 is connected to the PC by USB.
- The controller is unlocked and visible in Windows.
- 3 waypoint missions have already been saved in DJI Fly.

Step 2 is `COMPLETE` when:
- The script finds the RC2.
- The script reaches the waypoint folder.
- A timestamped Step 2 log file is created.
- UUID slot names are returned or a clear warning is logged if none exist yet.

Step 2 is `BLOCKED` if:
- The Step 1 config pointer is missing.
- The RC2 is not connected or not visible in Windows.
- The controller is locked or not in File Transfer mode.
- Fewer than 3 waypoint missions were saved, so there are not enough UUID slots to assign Mission A, Mission B, and Mission C.

Step 2 is `FAILED` if:
- The script starts correctly but hits an unexpected PowerShell, COM, file, or parse error.

Step 2 expected user-facing result:
- `INFO: Step 2 started.`
- `INFO: RC2 detected.`
- `INFO: Found X UUID slot(s).`
- or `BLOCKED: Save 3 waypoint missions in DJI Fly, then rerun Step 2.`
- `COMPLETE: Step 2 finished. Log saved to ...`

```powershell 
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
    throw "Waypoint folder not found on RC2. Go outdoors, connect the aircraft, confirm the Home Point, save 3 waypoint missions in DJI Fly, reconnect RC2, then retry Step 2."
  }

  $slots = @()
  foreach($it in $f.Items()){
    if($it.IsFolder -and $it.Name -match '^[0-9A-F-]{36}$'){
      $slots += $it.Name
    }
  }

  $slots = $slots | Sort-Object
  if(($slots | Measure-Object).Count -lt 3){
    Write-StepLog WARN "Fewer than 3 UUID slots found. Connect aircraft outdoors, confirm Home Point, then create and save 3 waypoint missions in DJI Fly first."
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
```

Expected result: list of UUID-like folder names.

## 3) Build a UUID Inventory (Date/Time + UUID + Author)

This scans the RC2 waypoint folder, copies each slot KMZ to a run-specific local `REGISTRY/slot_scan/<timestamp>` folder, extracts metadata, and writes `REGISTRY/uuid_inventory.csv` with user-readable date/time fields.
Use these local date/time fields to mirror DJI Fly "Sort by date" behavior for role assignment.

**Step 3 is READY when:**
- [ ] Step 1 COMPLETE â€” `RC2_Missions` workspace and config exist
- [ ] Step 2 COMPLETE â€” at least one UUID slot found on RC2
- [ ] RC2 is still connected by USB, unlocked, in MTP/File Transfer mode

**Step 3 status gates:**

| Status | Condition |
|--------|-----------|
| READY | All checkboxes above cleared |
| COMPLETE | `uuid_inventory.csv` written; table displayed in console |
| BLOCKED | RC2 disconnected mid-scan; waypoint folder unreachable |
| FAILED | Config pointer missing; config unreadable; no UUID slots found during re-scan |

```powershell
# â”€â”€ Step 3: Build UUID Inventory â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Load config
$configPointer = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
if(-not (Test-Path $configPointer)){
  throw "CONFIG_POINTER_NOT_FOUND. Run Step 1 first."
}
$configPath = (Get-Content $configPointer -Raw).Trim()
if(-not (Test-Path $configPath)){
  throw "CONFIG_NOT_FOUND. Run Step 1 again to regenerate local_config.json."
}
$config  = Get-Content $configPath -Raw | ConvertFrom-Json
$root    = $config.managerRoot
$logRoot = $config.logRoot

# â”€â”€ Logging setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logRoot "step3_inventory_$stamp.log"
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

try {
  Write-StepLog INFO "Step 3 started. Scanning RC2 UUID slots for inventory."

  # â”€â”€ Re-connect to RC2 via MTP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  $shell = New-Object -ComObject Shell.Application
  $pc    = $shell.Namespace('shell:MyComputerFolder')
  $rc    = $null
  foreach($i in $pc.Items()){
    if($i.Name -like '*DJI RC 2*'){ $rc = $i; break }
  }
  if(-not $rc){
    throw "DJI RC 2 not found. Connect RC2 by USB, unlock controller, set USB mode to File Transfer (MTP), then retry Step 3."
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
    throw "Waypoint folder not found on RC2. Confirm a mission was saved in DJI Fly, then retry Step 3."
  }
  Write-StepLog INFO "Waypoint folder located on RC2."

  function Wait-ForCopiedFile {
    param(
      [Parameter(Mandatory=$true)][string]$Path,
      [int]$TimeoutSeconds = 15
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastSize = -1
    while((Get-Date) -lt $deadline){
      if(Test-Path $Path){
        $item = Get-Item $Path -ErrorAction SilentlyContinue
        if($item){
          if($item.Length -gt 0 -and $item.Length -eq $lastSize){
            return $true
          }
          $lastSize = $item.Length
        }
      }
      Start-Sleep -Milliseconds 300
    }

    return (Test-Path $Path)
  }

  # â”€â”€ Copy KMZ files to a unique local scan folder for this run â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  $scanRoot = Join-Path $root "REGISTRY/slot_scan"
  $scanDir  = Join-Path $scanRoot $stamp
  New-Item -ItemType Directory -Force -Path $scanDir | Out-Null
  $dest = $shell.Namespace((Resolve-Path $scanDir).Path)

  $copied = 0
  foreach($slot in $f.Items()){
    if($slot.IsFolder -and $slot.Name -match '^[0-9A-F-]{36}$'){
      $sf = $slot.GetFolder()
      foreach($child in $sf.Items()){
        if(-not $child.IsFolder -and $child.Name -eq ($slot.Name + '.kmz')){
          Write-StepLog INFO "Copying KMZ: $($child.Name)"
          $dest.CopyHere($child, 16)
          $targetPath = Join-Path $scanDir $child.Name
          if(-not (Wait-ForCopiedFile -Path $targetPath)){
            throw "Timed out waiting for copied file: $targetPath"
          }
          $copied++
        }
      }
    }
  }

  if($copied -eq 0){
    throw "No KMZ files found in any UUID slot. Save at least one mission in DJI Fly, then retry Step 3."
  }
  Write-StepLog INFO "Copied $copied KMZ file(s) to $scanDir"

  # â”€â”€ Parse metadata from each KMZ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $rows = @()

  Get-ChildItem $scanDir -Filter *.kmz | ForEach-Object {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($_.FullName)
    try {
      $entry = $zip.Entries | Where-Object { $_.FullName -ieq 'wpmz/template.kml' } | Select-Object -First 1
      if(-not $entry){
        $entry = $zip.Entries | Where-Object { $_.FullName -ieq 'wpmz/waylines.wpml' } | Select-Object -First 1
      }
      $ct = ''; $ut = ''; $author = ''
      $ctLocal = ''; $utLocal = ''
      if($entry){
        $sr  = New-Object System.IO.StreamReader($entry.Open())
        $txt = $sr.ReadToEnd(); $sr.Close()
        $ct     = [regex]::Match($txt, '<wpml:createTime>(\d+)</wpml:createTime>').Groups[1].Value
        $ut     = [regex]::Match($txt, '<wpml:updateTime>(\d+)</wpml:updateTime>').Groups[1].Value
        $author = [regex]::Match($txt, '<wpml:author>([^<]+)</wpml:author>').Groups[1].Value
        if($ct){
          try { $ctLocal = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$ct).ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss') } catch {}
        }
        if($ut){
          try { $utLocal = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$ut).ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss') } catch {}
        }
      }
      $rows += [PSCustomObject]@{
        UUID          = $_.BaseName
        FileLastWriteLocal = $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
        CreateTimeLocal = $ctLocal
        UpdateTimeLocal = $utLocal
        CreateTimeMs  = $ct
        UpdateTimeMs  = $ut
        Author        = $author
        File          = $_.Name
      }
      Write-StepLog INFO "Parsed: $($_.BaseName) | fileDate=$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')) | author=$author"
    }
    finally { $zip.Dispose() }
  }

  # â”€â”€ Write inventory CSV â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  $invPath = Join-Path $root "REGISTRY/uuid_inventory.csv"
  $rows | Sort-Object FileLastWriteLocal -Descending |
    Export-Csv -NoTypeInformation -Path $invPath
  Write-StepLog INFO "uuid_inventory.csv written: $invPath"

  Write-StepLog INFO "Step 3 completed successfully."
  Write-Host ""
  Write-Host "Log file: $logFile"
  Write-Host "[PASS] Step 3 validation checks passed."
  Write-Host "[SUCCESS] Step 3 completed successfully."
  Write-Host "[COMPLETE] Step 3: UUID inventory saved."
  Write-Host ""
  $rows | Sort-Object FileLastWriteLocal -Descending |
    Format-Table UUID, FileLastWriteLocal, CreateTimeLocal, Author, File -AutoSize
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 3 failed."
  Write-Host "Step 3 failed. See log: $logFile"
  throw
}
```

**Expected output:**
```
[INFO] Step 3 started. Scanning RC2 UUID slots for inventory.
[INFO] RC2 device detected: DJI RC 2
[INFO] Waypoint folder located on RC2.
[INFO] Copying KMZ: exampB32C7AB0-5A9A-4E32-A837-BCB345278710.kmz
[INFO] Copied 1 KMZ file(s) to ...\REGISTRY\slot_scan
[INFO] Parsed: B32C7AB0-5A9A-4E32-A837-BCB345278710 | fileDate=... | author=...
[INFO] uuid_inventory.csv written: ...\REGISTRY\uuid_inventory.csv
[INFO] Step 3 completed successfully.
[COMPLETE] Step 3: UUID inventory saved.

UUID                                 FileLastWriteLocal    CreateTimeLocal      Author  File
----                                 ------------------    ---------------      ------  ----
B32C7AB0-5A9A-4E32-A837-BCB345278710 2026-04-08 09:09:07   2026-04-08 09:09:07  fly     B32C...kmz
```

## 4) Assign Mission A, Mission B, and Mission C UUIDs

This step reads `uuid_inventory.csv`, shows the available UUIDs sorted by local date/time, prompts you for the exact UUID to use for each slot, validates that all three are distinct, and writes `REGISTRY/uuid_roles.json`.

Operator rule for consistency with DJI Fly UI:
- In DJI Fly, set Mission History to `Sort by date`.
- In this script output, use `FileLastWriteLocal` as the matching decision field.

Recommended role selection:
- `Mission_C`: third working mission slot you want available for loading or testing
- `Mission_B`: validation slot for first controller-side testing
- `Mission_A`: slot you intend to use operationally after testing

```powershell
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
    throw "At least 3 UUIDs are required for Mission A, Mission B, and Mission C. Run Step 3 again after creating more missions."
  }

  Write-StepLog INFO ("Loaded {0} UUID entries from inventory." -f (($inventory | Measure-Object).Count))
  Write-Host ""
  Write-Host "Available UUIDs (newest first, by local file date):"
  $inventory | Format-Table UUID, FileLastWriteLocal, CreateTimeLocal, Author -AutoSize
  Write-Host ""
  Write-Host "Recommended: choose Mission_A for operational use, Mission_B for validation, and Mission_C as the third active slot."
  Write-Host ""

  $allowedUuids = @($inventory.UUID | ForEach-Object { $_.ToUpper() })

  $missionAUuid = Read-RoleUuid -Role "Mission A" -AllowedUuids $allowedUuids
  Write-StepLog INFO "Selected Mission A UUID: $missionAUuid"

  $missionBUuid = Read-RoleUuid -Role "Mission B" -AllowedUuids $allowedUuids -AlreadyUsed @($missionAUuid)
  Write-StepLog INFO "Selected Mission B UUID: $missionBUuid"

  $missionCUuid = Read-RoleUuid -Role "Mission C" -AllowedUuids $allowedUuids -AlreadyUsed @($missionAUuid, $missionBUuid)
  Write-StepLog INFO "Selected Mission C UUID: $missionCUuid"

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
```

## 4A) Milestone: Setup Ready (Gold Source Check)

You are setup and ready when Step 4 is complete and these JSON records are correct.

Why this milestone matters:
- DJI Fly does not natively show your Mission_A / Mission_B / Mission_C role map.
- Your local JSON files are the source of truth for this workflow.
- If these records are wrong, later deploy and copy steps target the wrong slots.

Gold source files to verify:
- `C:\Users\<YourUser>\RC2_Missions\REGISTRY\local_config.json`
- `C:\Users\<YourUser>\RC2_Missions\REGISTRY\uuid_roles.json`

Quick verification (PowerShell):

```powershell
$cfgPtr = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
$cfgPath = (Get-Content $cfgPtr -Raw).Trim()
Write-Host "Config pointer:" $cfgPath
Write-Host ""
Write-Host "local_config.json"
Get-Content $cfgPath
Write-Host ""
Write-Host "uuid_roles.json"
Get-Content (Join-Path ((Get-Content $cfgPath -Raw | ConvertFrom-Json).managerRoot) "REGISTRY/uuid_roles.json")
```

Milestone pass criteria:
- `local_config.json` points to the expected `managerRoot`.
- `uuid_roles.json` contains three valid UUID values for `Mission_A`, `Mission_B`, and `Mission_C`.
- The UUID values match your Step 4 console selections.

Operator note:
- Save mission files you care about before overwriting slots.
- This workflow is built around DJI folder structure and namespace behavior, even though role mapping itself is managed outside the DJI app.

Profile and risk acceptance note:
- The SOP tools are beta workflow tools. Users must read and accept a "use at your own risk" disclaimer before touring tools and procedures in `index.html`.
- Acceptance confirms the user understands Pilot in Command responsibility and accountability always remains with the pilot.
- This acceptance is a required gate to continue, not a replacement for operational judgment, training, or legal compliance.

Suggested profile tiers for user-facing language:
- Casual Explorer: tour tools, review SOP guidance, and inspect examples.
- Basic Operations: local mission planning and non-complex waypoint usage.
- Advanced Operations: more complex mission automation and higher operational discipline.
- BVLOS-Oriented Study Mode: planning and learning context only, with strict regulatory and operational controls.

My Profile and Advanced Access gating:
- `My Profile` in `index.html` should remain the primary identity and readiness checkpoint for feature access.
- Advanced tooling should require an additional explicit gate beyond basic acceptance, to reduce careless use.
- That advanced gate should confirm the user understands public safety obligations, regulatory boundaries, and operational responsibility before access is granted.
- Current validation rule in the UI: `Profile Usage Mode = Workspace Reuse` + eligible profile fields + Advanced Access acknowledgment checked.
- The `Use Mission Automation Structure` checkbox should unlock once the above conditions are met.
- `DroneSOP_Adv.json` export is not a prerequisite for unlocking; it is an output after advanced access is unlocked.

Validation and finalization checkpoints:
- Validated: profile summary shows advanced access as ready, and Mission Automation controls become selectable.
- Finalized (browser side): `DroneSOP_user.json` and optional `DroneSOP_Adv.json` are exported and archived in `RC2_Missions/REGISTRY/`.
- Finalized (RC2 side): Step 5 staging and Step 6 copy complete, then DJI Fly mission load check passes.

Platform compatibility:
- Mission Automation Manager and RC2 slot replacement workflow are Windows-first operations.
- iOS/iPadOS can be used for planning/profile work, but are not compatible with direct RC2 MTP copy operations.
- If using iOS/iPadOS, treat profile and KMZ export as handoff artifacts for later Windows execution.

Cloud and external storage fallback (worst case):
- A user can save the mission `.kmz` and profile JSON files to cloud/external storage.
- A Windows operator can later retrieve those files, run onboarding checks, and perform RC2 waypoint slot replacement through the standard Step 5/Step 6 path.

Recommended advanced-readiness checks:
- User affirms Pilot in Command accountability.
- User confirms awareness of applicable Transport Canada rules for their operation class.
- User confirms they will validate mission intent, airspace context, and safety constraints before field execution.
- User confirms they understand these tools assist planning and do not replace legal or operational judgment.

Canadian operations note:
- Micro drones may feel low risk, but risk and accountability increase quickly for Basic, Advanced, and BVLOS-oriented operations.
- Users should align all operations with current Transport Canada requirements and applicable Canadian standards.
- The goal of this tooling is to support safer automated workflows and community best practices, not to override regulatory obligations.

## 5) Deploy Function (Safe Copy with Auto Backup)
This function:
- loads UUID role map
- normalizes your input `.kmz` into the local mission-slot folder as `<UUID>.kmz`
- creates a timestamped local backup snapshot under `BACKUPS/<Role>/<timestamp>`

This step prepares the local staged package. It does not copy to the RC2 by itself.

First-time seeding note (recommended):
- Use `Dev\RC2 UUID PowerShell\Step5A.ps1` after Step 4.
- Step 5A reads `REGISTRY/uuid_roles.json`, finds your latest `REGISTRY/slot_scan/<timestamp>` folder (or a folder you pass), and seeds local slot files automatically.
- This gives Step 6 valid local staged files before the first controller copy.

Step 5A usage:

```powershell
# Seed Mission_A, Mission_B, and Mission_C from latest slot_scan folder
./data/rc2/scripts/Step5A.ps1

# Optional: seed only Mission_A and Mission_B
./data/rc2/scripts/Step5A.ps1 -SkipMissionC

# Optional: force overwrite existing seeded files
./data/rc2/scripts/Step5A.ps1 -Force

# Optional: seed from a specific scan folder
./data/rc2/scripts/Step5A.ps1 -ScanFolder "20260409_175733"
```

```powershell
function Invoke-RC2MissionDeploy {
  param(
    [Parameter(Mandatory=$true)][ValidateSet('Mission_B','Mission_A','Mission_C')] [string]$Role,
    [Parameter(Mandatory=$true)] [string]$SourceKmz
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

  "Prepared local deploy package: $normalized"
  "Pre-deploy backup created: $backupDir"
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
```

Note: `Invoke-RC2MissionDeploy` and `Initialize-RC2MissionSlotSeed` prepare local role packages and backup copies only. RC2 MTP copy is handled by Step 6.

## 6) RC2 Copy to Controller
Primary script for Step 6:
- `Dev\RC2 UUID PowerShell\Step6.ps1`

This step copies the currently staged local role packages to the matching RC2 UUID slot folders over MTP.

Default behavior:
- Copies `Mission_B`, `Mission_A`, and `Mission_C`
- To copy only Mission_B and Mission_A, run `Step6.ps1 -SkipMissionC`
- To copy only one role (recommended for Mission_B validation), run `Step6.ps1 -Roles Mission_B`

Step 6 reads from your local staged files:
- `Mission_B/<Mission_B_UUID>.kmz`
- `Mission_A/<Mission_A_UUID>.kmz`
- `Mission_C/<Mission_C_UUID>.kmz`

When `-Roles` is used, Step 6 reads and copies only the selected role(s).

Important first-run behavior:
- `Step6.ps1` expects local staged files for Mission_B, Mission_A, and Mission_C by default.
- On a new install, seed those local role files first with `Initialize-RC2MissionSlotSeed` before using Step 6.

## 7) Beginner Deployment Flow
1. Run `Step5A.ps1` once after Step 4 to seed your local role files from the role map and slot scan.
2. Export a new mission `.kmz` into your local RC2 missions workspace under your configured `managerRoot`.
  Preferred manual export location: `INCOMING`.
    Folder export option: save directly into `Mission_A`, `Mission_B`, or `Mission_C` only when filename and target role UUID are confirmed.

Operator decision table (export save location):

| Option | Save location | Use when | Required controls |
| --- | --- | --- | --- |
| Standard staging | `<managerRoot>/INCOMING` | Default for all users and all test runs | Run Step 5 deploy prep to normalize to role UUID before Step 6 |
| Direct role-folder save | `<managerRoot>/Mission_A`, `Mission_B`, or `Mission_C` | Advanced users with confirmed role map and UUID naming | Filename must be exact assigned UUID (`<UUID>.kmz`) and must match `REGISTRY/uuid_roles.json` |

3. Load Step 5 functions in the current PowerShell session.
4. Run `Invoke-RC2MissionDeploy -Role Mission_B -SourceKmz "<path to incoming kmz>"`.
5. Run `Step6.ps1 -Roles Mission_B` to copy only the staged Mission B package to the RC2 for first validation.
6. Archive the processed INCOMING file so INCOMING does not accumulate old exports:
  - `Move-RC2IncomingToArchive -SourceKmz "<incoming file path>" -Role Mission_B`
7. Validate Mission B in DJI Fly first.
8. If valid, run `Invoke-RC2MissionDeploy -Role Mission_A -SourceKmz "<path to incoming kmz>"` and run `Step6.ps1 -Roles Mission_A`.
9. Refresh Mission C whenever you want a third active slot loaded on the controller.

Automated staging shortcut (recommended for new users):
- Instead of manually loading Step 5 and calling functions, run one command:
  - `./data/rc2/scripts/Step5B_StageFromIncoming.ps1 -Role Mission_B -ArchiveIncoming`
- This stages the newest `INCOMING` mission file to Mission_B and archives the processed INCOMING file.

Profile Slot UUID note (GGCode export):
- `Profile Slot UUID` naming mode reads UUID values from the browser profile state, not directly from `uuid_roles.json`.
- After Step 4 remaps roles, verify the exported filename still matches the current role UUID in `REGISTRY/uuid_roles.json`.
- If export still uses an old UUID, update the profile slot UUID values in My Profile, or use UUID Slot mode and paste the current role UUID.
- If saving directly to `Mission_A`, `Mission_B`, or `Mission_C`, keep the export filename as the assigned role UUID (`<UUID>.kmz`) to preserve slot integrity.

After Export (Profile Slot UUID) - required user actions:
1. Save the `.kmz` to `<managerRoot>/INCOMING`.
2. Read target role UUID from `REGISTRY/uuid_roles.json` (example: Mission_B).
3. Compare exported filename UUID to target role UUID.
4. If mismatch, continue using Step 5 deploy prep (it normalizes to the role UUID) and record mismatch in run notes.
5. Stage to selected role:
  - `Invoke-RC2MissionDeploy -Role Mission_B -SourceKmz "<incoming file path>"`
6. Copy only selected role to RC2 for validation:
  - `Step6.ps1 -Roles Mission_B`
7. Archive processed INCOMING source file:
  - `Move-RC2IncomingToArchive -SourceKmz "<incoming file path>" -Role Mission_B`
8. Validate mission on RC2 before promoting to Mission_A.

Role-folder hygiene (non-cumulative):
- To keep only the active `<RoleUUID>.kmz` in a role folder, run:
  - `Invoke-RC2RoleFolderCleanup -Role Mission_B`
- Extra `.kmz` files are moved to `ARCHIVE/<Role>/cleanup_<timestamp>/`.

RC2 mission list ordering caveat:
- RC2 list order can remain tied to UUID slot chronology and may not reorder after a fresh `.kmz` copy.
- Validate success by slot UUID mapping and mission content, not list position alone.

MVP session note:
- For a first new-user walkthrough, Steps 1 through 8 are the critical path.
- Treat Step 9 and beyond as optional follow-on material to evaluate after the core slot workflow is proven.

## 8) Quick Mode (Experienced Users)
```powershell
$cfgPtr = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
$cfgPath = (Get-Content $cfgPtr -Raw).Trim()
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$incoming = Join-Path $cfg.managerRoot "INCOMING/new_mission.kmz"
. "./data/rc2/scripts/Step5.ps1"
Invoke-RC2MissionDeploy -Role Mission_B -SourceKmz $incoming
Invoke-RC2MissionDeploy -Role Mission_A -SourceKmz $incoming
& "./data/rc2/scripts/Step6.ps1"
```

## 9) Recovery Procedure (Fallback)
This section is optional and not part of the MVP first-run path.

If Mission B or Mission A mission fails:
1. Stop further deployments.
2. Select another usable mission package from your local staged files or `BACKUPS` folder under your configured `managerRoot`.
3. Stage the fallback file explicitly to the affected role.
4. Run the RC2 copy step to apply the staged package to the controller.
5. Reopen DJI Fly and verify mission availability.

### Step 8 Scripted Restore (LastKnownGood -> Mission B or Mission A)
Use the dedicated restore script:

```powershell
# Prepare LastKnownGood fallback package for Mission B
./data/rc2/scripts/Step8_RestoreFallback.ps1 -TargetRole Mission_B

# Prepare LastKnownGood fallback package for Mission A
./data/rc2/scripts/Step8_RestoreFallback.ps1 -TargetRole Mission_A

# Optional: prepare Mission C itself from another known-good file
./data/rc2/scripts/Step8_RestoreFallback.ps1 -TargetRole Mission_C -SourceFallbackKmz "<full path to known-good fallback kmz>"
```

Optional source override (if restoring from a specific backup file):

```powershell
./data/rc2/scripts/Step8_RestoreFallback.ps1 -TargetRole Mission_B -SourceFallbackKmz "<full path to known-good fallback kmz>"
```

Restore behavior:
1. Loads your role map from `REGISTRY/uuid_roles.json`.
2. Uses `Mission_C/<Mission_C_UUID>.kmz` by default if you do not provide another source KMZ.
3. Writes a local restore package to the selected target slot with normalized `<TargetRoleUUID>.kmz` naming.
4. Logs PASS/SUCCESS/FAILED status to `LOGS/step8_restore_fallback_*.log`.
5. Leaves Mission C available as a normal reusable mission slot.
6. Requires Step 6 afterward if you want the restored local package copied onto the RC2.

## 10) New User Validation Checklist
- RC2 detected by Windows and waypoint folder reachable.
- UUID inventory generated successfully.
- UUID role map file exists and has three valid UUIDs.
- Mission B staged and validated before Mission A promotion.
- Step 6 used to apply staged local packages to RC2.
- Mission C can be loaded and used as a normal third slot when needed.
- Local staged mission files remain organized enough to recreate or replace a slot quickly.

## 11) Team Notes to Fill In
- RC2 firmware version used:
- DJI Fly app version used:
- Preferred mission naming pattern in `INCOMING`:
- Who approves Mission A promotion:
- Where final slot mapping is stored/shared:

