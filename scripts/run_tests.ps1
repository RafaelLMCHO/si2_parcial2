$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)
docker compose exec -T db psql -U postgres -d fashionstore -v ON_ERROR_STOP=1 -f /workspace/tests/run_tests.sql

Push-Location backend
try {
    python -m pytest -q
}
finally {
    Pop-Location
}
