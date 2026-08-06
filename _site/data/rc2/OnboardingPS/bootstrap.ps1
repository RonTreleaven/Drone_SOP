$defaultWorkspaceRoot = Join-Path $env:USERPROFILE "RC2_Missions"
$inputRoot = Read-Host "Workspace root path (Enter for default: $defaultWorkspaceRoot)"
$workspaceRoot = if([string]::IsNullOrWhiteSpace($inputRoot)) { $defaultWorkspaceRoot } else { $inputRoot }

"Workspace root selected: $workspaceRoot"
"[PASS] Bootstrap input capture passed."
"[SUCCESS] Bootstrap completed successfully."