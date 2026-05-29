param(
  [string]$InputPath = "data/airspace/dah_gold_airspace.geojson",
  [string]$OutputPath = "data/airspace/reports/dah_gold_airspace_features.csv"
)

$ErrorActionPreference = "Stop"

function Get-GeometryMetrics {
  param([object]$Geometry)

  $vertexCount = 0
  $minLon = [double]::PositiveInfinity
  $minLat = [double]::PositiveInfinity
  $maxLon = [double]::NegativeInfinity
  $maxLat = [double]::NegativeInfinity
  $sumLon = 0.0
  $sumLat = 0.0
  $pointCount = 0

  if (-not $Geometry -or -not $Geometry.type) {
    return [pscustomobject]@{
      VertexCount = 0
      MinLon = $null
      MinLat = $null
      MaxLon = $null
      MaxLat = $null
      CentroidLon = $null
      CentroidLat = $null
    }
  }

  switch ($Geometry.type) {
    "Polygon" {
      foreach ($ring in $Geometry.coordinates) {
        foreach ($pt in $ring) {
          if ($pt -and $pt.Count -ge 2) {
            $lon = [double]$pt[0]
            $lat = [double]$pt[1]
            if ($lon -lt $minLon) { $minLon = $lon }
            if ($lon -gt $maxLon) { $maxLon = $lon }
            if ($lat -lt $minLat) { $minLat = $lat }
            if ($lat -gt $maxLat) { $maxLat = $lat }
            $sumLon += $lon
            $sumLat += $lat
            $pointCount += 1
            $vertexCount += 1
          }
        }
      }
    }
    "MultiPolygon" {
      foreach ($poly in $Geometry.coordinates) {
        foreach ($ring in $poly) {
          foreach ($pt in $ring) {
            if ($pt -and $pt.Count -ge 2) {
              $lon = [double]$pt[0]
              $lat = [double]$pt[1]
              if ($lon -lt $minLon) { $minLon = $lon }
              if ($lon -gt $maxLon) { $maxLon = $lon }
              if ($lat -lt $minLat) { $minLat = $lat }
              if ($lat -gt $maxLat) { $maxLat = $lat }
              $sumLon += $lon
              $sumLat += $lat
              $pointCount += 1
              $vertexCount += 1
            }
          }
        }
      }
    }
    default {
      if ($Geometry.coordinates) {
        foreach ($pt in $Geometry.coordinates) {
          if ($pt -and $pt.Count -ge 2) {
            $lon = [double]$pt[0]
            $lat = [double]$pt[1]
            if ($lon -lt $minLon) { $minLon = $lon }
            if ($lon -gt $maxLon) { $maxLon = $lon }
            if ($lat -lt $minLat) { $minLat = $lat }
            if ($lat -gt $maxLat) { $maxLat = $lat }
            $sumLon += $lon
            $sumLat += $lat
            $pointCount += 1
            $vertexCount += 1
          }
        }
      }
    }
  }

  if ($pointCount -eq 0) {
    return [pscustomobject]@{
      VertexCount = 0
      MinLon = $null
      MinLat = $null
      MaxLon = $null
      MaxLat = $null
      CentroidLon = $null
      CentroidLat = $null
    }
  }

  return [pscustomobject]@{
    VertexCount = $vertexCount
    MinLon = [math]::Round($minLon, 6)
    MinLat = [math]::Round($minLat, 6)
    MaxLon = [math]::Round($maxLon, 6)
    MaxLat = [math]::Round($maxLat, 6)
    CentroidLon = [math]::Round(($sumLon / $pointCount), 6)
    CentroidLat = [math]::Round(($sumLat / $pointCount), 6)
  }
}

function Get-ProvinceEstimate {
  param(
    [Nullable[double]]$Lon,
    [Nullable[double]]$Lat
  )

  if ($null -eq $Lon -or $null -eq $Lat) {
    return "Unknown"
  }

  $boxes = @(
    @{ Prov = "BC"; MinLon = -139.1; MaxLon = -114.0; MinLat = 48.2; MaxLat = 60.1 },
    @{ Prov = "AB"; MinLon = -120.0; MaxLon = -109.9; MinLat = 48.9; MaxLat = 60.0 },
    @{ Prov = "SK"; MinLon = -110.1; MaxLon = -101.2; MinLat = 49.0; MaxLat = 60.0 },
    @{ Prov = "MB"; MinLon = -102.1; MaxLon = -88.8; MinLat = 49.0; MaxLat = 60.1 },
    @{ Prov = "ON"; MinLon = -95.3; MaxLon = -74.0; MinLat = 41.7; MaxLat = 56.9 },
    @{ Prov = "QC"; MinLon = -79.9; MaxLon = -57.1; MinLat = 45.0; MaxLat = 62.6 },
    @{ Prov = "NB"; MinLon = -69.1; MaxLon = -63.6; MinLat = 44.5; MaxLat = 48.1 },
    @{ Prov = "NS"; MinLon = -66.5; MaxLon = -59.7; MinLat = 43.3; MaxLat = 47.2 },
    @{ Prov = "PE"; MinLon = -64.6; MaxLon = -61.9; MinLat = 45.9; MaxLat = 47.2 },
    @{ Prov = "NL"; MinLon = -67.8; MaxLon = -52.5; MinLat = 46.4; MaxLat = 60.6 },
    @{ Prov = "YT"; MinLon = -141.1; MaxLon = -123.5; MinLat = 59.9; MaxLat = 69.8 },
    @{ Prov = "NT"; MinLon = -136.5; MaxLon = -101.0; MinLat = 60.0; MaxLat = 78.0 },
    @{ Prov = "NU"; MinLon = -120.0; MaxLon = -60.0; MinLat = 60.0; MaxLat = 84.0 }
  )

  $hits = $boxes | Where-Object {
    $Lon -ge $_.MinLon -and $Lon -le $_.MaxLon -and $Lat -ge $_.MinLat -and $Lat -le $_.MaxLat
  }

  if ($hits.Count -eq 1) {
    return "$($hits[0].Prov) (bbox)"
  }
  if ($hits.Count -gt 1) {
    $codes = ($hits | ForEach-Object { $_.Prov }) -join "|"
    return "$codes (overlap)"
  }

  return "Unknown"
}

$data = Get-Content -Raw -Path $InputPath | ConvertFrom-Json
$features = @($data.features)

$rows = for ($i = 0; $i -lt $features.Count; $i++) {
  $feature = $features[$i]
  $props = $feature.properties
  $geom = Get-GeometryMetrics -Geometry $feature.geometry

  $zoneType = [string]$props.zone_type
  $class = [string]$props.class

  $typeCheckedDefault = $true
  $visibleDefault = $false
  if ($zoneType -in @("CONTROL_ZONE", "TERMINAL_CONTROL_AREA", "TRANSITION_AREA", "RESTRICTED", "DANGER", "ADVISORY")) {
    $visibleDefault = $true
  }
  if (-not $visibleDefault -and $class -in @("D", "F")) {
    $visibleDefault = $true
  }

  [pscustomobject]@{
    feature_index = $i
    id = [string]$feature.id
    source_id = [string]$props.id
    name = [string]$props.name
    class = $class
    designation = [string]$props.designation
    zone_type = $zoneType
    type = [string]$props.type
    lower = [string]$props.lower
    upper = [string]$props.upper
    lower_agl_m = [string]$props.lower_agl_m
    upper_agl_m = [string]$props.upper_agl_m
    lower_msl_m = [string]$props.lower_msl_m
    upper_msl_m = [string]$props.upper_msl_m
    active = [string]$props.active
    section = [string]$props.section
    geometry_type = [string]$feature.geometry.type
    vertex_count = $geom.VertexCount
    bbox_min_lon = $geom.MinLon
    bbox_min_lat = $geom.MinLat
    bbox_max_lon = $geom.MaxLon
    bbox_max_lat = $geom.MaxLat
    centroid_lon = $geom.CentroidLon
    centroid_lat = $geom.CentroidLat
    province_estimate = Get-ProvinceEstimate -Lon $geom.CentroidLon -Lat $geom.CentroidLat
    province_method = "centroid_bbox"
    type_checked_default = $typeCheckedDefault
    visible_default = $visibleDefault
  }
}

$dir = Split-Path -Parent $OutputPath
if ($dir -and -not (Test-Path $dir)) {
  New-Item -Path $dir -ItemType Directory -Force | Out-Null
}

$rows | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

$provinceCounts = $rows |
  Group-Object province_estimate |
  Sort-Object Count -Descending |
  Select-Object -First 10

Write-Output "Wrote: $OutputPath"
Write-Output "Rows: $($rows.Count)"
Write-Output "Top province estimates:"
$provinceCounts | ForEach-Object { Write-Output (" - {0}: {1}" -f $_.Name, $_.Count) }
