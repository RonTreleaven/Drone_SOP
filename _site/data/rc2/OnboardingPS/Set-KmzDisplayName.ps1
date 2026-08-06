<#
.SYNOPSIS
    Inject or update the KML Document name inside a staged RC2 mission KMZ.

.DESCRIPTION
    This script targets wpmz/template.kml inside a .kmz package and sets the
    Document-level <name> element to a human-readable value.

    Default behavior resolves the KMZ from your active RC2_Missions config using
    role -> UUID mapping. A timestamped backup is created before modification.

.PARAMETER Role
    Mission role to target (Mission_A, Mission_B, Mission_C). Ignored if -SourceKmz is used.

.PARAMETER DisplayName
    Human-readable mission name to inject into template.kml Document name.

.PARAMETER SourceKmz
    Optional explicit path to a KMZ file. If omitted, resolves from role mapping.

.PARAMETER NoBackup
    Skip backup creation. Not recommended.

.EXAMPLE
    & "./data/rc2/scripts/Set-KmzDisplayName.ps1" -Role Mission_C -DisplayName "Mission_C TEST"

.EXAMPLE
    & "./data/rc2/scripts/Set-KmzDisplayName.ps1" -SourceKmz "$env:USERPROFILE/RC2_Missions/Mission_C/<uuid>.kmz" -DisplayName "Mission_C TEST"
#>

param(
  [ValidateSet('Mission_A','Mission_B','Mission_C')]
  [string]$Role = 'Mission_C',

  [Parameter(Mandatory=$true)]
  [string]$DisplayName,

  [string]$SourceKmz,

  [switch]$NoBackup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-StagedKmzFromRole {
  param([string]$ResolvedRole)

  $configPointer = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
  if(-not (Test-Path $configPointer)){
    throw "CONFIG_POINTER_NOT_FOUND. Run Step 1 first."
  }

  $configPath = (Get-Content $configPointer -Raw).Trim()
  if(-not (Test-Path $configPath)){
    throw "CONFIG_NOT_FOUND. Run Step 1 again to regenerate local_config.json."
  }

  $config = Get-Content $configPath -Raw | ConvertFrom-Json
  $root = $config.managerRoot

  $rolesPath = Join-Path $root "REGISTRY/uuid_roles.json"
  if(-not (Test-Path $rolesPath)){
    throw "UUID_ROLES_NOT_FOUND. Run Step 4 first."
  }

  $roles = Get-Content $rolesPath -Raw | ConvertFrom-Json
  $uuid = $roles.$ResolvedRole
  if(-not $uuid -or $uuid -notmatch '^[0-9A-F-]{36}$'){
    throw "Invalid UUID for role ${ResolvedRole} in uuid_roles.json"
  }

  $kmzPath = Join-Path $root ("{0}/{1}.kmz" -f $ResolvedRole, $uuid)
  return $kmzPath
}

function Save-XmlUtf8NoBom {
  param([xml]$XmlDoc, [string]$Path)
  $settings = New-Object System.Xml.XmlWriterSettings
  $settings.Encoding = New-Object System.Text.UTF8Encoding($false)
  $settings.Indent = $true
  $settings.NewLineChars = "`r`n"
  $settings.NewLineHandling = [System.Xml.NewLineHandling]::Replace

  $writer = [System.Xml.XmlWriter]::Create($Path, $settings)
  try {
    $XmlDoc.Save($writer)
  }
  finally {
    $writer.Close()
  }
}

$targetKmz = if($SourceKmz){ $SourceKmz } else { Resolve-StagedKmzFromRole -ResolvedRole $Role }
if(-not (Test-Path $targetKmz)){
  throw "TARGET_KMZ_NOT_FOUND: $targetKmz"
}

$targetKmz = (Resolve-Path $targetKmz).Path
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "{0}.pre-nameinject_{1}.bak" -f $targetKmz, $stamp

Write-Host "[INFO] Target KMZ  : $targetKmz"
Write-Host "[INFO] DisplayName : $DisplayName"

if(-not $NoBackup){
  Copy-Item $targetKmz $backupPath -Force
  Write-Host "[INFO] Backup      : $backupPath"
}

$tempRoot = Join-Path $env:TEMP ("kmz_nameinject_{0}" -f [guid]::NewGuid().ToString('N'))
$extractDir = Join-Path $tempRoot "extract"
$repackDir = Join-Path $tempRoot "repack"
$sourceZip = Join-Path $tempRoot "source.zip"
New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
New-Item -ItemType Directory -Force -Path $repackDir | Out-Null

try {
  Copy-Item $targetKmz $sourceZip -Force
  Expand-Archive -Path $sourceZip -DestinationPath $extractDir -Force

  $templatePath = Join-Path $extractDir "wpmz/template.kml"
  if(-not (Test-Path $templatePath)){
    throw "TEMPLATE_KML_NOT_FOUND in KMZ: wpmz/template.kml"
  }

  [xml]$xml = Get-Content $templatePath -Raw
  $docNode = $xml.kml.Document
  if(-not $docNode){
    throw "INVALID_TEMPLATE_KML: Missing Document node."
  }

  $nameNode = $docNode.SelectSingleNode("*[local-name()='name']")
  if($nameNode){
    $nameNode.InnerText = $DisplayName
    Write-Host "[INFO] Updated existing <name> node."
  }
  else {
    $newName = $xml.CreateElement('name', 'http://www.opengis.net/kml/2.2')
    $newName.InnerText = $DisplayName
    $null = $docNode.InsertBefore($newName, $docNode.FirstChild)
    Write-Host "[INFO] Inserted new <name> node under <Document>."
  }

  Save-XmlUtf8NoBom -XmlDoc $xml -Path $templatePath

  $zipPath = Join-Path $repackDir "updated.zip"
  Compress-Archive -Path (Join-Path $extractDir '*') -DestinationPath $zipPath -Force
  Copy-Item $zipPath $targetKmz -Force

  Write-Host "[SUCCESS] KMZ updated with display name: $DisplayName"
  Write-Host "[NEXT] Run deployment step for role $Role to test RC2 UI rendering."
}
finally {
  if(Test-Path $tempRoot){
    Remove-Item -Path $tempRoot -Recurse -Force
  }
}
