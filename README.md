# FashionStore SaaS - Segundo Parcial

Implementación completa de **CU-01 a CU-37** para clientes PWA (Angular) y
Android (Flutter/Dart), con backend FastAPI multitenant, PostgreSQL 16 (RLS),
integraciones Stripe Sandbox / LLM / scikit-learn / Decart Lucy VTON, soporte
offline con Soft-Locks e idempotencia y gestión de backups.

## Estructura

| Carpeta | Contenido |
|---|---|
| `db/` | DDL modular, RLS, triggers, seeds, assets AR (`17_ar.sql`) y ajustes `CU-01..CU-37`. |
| `tests/` | Pruebas SQL de aislamiento, concurrencia, offline, RLS, límites SaaS y cobertura. |
| `backend/` | API FastAPI multitenant con JWT, RLS, auditoría, Stripe, LLM, ML, AR y Backups. |
| `frontend/` | PWA Angular con los módulos CU-01..CU-37 (incluyendo Bloqueos activos y Backups). |
| `mobile/` | App Flutter/Dart Android con paridad funcional, SQLite offline, Soft-Locks y Backups. |
| `docs/` | Robustez, secuencias, clases ICONIX y guías técnicas. |
| `scripts/` | Inicialización de DB, ejecución de servidores, verificación de contratos y pruebas. |

## Requisitos

- Docker Desktop
- Python 3.12+ (`backend/.venv` configurado)
- Node.js 20+ y npm
- Flutter 3.47+ con Android SDK para compilar la app móvil

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
Worker solo se activa en compilaciones de producción (`npm run build`).

## Arranque Android

El emulador Android accede al host mediante `10.0.2.2`.

```powershell
# Backend accesible desde el emulador
.\scripts\run_backend.ps1 -BindHost 0.0.0.0

# App en emulador o dispositivo conectado
.\scripts\run_mobile.ps1
```

Para un dispositivo físico en la misma red, usar la IP LAN de la PC:

```powershell
.\scripts\run_mobile.ps1 `
  -ApiBaseUrl http://192.168.1.10:8000/api/v1 `
  -Device <device-id>
```

El tráfico HTTP local está permitido solo en Android debug. Una compilación
release requiere HTTPS o una configuración de red explícita.

## Usuarios demo

| Rol | Empresa | Correo | Contraseña |
|---|---|---|---|
| Administrador | `demo` | `admin@demo.test` | `Admin123!` |
| Cliente | `demo` | `cliente@demo.test` | `Cliente123!` |
| Superadmin | global | `superadmin@fashionstore.test` | `Superadmin123!` |

## Variables de entorno (Integraciones Bloque 3)

Configurar en `backend/.env` tomando como plantilla [`backend/.env.example`](backend/.env.example):

| Caso de Uso | Variables | Comportamiento en ejecución |
|---|---|---|
| **CU-24 Stripe Sandbox** | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `PAYMENT_CURRENCY` | Con `sk_test_*` configurada usa `StripeGateway` real (PaymentIntent, confirmación, conciliación, reembolso) y verifica firma HMAC en `POST /api/v1/pagos/webhook/stripe`. Sin clave configurada conserva el fallback local para pruebas. |
| **CU-34 IA Generativa** | `LLM_API_KEY`, `LLM_MODEL`, `LLM_API_URL` | Clasifica consultas con LLM sobre un catálogo estricto de intenciones (**whitelist BR-08**); nunca ejecuta SQL generado por el modelo y realiza fallback determinista a regex si falta clave o falla el proveedor. Registra cada ejecución en `consulta_ia_log`. |
| **CU-36 Vestidor Virtual / Lucy VTON** | `DECART_API_KEY`, `DECART_MODEL`, `DECART_API_URL` | `POST /api/v1/vestidor/lucy-session` solicita sesión WebRTC al API de Decart y responde HTTP `503 DECART_NO_CONFIGURADO` si falta `DECART_API_KEY`. El catálogo AR carga assets sembrados en `db/17_ar.sql`. |

## Limitaciones y requisitos de datos ML (CU-35)

El módulo de analítica predictiva (`GET /api/v1/inteligencia/ml/dashboard`,
`/demanda`, `/segmentacion`) entrena modelos reales con `scikit-learn`:

- **Predicción de demanda (`LinearRegression`)**: requiere al menos **6 meses** de
  histórico de ventas confirmadas/pagadas por categoría (`min_meses = 6`). Si
  no existe ese histórico, devuelve `estado = "datos_insuficientes"`, `es_demo = false`
  y las métricas en `None` (no inyecta datos sintéticos en producción salvo que se
  solicite explícitamente `?demo=true`). Cuando entrena devuelve `r2` y `mse` reales.
- **Segmentación RFM de clientes (`KMeans`)**: requiere al menos **4 clientes**
  activos en la empresa (`min_clientes = 4`). Con menos clientes devuelve
  `estado = "datos_insuficientes"` (o dataset demo solo con `?demo=true`) y
  reporta `inertia` real al entrenar.

## Contratos API canónicos clave

| CU | Ruta canónica | Notas |
|---|---|---|
| CU-01 | `POST /api/v1/auth/register-tenant` | Alta pública de empresa (tenant) + usuario administrador inicial. |
| CU-05 | `GET /api/v1/auditoria/logs` | Consulta paginada y aislada por `empresa_id` sobre `bitacora_auditoria`. |
| CU-06 | `GET / POST / PUT / DELETE /api/v1/saas/planes` | CRUD completo de planes SaaS para `superadmin` con validación de código único y suscripciones activas. |
| CU-07 | `GET / PUT /api/v1/mi-suscripcion`, `POST /api/v1/mi-suscripcion/cancelar` | Consulta, cambio de plan con reglas `BR-02/BR-03` y cancelación desde administrador tenant. |
| CU-08 | `GET /api/v1/saas/facturas/{factura_id}/pdf` | Descarga de factura PDF generada con ReportLab y auditoría. |
| CU-18 | `GET /api/v1/inventario/prendas/{prenda_id}/disponibilidad` | **Contrato canónico** unificado. (`/api/v1/prendas/{prenda_id}/disponibilidad` se mantiene marcado `deprecated=True`). |
| CU-20 / CU-21 | `GET /api/v1/reservas/mis-reservas`, `POST /api/v1/reservas/{id}/completar` | Listado propio del cliente y cierre completado en tienda por staff/encargado/admin. |
| CU-24 | `GET /api/v1/pagos`, `POST /api/v1/pagos/{pago_id}/reembolsar`, `POST /api/v1/pagos/webhook/stripe` | Listado, reembolso total/parcial vía `StripeGateway` y webhook firmado. |
| CU-27 | `GET / POST /api/v1/sync/soft-locks`, `DELETE /api/v1/sync/soft-locks/{lock_id}` | Bloqueos temporales con TTL expuestos en la vista **Bloqueos activos** (`/offline/bloqueos` web y móvil). |
| CU-37 | `/api/v1/backups*` | Gestión integral de respaldos manuales/automáticos, nube/local y restauración en web y móvil. |

## Matriz de cobertura completa (CU-01 a CU-37)

| CU | Backend | Web (Angular) | Móvil (Flutter) | Test | Estado |
|---|---|---|---|---|---|
| CU-01 | `routers/auth.py` (`login`, `register-tenant`) | `features/auth/login`, `features/saas/empresa-form` | `features/auth/presentation/login_screen.dart` | `test_cu01_05.py`, `test_e2e_36_cu.py` | completo |
| CU-02 | `routers/auth.py` (`register`, `verify-email`) | `features/auth/{register,verify-email}` | `features/auth/presentation/{register,verify_email}_screen.dart` | `test_cu01_05.py`, `07_cobertura_36.sql`, `test_e2e_36_cu.py` | completo |
| CU-03 | `routers/users.py` (`/users/me*`) | `features/profile/profile.component.ts` | `features/profile/presentation/profile_screen.dart` | `test_cu01_05.py`, `test_e2e_36_cu.py` | completo |
| CU-04 | `routers/auth.py` (`refresh`, `logout`) | `core/auth.service.ts`, `auth.interceptor.ts` | `features/auth/data/auth_repository.dart` | `test_cu01_05.py`, `test_e2e_36_cu.py` | completo |
| CU-05 | `middleware/audit.py` + `routers/auditoria.py` | `features/auditoria/auditoria.component.ts` | `features/auditoria/presentation/auditoria_screen.dart` | `test_cu01_05.py`, `05_rls_auditoria.sql`, `test_e2e_36_cu.py` | completo |
| CU-06 | `routers/saas.py` (`/saas/planes*`) | `features/saas/planes/planes.component.ts` | `features/saas/presentation/planes_controller.dart` | `test_cu06_09.py`, `08_cu06_cu09.sql`, `test_e2e_36_cu.py` | completo |
| CU-07 | `routers/suscripciones.py` (`/mi-suscripcion*`) | `features/mi-suscripcion/mi-suscripcion.component.ts` | `features/saas/presentation/suscripciones_controller.dart` | `test_cu06_09.py`, `06_limites_planes.sql`, `test_e2e_36_cu.py` | completo |
| CU-08 | `routers/saas.py` (`/saas/facturas*`, `/pdf`) | `features/saas/facturacion/facturacion.component.ts` | `features/saas/presentation/facturacion_controller.dart` | `test_cu06_09.py`, `08_cu06_cu09.sql`, `test_e2e_36_cu.py` | completo |
| CU-09 | `routers/saas.py` (`/saas/metricas`, `/empresas*`) | `features/saas/{panel,metricas,empresa-detail}` | `features/saas/presentation/{saas_screen,metricas_controller}.dart` | `test_cu06_09.py`, `01_aislamiento_tenant.sql`, `test_e2e_36_cu.py` | completo |
| CU-10 | `routers/empleados.py` (`/empleados*`) | `features/empleados/empleados.component.ts` | `features/empleados/presentation/empleados_screen.dart` | `test_cu10_16.py`, `test_e2e_36_cu.py` | completo |
| CU-11 | `routers/sucursales.py` (`/sucursales*`) | `features/sucursales/sucursales.component.ts` | `features/sucursales/presentation/sucursales_screen.dart` | `test_cu10_16.py`, `06_limites_planes.sql`, `test_e2e_36_cu.py` | completo |
| CU-12 | `routers/catalogo.py` (`/catalogo/admin/prendas*`) | `features/catalogo-admin/catalogo-admin.component.ts` | `features/catalogo_admin/presentation/catalogo_admin_screen.dart` | `test_cu10_16.py`, `test_e2e_36_cu.py` | completo |
| CU-13 | `routers/catalogo.py` (`/catalogo/prendas*`) | `features/catalogo-cliente` | `features/catalogo/presentation/{catalogo,detalle_producto}_screen.dart` | `test_cu10_16.py`, `test_e2e_36_cu.py` | completo |
| CU-14 | `routers/catalogo.py` (`/catalogo/auxiliares` + filtros) | `features/catalogo-cliente` | `features/catalogo/presentation/widgets/filtros_catalogo_sheet.dart` | `test_e2e_36_cu.py` | completo |
| CU-15 | `routers/proveedores.py` (`/proveedores*`) | `features/proveedores/proveedores.component.ts` | `features/proveedores/presentation/proveedores_screen.dart` | `test_cu10_16.py`, `test_e2e_36_cu.py` | completo |
| CU-16 | `routers/colecciones.py` (`/temporadas-colecciones*`) | `features/temporadas/temporadas.component.ts` | `features/temporadas/presentation/temporadas_screen.dart` | `test_cu10_16.py`, `test_e2e_36_cu.py` | completo |
| CU-17 | `routers/inventario.py` (`/inventario*`) | `features/inventario/inventario.component.ts` | `features/inventario/presentation/inventario_screen.dart` | `test_cu17_inventario.py`, `02_stock_concurrente.sql`, `test_e2e_36_cu.py` | completo |
| CU-18 | `routers/inventario.py` (`/inventario/prendas/{prenda_id}/disponibilidad`) | `features/disponibilidad-tiendas` | `features/inventario/presentation/disponibilidad_screen.dart` | `test_cu18_disponibilidad.py`, `test_e2e_36_cu.py` | completo |
| CU-19 | `routers/reservas.py` (`/reservas/validar`, `/reservas`) | `features/reservas/reserva-creacion` | `features/reservas/presentation/reserva_creacion_controller.dart` | `test_cu19_reservas.py`, `02_stock_concurrente.sql`, `test_e2e_36_cu.py` | completo |
| CU-20 | `routers/reservas.py` (`/mis-reservas`, `/{id}/cancelar`) | `features/reservas/reserva-cliente` | `features/reservas/presentation/reserva_cliente_controller.dart` | `test_cu20_cancelar_reservas.py`, `07_cobertura_36.sql`, `test_e2e_36_cu.py` | completo |
| CU-21 | `routers/reservas.py` (`/por-preparar`, `/preparar`, `/completar`, `/incidencia`) | `features/reservas/reserva-staff` | `features/reservas/presentation/reserva_staff_controller.dart` | `test_cu21_preparar_reservas.py`, `test_e2e_36_cu.py` | completo |
| CU-22 | `routers/carrito.py` + `routers/checkout.py` | `features/checkout/checkout.component.ts` | `features/checkout/presentation/checkout_screen.dart` | `test_cu22_checkout.py`, `test_e2e_36_cu.py` | completo |
| CU-23 | `routers/pos.py` (`/pos/*`) | `features/pos/pos.component.ts` | `features/pos/presentation/pos_screen.dart` | `test_cu23_pos.py`, `test_e2e_36_cu.py` | completo |
| CU-24 | `routers/pagos.py` + `StripeGateway` | `features/pagos/pagos.component.ts` | `features/pagos/presentation/pagos_screen.dart` | `test_cu24_pagos.py`, `04_pagos_devoluciones.sql`, `test_e2e_36_cu.py` | completo |
| CU-25 | `routers/sync.py` (`/sync/catalogo-offline`) | `features/offline/catalogo-offline` | `features/offline/presentation/catalogo_offline_screen.dart` | `test_cu25_a_cu32_sync.py`, `07_cobertura_36.sql`, `test_e2e_36_cu.py` | completo |
| CU-26 | `routers/sync.py` (`/sync` reserva offline) | `features/offline/reserva-offline` | `features/offline/presentation/reserva_offline_screen.dart` | `test_cu25_a_cu32_sync.py`, `test_e2e_36_cu.py` | completo |
| CU-27 | `routers/sync.py` (`/sync/soft-locks*`) + `fn_expirar_reservas()` | `features/offline/bloqueos-activos` | `features/offline/presentation/bloqueos_activos_screen.dart` | `test_cu25_a_cu32_sync.py`, `07_cobertura_36.sql`, `test_e2e_36_cu.py` | completo |
| CU-28 | `routers/sync.py` (`/sync` venta offline) | `features/offline/venta-offline` | `features/offline/presentation/venta_offline_screen.dart` | `test_cu25_a_cu32_sync.py`, `03_offline_idempotencia.sql`, `test_e2e_36_cu.py` | completo |
| CU-29 | `routers/sync.py` (`/sync/validar-qr`, `/sync/nota-cambio`) | `features/offline/cambio-qr` | `features/offline/presentation/cambio_qr_screen.dart` | `test_cu25_a_cu32_sync.py`, `test_e2e_36_cu.py` | completo |
| CU-30 | `routers/sync.py` (`/sync` + `operacion_pendiente`) | `features/offline/cola-operaciones` | `features/offline/presentation/cola_operaciones_screen.dart` | `test_cu25_a_cu32_sync.py`, `test_e2e_36_cu.py` | completo |
| CU-31 | `routers/sync.py` (`/sync` idempotente RNF05) | `features/offline/cola-operaciones` | `features/offline/presentation/cola_operaciones_screen.dart` | `test_cu25_a_cu32_sync.py`, `03_offline_idempotencia.sql`, `test_e2e_36_cu.py` | completo |
| CU-32 | `routers/sync.py` (`/sync/conflictos*`) | `features/offline/conflictos` | `features/offline/presentation/conflictos_screen.dart` | `test_cu25_a_cu32_sync.py`, `test_e2e_36_cu.py` | completo |
| CU-33 | `routers/reportes.py` (`/reportes/convencionales/*`) | `features/reportes/reportes-convencionales.component.ts` | `features/reportes/presentation/reportes_convencionales_screen.dart` | `test_cu33_a_cu36.py`, `test_e2e_36_cu.py` | completo |
| CU-34 | `routers/reportes.py` (`/reportes/ia/*`) + `ia_reporte_service.py` | `features/reportes/reporte-ia.component.ts` | `features/reportes/presentation/reporte_ia_screen.dart` | `test_cu33_a_cu36.py`, `07_cobertura_36.sql`, `test_e2e_36_cu.py` | completo |
| CU-35 | `routers/inteligencia.py` (`/inteligencia/ml/*`) + `ml_analytics_service.py` | `features/analytics-ml/dashboard-ml.component.ts` | `features/analytics_ml/presentation/dashboard_ml_screen.dart` | `test_cu33_a_cu36.py`, `test_e2e_36_cu.py` | completo |
| CU-36 | `routers/vestidor.py` (`/vestidor/*`) + `vestidor_ar_service.py` | `features/vestidor-virtual/vestidor-virtual.component.ts` | `features/vestidor_virtual/presentation/vestidor_virtual_screen.dart` | `test_cu33_a_cu36.py`, `07_cobertura_36.sql`, `test_e2e_36_cu.py` | completo |
| CU-37 | `routers/backups.py` (`/backups*`) | `features/backups/backups.component.ts` | `features/backups/presentation/backups_screen.dart` | `test_cu37_backups.py`, `07_cobertura_36.sql`, `test_e2e_36_cu.py` | completo |

## Pruebas

```powershell
# Verificación estática de contratos backend <-> web/móvil
.\scripts\verify_api_contracts.ps1

# Inicializar/reiniciar DB en PostgreSQL 16 (puerto 5434) y ejecutar suite SQL + API completa
.\scripts\init_db.ps1
.\scripts\run_tests.ps1

# Pruebas offline del backend (sin PostgreSQL activo)
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_cu25_a_cu32_sync.py tests/test_cu33_a_cu36.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_cu01_05.py tests/test_cu18_disponibilidad.py tests/test_cu24_pagos.py tests/test_e2e_36_cu.py -k "offline" -q

# App Flutter
cd mobile
flutter analyze
flutter test

# PWA Angular
cd frontend
npm run build
```

## Comportamiento offline

- La PWA conserva tokens, catálogo cacheado, soft-locks y cola en almacenamiento
  del navegador; la app Flutter usa `flutter_secure_storage` para tokens y SQLite
  para catálogo, usuario, tenant, última sincronización, soft-locks locales y cola.
- Sin conexión se pueden registrar reservas/ventas offline, emitir soft-locks y
  validar tickets QR HMAC; al reconectar se sincronizan de forma idempotente y se
  resuelven conflictos desde la UI dedicada.
- El logout elimina la sesión local y conserva la cola offline y el tenant.
- Las respuestas `401` intentan refresh una vez; un error de red no cierra la sesión.

## Notas de seguridad

- El login resuelve el tenant con `empresa_slug` porque el correo es único por empresa.
- El registro exige verificar el correo antes de iniciar sesión.
- El JWT incluye `sid`; el logout revoca la sesión en `sesion.revocado_en`.
- El middleware de auditoría redacta contraseñas, tokens y secretos.
- En modo demo el token de verificación se devuelve en la respuesta de registro;
  desactivar en producción con `EXPOSE_VERIFICATION_TOKEN=false`.
- Todos los endpoints privados autentican el JWT **antes** de resolver recursos de base
  de datos y aplican aislamiento multitenant mediante RLS en PostgreSQL (`app.empresa_id`).

La guía detallada de clientes iniciales está en [`docs/CU01_CU04_MOVIL.md`](docs/CU01_CU04_MOVIL.md).
