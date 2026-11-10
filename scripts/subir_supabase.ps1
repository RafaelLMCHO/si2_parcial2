param(
    [Parameter(Mandatory = $false)]
    [string]$SupabaseUrl = "",

    [switch]$SoloPrepararDump,

    [switch]$UsarDumpExistente
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$RawDump = Join-Path $RepoRoot 'supabase_dump.sql'
$ReadyDump = Join-Path $RepoRoot 'supabase_dump_ready.sql'

if (-not ($UsarDumpExistente -and (Test-Path $ReadyDump))) {
    Write-Host '1/4 Exportando base de datos completa desde Docker (fashionstore)...' -ForegroundColor Cyan
    docker compose up -d db | Out-Null
    docker compose exec -T db pg_dump -U postgres -d fashionstore --no-owner --no-privileges -f /tmp/supabase_dump.sql
    if ($LASTEXITCODE -ne 0) { throw 'Error al ejecutar pg_dump en Docker.' }

    docker cp fashionstore-segundo-db:/tmp/supabase_dump.sql $RawDump
    if ($LASTEXITCODE -ne 0) { throw 'Error al copiar supabase_dump.sql desde el contenedor.' }

    Write-Host '2/4 Adaptando dump para compatibilidad 100% con Supabase (extensiones, roles y RLS)...' -ForegroundColor Cyan
    $sql = Get-Content $RawDump -Raw -Encoding UTF8

# Quitar directivas \restrict / \unrestrict y comentarios de extension/schema que requieren superuser en Supabase
$sql = [regex]::Replace($sql, '(?m)^\\(un)?restrict\s+.*$\r?\n?', '')
$sql = [regex]::Replace($sql, '(?m)^COMMENT ON EXTENSION\s+.*$\r?\n?', '')
$sql = [regex]::Replace($sql, '(?m)^COMMENT ON SCHEMA public IS .*$\r?\n?', '')

$header = @"
-- ============================================================================
-- PREPARACION AUTOMATICA PARA SUPABASE (FashionStore Multi-Tenant)
-- ============================================================================
SET search_path TO public, extensions;

DO `$`$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'citext') THEN
        EXECUTE 'ALTER EXTENSION citext SET SCHEMA public';
    ELSE
        EXECUTE 'CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto') THEN
        EXECUTE 'ALTER EXTENSION pgcrypto SET SCHEMA public';
    ELSE
        EXECUTE 'CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public';
    END IF;
END `$`$;

DO `$`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fashion_app') THEN
        EXECUTE 'CREATE ROLE fashion_app NOLOGIN NOBYPASSRLS';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fashion_superadmin') THEN
        EXECUTE 'CREATE ROLE fashion_superadmin NOLOGIN NOBYPASSRLS';
    END IF;
END `$`$;

GRANT fashion_app, fashion_superadmin TO postgres;

"@

$footer = @"

-- ============================================================================
-- POST-MIGRACION SUPABASE: PERMISOS Y POLITICAS RLS PARA SUPERADMIN SIN BYPASSRLS
-- ============================================================================
SET search_path TO public, extensions;
ALTER DATABASE postgres SET search_path TO public, extensions;

GRANT USAGE ON SCHEMA public TO fashion_app, fashion_superadmin;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fashion_app, fashion_superadmin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fashion_app, fashion_superadmin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fashion_app, fashion_superadmin;

REVOKE INSERT, UPDATE, DELETE ON public.plan, public.plan_limite, public.permiso, public.ciudad, public.color, public.talla FROM fashion_app;
REVOKE INSERT, UPDATE, DELETE ON public.bitacora_auditoria FROM fashion_app;

-- En Supabase no existe BYPASSRLS para roles de usuario; permitimos acceso global a fashion_superadmin
DO `$`$
DECLARE
    p record;
    new_qual text;
    new_with_check text;
    cmd text;
BEGIN
    FOR p IN
        SELECT schemaname, tablename, policyname, qual, with_check
          FROM pg_policies
         WHERE schemaname = 'public'
    LOOP
        new_qual := CASE
            WHEN p.qual IS NOT NULL AND p.qual <> '' THEN '(' || p.qual || ') OR (current_user = ''fashion_superadmin'')'
            ELSE NULL
        END;
        new_with_check := CASE
            WHEN p.with_check IS NOT NULL AND p.with_check <> '' THEN '(' || p.with_check || ') OR (current_user = ''fashion_superadmin'')'
            ELSE NULL
        END;

        cmd := format('ALTER POLICY %I ON %I.%I', p.policyname, p.schemaname, p.tablename);
        IF new_qual IS NOT NULL THEN
            cmd := cmd || format(' USING (%s)', new_qual);
        END IF;
        IF new_with_check IS NOT NULL THEN
            cmd := cmd || format(' WITH CHECK (%s)', new_with_check);
        END IF;
        EXECUTE cmd;
    END LOOP;
END `$`$;
"@

[System.IO.File]::WriteAllText($ReadyDump, $header + $sql + $footer, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "Dump listo generado en: $ReadyDump" -ForegroundColor Green
}

if ($SoloPrepararDump -or [string]::IsNullOrWhiteSpace($SupabaseUrl)) {
    Write-Host 'Modo preparacion completado. Ejecuta con -SupabaseUrl "postgresql://..." para subirlo a Supabase.' -ForegroundColor Yellow
    exit 0
}

# Extraer componentes de la URI para evitar problemas de escape en PowerShell/Docker
$RawUrl = $SupabaseUrl.Trim()
if ($RawUrl -notmatch '^postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):(\d+)/([^?]+)') {
    throw 'Formato de URL invalido. Debe ser postgresql://usuario:password@host:5432/postgres'
}
$DbUser = $Matches[1]
$DbPassRaw = $Matches[2]
$DbPassDecoded = [System.Uri]::UnescapeDataString($DbPassRaw)
$DbPassEncoded = $DbPassDecoded.Replace('$', '%24')
$DbHost = $Matches[3]
$DbPort = $Matches[4]
$DbName = $Matches[5]

$CleanUrl = "postgresql://${DbUser}:${DbPassEncoded}@${DbHost}:${DbPort}/${DbName}?sslmode=require"

Write-Host '3/4 Subiendo esquema, politicas RLS y datos de las 6 empresas a Supabase...' -ForegroundColor Cyan
docker cp $ReadyDump fashionstore-segundo-db:/tmp/supabase_dump_ready.sql
if ($LASTEXITCODE -ne 0) { throw 'Error al copiar supabase_dump_ready.sql al contenedor.' }

docker compose exec -T -e "PGPASSWORD=$DbPassDecoded" -e "PGSSLMODE=require" db psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -v ON_ERROR_STOP=1 -f /tmp/supabase_dump_ready.sql
if ($LASTEXITCODE -ne 0) { throw 'Fallo la carga en Supabase. Verifica que la base de datos en Supabase este vacia y la URL sea Session Pooler (:5432).' }

Write-Host '4/4 Actualizando backend/.env con la URL de Supabase...' -ForegroundColor Cyan
$EnvFile = Join-Path $RepoRoot 'backend\.env'
if (Test-Path $EnvFile) {
    Copy-Item $EnvFile "$EnvFile.local.bak" -Force
    $envContent = Get-Content $EnvFile -Raw -Encoding UTF8
    if ($envContent -match '(?m)^DATABASE_URL=.*$') {
        $envContent = [regex]::Replace($envContent, '(?m)^DATABASE_URL=.*$', "DATABASE_URL=$CleanUrl")
    } else {
        $envContent = "DATABASE_URL=$CleanUrl`r`n" + $envContent
    }
    [System.IO.File]::WriteAllText($EnvFile, $envContent, (New-Object System.Text.UTF8Encoding($false)))
}

Write-Host 'Migracion a Supabase completada con exito.' -ForegroundColor Green

