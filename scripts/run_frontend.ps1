param(
  [string]$BindHost = '127.0.0.1'
)

$ErrorActionPreference = 'Stop'

Set-Location (Join-Path (Split-Path -Parent $PSScriptRoot) 'frontend')
npm start -- --host $BindHost --port 4200
