$cfgPtr = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
$cfgPath = (Get-Content $cfgPtr -Raw).Trim()
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$incoming = Join-Path $cfg.managerRoot "INCOMING/new_mission.kmz"

try {
	if(-not (Get-Command Invoke-RC2MissionDeploy -ErrorAction SilentlyContinue)){
		throw "Invoke-RC2MissionDeploy is not loaded. Run Step5.ps1 in this PowerShell session first."
	}

	Invoke-RC2MissionDeploy -Role Mission_B -SourceKmz $incoming
	Invoke-RC2MissionDeploy -Role Mission_A -SourceKmz $incoming
	Write-Host "[PASS] Step 7 validation checks passed."
	Write-Host "[SUCCESS] Step 7 completed successfully."
}
catch {
	Write-Host "[FAILED] Step 7 failed."
	Write-Host "Error: $($_.Exception.Message)"
	if($_.FullyQualifiedErrorId){
		Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
	}
	throw
}