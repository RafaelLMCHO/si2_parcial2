$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)
docker compose up -d db

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    docker compose exec -T db pg_isready -U postgres -d fashionstore *> $null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    throw 'PostgreSQL no respondio a tiempo.'
}

docker compose exec -T db psql -U postgres -d fashionstore -v ON_ERROR_STOP=1 -f /workspace/tests/00_reset.sql
docker compose exec -T db psql -U postgres -d fashionstore -v ON_ERROR_STOP=1 -f /workspace/db/run_all.sql

Write-Host 'Base de datos FashionStore lista en localhost:5434.'
