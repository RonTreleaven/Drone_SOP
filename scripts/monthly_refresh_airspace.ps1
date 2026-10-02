$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# Maximum allowed age (in days) for the local canonical CA airspace source
# before it is treated as stale. When CA download URLs are unavailable and the
# script falls back to this file, a file older than this fails the run so the
# staleness surfaces instead of silently shipping outdated airspace data.
$maxCaAspAgeDays = 45

$pythonExe = "C:/Program Files/Python312/python.exe"
$sourceDir = "data/airspace/_sources"
$reportDir = "data/airspace/reports"
$openAipExportsUrl = "https://www.openaip.net/data/exports?page=1&limit=50&sortBy=createdAt&sortDesc=true&format=geojson&contentType=airspace%2Cairport&country=CA&failed=false"

function Resolve-OpenAipCanadaSignedUrls {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ExportsUrl
  )

  $html = (Invoke-WebRequest -Uri $ExportsUrl -UseBasicParsing -TimeoutSec 120).Content
  # OpenAIP moved exports from storage.googleapis.com signed URLs to
  # s3.openaip.net AWS-signed URLs rendered server-side in the SvelteKit
  # payload. Match any host for the CA system export files instead.
  $pattern = 'https://[^"''<>\s)]+?ca_(?:asp|apt)\.geojson\?[^"''<>\s)]+'
  $allUrls = [regex]::Matches($html, $pattern) | ForEach-Object {
    $_.Value.Replace("&amp;", "&")
  } | Select-Object -Unique

  if (-not $allUrls -or $allUrls.Count -eq 0) {
    throw "No signed OpenAIP download URLs were found in exports page payload."
  }

  $aspUrl = $allUrls | Where-Object { $_ -match "ca_asp\.geojson" } | Select-Object -First 1
  $aptUrl = $allUrls | Where-Object { $_ -match "ca_apt\.geojson" } | Select-Object -First 1

  [pscustomobject]@{
    AspUrl = $aspUrl
    AptUrl = $aptUrl
  }
}

if (-not (Test-Path $sourceDir)) {
  New-Item -Path $sourceDir -ItemType Directory -Force | Out-Null
}
if (-not (Test-Path $reportDir)) {
  New-Item -Path $reportDir -ItemType Directory -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $reportDir ("monthly_refresh_" + $stamp + ".log")
$statusPath = Join-Path $reportDir "LAST_STATUS.json"

function Write-Status {
  param(
    [Parameter(Mandatory = $true)][ValidateSet("success", "failed")][string]$Status,
    [string]$Message = ""
  )
  $obj = [pscustomobject]@{
    status    = $Status
    message   = $Message
    timestamp = (Get-Date).ToString("s")
    log       = (Resolve-Path $logPath).Path
  }
  $obj | ConvertTo-Json | Set-Content -Path $statusPath -Encoding UTF8
}

$cmd = @(
  "scripts/refresh_airspace_data.py",
  "--download-openair",
  "--require-web-openair",
  "--download-airports-csv",
  "--discover-latest-dah-url",
  "--download-dah-pdf",
  "--extract-dah-special-zones"
)

$envCaAspUrl = $env:OPENAIP_CA_ASP_URL
$envCaAptUrl = $env:OPENAIP_CA_APT_URL
$resolvedCa = $null
$caResolutionError = ""

try {
  $resolvedCa = Resolve-OpenAipCanadaSignedUrls -ExportsUrl $openAipExportsUrl
}
catch {
  $caResolutionError = $_.Exception.Message
}

$caAspUrl = if ($envCaAspUrl) { $envCaAspUrl } elseif ($resolvedCa) { $resolvedCa.AspUrl } else { $null }
$caAptUrl = if ($envCaAptUrl) { $envCaAptUrl } elseif ($resolvedCa) { $resolvedCa.AptUrl } else { $null }
$caUrlSource = if ($envCaAspUrl -or $envCaAptUrl) { "env" } elseif ($resolvedCa) { "openaip" } else { "none" }

if ($caAspUrl) {
  $cmd += @("--download-ca-sources", "--require-web-ca-asp", "--ca-asp-url", $caAspUrl)
  if ($caAptUrl) {
    $cmd += @("--ca-apt-url", $caAptUrl)
  }
}

"Monthly refresh started: $(Get-Date -Format s)" | Tee-Object -FilePath $logPath
"Working directory: $repoRoot" | Tee-Object -FilePath $logPath -Append
if ($caAspUrl) {
  if ($caUrlSource -eq "openaip") {
    "CA source URLs: discovered from OpenAIP exports page." | Tee-Object -FilePath $logPath -Append
  }
  elseif ($caUrlSource -eq "env") {
    "CA source URLs: using OPENAIP_CA_ASP_URL / OPENAIP_CA_APT_URL environment values." | Tee-Object -FilePath $logPath -Append
  }

  if (-not $caAptUrl) {
    "CA airport source URL not available; ca_apt download skipped and local canonical file will be retained." | Tee-Object -FilePath $logPath -Append
  }
}
else {
  if ($caResolutionError) {
    "CA source URL discovery failed: $caResolutionError" | Tee-Object -FilePath $logPath -Append
  }
  "CA source URLs unavailable; CA download skipped and local canonical ca_asp/ca_apt files will be used." | Tee-Object -FilePath $logPath -Append

  # Fail the run if the fallback CA source is older than the allowed window,
  # so stale airspace data is surfaced loudly rather than silently reused.
  $caAspFile = Join-Path $sourceDir "ca_asp.geojson"
  if (Test-Path $caAspFile) {
    $caAgeDays = [int]((Get-Date) - (Get-Item $caAspFile).LastWriteTime).TotalDays
    "Local canonical ca_asp.geojson age: $caAgeDays day(s)." | Tee-Object -FilePath $logPath -Append
    if ($caAgeDays -gt $maxCaAspAgeDays) {
      $failMsg = "CA download URLs unavailable and local ca_asp.geojson is $caAgeDays day(s) old, exceeding the $maxCaAspAgeDays-day freshness limit. Fix OpenAIP discovery or set OPENAIP_CA_ASP_URL/OPENAIP_CA_APT_URL, then rerun."
      "Monthly refresh failed: $failMsg" | Tee-Object -FilePath $logPath -Append
      Write-Status -Status "failed" -Message $failMsg
      exit 1
    }
  }
}
"Command: $pythonExe $($cmd -join ' ')" | Tee-Object -FilePath $logPath -Append

& $pythonExe @cmd 2>&1 | Tee-Object -FilePath $logPath -Append
if ($LASTEXITCODE -ne 0) {
  $failMsg = "refresh_airspace_data.py exited with code $LASTEXITCODE."
  "Monthly refresh failed: $failMsg" | Tee-Object -FilePath $logPath -Append
  Write-Status -Status "failed" -Message $failMsg
  exit 1
}
"Monthly refresh completed successfully." | Tee-Object -FilePath $logPath -Append
Write-Status -Status "success" -Message "Refresh completed successfully."
exit 0
