# FashionStore SaaS - Segundo Parcial

Implementacion de CU-01 a CU-04 para clientes PWA (Angular) y Android
(Flutter/Dart), con backend FastAPI, PostgreSQL 16 y auditoria CU-05.

## Estructura

| Carpeta | Contenido |
|---|---|
| `db/` | DDL modular, RLS, triggers, seeds y ajustes CU-01..CU-05. |
| `tests/` | Pruebas SQL de aislamiento, RLS, auditoria y cobertura. |
| `backend/` | API FastAPI con JWT, RLS multitenant y auditoria. |
| `frontend/` | PWA Angular con login, registro, verificacion y perfil. |
| `mobile/` | App Flutter/Dart Android con los mismos CU y soporte offline. |
| `docs/` | Robustez, secuencias, clases ICONIX y guia movil. |
| `scripts/` | Arranque de base de datos, backend, PWA y app movil. |

## Requisitos

- Docker Desktop
- Python 3.12
- Node.js 20+ y npm
- Flutter 3.47+ con Android SDK para compilar la app movil

## Arranque web

```powershell
# 1. Base de datos (PostgreSQL 16 en localhost:5434)
.\scripts\init_db.ps1

# 2. Backend (http://127.0.0.1:8000)
.\scripts\run_backend.ps1

# 3. PWA Angular (http://127.0.0.1:4200)
.\scripts\run_frontend.ps1
```

La PWA usa `/api/v1` y el proxy de Angular hacia `127.0.0.1:8000`. El Service
Worker solo se activa en compilaciones de produccion (`npm run build`).

## Arranque Android

El emulador Android accede al host mediante `10.0.2.2`.

```powershell
# Backend accesible desde el emulador
.\scripts\run_backend.ps1 -BindHost 0.0.0.0

# App en emulador o dispositivo conectado
.\scripts\run_mobile.ps1
```

Para un dispositivo fisico en la misma red, usar la IP LAN de la PC:

```powershell
.\scripts\run_mobile.ps1 `
  -ApiBaseUrl http://192.168.1.10:8000/api/v1 `
  -Device <device-id>
```

El trafico HTTP local esta permitido solo en Android debug. Una compilacion
release requiere HTTPS o una configuracion de red explicita. El APK debug se
genera en `mobile/build/app/outputs/flutter-apk/app-debug.apk`.

## Usuarios demo

| Rol | Empresa | Correo | Contrasena |
|---|---|---|---|
| Administrador | `demo` | `admin@demo.test` | `Admin123!` |
| Cliente | `demo` | `cliente@demo.test` | `Cliente123!` |
| Superadmin | global | `superadmin@fashionstore.test` | `Superadmin123!` |

## Pruebas

```powershell
# Suite SQL y API
.\scripts\run_tests.ps1

# App Flutter
cd mobile
flutter analyze
flutter test

# PWA
cd frontend
npm run build
```

## Endpoints CU-01..CU-05

| Metodo | Ruta |
|---|---|
| POST | `/api/v1/auth/login` |
| POST | `/api/v1/auth/refresh` |
| POST | `/api/v1/auth/logout` |
| POST | `/api/v1/auth/register` |
| POST | `/api/v1/auth/verify-email` |
| GET | `/api/v1/users/me` |
| PATCH | `/api/v1/users/me` |
| POST | `/api/v1/users/me/password` |

## Comportamiento offline

- La PWA conserva tokens y usuario en `localStorage`; la app Flutter usa
  `flutter_secure_storage` para tokens y SQLite para usuario, tenant, ultima
  sincronizacion y cola offline.
- Sin conexion se puede consultar el perfil cacheado, pero no guardar cambios,
  verificar correo ni iniciar sesion.
- El logout elimina la sesion local y conserva la cola offline y el tenant.
- Las respuestas `401` intentan refresh una vez; un error de red no cierra la
  sesion.

## Notas de seguridad

- El login resuelve el tenant con `empresa_slug` porque el correo es unico por
  empresa.
- El registro exige verificar el correo antes de iniciar sesion.
- El JWT incluye `sid`; el logout revoca la sesion en `sesion.revocado_en`.
- El middleware de auditoria redacta contrasenas, tokens y secretos.
- En modo demo el token de verificacion se devuelve en la respuesta de registro;
  desactivar con `EXPOSE_VERIFICATION_TOKEN=false`.
- CU-03 no administra direcciones: solo nombre, telefono, seguridad y estado de
  cuenta.

La guia detallada de clientes esta en `docs/CU01_CU04_MOVIL.md`.
