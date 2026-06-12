param(
    [string]$TaskName = "DroneSOP-AirspaceRefresh-56Day-Push"
)

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "Scheduled task '$TaskName' was not found."
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Scheduled task '$TaskName' removed."