$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)

docker compose up -d db
if ($LASTEXITCODE -ne 0) { throw 'No se pudo levantar el contenedor de base de datos.' }

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

Write-Host 'Cargando datos completos para las 5 empresas adicionales (zara, mango, hm, pullbear, bershka)...'
docker compose exec -T db psql -U postgres -d fashionstore -v ON_ERROR_STOP=1 -f /workspace/db/28_seed_empresas_adicionales.sql
if ($LASTEXITCODE -ne 0) { throw 'Fallo la ejecucion de db/28_seed_empresas_adicionales.sql.' }

Write-Host 'Empresas adicionales pobladas correctamente (clientes: cliente@<slug>.bo y cliente1..6@<slug>.bo / Cliente123!).'

