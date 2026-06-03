param(
  [string]$InputPath = "data/ca_asp.geojson"
)

$ErrorActionPreference = "Stop"

function Get-Prop {
  param($Props, [string[]]$Keys)
  foreach ($k in $Keys) {
    if ($Props.PSObject.Properties.Name -contains $k) {
      $v = $Props.$k
      if ($null -ne $v -and "$v" -ne "") {
        return $v
      }
    }
  }
  return $null
}

function Extract-Class {
  param($Props)
  $raw = Get-Prop $Props @("class", "airspace_class", "airspaceClass", "classification", "icaoClass", "type")
  if ($null -eq $raw) { return "" }

  if ($raw -is [int] -or $raw -is [long] -or $raw -is [double]) {
    $map = @{ 0 = "A"; 1 = "B"; 2 = "C"; 3 = "D"; 4 = "E"; 5 = "F"; 6 = "G" }
    $i = [int]$raw
    if ($map.ContainsKey($i)) { return $map[$i] }
    return ""
  }

  $text = ("$raw").Trim().ToUpper()
  if ($text.Length -eq 1 -and "ABCDEFG".Contains($text)) {
    return $text
  }
  foreach ($c in @("A", "B", "C", "D", "E", "F", "G")) {
    if ($text -eq $c -or $text.Contains("CLASS $c")) {
      return $c
    }
  }
  return $text
}

function Is-Canadian {
  param($Props)
  $country = Get-Prop $Props @("country", "iso_country", "country_code", "countryCode")
  if ($country -is [string]) {
    $u = $country.Trim().ToUpper()
    if ($u -in @("CA", "CAN", "CANADA")) {
      return $true
    }
  }
  return $false
}

function Group-CountLines {
  param(
    [Parameter(Mandatory = $true)]$Rows,
    [Parameter(Mandatory = $true)][string]$Property,
    [int]$Top = 0
  )

  $groups = $Rows | Group-Object $Property | Sort-Object Count -Descending
  if ($Top -gt 0) {
    $groups = $groups | Select-Object -First $Top
  }

  return $groups | ForEach-Object { "  {0}: {1}" -f $_.Name, $_.Count }
}

if (-not (Test-Path $InputPath)) {
  throw "Missing input file: $InputPath"
}

$json = Get-Content -Raw -Path $InputPath | ConvertFrom-Json
$features = @($json.features)

$rows = foreach ($feature in $features) {
  $props = $feature.properties
  $name = Get-Prop $props @("name", "title", "label", "id", "identifier")

  $lowerValue = $null
  $lowerDatum = $null
  $lowerUnit = $null
  if ($props.PSObject.Properties.Name -contains "lowerLimit") {
    $ll = $props.lowerLimit
    if ($ll) {
      if ($ll.PSObject.Properties.Name -contains "value") { $lowerValue = $ll.value }
      if ($ll.PSObject.Properties.Name -contains "referenceDatum") { $lowerDatum = $ll.referenceDatum }
      if ($ll.PSObject.Properties.Name -contains "unit") { $lowerUnit = $ll.unit }
    }
  }

  [pscustomobject]@{
    geometry_type = "{0}" -f $feature.geometry.type
    class = Extract-Class $props
    class_raw = "{0}" -f (Get-Prop $props @("class", "airspace_class", "airspaceClass", "classification", "icaoClass", "type"))
    zone_type = "{0}" -f (Get-Prop $props @("zone_type", "type", "airspaceType"))
    designation = "{0}" -f (Get-Prop $props @("designation", "activity"))
    country = "{0}" -f (Get-Prop $props @("country", "iso_country", "country_code", "countryCode"))
    is_canadian = Is-Canadian $props
    is_airway = (("{0}" -f $name).ToUpper().Contains("AIRWAY"))
    lower_datum = "{0}" -f $lowerDatum
    lower_unit = "{0}" -f $lowerUnit
    lower_value = "{0}" -f $lowerValue
  }
}

Write-Output "TOTAL_FEATURES=$($rows.Count)"
Write-Output "GEOMETRY_TYPES"
Group-CountLines -Rows $rows -Property "geometry_type"
Write-Output "CANADA_FLAG"
Write-Output ("  CA_true: {0}" -f (($rows | Where-Object is_canadian).Count))
Write-Output ("  CA_false: {0}" -f (($rows | Where-Object { -not $_.is_canadian }).Count))
Write-Output "AIRWAY_BY_NAME"
Write-Output ("  airway_true: {0}" -f (($rows | Where-Object is_airway).Count))
Write-Output ("  airway_false: {0}" -f (($rows | Where-Object { -not $_.is_airway }).Count))
Write-Output "CLASS_EXTRACTED"
Group-CountLines -Rows $rows -Property "class"
Write-Output "RAW_CLASS_TOP20"
Group-CountLines -Rows $rows -Property "class_raw" -Top 20
Write-Output "BLANK_CLASS_BREAKDOWN"
$blankClass = $rows | Where-Object { $_.class -eq "" }
Write-Output ("  blank_total: {0}" -f $blankClass.Count)
Write-Output ("  blank_airway: {0}" -f (($blankClass | Where-Object is_airway).Count))
Write-Output ("  blank_non_airway: {0}" -f (($blankClass | Where-Object { -not $_.is_airway }).Count))
Write-Output "ZONE_TYPE_TOP20"
Group-CountLines -Rows $rows -Property "zone_type" -Top 20
Write-Output "DESIGNATION_TOP20"
Group-CountLines -Rows $rows -Property "designation" -Top 20
Write-Output "LOWER_DATUM"
Group-CountLines -Rows $rows -Property "lower_datum"
Write-Output "LOWER_UNIT"
Group-CountLines -Rows $rows -Property "lower_unit"
