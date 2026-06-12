param(
    [string]$TaskName = "DroneSOP-AirspaceRefresh-56Day",
    [string]$Time = "06:00",
    [ValidateSet("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")]
    [string]$DayOfWeek = "",
    [string]$TaskDescription = "Refresh Drone SOP airspace data every 56 days (8-week cadence)."
)

$timePattern = '^(?:[01]\d|2[0-3]):[0-5]\d$'
if ($Time -notmatch $timePattern) {
    throw "Time must be in 24-hour HH:mm format, for example 06:00 or 18:30."
}

$scriptRoot = Split-Path -Parent $PSCommandPath
$runnerPath = Join-Path $scriptRoot "monthly_refresh_airspace.ps1"
if (-not (Test-Path $runnerPath)) {
    throw "Runner script not found at: $runnerPath"
}

if (-not $DayOfWeek) {
    $DayOfWeek = (Get-Date).DayOfWeek.ToString()
}

$triggerTime = [datetime]::ParseExact($Time, "HH:mm", [System.Globalization.CultureInfo]::InvariantCulture)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runnerPath`""
$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 8 -DaysOfWeek $DayOfWeek -At $triggerTime
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $TaskDescription -Force | Out-Null

$taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Scheduled task '$TaskName' registered."
Write-Host "Cadence       : Every 8 weeks (56 days)"
Write-Host "Day/Time      : $DayOfWeek at $Time"
Write-Host "Next run time : $($taskInfo.NextRunTime)"
Write-Host "Last run time : $($taskInfo.LastRunTime)"
Write-Host "Runner script : $runnerPath"