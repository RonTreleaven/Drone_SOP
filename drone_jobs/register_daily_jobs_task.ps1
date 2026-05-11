param(
    [string]$TaskName = "DroneSOP-DailyJobsRefresh",
    [string]$Time = "06:15",
    [string]$TaskDescription = "Refresh Drone SOP jobs data for JobBoard.html"
)

$timePattern = '^(?:[01]\d|2[0-3]):[0-5]\d$'
if ($Time -notmatch $timePattern) {
    throw "Time must be in 24-hour HH:mm format, for example 06:15 or 18:30."
}

$scriptRoot = Split-Path -Parent $PSCommandPath
$runnerPath = Join-Path $scriptRoot "run_jobs_refresh_daily.cmd"

if (-not (Test-Path $runnerPath)) {
    throw "Runner script not found at: $runnerPath"
}

$triggerTime = [datetime]::ParseExact($Time, "HH:mm", [System.Globalization.CultureInfo]::InvariantCulture)
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$runnerPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At $triggerTime
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Description $TaskDescription -Force | Out-Null

$taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Scheduled task '$TaskName' registered."
Write-Host "Daily run time: $Time"
Write-Host "Next run time : $($taskInfo.NextRunTime)"
Write-Host "Last run time : $($taskInfo.LastRunTime)"
Write-Host "Runner script : $runnerPath"
