$tokens = @("airport-circles-flyout", "notams-flyout", "pilot-flyout-v2", "airport-type-control", "launchAirportsMode", "forceAirportsOffOnLaunch", "setNotamsFlyoutOpen", "toggleAllNotamDetails", "showAllNotamDetailBtn", "getPilotLocationFromQuery", "refresh-fir-stale", "home-logo-control { background: transparent", "pilotToggleCtl", "notamsToggleBtn")
$current = Get-Content "NotamsMap.html" -Raw
$v4 = Get-Content "NotamsMapv4.html" -Raw
Write-Host "Token Analysis:"
foreach ($t in $tokens) {
    $countCurrent = ([regex]::Matches($current, [regex]::Escape($t))).Count
    $countV4 = ([regex]::Matches($v4, [regex]::Escape($t))).Count
    Write-Host "$t -> Current: $countCurrent, v4: $countV4"
}
$classesC = [regex]::Matches($current, "\.([a-zA-Z0-9_-]+)") | % { $_.Groups[1].Value } | Group-Object | Select Name, Count
$classesV = [regex]::Matches($v4, "\.([a-zA-Z0-9_-]+)") | % { $_.Groups[1].Value } | Select -Unique
$missing = $classesC | ? { $n = $_.Name; -not ($classesV -contains $n) } | Sort Count -Desc | Select -First 8
Write-Host "`nTop 8 missing CSS classes:"
$missing | Ft -AutoSize
