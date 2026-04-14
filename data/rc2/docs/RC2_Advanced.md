# RC2_Advanced

## Purpose
This SOP explains how to safely manage DJI RC 2 waypoint missions using UUID slots, replace mission payloads with Drone_SOP generated KMZ files, and reduce risk of breaking DJI Fly mission indexing.

## Profile Files In REGISTRY

Use these normalized profile export names:
- `DroneSOP_user.json` (My Profile)
- `DroneSOP_Adv.json` (Mission Automation / Advanced Profile)

Recommended save target:
- `RC2_Missions/REGISTRY/`

Validation:
- Confirm both files exist in `REGISTRY` before UUID role checks and mission slot automation tasks.

## Scope
Use this procedure when:
- You want repeatable mission updates on DJI RC 2.
- You are replacing existing DJI Fly waypoint missions with updated Drone_SOP exports.
- You need to identify active UUID slots and maintain rollback capability.

Do not use this procedure if:
- You are unsure which UUID slot is production.
- You cannot create a backup before replacement.

## Core Concept
DJI Fly stores waypoint missions in UUID-named slots under Android app data. The UUID is effectively the mission key. Keep UUID slot names stable and replace mission content inside the chosen slot.

Recommended slot model:
- PROD: primary slot flown in operations
- TEST: staging slot for validation
- ROLLBACK: known-good last mission

## Prerequisites
- Windows PC with USB-C connection to RC 2
- RC 2 connected and visible in Windows as a portable device (MTP), typically shown like: This PC > DJI RC 2
- Drone_SOP mission KMZ exported and validated
- PowerShell access
- Operator understands backup and restore steps

## Critical Paths on RC 2
Within the RC 2 MTP tree:
- Internal shared storage/Android/data/dji.go.v5/files/waypoint

Inside waypoint folder:
- UUID mission folders (for example 770541D2-304E-4857-921B-168A46F952DA)
- each UUID folder contains:
  - UUID.kmz
  - image/ (preview assets)
- support folders also exist, such as capability and map_preview

## Safety and Risk Controls
- Always backup target UUID slot before replacement.
- Never mass-delete UUID folders without verified backups.
- Keep at least one rollback slot untouched.
- Replace one slot at a time and validate in DJI Fly before next change.
- If DJI Fly behaves unexpectedly, restore previous slot backup immediately.

## Recommended Workflow
1. Create and save at least one DJI-native waypoint mission in DJI Fly (creates valid UUID slot).
2. On PC, locate waypoint UUID folders.
3. Identify target slot (PROD or TEST).
4. Backup target UUID folder/KMZ.
5. Replace target UUID mission content with validated Drone_SOP KMZ payload.
6. Reopen DJI Fly and verify mission loads and previews correctly.
7. Fly TEST slot first, then promote to PROD.

## Can Any Slot Be Used?
Yes. You are not required to use only the newest slot. Any existing UUID slot can be reused consistently.

Best practice:
- Choose fixed slots for PROD/TEST/ROLLBACK.
- Keep the slot identity stable over time.

## RC2 Cleanup Guidance
Goal: keep DJI Fly mission store healthy and understandable.

Suggested cleanup method:
1. Inventory all UUID slots.
2. Classify each as PROD, TEST, ROLLBACK, or RETIRE.
3. Backup all RETIRE slots to PC.
4. Remove only retired slots in small batches.
5. Reopen DJI Fly after each batch and verify mission list integrity.

Map download cleanup:
- Prefer deleting old map cache from within DJI Fly app settings where possible.
- Avoid deleting unknown Android app cache directories manually unless necessary.

## DJI Simulator Question
Can custom injected KMZ missions be flown in simulator?
- Treat as not guaranteed.
- DJI simulator behavior can differ from live mission execution and may not honor all waypoint actions.
- Use simulator for rough logic checks only.
- Final validation must be on aircraft in controlled conditions.

## PowerShell Commands Used in This Session

### 1) Enumerate RC2 waypoint UUID slots via MTP shell namespace  
## Connect the RC2 to the computer before running this script
## Looking for Waypoint_UUID_Slots
## Create a mission on the DJI Fly application first... any mission will do, just save it.
## 

```powershell
$s=New-Object -ComObject Shell.Application
$pc=$s.Namespace('shell:MyComputerFolder')
$rc=$null
foreach($i in $pc.Items()){ if($i.Name -like '*DJI RC 2*'){ $rc=$i; break } }
if(-not $rc){ 'RC2_NOT_FOUND'; exit 1 }
function g($folder,$name){
  if(-not $folder){ return $null }
  foreach($x in $folder.Items()){ if($x.Name -eq $name){ return $x.GetFolder() } }
  return $null
}
$f=$rc.GetFolder()
$f=g $f 'Internal shared storage'
$f=g $f 'Android'
$f=g $f 'data'
$f=g $f 'dji.go.v5'
$f=g $f 'files'
$f=g $f 'waypoint'
if(-not $f){ 'WAYPOINT_FOLDER_NOT_FOUND'; exit 1 }
'WAYPOINT_UUID_SLOTS:'
foreach($it in $f.Items()){
  if($it.IsFolder){ '[DIR] ' + $it.Name } else { '[FILE] ' + $it.Name }
}
```

### 2) List contents of each UUID slot
```powershell
# assumes $f points to waypoint folder from previous script
foreach($slot in $f.Items()){
  if($slot.IsFolder -and $slot.Name -match '^[0-9A-F-]{36}$'){
    '--- ' + $slot.Name + ' ---'
    $sf=$slot.GetFolder()
    foreach($child in $sf.Items()){
      if($child.IsFolder){ '[DIR] ' + $child.Name } else { '[FILE] ' + $child.Name }
    }
  }
}
```

### 3) Copy RC2 slot KMZ files to local workspace for analysis
```powershell
$ErrorActionPreference='Stop'
Set-Location "c:/Users/Ron Treleaven/Drone_SOP"
$outDir = "Dev/rc2_slot_scan"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$dest=$s.Namespace((Resolve-Path $outDir).Path)
foreach($slot in $f.Items()){
  if($slot.IsFolder -and $slot.Name -match '^[0-9A-F-]{36}$'){
    $sf=$slot.GetFolder()
    foreach($child in $sf.Items()){
      if(-not $child.IsFolder -and $child.Name -eq ($slot.Name + '.kmz')){
        $dest.CopyHere($child, 16)
        Start-Sleep -Milliseconds 300
      }
    }
  }
}
Get-ChildItem $outDir -Filter *.kmz | Select-Object -ExpandProperty Name
```

### 4) Parse createTime from copied KMZ files to identify most recent slot
```powershell
Set-Location "c:/Users/Ron Treleaven/Drone_SOP"
Add-Type -AssemblyName System.IO.Compression.FileSystem
$rows=@()
Get-ChildItem "Dev/rc2_slot_scan" -Filter *.kmz | ForEach-Object {
  $zip=[System.IO.Compression.ZipFile]::OpenRead($_.FullName)
  try {
    $entry=$zip.Entries | Where-Object { $_.FullName -ieq 'wpmz/template.kml' } | Select-Object -First 1
    if(-not $entry){
      $entry=$zip.Entries | Where-Object { $_.FullName -ieq 'wpmz/waylines.wpml' } | Select-Object -First 1
    }
    if($entry){
      $sr=New-Object System.IO.StreamReader($entry.Open())
      $txt=$sr.ReadToEnd()
      $sr.Close()
      $ct=[regex]::Match($txt,'<wpml:createTime>(\d+)</wpml:createTime>').Groups[1].Value
      $ut=[regex]::Match($txt,'<wpml:updateTime>(\d+)</wpml:updateTime>').Groups[1].Value
      $author=[regex]::Match($txt,'<wpml:author>([^<]+)</wpml:author>').Groups[1].Value
      $rows+=[PSCustomObject]@{ UUID=$_.BaseName; CreateTimeMs=$ct; UpdateTimeMs=$ut; Author=$author }
    }
  }
  finally { $zip.Dispose() }
}
$rows | Sort-Object {[long]($_.CreateTimeMs)} -Descending | Format-Table -AutoSize | Out-String
```

## Validation Checklist Before Field Flight
- Mission imports and opens in DJI Fly without warning.
- Correct slot selected (PROD or TEST).
- Height/speed/finish action match plan.
- startRecord and stopRecord actions present if expected.
- Gimbal pitch action present at first waypoint if expected.
- Rollback slot remains intact.

## Recovery Procedure
If mission fails to load or behaves unexpectedly:
1. Stop further slot replacements.
2. Restore previously backed up KMZ into affected UUID slot.
3. Reopen DJI Fly and verify mission list.
4. Re-test in TEST slot before PROD rollout.

## Notes for New Pilots
- UUID slot handling is powerful but easy to misuse.
- Follow this SOP exactly and avoid ad-hoc file deletions.
- Ask for review before changing PROD slot process.
