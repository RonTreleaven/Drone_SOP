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
        return "{0}" -f $v
      }
    }
  }
  return ""
}

$json = Get-Content -Raw -Path $InputPath | ConvertFrom-Json
$features = @($json.features)

$rows = foreach ($feature in $features) {
  $props = $feature.properties
  [pscustomobject]@{
    name = Get-Prop $props @("name", "title", "label", "id", "identifier")
    zone_type = Get-Prop $props @("zone_type", "type", "airspaceType")
    designation = Get-Prop $props @("designation", "activity")
    class_raw = Get-Prop $props @("class", "airspace_class", "airspaceClass", "classification", "icaoClass", "type")
  }
}

$adizName = @($rows | Where-Object { $_.name -match "(^|[^A-Z])ADIZ([^A-Z]|$)" })
$moaName = @($rows | Where-Object { $_.name -match "(^|[^A-Z])MOA([^A-Z]|$)" })
$adizAny = @($rows | Where-Object { (($_.name + " " + $_.zone_type + " " + $_.designation + " " + $_.class_raw).ToUpper().Contains("ADIZ")) })
$moaAny = @($rows | Where-Object { (($_.name + " " + $_.zone_type + " " + $_.designation + " " + $_.class_raw).ToUpper().Contains("MOA")) })

Write-Output ("TOTAL={0}" -f $rows.Count)
Write-Output ("ADIZ_name_matches={0}" -f $adizName.Count)
Write-Output ("MOA_name_matches={0}" -f $moaName.Count)
Write-Output ("ADIZ_anyfield_matches={0}" -f $adizAny.Count)
Write-Output ("MOA_anyfield_matches={0}" -f $moaAny.Count)

Write-Output "SAMPLE_MOA_NAMES"
$moaName | Select-Object -First 10 -ExpandProperty name
Write-Output "SAMPLE_ADIZ_NAMES"
$adizName | Select-Object -First 10 -ExpandProperty name
