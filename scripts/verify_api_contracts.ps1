<#
.SYNOPSIS
    Verifica estaticamente que todas las rutas HTTP consumidas en frontend/src/app
    y mobile/lib existan en backend/app/api/routers/*.py y backend/app/main.py.
    No levanta ningun servidor ni requiere dependencias de red.
#>
[CmdletBinding()]
param(
    [switch]$ShowAll
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $RepoRoot 'backend\app'
$MainPyPath = Join-Path $BackendRoot 'main.py'
$ConfigPyPath = Join-Path $BackendRoot 'core\config.py'
$RoutersDir = Join-Path $BackendRoot 'api\routers'
$FrontendAppDir = Join-Path $RepoRoot 'frontend\src\app'
$MobileLibDir = Join-Path $RepoRoot 'mobile\lib'

function Normalize-ApiPath {
    param(
        [string]$RawPath,
        [string]$ApiPrefix = '/api/v1',
        [string]$BaseUrl = ''
    )

    if (-not $RawPath) { return '' }
    $p = ($RawPath -replace '\s+', ' ').Trim()

    if ($BaseUrl) {
        $p = $p.Replace('${this.baseUrl}', $BaseUrl)
    }
    $p = $p.Replace('${environment.apiUrl}', $ApiPrefix)
    $p = $p.Replace('${this.apiUrl}', $ApiPrefix)
    $p = $p.Replace('${this.carritoUrl}', "$ApiPrefix/carrito")
    $p = $p.Replace('${AppConfig.apiBaseUrl}', $ApiPrefix)

    # Reemplazar interpolaciones ${...} (TS/Dart) y $var (Dart) por {param}
    $p = [regex]::Replace($p, '\$\{[^}]+\}', '{param}')
    $p = [regex]::Replace($p, '\$[A-Za-z_][A-Za-z0-9_]*', '{param}')
    # Normalizar parametros path backend {reserva_id}, {id}, etc.
    $p = [regex]::Replace($p, '\{[^}]+\}', '{param}')

    $qIdx = $p.IndexOf('?')
    if ($qIdx -ge 0) {
        $p = $p.Substring(0, $qIdx)
    }

    if ($p -eq '' -or $p -eq '/') {
        if ($BaseUrl) { $p = $BaseUrl }
    }

    if (-not $p.StartsWith($ApiPrefix) -and -not $p.StartsWith('/health')) {
        if (-not $p.StartsWith('/')) {
            $p = '/' + $p
        }
        $p = $ApiPrefix.TrimEnd('/') + $p
    }

    if ($p.Length -gt 1) {
        $p = $p.TrimEnd('/')
    }
    return $p
}

# 1. Leer api_prefix desde config.py
$ApiPrefix = '/api/v1'
if (Test-Path $ConfigPyPath) {
    $cfgText = Get-Content -Raw -Encoding UTF8 $ConfigPyPath
    $mPrefix = [regex]::Match($cfgText, 'api_prefix\s*:\s*str\s*=\s*[''"]([^''"]+)[''"]')
    if ($mPrefix.Success) {
        $ApiPrefix = $mPrefix.Groups[1].Value.TrimEnd('/')
    }
}

# 2. Leer app.include_router(...) y rutas directas @app.* desde backend/app/main.py
$MainText = Get-Content -Raw -Encoding UTF8 $MainPyPath
$MainLines = $MainText -split "`r?`n"

$IncludedRouters = @{} # key: "module.router_var" -> outer prefix
foreach ($line in $MainLines) {
    $trim = $line.Trim()
    if ($trim.StartsWith('#')) { continue }
    $mInc = [regex]::Match($trim, 'app\.include_router\(\s*([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)(?:.*prefix\s*=\s*([^,\)]+))?')
    if ($mInc.Success) {
        $modName = $mInc.Groups[1].Value
        $varName = $mInc.Groups[2].Value
        $rawPfx = $mInc.Groups[3].Value.Trim()
        $outerPfx = ''
        if ($rawPfx -eq 'settings.api_prefix' -or $rawPfx -eq '') {
            $outerPfx = if ($rawPfx -eq 'settings.api_prefix') { $ApiPrefix } else { '' }
        } else {
            $outerPfx = $rawPfx.Trim("'", '"')
        }
        $IncludedRouters["$modName.$varName"] = $outerPfx
    }
}

$BackendRoutes = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

# Rutas directas en app (e.g. @app.get("/health"))
$appRouteMatches = [regex]::Matches($MainText, '@app\.(get|post|put|patch|delete)\(\s*[''"]([^''"]*)[''"]', [System.Text.RegularExpressions.RegexOptions]::Singleline)
foreach ($m in $appRouteMatches) {
    $method = $m.Groups[1].Value.ToUpperInvariant()
    $path = [regex]::Replace($m.Groups[2].Value, '\{[^}]+\}', '{param}')
    if ($path.Length -gt 1) { $path = $path.TrimEnd('/') }
    [void]$BackendRoutes.Add("$method $path")
}

# 3. Parsear routers en backend/app/api/routers/*.py
Get-ChildItem -Path $RoutersDir -Filter '*.py' | Sort-Object Name | ForEach-Object {
    $modName = $_.BaseName
    if ($modName -eq '__init__') { return }
    $text = Get-Content -Raw -Encoding UTF8 $_.FullName

    # Encontrar variables APIRouter en el archivo
    $routerPrefixes = @{}
    $routerDecls = [regex]::Matches($text, '(?m)^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*APIRouter\((.*?)\)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    foreach ($rd in $routerDecls) {
        $varName = $rd.Groups[1].Value
        $argsText = $rd.Groups[2].Value
        $innerPrefix = ''
        $mPfx = [regex]::Match($argsText, 'prefix\s*=\s*[''"]([^''"]*)[''"]')
        if ($mPfx.Success) {
            $innerPrefix = $mPfx.Groups[1].Value
        }
        $outerPrefix = if ($IncludedRouters.ContainsKey("$modName.$varName")) {
            $IncludedRouters["$modName.$varName"]
        } else {
            $ApiPrefix
        }
        $routerPrefixes[$varName] = ($outerPrefix.TrimEnd('/') + '/' + $innerPrefix.TrimStart('/')).TrimEnd('/')
    }

    # Encontrar decoradores @<var>.(get|post|put|patch|delete)("...") (soporta multilinea)
    $decMatches = [regex]::Matches($text, '@([A-Za-z_][A-Za-z0-9_]*)\.(get|post|put|patch|delete)\(\s*([''"])([^''"]*)\3', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    foreach ($dm in $decMatches) {
        $varName = $dm.Groups[1].Value
        $method = $dm.Groups[2].Value.ToUpperInvariant()
        $subPath = $dm.Groups[4].Value
        if (-not $routerPrefixes.ContainsKey($varName)) { continue }
        $basePfx = $routerPrefixes[$varName]
        $fullPath = if ($subPath -eq '' -or $subPath -eq '/') {
            $basePfx
        } elseif ($subPath.StartsWith('/')) {
            $basePfx + $subPath
        } else {
            $basePfx + '/' + $subPath
        }
        $fullPath = [regex]::Replace($fullPath, '\{[^}]+\}', '{param}')
        if ($fullPath.Length -gt 1) { $fullPath = $fullPath.TrimEnd('/') }
        [void]$BackendRoutes.Add("$method $fullPath")
    }
}

Write-Host "Rutas backend detectadas: $($BackendRoutes.Count)" -ForegroundColor Cyan

# 4. Escanear llamadas HTTP en frontend/src/app (*.ts) y mobile/lib (*.dart)
$Missing = [System.Collections.Generic.List[psobject]]::new()
$CheckedCount = 0

function Check-ClientCall {
    param(
        [string]$Client,
        [string]$Method,
        [string]$RawUrl,
        [string]$BaseUrl,
        [string]$RelFile,
        [int]$LineNumber
    )
    $script:CheckedCount++
    $resolved = Normalize-ApiPath -RawPath $RawUrl -ApiPrefix $ApiPrefix -BaseUrl $BaseUrl
    $key = "$Method $resolved"
    $exists = $BackendRoutes.Contains($key)
    if ($ShowAll) {
        $tag = if ($exists) { '[OK]  ' } else { '[MISS]' }
        Write-Host "$tag [$Client] $Method $resolved ($RelFile`:$LineNumber)"
    }
    if (-not $exists) {
        $script:Missing.Add([pscustomobject]@{
            Client   = $Client
            Method   = $Method
            Endpoint = $resolved
            Location = "$RelFile`:$LineNumber"
        })
    }
}

# Frontend Angular (.ts)
Get-ChildItem -Path $FrontendAppDir -Recurse -Filter '*.ts' | Sort-Object FullName | ForEach-Object {
    $file = $_
    $text = Get-Content -Raw -Encoding UTF8 $file.FullName
    $rel = $file.FullName.Substring($RepoRoot.Length + 1).Replace('\', '/')

    # Resolver this.baseUrl por archivo si existe
    $baseUrl = ''
    $mBase = [regex]::Match($text, '(?:baseUrl|apiUrl)\s*=\s*(?:`|''|")([^`''"]+)(?:`|''|")')
    if ($mBase.Success) {
        $cand = $mBase.Groups[1].Value
        if ($cand.Contains('${environment.apiUrl}') -or $cand.Contains('${this.apiUrl}') -or $cand.StartsWith('/')) {
            $baseUrl = $cand.Replace('${environment.apiUrl}', $ApiPrefix).Replace('${this.apiUrl}', $ApiPrefix)
            if (-not $baseUrl.StartsWith($ApiPrefix) -and $baseUrl.StartsWith('/')) {
                $baseUrl = $ApiPrefix + $baseUrl
            }
            $baseUrl = $baseUrl.TrimEnd('/')
        }
    }

    # Llamadas con string literal o template string
    $feRegex = [regex]::new('\b(?:this\.)?(?:http|_http)\.(get|post|put|patch|delete)\s*(?:<[^>]*>)?\s*\(\s*([`''"])(.*?)\2', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    foreach ($m in $feRegex.Matches($text)) {
        $method = $m.Groups[1].Value.ToUpperInvariant()
        $rawUrl = $m.Groups[3].Value
        $line = ($text.Substring(0, $m.Index) -split "`n").Count
        Check-ClientCall -Client 'WEB' -Method $method -RawUrl $rawUrl -BaseUrl $baseUrl -RelFile $rel -LineNumber $line
    }

    # Llamadas directas con this.baseUrl o this.carritoUrl sin sufijo
    $feVarRegex = [regex]::new('\b(?:this\.)?(?:http|_http)\.(get|post|put|patch|delete)\s*(?:<[^>]*>)?\s*\(\s*this\.(baseUrl|carritoUrl)\b', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    foreach ($m in $feVarRegex.Matches($text)) {
        $method = $m.Groups[1].Value.ToUpperInvariant()
        $varRef = $m.Groups[2].Value
        $rawUrl = if ($varRef -eq 'carritoUrl') { "$ApiPrefix/carrito" } elseif ($baseUrl) { $baseUrl } else { continue }
        $line = ($text.Substring(0, $m.Index) -split "`n").Count
        Check-ClientCall -Client 'WEB' -Method $method -RawUrl $rawUrl -BaseUrl $baseUrl -RelFile $rel -LineNumber $line
    }
}

# Mobile Flutter (.dart)
Get-ChildItem -Path $MobileLibDir -Recurse -Filter '*.dart' | Sort-Object FullName | ForEach-Object {
    $file = $_
    $text = Get-Content -Raw -Encoding UTF8 $file.FullName
    $rel = $file.FullName.Substring($RepoRoot.Length + 1).Replace('\', '/')

    # Llamadas apiClient.get/post/put/patch/delete con literal de ruta
    $mobRegex = [regex]::new('\b[A-Za-z_][A-Za-z0-9_]*\.(get|post|put|patch|delete)\s*(?:<[^>]*>)?\s*\(\s*([''"])(.*?)\2', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    foreach ($m in $mobRegex.Matches($text)) {
        $method = $m.Groups[1].Value.ToUpperInvariant()
        $rawUrl = ($m.Groups[3].Value -replace '\s+', ' ').Trim()
        if (-not $rawUrl.StartsWith('/') -and -not $rawUrl.Contains('${')) { continue }
        $line = ($text.Substring(0, $m.Index) -split "`n").Count
        Check-ClientCall -Client 'MOB' -Method $method -RawUrl $rawUrl -BaseUrl '' -RelFile $rel -LineNumber $line
    }

    # Helpers internos tipo _ejecutar('/reservas/$id/completar', ...) o final endpoint = ... '/reservas/...'
    $mobHelperRegex = [regex]::new('_[A-Za-z0-9_]*\s*\(\s*([''"])(/[^''"]*)\1', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    foreach ($m in $mobHelperRegex.Matches($text)) {
        $rawUrl = ($m.Groups[2].Value -replace '\s+', ' ').Trim()
        $line = ($text.Substring(0, $m.Index) -split "`n").Count
        # Solo verificar si la funcion helper hace post()
        if ($text -match '_ejecutar\w*\([^)]*\).*?\.post\(' -or $text -match '\.post\(endpoint') {
            Check-ClientCall -Client 'MOB' -Method 'POST' -RawUrl $rawUrl -BaseUrl '' -RelFile $rel -LineNumber $line
        }
    }
}

Write-Host "Llamadas HTTP analizadas: $CheckedCount" -ForegroundColor Cyan

if ($Missing.Count -gt 0) {
    Write-Host "`n[ERROR] Se encontraron $($Missing.Count) llamadas con rutas inexistentes en el backend:" -ForegroundColor Red
    foreach ($item in $Missing) {
        Write-Host ("  [{0}] {1,-6} {2,-55} ({3})" -f $item.Client, $item.Method, $item.Endpoint, $item.Location) -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "`n[OK] Todas las rutas consumidas en frontend y mobile existen en el backend." -ForegroundColor Green
exit 0
