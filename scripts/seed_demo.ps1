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

Write-Host 'Cargando datos demo del tenant demo...'
docker compose exec -T db psql -U postgres -d fashionstore -v ON_ERROR_STOP=1 -f /workspace/db/25_seed_demo.sql
if ($LASTEXITCODE -ne 0) { throw 'Fallo la ejecucion de db/25_seed_demo.sql.' }

Write-Host 'Datos demo cargados. Usuarios: admin@demo.test / cliente@demo.test / cajero@demo.test / encargado@demo.test (password: Admin123! / Cliente123! / Cajero123! / Encargado123!).'
