# MAM RC2 PowerShell Wiki

## Purpose
This page documents the intended use of the RC2 PowerShell workflow and how hosted artifacts in data/rc2 support operations.

## Scope
- Script discovery and version visibility via hosted static files
- Safe transfer pattern for Mission_B validation
- Maintenance process for promoting scripts/schema/docs to hosted paths

## Execution Model
- Hosted page/data paths are static distribution only.
- PowerShell scripts execute locally on Windows.
- RC2 write operations occur only when user confirms in Step6 PromptBeforeCopy mode.

## AJV Prerequisite (Optional But Recommended)
Use AJV to validate Step9 JSON output against schema.  Install in a PowerShell terminal.

Install:

```powershell
npm install -g ajv-cli
```

Verify:

```powershell
ajv help validate
```

If npm is missing, install Node.js LTS first, then rerun the commands.

## Safe User Sequence

Four wrapper scripts guide you through the full mission-deployment workflow, after you have completed the New User onboarding and have created the /<user>/RC2_Missions file structures.

Each wrapper prints a plain-language description of what it will do at runtime —
no memorisation of parameter flags is required. Run them in order from the repository root in PowerShell.

### Step 1 — Run-StageIncoming.ps1

**What it does:** Finds the newest KMZ file in your INCOMING folder, copies it into
the chosen mission role folder (Mission_A, Mission_B, or Mission_C), then moves the
source file to ARCHIVE so it cannot be staged a second time by accident.

**Prompts for:** Role (if not supplied as a parameter).

```powershell
& "./data/rc2/scripts/Run-StageIncoming.ps1"
# or with role pre-supplied:
& "./data/rc2/scripts/Run-StageIncoming.ps1" -Role Mission_B
```

Underlying script: **Step5B_StageFromIncoming.ps1** — flags applied: `-ArchiveIncoming`

---

### Step 2 — Run-HealthCheck.ps1

**What it checks:**

1. UUID role mapping — uuid_roles.json format and completeness.
2. Inventory alignment — uuid_inventory.csv vs registry, no orphan/missing entries.
3. Staged KMZ files — each role folder has a package ready to deploy.
4. RC2 live slot state — on-device waypoint UUIDs match the registry (RC2 must be connected).

Any WARNING or ERROR causes a non-zero exit and blocks deployment.

**Prerequisite:** RC2 controller must be powered on and connected via USB.

```powershell
& "./data/rc2/scripts/Run-HealthCheck.ps1"
```

Underlying script: **Step9_HealthCheck.ps1** — flags applied: `-CheckRC2 -FailOnWarning`

---

### Step 3 — Run-DeployPreview.ps1

**What it does:** Reads the staged role KMZ and UUID slot mapping, then prints a full
deployment plan showing exactly which files would be copied to which RC2 UUID slot folders.
**No files are transferred, moved, or deleted** during a dry run.

Use this step to verify the plan is correct before committing to the RC2.

**Prompts for:** Role (if not supplied as a parameter).

```powershell
& "./data/rc2/scripts/Run-DeployPreview.ps1"
# or with role pre-supplied:
& "./data/rc2/scripts/Run-DeployPreview.ps1" -Role Mission_B
```

Underlying script: **Step6.ps1** — flags applied: `-DryRun`

---

### Step 4 — Run-Deploy.ps1

**What it does:** Copies the staged KMZ package to the matching RC2 UUID slot folders
via MTP. Displays the deployment plan, then requires you to type `YES` before any file
is written. Typing anything else cancels the transfer cleanly with no partial writes.

**Prerequisites before running:**
- Run-StageIncoming completed (role folder has a staged KMZ).
- Run-HealthCheck exited with code 0 (all checks passed).
- Run-DeployPreview reviewed and the plan looks correct.
- RC2 controller powered on and connected via USB.

**Prompts for:** Role (if not supplied), then `YES` confirmation before transfer.

```powershell
& "./data/rc2/scripts/Run-Deploy.ps1"
# or with role pre-supplied:
& "./data/rc2/scripts/Run-Deploy.ps1" -Role Mission_B
```

Underlying script: **Step6.ps1** — flags applied: `-PromptBeforeCopy`

## RC2 Display Behavior (Important)

RC2 does not use mission role labels (Mission_A/B/C) directly in the list UI.
In practice, list order is driven by file timestamp/order on device.

Operational rule used in this workflow:
- Deploy in this order: `Mission_C -> Mission_B -> Mission_A`
- Newest-first sort on RC2 appears as: `A, B, C`
- Oldest-first sort on RC2 appears as: `C, B, A`

This is the supported human-readable mapping method for this SOP.

## RC2 Field Verification Checklist

After each full ordered deploy:
1. Open RC2 mission list with **Newest first**; verify visual order is A, B, C.
2. Toggle to **Oldest first**; verify visual order is C, B, A.
3. If mission footprint is hard to distinguish, export three clearly different test patterns (example: triangle, line, box).
4. If RC2 does not auto-locate mission on map, use map browse/set-location and verify the expected pattern before flight.


## Engine Scripts (Called by Wrappers)

These are the underlying scripts. They accept granular parameters and are invoked
automatically by the Run-* wrappers. Use them directly only when fine-grained control
is needed.

- **Step5.ps1** — role package normalization and helper functions (dot-sourced by Step5B).
- **Step5B_StageFromIncoming.ps1** — picks the newest source KMZ and stages the role package.
- **Step6.ps1** — RC2 MTP transfer with `-DryRun` preview and `-PromptBeforeCopy` gate.
- **Step9_HealthCheck.ps1** — mapping, drift, staged-file, and optional RC2 live slot checks.

When INCOMING is empty and you need to supply an explicit KMZ path directly to Step5B:

```powershell
& "./data/rc2/scripts/Step5B_StageFromIncoming.ps1" -Role Mission_B -SourceKmz "$env:USERPROFILE/RC2_Missions/INCOMING/<file>.kmz" -ArchiveIncoming
```

Common error messages from Step5B:
- `NO_KMZ_IN_INCOMING` — INCOMING folder exists but contains no .kmz file.
- `SOURCE_KMZ_NOT_FOUND` — explicit `-SourceKmz` path does not exist.
- `CONFIG_POINTER_NOT_FOUND` — Step 1 has not been run for this Windows user profile.

## Hosted Artifact Paths
- /data/rc2/rc2-index.html
- /data/rc2/manifest.json
- /data/rc2/scripts/
- /data/rc2/docs/
- /data/schema/step9_healthcheck_report.schema.json

## Controlled New User Package Channel
- Hidden package folder: /data/rc2/_private/packages/
- Hidden package manifest: /data/rc2/_private/manifests/new-user-package.manifest.json
- Builder script: scripts/rc2/Build-RC2NewUserPackage.ps1

Build/update command:

```powershell
./scripts/rc2/Build-RC2NewUserPackage.ps1 -Version 1.0.0
```

Use this channel for curated onboarding bundles only (approved script set), not all development scripts.

## Maintenance
1. Edit source files under Dev/RC2 UUID PowerShell and Markdown Docs.
2. Promote copies into data/rc2 and data/schema.
3. Run AJV schema validation for generated Step9 reports.
4. Update manifest entries when artifacts change..
