param(
  [string]$Version = "1.0.0",
  [string]$OutputRoot = "data/rc2/_private/packages"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
Set-Location $repoRoot

$stageRoot = Join-Path $env:TEMP ("rc2_new_user_pkg_" + [Guid]::NewGuid().ToString("N"))
$bundleRoot = Join-Path $stageRoot "rc2-new-user"
$scriptsOut = Join-Path $bundleRoot "scripts"
$docsOut = Join-Path $bundleRoot "docs"
$schemaOut = Join-Path $bundleRoot "schema"

New-Item -ItemType Directory -Force -Path $scriptsOut | Out-Null
New-Item -ItemType Directory -Force -Path $docsOut | Out-Null
New-Item -ItemType Directory -Force -Path $schemaOut | Out-Null

$sourceScriptDir = Join-Path $repoRoot "Dev/RC2 UUID PowerShell"
$sourceDocsDir = Join-Path $repoRoot "Markdown Docs"

$scriptFiles = @(
  "Step1.ps1",
  "Step2.ps1",
  "Step3.ps1",
  "Step4.ps1",
  "Step5.ps1",
  "Step5B_StageFromIncoming.ps1",
  "Step6.ps1",
  "Step9_HealthCheck.ps1"
)

foreach($name in $scriptFiles){
  $src = Join-Path $sourceScriptDir $name
  if(-not (Test-Path $src)){ throw "Missing source script: $src" }
  Copy-Item -Path $src -Destination (Join-Path $scriptsOut $name) -Force
}

$docFiles = @(
  "Saving Missions to RC2.md",
  "RC2 UUID Mission Integration - New User Onboarding.md"
)

foreach($name in $docFiles){
  $src = Join-Path $sourceDocsDir $name
  if(-not (Test-Path $src)){ throw "Missing source doc: $src" }
  Copy-Item -Path $src -Destination (Join-Path $docsOut $name) -Force
}

$schemaSrc = Join-Path $repoRoot "Dev/RC2 UUID PowerShell/Step9_HealthCheck.report.schema.json"
if(-not (Test-Path $schemaSrc)){ throw "Missing source schema: $schemaSrc" }
Copy-Item -Path $schemaSrc -Destination (Join-Path $schemaOut "Step9_HealthCheck.report.schema.json") -Force

$readme = @"
RC2 New User Bundle

Version: $Version

This package is a controlled onboarding set for Windows PowerShell.

Suggested sequence:
1) Step1
2) Step2
3) Step3
4) Step4
5) Step5B
6) Step9
7) Step6 (DryRun first)
"@
Set-Content -Path (Join-Path $bundleRoot "README.txt") -Value $readme -Encoding UTF8

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$zipName = "rc2-new-user-scripts-v$Version.zip"
$zipPath = Join-Path $OutputRoot $zipName
if(Test-Path $zipPath){ Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $bundleRoot "*") -DestinationPath $zipPath -CompressionLevel Optimal

$hash = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash
$manifestPath = Join-Path $repoRoot "data/rc2/_private/manifests/new-user-package.manifest.json"
$manifest = [ordered]@{
  manifestVersion = "1.0.0"
  packageType = "rc2-new-user"
  packageVersion = $Version
  fileName = $zipName
  relativePath = "/data/rc2/_private/packages/$zipName"
  sha256 = $hash
  generatedAt = (Get-Date).ToString("s")
  includes = [ordered]@{
    scripts = $scriptFiles
    docs = $docFiles
    schema = @("Step9_HealthCheck.report.schema.json")
  }
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $manifestPath -Encoding UTF8

Remove-Item -Path $stageRoot -Recurse -Force
Write-Host "[SUCCESS] Package built: $zipPath"
Write-Host "[SUCCESS] Manifest written: $manifestPath"
Write-Host "[INFO] SHA256: $hash"
