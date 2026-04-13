# Saving Missions to RC2

## Purpose
This SOP explains how to export one mission from GGCode, map it to the correct RC2 slot UUID, stage it safely, and copy it to the RC2 controller.

Use this with the onboarding workflow:
- RC2 UUID Mission Integration - New User Onboarding

This document is focused on one mission test run that a new user can repeat.

## Scope
- Source: GGCode mission already loaded and ready to export
- Target: Existing RC2 slot mapped in REGISTRY/uuid_roles.json
- Output: A staged slot package named as <UUID>.kmz, then copied to RC2

## Safety And Control Rules
1. Start with Mission_B for first validation.
2. Do not overwrite unknown slots.
3. Confirm slot UUID before any rename or deploy.
4. Keep backups before each replacement.
5. If a UUID check fails, stop and fix mapping before continuing.

## Prerequisites
- Step 1 to Step 4 are complete from onboarding.
- The role map file exists: REGISTRY/uuid_roles.json.
- You know which role to test first (recommended: Mission_B).
- GGCode advanced export access is enabled in My Profile.
- RC2 is available for Step 6 copy when staging is complete.

## What GGCode Export Actually Does
In GGCode Export & Files drawer:
- Export KMZ: creates a DJI KMZ and downloads it.
- Export KMZ To Folder: writes the KMZ into a selected folder (Chromium browsers with folder permissions).
- DJI KMZ Name modes:
  - Readable (default): mission-style human name.
  - Profile Slot UUID: uses UUID from My Profile slot map if set.
  - UUID Slot (advanced): uses manually pasted UUID.

Important:
- UUID is not auto-discovered in browser from RC2.
- You must validate UUID against your REGISTRY mapping before replacement.
- Profile Slot UUID mode uses browser-stored profile values and can lag behind a fresh Step 4 role remap.
- Always confirm exported filename equals the current target UUID from REGISTRY/uuid_roles.json.

## Current Web Integration Mapping (MAM And GGCode)

This section links the current browser workflow to the Step5B and Step6 PowerShell flow.

MAM side (index.html):
- Load UUID Roles reads REGISTRY/uuid_roles.json from the selected RC2_Missions root or REGISTRY folder.
- Mission A, Mission B, Mission C UUID fields are populated from Mission_A, Mission_B, Mission_C.
- Mission profile values are persisted to dsop.missionAutomationProfile.v1.
- The loaded REGISTRY snapshot is also persisted to dsop.uuidRolesRegistry.v1 for GGCode preflight checks.

GGCode side (GGcode.html):
- Profile Slot mode reads defaultExportSlot plus rc2UuidMissionA/B/C from dsop.missionAutomationProfile.v1.
- KMZ naming in Profile Slot mode uses the selected slot UUID for filename suggestion.
- Before KMZ export, GGCode now compares selected slot UUID against dsop.uuidRolesRegistry.v1.
- If Profile Slot UUID does not match REGISTRY snapshot, KMZ export is blocked with a mismatch warning.

PowerShell link (Step5B and Step6):
- Step5B stages newest INCOMING .kmz to role folder using UUID from REGISTRY/uuid_roles.json.
- Step6 copies role packages to RC2 slot folders by UUID and validates target presence.
- Combined with the GGCode preflight mismatch block, this reduces accidental wrong-slot deployment.

Operator note:
- If Step 4 remaps roles, run Load UUID Roles again before exporting from GGCode.
- Treat dsop.uuidRolesRegistry.v1 as the browser-side mirror of current REGISTRY role mapping.

## Single-Mission Test Flow (Recommended)

### 1) Select Target Role
Use Mission_B first.

Reason:
- Mission_B is the validation slot in the onboarding model.

### 2) Read Target UUID From Registry
Open PowerShell and run:

```powershell
$cfgPtr = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
$cfgPath = (Get-Content $cfgPtr -Raw).Trim()
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$root = $cfg.managerRoot
$rolesPath = Join-Path $root "REGISTRY/uuid_roles.json"
$roles = Get-Content $rolesPath -Raw | ConvertFrom-Json
$targetRole = "Mission_B"
$targetUuid = $roles.$targetRole
"Role: $targetRole"
"UUID: $targetUuid"
```

Pass criteria:
- UUID exists and is 36-character UUID format.

### 3) Export Mission From GGCode
In GGCode:
1. Open Export & Files.
2. Set DJI KMZ Name to Profile Slot UUID or UUID Slot.
3. If using UUID Slot mode, paste the exact target UUID from Step 2.
4. Click Export KMZ.
5. In save prompt, confirm final filename is <targetUuid>.kmz.

If filename is not exactly UUID-based:
- Cancel save.
- Fix naming mode.
- Re-export.

If filename matches an older role UUID:
- Update My Profile slot UUID fields to the refreshed role map values.
- Or switch to UUID Slot mode and paste the target UUID directly.

After Export (Profile Slot UUID) - user sequence:
1. Save export to <managerRoot>/INCOMING.
2. Confirm target role UUID from REGISTRY/uuid_roles.json.
3. Compare exported filename UUID with target role UUID.
4. Stage file to role with Step 5 deploy prep:
  - Invoke-RC2MissionDeploy -Role Mission_B -SourceKmz "<incoming file path>"
5. Copy only selected role to RC2:
  - Step6.ps1 -Roles Mission_B
6. Validate on RC2; only then promote same mission to Mission_A.

### 4) Place Export In INCOMING
Move the exported KMZ into:
- <managerRoot>/INCOMING/

Alternative save path:
- You may save directly into <managerRoot>/Mission_A, <managerRoot>/Mission_B, or <managerRoot>/Mission_C when using assigned UUID slot names.
- If you use direct role-folder save, filename must be exactly <assigned role UUID>.kmz.

Operator decision table (export save location):

| Option | Save location | Use when | Required controls |
| --- | --- | --- | --- |
| Standard staging | <managerRoot>/INCOMING | Default for all users and test runs | Run Step 5 deploy prep to normalize to role UUID before Step 6 |
| Direct role-folder save | <managerRoot>/Mission_A, Mission_B, or Mission_C | Advanced use with confirmed role map and UUID naming | Filename must be exact assigned UUID (<UUID>.kmz) and must match REGISTRY/uuid_roles.json |

Recommended naming in INCOMING:
- Keep the exported file exactly as <UUID>.kmz when replacing a slot.
- Optional trace copy in ARCHIVE with a readable timestamped name.

### 5) Stage To Local Role Package (Safe Replace)
Preferred (single command script):

```powershell
./data/rc2/scripts/Step5B_StageFromIncoming.ps1 -Role Mission_B -ArchiveIncoming
```

What this does:
- Picks newest `.kmz` from `INCOMING` (unless `-SourceKmz` is provided).
- Stages it to the selected role using assigned role UUID naming.
- Optionally archives the processed INCOMING file when `-ArchiveIncoming` is used.

Alternative (manual function invocation):

Run in the same PowerShell session:

```powershell
. "./data/rc2/scripts/Step5.ps1"
$incoming = Join-Path $root "INCOMING/$targetUuid.kmz"
Invoke-RC2MissionDeploy -Role $targetRole -SourceKmz $incoming
```

Expected results:
- Local staged file written to <managerRoot>/<Role>/<UUID>.kmz
- Backup snapshot written to BACKUPS/<Role>/<timestamp>/

If you prefer explicit source selection with Step5B:

```powershell
./data/rc2/scripts/Step5B_StageFromIncoming.ps1 -Role Mission_B -SourceKmz "$env:USERPROFILE/RC2_Missions/INCOMING/<file>.kmz" -ArchiveIncoming
```

### 6) Validate UUID Match Before Controller Copy
Run:

```powershell
$staged = Join-Path $root "$targetRole/$targetUuid.kmz"
"Staged exists: $(Test-Path $staged)"
"Expected staged file: $staged"
```

Pass criteria:
- Staged file exists.
- File name UUID equals target role UUID from REGISTRY mapping.

### 7) Copy Staged Package To RC2
Run Step 6 script for Mission_B-only validation:

```powershell
./data/rc2/scripts/Step6.ps1 -Roles Mission_B
```

Optional full slot sync:

```powershell
./data/rc2/scripts/Step6.ps1
```

Optional when intentionally leaving Mission_C unchanged:

```powershell
./data/rc2/scripts/Step6.ps1 -SkipMissionC
```

After successful copy, archive the processed INCOMING file:

```powershell
Move-RC2IncomingToArchive -SourceKmz "<incoming file path>" -Role Mission_B
```

### 8) Controller-Side Validation
On RC2 / DJI Fly:
1. Open waypoint missions.
2. Verify Mission_B slot shows updated mission.
3. Load mission and inspect basic metadata and route shape.
4. If validation passes, promote same mission to Mission_A using same flow.

Role-folder hygiene (recommended):
- Run `Invoke-RC2RoleFolderCleanup -Role Mission_B` after repeated tests to keep Mission_B folder single-file clean.
- Extra role-folder `.kmz` files are archived to `ARCHIVE/<Role>/cleanup_<timestamp>/`.

RC2 mission list ordering caveat:
- RC2 list order may remain tied to UUID slot chronology after copy operations.
- Validate by mapped slot UUID and mission content, not list position alone.

## Optional Path: Export KMZ To Folder
Use only after baseline flow is proven.

Notes:
- Browser must support folder APIs (Chrome/Edge on secure context).
- You must grant folder write permission.
- GGCode writes into profile-configured subfolder for selected slot.

Still required:
- Confirm target UUID and final file name are correct.
- Keep local backup and registry checks.

## Step 9 Health Check (Recommended Before Step 6)

Purpose:
- Validate role UUID quality and uniqueness in REGISTRY/uuid_roles.json.
- Compare role UUIDs against uuid_inventory.csv (drift signal).
- Confirm expected staged role packages exist in Mission_A/B/C folders.
- Optionally verify RC2 live slot folder presence by UUID.

Run local-only checks:

```powershell
./data/rc2/scripts/Step9_HealthCheck.ps1
```

Run with RC2 live slot check enabled:

```powershell
./data/rc2/scripts/Step9_HealthCheck.ps1 -CheckRC2
```

Block automation on warnings too:

```powershell
./data/rc2/scripts/Step9_HealthCheck.ps1 -CheckRC2 -FailOnWarning
```

Output:
- Log: RC2_Missions/LOGS/step9_healthcheck_yyyymmdd_hhmmss.log
- Report JSON: RC2_Missions/REGISTRY/health/step9_healthcheck_yyyymmdd_hhmmss.json
- JSON schema: Dev/RC2 UUID PowerShell/Step9_HealthCheck.report.schema.json

Exit codes:
- 0 = COMPLETE or BLOCKED (warnings only, when -FailOnWarning is not set)
- 2 = FAILED (blocking failures)
- 3 = BLOCKED with warnings when -FailOnWarning is set

Health check status code intent:
- OK: check passed
- MISSING: expected artifact or slot not present
- DRIFT: role UUID not found in current inventory
- DUPLICATE: same UUID assigned to multiple roles
- INVALID: malformed or missing role UUID value

## Failure Handling
- UUID mismatch (registry vs filename): stop and correct mapping or export name.
- Missing INCOMING file: re-export and verify path.
- Step5 deploy error: confirm Step 1 config pointer and uuid_roles.json.
- Step6 copy error: confirm RC2 is connected, unlocked, and visible in Windows MTP.

## Single Mission Test Record
Date:
Operator:
Target Role:
Target UUID:
GGCode Naming Mode Used:

Checklist:
- [ ] READY: roles file loaded and target UUID confirmed.
- [ ] READY: mission loaded in GGCode.
- [ ] COMPLETE: exported KMZ filename is exactly <UUID>.kmz.
- [ ] COMPLETE: file moved to INCOMING.
- [ ] COMPLETE: Invoke-RC2MissionDeploy staged role package.
- [ ] COMPLETE: backup snapshot created.
- [ ] COMPLETE: Step6 copied staged package to RC2.
- [ ] COMPLETE: mission visible and loadable in DJI Fly.

Outcome:
- PASS / BLOCKED / FAILED
- Notes:

## Promotion After Mission_B Passes
Repeat the same process for Mission_A:
1. Read Mission_A UUID from REGISTRY mapping.
2. Export with Mission_A UUID name.
3. Stage with Invoke-RC2MissionDeploy -Role Mission_A.
4. Run Step6 with role targeting and verify in DJI Fly.

```powershell
./data/rc2/scripts/Step6.ps1 -Roles Mission_A
```

