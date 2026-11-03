param(
  [string]$ApiBaseUrl = 'http://10.0.2.2:8000/api/v1',
  [string]$Device = ''
)

$ErrorActionPreference = 'Stop'

Set-Location (Join-Path (Split-Path -Parent $PSScriptRoot) 'mobile')

$flutterArgs = @('run', "--dart-define=API_BASE_URL=$ApiBaseUrl")
if (-not [string]::IsNullOrWhiteSpace($Device)) {
  $flutterArgs += @('-d', $Device)
}

flutter @flutterArgs
