param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('Mission_B','Mission_A','Mission_C')]
  [string]$TargetRole,

  [string]$SourceRollbackKmz
)

$fallbackScript = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "Step8_RestoreFallback.ps1"
if(-not (Test-Path $fallbackScript)){
  throw "Step8_RestoreFallback.ps1 not found beside this script: $fallbackScript"
}

$invokeArgs = @{ TargetRole = $TargetRole }
if(-not [string]::IsNullOrWhiteSpace($SourceRollbackKmz)){
  $invokeArgs.SourceFallbackKmz = $SourceRollbackKmz
}

& $fallbackScript @invokeArgs
