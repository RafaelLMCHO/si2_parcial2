param(
  [string]$BindHost = '127.0.0.1'
)

$ErrorActionPreference = 'Stop'

Set-Location (Join-Path (Split-Path -Parent $PSScriptRoot) 'backend')
python -m uvicorn app.main:app --reload --host $BindHost --port 8000
