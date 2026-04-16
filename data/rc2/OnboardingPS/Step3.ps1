# ── Step 3: Build UUID Inventory ─────────────────────────────────────────────

# Load config
$configPointer = Join-Path $env:USERPROFILE "rc2_missions_config_path.txt"
if(-not (Test-Path $configPointer)){
  throw "CONFIG_POINTER_NOT_FOUND. Run Step 1 first."
}
$configPath = (Get-Content $configPointer -Raw).Trim()
if(-not (Test-Path $configPath)){
  throw "CONFIG_NOT_FOUND. Run Step 1 again to regenerate local_config.json."
}
$config  = Get-Content $configPath -Raw | ConvertFrom-Json
$root    = $config.managerRoot
$logRoot = $config.logRoot

# ── Logging setup ─────────────────────────────────────────────────────────────
$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logRoot "step3_inventory_$stamp.log"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Write-StepLog {
  param([string]$Level, [string]$Message)
  $entry = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level.ToUpper(), $Message
  $entry | Add-Content -Path $logFile -Encoding UTF8
  Write-Host $entry
}

function Get-MtpChildFolder {
  param($folder, [string]$name)
  if(-not $folder){ return $null }
  foreach($x in $folder.Items()){
    if($x.Name -eq $name){ return $x.GetFolder() }
  }
  return $null
}

try {
  Write-StepLog INFO "Step 3 started. Scanning RC2 UUID slots for inventory."

  # ── Re-connect to RC2 via MTP ──────────────────────────────────────────────
  $shell = New-Object -ComObject Shell.Application
  $pc    = $shell.Namespace('shell:MyComputerFolder')
  $rc    = $null
  foreach($i in $pc.Items()){
    if($i.Name -like '*DJI RC 2*'){ $rc = $i; break }
  }
  if(-not $rc){
    throw "DJI RC 2 not found. Connect RC2 by USB, unlock controller, set USB mode to File Transfer (MTP), then retry Step 3."
  }
  Write-StepLog INFO "RC2 device detected: $($rc.Name)"

  $f = $rc.GetFolder()
  $f = Get-MtpChildFolder $f 'Internal shared storage'
  $f = Get-MtpChildFolder $f 'Android'
  $f = Get-MtpChildFolder $f 'data'
  $f = Get-MtpChildFolder $f 'dji.go.v5'
  $f = Get-MtpChildFolder $f 'files'
  $f = Get-MtpChildFolder $f 'waypoint'

  if(-not $f){
    throw "Waypoint folder not found on RC2. Confirm a mission was saved in DJI Fly, then retry Step 3."
  }
  Write-StepLog INFO "Waypoint folder located on RC2."

  function Wait-ForCopiedFile {
    param(
      [Parameter(Mandatory=$true)][string]$Path,
      [int]$TimeoutSeconds = 15
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastSize = -1
    while((Get-Date) -lt $deadline){
      if(Test-Path $Path){
        $item = Get-Item $Path -ErrorAction SilentlyContinue
        if($item){
          if($item.Length -gt 0 -and $item.Length -eq $lastSize){
            return $true
          }
          $lastSize = $item.Length
        }
      }
      Start-Sleep -Milliseconds 300
    }

    return (Test-Path $Path)
  }

  # ── Copy KMZ files to a unique local scan folder for this run ─────────────
  $scanRoot = Join-Path $root "REGISTRY/slot_scan"
  $scanDir  = Join-Path $scanRoot $stamp
  New-Item -ItemType Directory -Force -Path $scanDir | Out-Null
  $dest = $shell.Namespace((Resolve-Path $scanDir).Path)

  $copied = 0
  foreach($slot in $f.Items()){
    if($slot.IsFolder -and $slot.Name -match '^[0-9A-F-]{36}$'){
      $sf = $slot.GetFolder()
      foreach($child in $sf.Items()){
        if(-not $child.IsFolder -and $child.Name -eq ($slot.Name + '.kmz')){
          Write-StepLog INFO "Copying KMZ: $($child.Name)"
          $dest.CopyHere($child, 16)
          $targetPath = Join-Path $scanDir $child.Name
          if(-not (Wait-ForCopiedFile -Path $targetPath)){
            throw "Timed out waiting for copied file: $targetPath"
          }
          $copied++
        }
      }
    }
  }

  if($copied -eq 0){
    throw "No KMZ files found in any UUID slot. Save at least one mission in DJI Fly, then retry Step 3."
  }
  Write-StepLog INFO "Copied $copied KMZ file(s) to $scanDir"

  # ── Parse metadata from each KMZ ──────────────────────────────────────────
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $rows = @()

  Get-ChildItem $scanDir -Filter *.kmz | ForEach-Object {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($_.FullName)
    try {
      $entry = $zip.Entries | Where-Object { $_.FullName -ieq 'wpmz/template.kml' } | Select-Object -First 1
      if(-not $entry){
        $entry = $zip.Entries | Where-Object { $_.FullName -ieq 'wpmz/waylines.wpml' } | Select-Object -First 1
      }
      $ct = ''; $ut = ''; $author = ''
      $ctLocal = ''; $utLocal = ''
      if($entry){
        $sr  = New-Object System.IO.StreamReader($entry.Open())
        $txt = $sr.ReadToEnd(); $sr.Close()
        $ct     = [regex]::Match($txt, '<wpml:createTime>(\d+)</wpml:createTime>').Groups[1].Value
        $ut     = [regex]::Match($txt, '<wpml:updateTime>(\d+)</wpml:updateTime>').Groups[1].Value
        $author = [regex]::Match($txt, '<wpml:author>([^<]+)</wpml:author>').Groups[1].Value
        if($ct){
          try { $ctLocal = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$ct).ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss') } catch {}
        }
        if($ut){
          try { $utLocal = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$ut).ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss') } catch {}
        }
      }
      $rows += [PSCustomObject]@{
        UUID          = $_.BaseName
        FileLastWriteLocal = $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
        CreateTimeLocal = $ctLocal
        UpdateTimeLocal = $utLocal
        CreateTimeMs  = $ct
        UpdateTimeMs  = $ut
        Author        = $author
        File          = $_.Name
      }
      Write-StepLog INFO "Parsed: $($_.BaseName) | fileDate=$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')) | author=$author"
    }
    finally { $zip.Dispose() }
  }

  # ── Write inventory CSV ────────────────────────────────────────────────────
  $invPath = Join-Path $root "REGISTRY/uuid_inventory.csv"
  $rows | Sort-Object FileLastWriteLocal -Descending |
    Export-Csv -NoTypeInformation -Path $invPath
  Write-StepLog INFO "uuid_inventory.csv written: $invPath"

  Write-StepLog INFO "Step 3 completed successfully."
  Write-Host ""
  Write-Host "Log file: $logFile"
  Write-Host "[PASS] Step 3 validation checks passed."
  Write-Host "[SUCCESS] Step 3 completed successfully."
  Write-Host "[COMPLETE] Step 3: UUID inventory saved."
  Write-Host ""
  $rows | Sort-Object FileLastWriteLocal -Descending |
    Format-Table UUID, FileLastWriteLocal, CreateTimeLocal, Author, File -AutoSize
}
catch {
  Write-StepLog ERROR $_.Exception.Message
  if($_.FullyQualifiedErrorId){
    Write-StepLog ERROR "FullyQualifiedErrorId: $($_.FullyQualifiedErrorId)"
    Write-Host "Error ID: $($_.FullyQualifiedErrorId)"
  }
  Write-Host "[FAILED] Step 3 failed."
  Write-Host "Step 3 failed. See log: $logFile"
  throw
}