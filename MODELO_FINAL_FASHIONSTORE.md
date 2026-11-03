# FashionStore SaaS Multitenant

## Modelo final de base de datos

**Motor:** PostgreSQL 16  
**Fecha:** 2026-10-25  
**Alcance:** SaaS multitenant, catÃ¡logo de moda, inventario por sucursal, ventas presenciales y en lÃ­nea, operaciÃ³n offline, suscripciones, RBAC granular, Machine Learning, IA generativa y auditorÃ­a.

---

## 1. Resumen ejecutivo

El modelo original de 32 tablas fue revisado y ampliado a **56 tablas finales**. Se agregaron **24 tablas** para cubrir RBAC granular, facturaciÃ³n SaaS, historial de precios, transferencias de inventario, devoluciones, dispositivos offline, e-commerce, cupones, trazabilidad de estados de venta, verificaciÃ³n de correo, recursos de catÃ¡logo, versionado para sincronizaciÃ³n, reportes exportados y prueba virtual con AR.

### Decisiones estructurales

- Esquema compartido con aislamiento por `empresa_id`.
- RLS en todas las tablas de tenant.
- Claves forÃ¡neas compuestas `(empresa_id, tabla_id)` para impedir referencias cruzadas.
- Login por tenant con correo Ãºnico dentro de cada empresa.
- Superadmin global con rol global y auditorÃ­a de acceso.
- RBAC granular mediante `permiso` y `rol_permiso`.
- `venta` funciona como pedido/orden, con ciclo de estados completo.
- Offline con dispositivo identificado, idempotencia, firma QR y resoluciÃ³n de conflictos.
- E-commerce completo: direcciones, envÃ­os, cupones y devoluciones.
- ML e IA aislados por tenant, salvo modelos globales explÃ­citamente marcados.
- AuditorÃ­a append-only y particionada.

### Cambios principales respecto al modelo original

| Tema | Modelo original | Modelo final |
|---|---|---|
| Tablas | 32 | 56 |
| Superadmin | `usuario.empresa_id` NULL con rol de tenant | Rol global con `es_global` y validaciÃ³n |
| SKU | `UNIQUE` global | `UNIQUE(empresa_id, sku)` |
| Aislamiento | `empresa_id` parcial | `empresa_id` en toda tabla de negocio + FK compuestas + RLS |
| Ventas | `cajero_id` y `sucursal_id` obligatorios | Nulos para ventas web; `canal` y estados completos |
| Cambios/devoluciones | 1:1 contra una lÃ­nea | Encabezado + detalle, con devoluciÃ³n y cambio |
| Offline | Solo `operacion_pendiente` | Dispositivo, idempotencia, firma QR, reintentos y conflictos |
| Suscripciones | Sin unicidad ni pagos | SuscripciÃ³n activa Ãºnica y pagos SaaS |
| Permisos | Cuatro roles fijos | Roles + permisos granulares |
| AuditorÃ­a | Declarada inmutable | Append-only, particionada y con datos antes/despuÃ©s |

---

## 2. Convenciones

- **Identificadores:** `UUID` con `DEFAULT gen_random_uuid()` salvo catÃ¡logos globales pequeÃ±os (`SERIAL`) y auditorÃ­a (`BIGSERIAL`).
- **Fechas:** `TIMESTAMPTZ`; fechas de negocio sin hora: `DATE`.
- **Dinero:** `NUMERIC(12,2)`; moneda explÃ­cita `CHAR(3)` con valor por defecto `'BOB'`.
- **Correos:** `CITEXT` para comparaciÃ³n sin distinguir mayÃºsculas.
- **Nombres:** `snake_case`, en singular.
- **Tenant:** toda tabla de negocio incluye `empresa_id UUID NOT NULL`.
- **Integridad de tenant:** las tablas padre incluyen `UNIQUE(empresa_id, id)` y las hijas usan FK compuesta.
- **Borrado:** `deleted_at` para soft delete; CASCADE solo en detalles hijos; RESTRICT en maestros y transaccionales.
- **AuditorÃ­a:** las tablas mutables incluyen `created_at` y `updated_at`; las transaccionales principales incluyen `deleted_at`.
- **Estados:** restringidos con `CHECK` o dominios; no se usan VARCHAR libres.
- **RLS:** `SET LOCAL app.empresa_id` por transacciÃ³n; `app.is_superadmin` solo para el rol de plataforma.
- **Particionado:** auditorÃ­a, movimientos de inventario y consultas IA se particionan por rango de fecha.

---

## 3. Inventario de tablas

| # | Tabla | Ãmbito | PropÃ³sito |
|---:|---|---|---|
| 1 | `empresa` | Global raÃ­z | Tenant contratante del SaaS |
| 2 | `plan` | Global | CatÃ¡logo de planes |
| 3 | `plan_limite` | Global | LÃ­mites por recurso y perÃ­odo |
| 4 | `suscripcion` | Tenant | Contrato de servicio por empresa |
| 5 | `pago_suscripcion` | Tenant | Pagos y conciliaciÃ³n del SaaS |
| 6 | `rol` | Global/Tenant | Roles globales y por empresa |
| 7 | `permiso` | Global | Permisos atÃ³micos del sistema |
| 8 | `rol_permiso` | Global | AsignaciÃ³n de permisos a roles |
| 9 | `usuario` | Global/Tenant | Empleados, clientes y superadmin |
| 10 | `sesion` | Tenant/Global | Sesiones y refresh tokens |
| 11 | `ciudad` | Global | CatÃ¡logo de ciudades |
| 12 | `sucursal` | Tenant | Puntos fÃ­sicos de venta |
| 13 | `bitacora_auditoria` | Global/Tenant | Trazabilidad append-only |
| 14 | `categoria` | Tenant | CategorÃ­as de prendas |
| 15 | `temporada` | Tenant | Temporadas comerciales |
| 16 | `coleccion` | Tenant | Colecciones por temporada |
| 17 | `proveedor` | Tenant | Proveedores y fabricantes |
| 18 | `prenda` | Tenant | Ficha tÃ©cnica base |
| 19 | `color` | Global | CatÃ¡logo de colores |
| 20 | `talla` | Global | CatÃ¡logo de tallas |
| 21 | `variante` | Tenant | Prenda + color + talla + SKU |
| 22 | `precio_historial` | Tenant | Historial de precios por variante y sucursal |
| 23 | `inventario` | Tenant | Stock por sucursal y variante |
| 24 | `movimiento_inventario` | Tenant | Kardex transaccional append-only |
| 25 | `transferencia_inventario` | Tenant | Encabezado de transferencia entre sucursales |
| 26 | `transferencia_detalle` | Tenant | LÃ­neas de transferencia |
| 27 | `reserva` | Tenant | Reserva de prendas para visita |
| 28 | `reserva_detalle` | Tenant | Variantes reservadas |
| 29 | `carrito` | Tenant | Carrito de compras |
| 30 | `carrito_detalle` | Tenant | LÃ­neas del carrito |
| 31 | `venta` | Tenant | Venta, pedido y orden online/offline |
| 32 | `venta_detalle` | Tenant | LÃ­neas de venta con precio histÃ³rico |
| 33 | `pago` | Tenant | Cobros y conciliaciÃ³n |
| 34 | `cambio_prenda` | Tenant | Encabezado de cambio o devoluciÃ³n |
| 35 | `cambio_detalle` | Tenant | LÃ­neas de cambio o devoluciÃ³n |
| 36 | `operacion_pendiente` | Tenant | Cola offline idempotente |
| 37 | `resolucion_conflicto` | Tenant | Tratamiento de conflictos offline |
| 38 | `dispositivo` | Tenant | Dispositivos POS/mÃ³viles y claves |
| 39 | `direccion_cliente` | Tenant | Direcciones de entrega |
| 40 | `envio` | Tenant | LogÃ­stica y seguimiento |
| 41 | `cupon` | Tenant | Cupones y promociones |
| 42 | `cupon_uso` | Tenant | Uso y control de cupones |
| 43 | `venta_estado_historial` | Tenant | Trazabilidad del ciclo de pedido |
| 44 | `modelo_ml` | Global/Tenant | Metadatos de modelos ML |
| 45 | `prediccion_demanda` | Tenant | Predicciones por categorÃ­a y perÃ­odo |
| 46 | `segmento_cliente` | Tenant | SegmentaciÃ³n de clientes |
| 47 | `consulta_ia_log` | Tenant | AuditorÃ­a y cachÃ© de consultas IA |
| 48 | `verificacion_correo` | Tenant | Tokens de verificaciÃ³n de correo |
| 49 | `prenda_recurso` | Tenant | ImÃ¡genes, texturas, videos y modelos 3D |
| 50 | `catalogo_version` | Tenant | VersiÃ³n de catÃ¡logo para sincronizaciÃ³n delta |
| 51 | `reserva_estado_historial` | Tenant | Trazabilidad de estados de reserva |
| 52 | `reporte_exportado` | Tenant | PDF/Excel/CSV generados desde IA |
| 53 | `avatar_cliente` | Tenant | Avatar virtual del cliente |
| 54 | `medida_corporal` | Tenant | Medidas corporales para AR |
| 55 | `prenda_ar` | Tenant | Prenda preparada para prueba virtual |
| 56 | `sesion_prueba_virtual` | Tenant | Sesiones de probador virtual |

---

## 4. Diccionario de tablas

### 4.1 NÃºcleo SaaS

#### 1. `empresa`

**Ãmbito:** global raÃ­z. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador del tenant |
| `slug` | VARCHAR(80) | UNIQUE, NOT NULL | Identificador para subdominio/routing |
| `razon_social` | VARCHAR(150) | NOT NULL | RazÃ³n social |
| `nit` | VARCHAR(30) | UNIQUE, NOT NULL | IdentificaciÃ³n tributaria |
| `correo_contacto` | CITEXT | NOT NULL | Correo del administrador |
| `telefono` | VARCHAR(30) | NULL | TelÃ©fono corporativo |
| `direccion_fiscal` | VARCHAR(255) | NULL | DirecciÃ³n fiscal |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda funcional |
| `zona_horaria` | VARCHAR(50) | NOT NULL, DEFAULT `'America/La_Paz'` | Zona horaria |
| `logo_url` | VARCHAR(255) | NULL | Logo del tenant |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'activa'`, CHECK (`activa`,`suspendida`,`inactiva`) | Estado operativo |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Relaciones:** 1:N con `suscripcion`, `pago_suscripcion`, `rol`, `usuario`, `sucursal`, `categoria`, `temporada`, `proveedor`, `prenda`, `variante`, `inventario`, `venta`, `dispositivo`, `cupon`, `consulta_ia_log`, entre otras.

#### 2. `plan`

**Ãmbito:** global. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | SERIAL | PK | Identificador del plan |
| `codigo` | VARCHAR(30) | UNIQUE, NOT NULL | CÃ³digo estable (`basico`, `profesional`) |
| `nombre` | VARCHAR(50) | UNIQUE, NOT NULL | Nombre comercial |
| `descripcion` | TEXT | NULL | DescripciÃ³n |
| `precio_mensual` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Precio de referencia |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `permite_ia` | BOOLEAN | NOT NULL, DEFAULT FALSE | Habilita IA |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponibilidad |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Relaciones:** 1:N con `plan_limite` y `suscripcion`.

#### 3. `plan_limite`

**Ãmbito:** global. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `plan_id` | INTEGER | FK `plan(id)`, NOT NULL | Plan |
| `recurso` | VARCHAR(50) | NOT NULL, CHECK (`sucursales`,`usuarios`,`productos`,`almacenamiento_mb`,`consultas_ia_mes`) | Recurso limitado |
| `limite` | INTEGER | NOT NULL, CHECK `>= 0` | Cupo permitido |
| `periodo` | VARCHAR(20) | NOT NULL, DEFAULT `'total'`, CHECK (`total`,`mensual`,`diario`) | Ventana de mediciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(plan_id, recurso, periodo)`.

#### 4. `suscripcion`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `plan_id` | INTEGER | FK `plan(id)`, NOT NULL | Plan contratado |
| `fecha_inicio` | DATE | NOT NULL | Inicio |
| `fecha_vencimiento` | DATE | NOT NULL | Vencimiento |
| `precio_pactado` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Precio histÃ³rico del contrato |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `ciclo` | VARCHAR(20) | NOT NULL, DEFAULT `'mensual'`, CHECK (`mensual`,`anual`) | Ciclo |
| `renovacion_automatica` | BOOLEAN | NOT NULL, DEFAULT TRUE | RenovaciÃ³n |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'activa'`, CHECK (`activa`,`vencida`,`suspendida`,`cancelada`) | Estado |
| `cancelada_en` | TIMESTAMPTZ | NULL | Fecha de cancelaciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `CHECK (fecha_inicio < fecha_vencimiento)`; `UNIQUE(empresa_id, id)`; Ã­ndice Ãºnico parcial `(empresa_id) WHERE estado = 'activa'`.

#### 5. `pago_suscripcion`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `suscripcion_id` | UUID | FK compuesta `(empresa_id, suscripcion_id)`, NOT NULL | SuscripciÃ³n |
| `monto` | NUMERIC(12,2) | NOT NULL, CHECK `> 0` | Monto pagado |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `periodo_desde` | DATE | NULL | Inicio del perÃ­odo pagado |
| `periodo_hasta` | DATE | NULL | Fin del perÃ­odo pagado |
| `metodo` | VARCHAR(30) | NOT NULL, CHECK (`efectivo`,`tarjeta`,`qr`,`transferencia`,`pasarela`) | MÃ©todo |
| `referencia_externa` | VARCHAR(100) | NULL | ID de pasarela o banco |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'completado'`, CHECK (`pendiente`,`completado`,`fallido`,`reembolsado`) | Estado |
| `pagado_en` | TIMESTAMPTZ | NULL | Fecha de pago |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `CHECK (periodo_desde IS NULL OR periodo_hasta IS NULL OR periodo_desde <= periodo_hasta)`; Ã­ndice Ãºnico parcial `(empresa_id, referencia_externa) WHERE referencia_externa IS NOT NULL`.

### 4.2 RBAC y seguridad

#### 6. `rol`

**Ãmbito:** global o tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NULL | NULL para rol global |
| `es_global` | BOOLEAN | NOT NULL, DEFAULT FALSE | Rol de plataforma |
| `nombre` | VARCHAR(50) | NOT NULL | Nombre del rol |
| `descripcion` | TEXT | NULL | DescripciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `CHECK ((es_global AND empresa_id IS NULL) OR (NOT es_global AND empresa_id IS NOT NULL))`; `UNIQUE(empresa_id, nombre)`; Ã­ndice Ãºnico parcial `(nombre) WHERE es_global`.

#### 7. `permiso`

**Ãmbito:** global. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `codigo` | VARCHAR(80) | UNIQUE, NOT NULL | CÃ³digo atÃ³mico (`ventas.crear`, `inventario.ajustar`) |
| `modulo` | VARCHAR(50) | NOT NULL | MÃ³dulo funcional |
| `descripcion` | TEXT | NULL | DescripciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

#### 8. `rol_permiso`

**Ãmbito:** global. **PK:** compuesta.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `rol_id` | UUID | FK `rol(id)`, ON DELETE CASCADE, NOT NULL | Rol |
| `permiso_id` | UUID | FK `permiso(id)`, ON DELETE CASCADE, NOT NULL | Permiso |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `PRIMARY KEY (rol_id, permiso_id)`.

#### 9. `usuario`

**Ãmbito:** global o tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NULL | NULL solo para Superadmin |
| `rol_id` | UUID | FK `rol(id)`, NOT NULL | Rol asignado |
| `sucursal_id` | UUID | FK `sucursal(id)`, NULL | Sucursal principal |
| `nombre_completo` | VARCHAR(150) | NOT NULL | Nombre completo |
| `correo` | CITEXT | NOT NULL | Correo de acceso |
| `password_hash` | VARCHAR(255) | NOT NULL | Hash bcrypt/argon2id |
| `telefono` | VARCHAR(30) | NULL | TelÃ©fono |
| `email_verificado` | BOOLEAN | NOT NULL, DEFAULT FALSE | VerificaciÃ³n |
| `email_verificado_en` | TIMESTAMPTZ | NULL | Fecha de verificaciÃ³n efectiva |
| `intentos_fallidos` | SMALLINT | NOT NULL, DEFAULT 0, CHECK `>= 0` | Intentos fallidos |
| `bloqueado_hasta` | TIMESTAMPTZ | NULL | Bloqueo temporal |
| `ultimo_login` | TIMESTAMPTZ | NULL | Ãšltimo acceso |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Estado |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, correo)`; Ã­ndice Ãºnico parcial `(correo) WHERE empresa_id IS NULL`; `UNIQUE(empresa_id, id)`. Un trigger valida que el rol sea global cuando `empresa_id IS NULL`, o de la misma empresa cuando no lo sea; la sucursal debe pertenecer al mismo tenant.

#### 10. `sesion`

**Ãmbito:** tenant o global. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NULL | NULL para sesiÃ³n de Superadmin |
| `usuario_id` | UUID | FK `usuario(id)`, NOT NULL | Usuario |
| `refresh_token_hash` | VARCHAR(255) | UNIQUE, NOT NULL | Hash del refresh token |
| `user_agent` | VARCHAR(255) | NULL | Navegador/dispositivo |
| `ip_origen` | INET | NULL | IP de origen |
| `expira_en` | TIMESTAMPTZ | NOT NULL | ExpiraciÃ³n |
| `revocado_en` | TIMESTAMPTZ | NULL | RevocaciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `CHECK (expira_en > created_at)`.

### 4.3 GeografÃ­a, sucursales y auditorÃ­a

#### 11. `ciudad`

**Ãmbito:** global. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | SERIAL | PK | Identificador |
| `nombre` | VARCHAR(100) | NOT NULL | Ciudad |
| `pais` | VARCHAR(50) | NOT NULL, DEFAULT `'Bolivia'` | PaÃ­s |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(nombre, pais)`.

#### 12. `sucursal`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `ciudad_id` | INTEGER | FK `ciudad(id)`, NOT NULL | Ciudad |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre de tienda |
| `direccion` | VARCHAR(255) | NOT NULL | DirecciÃ³n |
| `telefono` | VARCHAR(30) | NULL | TelÃ©fono |
| `activa` | BOOLEAN | NOT NULL, DEFAULT TRUE | Operativa |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, nombre)`; `UNIQUE(empresa_id, id)`.

#### 13. `bitacora_auditoria`

**Ãmbito:** global/tenant. **PK:** `(id, ocurrido_en)` por particionado.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | BIGSERIAL | PK compuesta | Identificador de traza |
| `empresa_id` | UUID | FK `empresa(id)`, NULL | Tenant del actor |
| `empresa_afectada_id` | UUID | FK `empresa(id)`, NULL | Tenant afectado por Superadmin |
| `usuario_id` | UUID | FK `usuario(id)`, NULL | Actor |
| `accion` | VARCHAR(100) | NOT NULL | AcciÃ³n (`LOGIN`, `VENTA`, `SYNC_OFFLINE`, etc.) |
| `entidad` | VARCHAR(80) | NULL | Tabla o recurso afectado |
| `entidad_id` | UUID | NULL | ID del recurso |
| `datos_antes` | JSONB | NULL | Estado previo |
| `datos_despues` | JSONB | NULL | Estado posterior |
| `endpoint` | VARCHAR(255) | NULL | Ruta API |
| `metodo_http` | VARCHAR(10) | NULL | MÃ©todo HTTP |
| `ip_origen` | INET | NULL | IP |
| `user_agent` | VARCHAR(255) | NULL | Cliente |
| `es_accion_superadmin` | BOOLEAN | NOT NULL, DEFAULT FALSE | AcciÃ³n de plataforma |
| `correlacion_id` | UUID | NULL | Traza distribuida |
| `ocurrido_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha del evento |

**Restricciones:** particiÃ³n por `RANGE(ocurrido_en)` mensual; sin UPDATE/DELETE para el rol de aplicaciÃ³n; inserciÃ³n vÃ­a funciÃ³n `SECURITY DEFINER`.

### 4.4 CatÃ¡logo

#### 14. `categoria`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre |
| `descripcion` | TEXT | NULL | DescripciÃ³n |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, nombre)`; `UNIQUE(empresa_id, id)`.

#### 15. `temporada`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre |
| `fecha_inicio` | DATE | NOT NULL | Inicio |
| `fecha_fin` | DATE | NOT NULL | Fin |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, nombre)`; `CHECK (fecha_inicio < fecha_fin)`; `UNIQUE(empresa_id, id)`.

#### 16. `coleccion`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `temporada_id` | UUID | FK compuesta `(empresa_id, temporada_id)`, NOT NULL | Temporada |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre |
| `descripcion` | TEXT | NULL | DescripciÃ³n |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, temporada_id, nombre)`; `UNIQUE(empresa_id, id)`.

#### 17. `proveedor`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `razon_social` | VARCHAR(150) | NOT NULL | RazÃ³n social |
| `nit` | VARCHAR(30) | NOT NULL | IdentificaciÃ³n fiscal |
| `contacto` | VARCHAR(100) | NULL | Contacto |
| `telefono` | VARCHAR(30) | NULL | TelÃ©fono |
| `correo` | CITEXT | NULL | Correo |
| `direccion` | VARCHAR(255) | NULL | DirecciÃ³n |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, nit)`; `UNIQUE(empresa_id, id)`.

#### 18. `prenda`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `categoria_id` | UUID | FK compuesta `(empresa_id, categoria_id)`, NOT NULL | CategorÃ­a |
| `temporada_id` | UUID | FK compuesta `(empresa_id, temporada_id)`, NULL | Temporada |
| `coleccion_id` | UUID | FK compuesta `(empresa_id, coleccion_id)`, NULL | ColecciÃ³n |
| `proveedor_id` | UUID | FK compuesta `(empresa_id, proveedor_id)`, NULL | Proveedor |
| `nombre` | VARCHAR(150) | NOT NULL | Nombre comercial |
| `descripcion` | TEXT | NULL | Ficha tÃ©cnica |
| `precio_base` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Precio base |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `modelo_3d_url` | VARCHAR(255) | NULL | Modelo 3D/AR |
| `imagen_url` | VARCHAR(255) | NULL | Imagen principal |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, id)`; `CHECK (coleccion_id IS NULL OR temporada_id IS NOT NULL)`; trigger que valida que la colecciÃ³n pertenezca a la temporada indicada.

#### 19. `color`

**Ãmbito:** global. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | SERIAL | PK | Identificador |
| `nombre` | VARCHAR(50) | UNIQUE, NOT NULL | Nombre |
| `codigo_hex` | VARCHAR(10) | NULL, CHECK formato `#RRGGBB` | Color hexadecimal |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

#### 20. `talla`

**Ãmbito:** global. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | SERIAL | PK | Identificador |
| `codigo` | VARCHAR(10) | UNIQUE, NOT NULL | CÃ³digo (`XS`, `S`, `M`, `38`, etc.) |
| `orden` | INTEGER | NOT NULL, DEFAULT 0 | Orden visual |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

#### 21. `variante`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `prenda_id` | UUID | FK compuesta `(empresa_id, prenda_id)`, NOT NULL | Prenda |
| `color_id` | INTEGER | FK `color(id)`, NOT NULL | Color |
| `talla_id` | INTEGER | FK `talla(id)`, NOT NULL | Talla |
| `sku` | VARCHAR(50) | NOT NULL | SKU o cÃ³digo de barras |
| `precio_ajustado` | NUMERIC(12,2) | NULL, CHECK `>= 0` | Precio especÃ­fico |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, sku)`; `UNIQUE(empresa_id, prenda_id, color_id, talla_id)`; `UNIQUE(empresa_id, id)`.

#### 22. `precio_historial`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `variante_id` | UUID | FK compuesta `(empresa_id, variante_id)`, NOT NULL | Variante |
| `sucursal_id` | UUID | FK compuesta `(empresa_id, sucursal_id)`, NULL | Precio por sucursal |
| `precio` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Precio vigente |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `vigente_desde` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Inicio de vigencia |
| `vigente_hasta` | TIMESTAMPTZ | NULL | Fin de vigencia |
| `creado_por` | UUID | FK compuesta `(empresa_id, creado_por)`, NOT NULL | Usuario responsable |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `CHECK (vigente_hasta IS NULL OR vigente_hasta > vigente_desde)`; Ã­ndice `(empresa_id, variante_id, vigente_desde DESC)`.

### 4.5 Inventario

#### 23. `inventario`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `variante_id` | UUID | FK compuesta `(empresa_id, variante_id)`, NOT NULL | Variante |
| `sucursal_id` | UUID | FK compuesta `(empresa_id, sucursal_id)`, NOT NULL | Sucursal |
| `stock_disponible` | INTEGER | NOT NULL, DEFAULT 0, CHECK `>= 0` | Unidades disponibles |
| `stock_reservado` | INTEGER | NOT NULL, DEFAULT 0, CHECK `>= 0` | Unidades reservadas |
| `stock_minimo` | INTEGER | NOT NULL, DEFAULT 0, CHECK `>= 0` | Punto de reposiciÃ³n |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Bloqueo optimista |
| `ultima_actualizacion` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima actualizaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, sucursal_id, variante_id)`.

#### 24. `movimiento_inventario`

**Ãmbito:** tenant. **PK:** `(id, ocurrido_en)` por particionado.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK compuesta, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `variante_id` | UUID | FK compuesta, NOT NULL | Variante |
| `sucursal_id` | UUID | FK compuesta, NOT NULL | Sucursal |
| `tipo` | VARCHAR(30) | NOT NULL, CHECK (`INGRESO`,`MERMA`,`TRANSFERENCIA_SALIDA`,`TRANSFERENCIA_ENTRADA`,`VENTA`,`AJUSTE`,`DEVOLUCION`,`RESERVA`,`LIBERACION_RESERVA`) | Tipo |
| `cantidad_delta` | INTEGER | NOT NULL, CHECK `<> 0` | VariaciÃ³n firmada |
| `saldo_anterior` | INTEGER | NOT NULL | Stock previo |
| `stock_resultante` | INTEGER | NOT NULL, CHECK `>= 0` | Stock resultante |
| `documento_tipo` | VARCHAR(30) | NULL, CHECK (`VENTA`,`RESERVA`,`TRANSFERENCIA`,`AJUSTE`,`DEVOLUCION`,`COMPRA`,`OPERACION_OFFLINE`) | Documento origen |
| `documento_id` | UUID | NULL | ID del documento origen |
| `transferencia_id` | UUID | NULL | Transferencia asociada |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Responsable |
| `costo_unitario` | NUMERIC(12,2) | NULL, CHECK `>= 0` | Costo |
| `motivo` | VARCHAR(255) | NULL | JustificaciÃ³n |
| `ocurrido_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha del movimiento |

**Restricciones:** `CHECK (stock_resultante = saldo_anterior + cantidad_delta)`; append-only; Ã­ndice `(empresa_id, variante_id, ocurrido_en DESC)`.

#### 25. `transferencia_inventario`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `sucursal_origen_id` | UUID | FK compuesta, NOT NULL | Origen |
| `sucursal_destino_id` | UUID | FK compuesta, NOT NULL | Destino |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'pendiente'`, CHECK (`pendiente`,`en_transito`,`recibida`,`cancelada`) | Estado |
| `solicitado_por` | UUID | FK compuesta, NOT NULL | Solicitante |
| `recibido_por` | UUID | FK compuesta, NULL | Receptor |
| `fecha_solicitud` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Solicitud |
| `fecha_recepcion` | TIMESTAMPTZ | NULL | RecepciÃ³n |
| `observacion` | TEXT | NULL | Notas |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `CHECK (sucursal_origen_id <> sucursal_destino_id)`; `UNIQUE(empresa_id, id)`.

#### 26. `transferencia_detalle`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `transferencia_id` | UUID | FK compuesta, NOT NULL | Transferencia |
| `variante_id` | UUID | FK compuesta, NOT NULL | Variante |
| `cantidad_solicitada` | INTEGER | NOT NULL, CHECK `> 0` | Solicitada |
| `cantidad_recibida` | INTEGER | NOT NULL, DEFAULT 0, CHECK `>= 0` | Recibida |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, transferencia_id, variante_id)`; `CHECK (cantidad_recibida <= cantidad_solicitada)`.

### 4.6 Reservas, carrito y ventas

#### 27. `reserva`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Cliente |
| `sucursal_id` | UUID | FK compuesta, NOT NULL | Sucursal |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'activa'`, CHECK (`activa`,`confirmada`,`expirada`,`cancelada`,`convertida`) | Estado |
| `fecha_visita` | TIMESTAMPTZ | NULL | Visita pactada |
| `expira_en` | TIMESTAMPTZ | NOT NULL | ExpiraciÃ³n del apartado |
| `dispositivo_id` | UUID | FK compuesta `(empresa_id, dispositivo_id)`, NULL | Dispositivo que originÃ³ la reserva offline |
| `liberada_en` | TIMESTAMPTZ | NULL | Momento de liberaciÃ³n de stock |
| `motivo_cierre` | VARCHAR(200) | NULL | Motivo de cancelaciÃ³n, expiraciÃ³n o conversiÃ³n |
| `observacion` | TEXT | NULL | Notas |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `CHECK (expira_en > created_at)`; `UNIQUE(empresa_id, id)`; FK `fk_reserva_dispositivo`. Los cambios de estado a `cancelada`, `expirada`, `convertida` o `completada` liberan el stock reservado una sola vez y registran `liberada_en` e historial.

#### 28. `reserva_detalle`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `reserva_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Reserva |
| `variante_id` | UUID | FK compuesta, NOT NULL | Variante |
| `cantidad` | INTEGER | NOT NULL, DEFAULT 1, CHECK `> 0` | Cantidad |
| `precio_unitario_referencia` | NUMERIC(12,2) | NULL, CHECK `>= 0` | Precio referencial |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, reserva_id, variante_id)`.

#### 29. `carrito`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Cliente |
| `sucursal_id` | UUID | FK compuesta, NULL | Sucursal de retiro |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'activo'`, CHECK (`activo`,`convertido`,`abandonado`) | Estado |
| `expira_en` | TIMESTAMPTZ | NULL | ExpiraciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** Ã­ndice Ãºnico parcial `(empresa_id, usuario_id) WHERE estado = 'activo'`; `UNIQUE(empresa_id, id)`.

#### 30. `carrito_detalle`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `carrito_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Carrito |
| `variante_id` | UUID | FK compuesta, NOT NULL | Variante |
| `cantidad` | INTEGER | NOT NULL, DEFAULT 1, CHECK `> 0` | Cantidad |
| `precio_unitario_referencia` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Precio de referencia |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, carrito_id, variante_id)`.

#### 31. `venta`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `numero` | VARCHAR(30) | NOT NULL | NÃºmero legible por tenant |
| `sucursal_id` | UUID | FK compuesta, NULL | Sucursal (NULL en web) |
| `usuario_id` | UUID | FK compuesta, NULL | Cliente |
| `cajero_id` | UUID | FK compuesta, NULL | Cajero (NULL en web) |
| `canal` | VARCHAR(20) | NOT NULL, CHECK (`POS`,`WEB`,`OFFLINE`) | Canal |
| `fecha_hora` | TIMESTAMPTZ | NOT NULL | Fecha de negocio |
| `fecha_hora_cliente` | TIMESTAMPTZ | NULL | Hora del cliente offline |
| `fecha_recepcion_servidor` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | RecepciÃ³n |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `subtotal` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Subtotal |
| `descuento` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Descuento |
| `impuesto` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Impuesto |
| `total` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Total |
| `estado` | VARCHAR(30) | NOT NULL, DEFAULT `'pendiente_pago'`, CHECK (`pendiente_pago`,`pagada`,`preparando`,`enviada`,`entregada`,`completada`,`anulada`,`devuelta`,`pendiente_sync`) | Estado |
| `direccion_id` | UUID | FK compuesta, NULL | DirecciÃ³n de entrega |
| `cupon_id` | UUID | FK compuesta, NULL | CupÃ³n aplicado |
| `idempotency_key` | VARCHAR(100) | NOT NULL | Idempotencia |
| `firma_qr` | VARCHAR(255) | NULL | Firma del comprobante offline |
| `qr_nonce` | VARCHAR(100) | NULL | Nonce anti-replay |
| `firma_algoritmo` | VARCHAR(20) | NULL, CHECK (`HMAC-SHA256`,`Ed25519`) | Algoritmo |
| `firma_version` | SMALLINT | NOT NULL, DEFAULT 1 | VersiÃ³n de firma |
| `firmado_en` | TIMESTAMPTZ | NULL | Fecha de firma |
| `dispositivo_id` | UUID | FK compuesta, NULL | Dispositivo offline |
| `notas` | TEXT | NULL | Observaciones |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, numero)`; `UNIQUE(empresa_id, idempotency_key)`; `UNIQUE(empresa_id, id)`; `CHECK (total = subtotal - descuento + impuesto)`; `CHECK (descuento <= subtotal)`; `CHECK (canal <> 'POS' OR sucursal_id IS NOT NULL)`; `CHECK (canal <> 'POS' OR cajero_id IS NOT NULL)`.

**Nota:** `numero` se genera por tenant en la capa de servicio. Si se requiere numeraciÃ³n fiscal offline, agregar una tabla de secuencias por dispositivo.

#### 32. `venta_detalle`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `venta_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Venta |
| `variante_id` | UUID | FK compuesta, NOT NULL | Variante |
| `cantidad` | INTEGER | NOT NULL, CHECK `> 0` | Cantidad |
| `precio_lista` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Precio de lista |
| `precio_unitario` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Precio aplicado |
| `descuento_linea` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Descuento de lÃ­nea |
| `subtotal` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Subtotal |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, venta_id, variante_id)`; `UNIQUE(empresa_id, id)`; `CHECK (subtotal = (cantidad * precio_unitario) - descuento_linea)`.

#### 33. `pago`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `venta_id` | UUID | FK compuesta, NOT NULL | Venta |
| `monto` | NUMERIC(12,2) | NOT NULL, CHECK `> 0` | Monto |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `metodo` | VARCHAR(30) | NOT NULL, CHECK (`efectivo`,`tarjeta`,`qr`,`pasarela`,`transferencia`,`vale`) | MÃ©todo |
| `pasarela_id` | VARCHAR(100) | NULL | ID de pasarela |
| `idempotency_key` | VARCHAR(100) | NOT NULL | Idempotencia |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'completado'`, CHECK (`pendiente`,`completado`,`fallido`,`reembolsado`) | Estado |
| `referencia` | VARCHAR(100) | NULL | Referencia externa |
| `pagado_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha de pago |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, idempotency_key)`; Ã­ndice Ãºnico parcial `(empresa_id, pasarela_id) WHERE pasarela_id IS NOT NULL`; trigger que impide que la suma de pagos completados supere `venta.total`.

#### 34. `cambio_prenda`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `venta_id` | UUID | FK compuesta, NOT NULL | Venta original |
| `tipo` | VARCHAR(20) | NOT NULL, CHECK (`CAMBIO`,`DEVOLUCION`) | Tipo |
| `motivo` | VARCHAR(150) | NOT NULL | Motivo |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'registrado'`, CHECK (`registrado`,`aprobado`,`rechazado`,`completado`) | Estado |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Responsable |
| `sucursal_id` | UUID | FK compuesta, NOT NULL | Sucursal |
| `diferencia_total` | NUMERIC(12,2) | NOT NULL, DEFAULT 0 | Ajuste econÃ³mico |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `fecha` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha |
| `observacion` | TEXT | NULL | Notas |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, id)`.

#### 35. `cambio_detalle`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `cambio_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Cambio/devoluciÃ³n |
| `venta_detalle_id` | UUID | FK compuesta, NOT NULL | LÃ­nea original |
| `variante_nueva_id` | UUID | FK compuesta, NULL | Variante nueva (NULL en devoluciÃ³n) |
| `cantidad` | INTEGER | NOT NULL, CHECK `> 0` | Cantidad |
| `precio_unitario_original` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Precio original |
| `precio_unitario_nuevo` | NUMERIC(12,2) | NULL, CHECK `>= 0` | Precio nuevo |
| `diferencia` | NUMERIC(12,2) | NOT NULL, DEFAULT 0 | Diferencia |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Regla:** trigger que valida que la cantidad acumulada devuelta/cambiada no supere la cantidad vendida en `venta_detalle`.

### 4.7 Offline

#### 36. `dispositivo`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `sucursal_id` | UUID | FK compuesta, NOT NULL | Sucursal |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre del dispositivo |
| `serial` | VARCHAR(100) | NOT NULL | Serial Ãºnico por tenant |
| `clave_publica` | TEXT | NULL | Clave pÃºblica Ed25519 |
| `ultima_sync` | TIMESTAMPTZ | NULL | Ãšltimo sync |
| `catalogo_version` | BIGINT | NOT NULL, DEFAULT 0, CHECK `>= 0` | Ãšltima versiÃ³n de catÃ¡logo sincronizada |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'activo'`, CHECK (`activo`,`revocado`) | Estado |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, serial)`; `UNIQUE(empresa_id, id)`. `catalogo_version` se compara con `catalogo_version.version` para descargar solo el delta.

#### 37. `operacion_pendiente`

**Ãmbito:** tenant. **PK:** `id` generado en cliente.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK | UUID generado en el cliente |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `sucursal_id` | UUID | FK compuesta, NOT NULL | Sucursal |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Usuario |
| `dispositivo_id` | UUID | FK compuesta, NOT NULL | Dispositivo |
| `tipo` | VARCHAR(30) | NOT NULL, CHECK (`VENTA_OFFLINE`,`RESERVA_OFFLINE`,`CAMBIO_OFFLINE`) | Tipo |
| `idempotency_key` | VARCHAR(100) | NOT NULL | Clave de idempotencia |
| `payload_json` | JSONB | NOT NULL | Payload capturado |
| `payload_version` | SMALLINT | NOT NULL, DEFAULT 1 | VersiÃ³n del payload |
| `hash_payload` | VARCHAR(64) | NULL | Hash de integridad |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'pendiente'`, CHECK (`pendiente`,`procesando`,`confirmada`,`conflicto`,`rechazada`) | Estado |
| `intentos` | SMALLINT | NOT NULL, DEFAULT 0, CHECK `>= 0` | Reintentos |
| `ultimo_error` | TEXT | NULL | Ãšltimo error |
| `proximo_intento` | TIMESTAMPTZ | NULL | Backoff |
| `venta_id` | UUID | FK compuesta, NULL | Venta resultante |
| `fecha_operacion_cliente` | TIMESTAMPTZ | NOT NULL | Hora del cliente |
| `fecha_recepcion` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | RecepciÃ³n |
| `procesado_en` | TIMESTAMPTZ | NULL | Procesamiento |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, idempotency_key)`; `UNIQUE(empresa_id, id)`; Ã­ndice Ãºnico parcial `(empresa_id, venta_id) WHERE venta_id IS NOT NULL`.

#### 38. `resolucion_conflicto`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `operacion_pendiente_id` | UUID | FK compuesta, UNIQUE, NOT NULL | OperaciÃ³n |
| `estrategia` | VARCHAR(50) | NOT NULL, CHECK (`AJUSTE_MANUAL`,`TRANSFERENCIA_SUCURSAL`,`VALE_CREDITO`,`DESCARTE`,`REINTENTO`) | Estrategia |
| `motivo` | TEXT | NOT NULL | JustificaciÃ³n |
| `detalle_json` | JSONB | NULL | Detalle del conflicto |
| `resultado_json` | JSONB | NULL | Resultado aplicado |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'resuelto'`, CHECK (`pendiente`,`resuelto`,`rechazado`) | Estado |
| `resuelto_por` | UUID | FK compuesta, NOT NULL | Usuario que resuelve |
| `resuelto_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha de resoluciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, operacion_pendiente_id)`.

### 4.8 E-commerce

#### 39. `direccion_cliente`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Cliente |
| `alias` | VARCHAR(50) | NULL | Etiqueta (`Casa`, `Oficina`) |
| `destinatario` | VARCHAR(150) | NOT NULL | Persona que recibe |
| `telefono` | VARCHAR(30) | NOT NULL | TelÃ©fono de contacto |
| `linea1` | VARCHAR(255) | NOT NULL | DirecciÃ³n principal |
| `linea2` | VARCHAR(255) | NULL | Complemento |
| `ciudad_id` | INTEGER | FK `ciudad(id)`, NOT NULL | Ciudad |
| `codigo_postal` | VARCHAR(20) | NULL | CÃ³digo postal |
| `referencia` | TEXT | NULL | Referencia de entrega |
| `es_principal` | BOOLEAN | NOT NULL, DEFAULT FALSE | DirecciÃ³n predeterminada |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** Ã­ndice Ãºnico parcial `(empresa_id, usuario_id) WHERE es_principal AND deleted_at IS NULL`; `UNIQUE(empresa_id, id)`.

#### 40. `envio`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `venta_id` | UUID | FK compuesta, NOT NULL | Venta/pedido |
| `direccion_id` | UUID | FK compuesta, NOT NULL | DirecciÃ³n de entrega |
| `transportista` | VARCHAR(100) | NULL | Empresa de logÃ­stica |
| `tracking` | VARCHAR(100) | NULL | CÃ³digo de seguimiento |
| `estado` | VARCHAR(30) | NOT NULL, DEFAULT `'pendiente'`, CHECK (`pendiente`,`preparando`,`en_transito`,`entregado`,`fallido`,`devuelto`,`cancelado`) | Estado |
| `costo` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Costo de envÃ­o |
| `moneda` | CHAR(3) | NOT NULL, DEFAULT `'BOB'` | Moneda |
| `fecha_estimada` | DATE | NULL | Entrega estimada |
| `fecha_entrega` | TIMESTAMPTZ | NULL | Entrega real |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** Ã­ndice Ãºnico parcial `(empresa_id, tracking) WHERE tracking IS NOT NULL`; trigger que exige `fecha_entrega` cuando el estado es `entregado`.

#### 41. `cupon`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `codigo` | CITEXT | NOT NULL | CÃ³digo del cupÃ³n |
| `descripcion` | TEXT | NULL | DescripciÃ³n |
| `tipo` | VARCHAR(20) | NOT NULL, CHECK (`PORCENTAJE`,`MONTO_FIJO`) | Tipo |
| `valor` | NUMERIC(12,2) | NOT NULL, CHECK `> 0` | Valor |
| `monto_minimo` | NUMERIC(12,2) | NOT NULL, DEFAULT 0, CHECK `>= 0` | Compra mÃ­nima |
| `usos_maximos` | INTEGER | NULL, CHECK `> 0` | Usos totales |
| `usos_por_usuario` | INTEGER | NOT NULL, DEFAULT 1, CHECK `> 0` | Usos por cliente |
| `fecha_inicio` | TIMESTAMPTZ | NOT NULL | Inicio |
| `fecha_fin` | TIMESTAMPTZ | NOT NULL | Fin |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, codigo)`; `UNIQUE(empresa_id, id)`; `CHECK (fecha_inicio < fecha_fin)`; `CHECK (tipo <> 'PORCENTAJE' OR valor <= 100)`.

#### 42. `cupon_uso`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `cupon_id` | UUID | FK compuesta, NOT NULL | CupÃ³n |
| `venta_id` | UUID | FK compuesta, NOT NULL | Venta |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Cliente |
| `monto_descontado` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Descuento aplicado |
| `usado_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha de uso |

**Restricciones:** `UNIQUE(empresa_id, cupon_id, venta_id)`; trigger que controla `usos_maximos` y `usos_por_usuario`.

#### 43. `venta_estado_historial`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `venta_id` | UUID | FK compuesta, NOT NULL | Venta |
| `estado_anterior` | VARCHAR(30) | NULL | Estado previo |
| `estado_nuevo` | VARCHAR(30) | NOT NULL | Estado nuevo |
| `motivo` | VARCHAR(255) | NULL | Motivo |
| `usuario_id` | UUID | FK compuesta, NULL | Responsable |
| `ocurrido_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha del cambio |

**Restricciones:** Ã­ndice `(empresa_id, venta_id, ocurrido_en)`.

### 4.9 Machine Learning e IA

#### 44. `modelo_ml`

**Ãmbito:** global o tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NULL | NULL para modelo global |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre |
| `tipo` | VARCHAR(50) | NOT NULL, CHECK (`SUPERVISADO_DEMANDA`,`NO_SUPERVISADO_SEGMENTACION`) | Tipo |
| `algoritmo` | VARCHAR(50) | NOT NULL, CHECK (`LinearRegression`,`RandomForest`,`KMeans`,`XGBoost`,`Otro`) | Algoritmo |
| `version` | VARCHAR(30) | NOT NULL | VersiÃ³n |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'entrenando'`, CHECK (`entrenando`,`activo`,`retirado`,`fallido`) | Estado |
| `metricas_json` | JSONB | NOT NULL | MÃ©tricas |
| `hiperparametros_json` | JSONB | NULL | HiperparÃ¡metros |
| `dataset_desde` | DATE | NULL | Inicio del dataset |
| `dataset_hasta` | DATE | NULL | Fin del dataset |
| `dataset_hash` | VARCHAR(64) | NULL | Huella del dataset |
| `artefacto_url` | VARCHAR(255) | NOT NULL | Ruta del artefacto |
| `fecha_entrenamiento` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Entrenamiento |
| `activado_en` | TIMESTAMPTZ | NULL | ActivaciÃ³n |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE NULLS NOT DISTINCT (empresa_id, nombre, version)`; `CHECK (dataset_desde IS NULL OR dataset_hasta IS NULL OR dataset_desde <= dataset_hasta)`.

#### 45. `prediccion_demanda`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `modelo_ml_id` | UUID | FK `modelo_ml(id)`, NOT NULL | Modelo |
| `categoria_id` | UUID | FK compuesta, NOT NULL | CategorÃ­a |
| `periodo_proyectado` | VARCHAR(30) | NOT NULL | Mes o semana (`2026-11`) |
| `demanda_estimada` | NUMERIC(12,2) | NOT NULL, CHECK `>= 0` | Demanda estimada |
| `unidad` | VARCHAR(20) | NOT NULL, DEFAULT `'unidades'`, CHECK (`unidades`,`monto`) | Unidad |
| `intervalo_inferior` | NUMERIC(12,2) | NULL | LÃ­mite inferior |
| `intervalo_superior` | NUMERIC(12,2) | NULL | LÃ­mite superior |
| `generado_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | EjecuciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, modelo_ml_id, categoria_id, periodo_proyectado)`; `CHECK (intervalo_inferior IS NULL OR intervalo_superior IS NULL OR intervalo_inferior <= demanda_estimada AND demanda_estimada <= intervalo_superior)`.

#### 46. `segmento_cliente`

**Ãmbito:** tenant. **PK:** `id`.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `modelo_ml_id` | UUID | FK `modelo_ml(id)`, NOT NULL | Modelo |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Cliente |
| `segmento_nombre` | VARCHAR(50) | NOT NULL | ClÃºster asignado |
| `cluster_id` | INTEGER | NULL | ID numÃ©rico del clÃºster |
| `score_frecuencia` | NUMERIC(5,2) | NULL, CHECK `>= 0` | Frecuencia normalizada |
| `score_ticket_medio` | NUMERIC(12,2) | NULL, CHECK `>= 0` | Ticket promedio |
| `vigente_desde` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Inicio de vigencia |
| `vigente_hasta` | TIMESTAMPTZ | NULL | Fin de vigencia |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, modelo_ml_id, usuario_id, vigente_desde)`; `CHECK (vigente_hasta IS NULL OR vigente_hasta > vigente_desde)`.

#### 47. `consulta_ia_log`

**Ãmbito:** tenant. **PK:** `(id, ocurrido_en)` por particionado.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK compuesta, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Usuario |
| `prompt` | TEXT | NOT NULL | Consulta en lenguaje natural |
| `respuesta` | TEXT | NULL | Respuesta generada |
| `modelo_llm` | VARCHAR(80) | NULL | Modelo utilizado |
| `canal` | VARCHAR(20) | NOT NULL, DEFAULT `'texto'`, CHECK (`texto`,`voz`) | Canal |
| `reporte_tipo` | VARCHAR(100) | NOT NULL | Reporte autorizado |
| `parametros_json` | JSONB | NOT NULL | ParÃ¡metros extraÃ­dos |
| `tokens_entrada` | INTEGER | NULL, CHECK `>= 0` | Tokens de entrada |
| `tokens_salida` | INTEGER | NULL, CHECK `>= 0` | Tokens de salida |
| `costo` | NUMERIC(12,6) | NULL, CHECK `>= 0` | Costo estimado |
| `latencia_ms` | INTEGER | NULL, CHECK `>= 0` | Latencia |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'exitoso'`, CHECK (`exitoso`,`fallido`,`rechazado`) | Estado |
| `cache_key` | VARCHAR(100) | NULL | Clave de cachÃ© |
| `audio_url` | VARCHAR(255) | NULL | URL del audio generado o recibido |
| `audio_mime` | VARCHAR(40) | NULL | Tipo MIME del audio |
| `tts_modelo` | VARCHAR(80) | NULL | Modelo de texto a voz |
| `tts_voz` | VARCHAR(80) | NULL | Voz utilizada |
| `duracion_audio_ms` | INTEGER | NULL, CHECK `>= 0` | DuraciÃ³n del audio |
| `ocurrido_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha de ejecuciÃ³n |

**Restricciones:** Ã­ndice `(empresa_id, ocurrido_en DESC)` y GIN sobre `parametros_json`; retenciÃ³n y redacciÃ³n de PII definidas por polÃ­tica. El canal `voz` requiere `audio_url` y `audio_mime`; la respuesta TTS se audita con `tts_modelo` y `tts_voz`.

### 4.10 Extensiones de cobertura funcional

Esta secciÃ³n incorpora las tablas agregadas para cerrar las brechas de los 36 casos de uso.

#### 48. `verificacion_correo`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-02.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta `(empresa_id, usuario_id)`, NOT NULL | Usuario a verificar |
| `token_hash` | TEXT | UNIQUE, NOT NULL | Hash del token enviado por correo |
| `expira_en` | TIMESTAMPTZ | NOT NULL | Vigencia del token |
| `verificado_en` | TIMESTAMPTZ | NULL | Momento de confirmaciÃ³n |
| `creado_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | EmisiÃ³n |

**Restricciones:** `UNIQUE(empresa_id, id)`; `CHECK (expira_en > creado_en)`; FK con `ON DELETE CASCADE` desde `usuario`. El token nunca se almacena en texto plano.

#### 49. `prenda_recurso`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-25.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `prenda_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Prenda |
| `tipo` | VARCHAR(20) | NOT NULL, CHECK (`imagen`,`modelo_3d`,`textura`,`video`) | Tipo de recurso |
| `url` | VARCHAR(255) | NOT NULL | UbicaciÃ³n del recurso |
| `mime_type` | VARCHAR(80) | NULL | Tipo MIME |
| `orden` | SMALLINT | NOT NULL, DEFAULT 0 | Orden de presentaciÃ³n |
| `es_principal` | BOOLEAN | NOT NULL, DEFAULT FALSE | Recurso principal del tipo |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, id)`; Ã­ndice Ãºnico parcial para un solo recurso principal por `(empresa_id, prenda_id, tipo)`.

#### 50. `catalogo_version`

**Ãmbito:** tenant. **PK:** `empresa_id`. **Caso de uso:** CU-25/CU-27.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `empresa_id` | UUID | PK, FK `empresa(id)`, ON DELETE CASCADE | Tenant |
| `version` | BIGINT | NOT NULL, DEFAULT 1, CHECK `> 0` | VersiÃ³n monotÃ³nica del catÃ¡logo |
| `actualizado_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltimo cambio |

**Restricciones:** una fila por tenant. Los triggers de `prenda`, `variante`, `categoria`, `temporada`, `coleccion`, `proveedor`, `precio_historial` y `prenda_recurso` incrementan la versiÃ³n; los dispositivos comparan su `catalogo_version` para sincronizar solo el delta.

#### 51. `reserva_estado_historial`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-27.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Identificador de traza |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `reserva_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Reserva |
| `estado_anterior` | VARCHAR(20) | NULL | Estado previo |
| `estado_nuevo` | VARCHAR(20) | NOT NULL | Estado nuevo |
| `motivo` | VARCHAR(200) | NULL | Motivo del cambio |
| `usuario_id` | UUID | FK compuesta, NULL | Actor |
| `ocurrido_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Fecha del cambio |

**Restricciones:** Ã­ndice `(empresa_id, reserva_id, ocurrido_en DESC)`. Se escribe mediante trigger en cada cambio de `reserva.estado`.

#### 52. `reporte_exportado`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-34/CU-35.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Usuario que solicitÃ³ |
| `consulta_ia_log_id` | UUID | NULL | Consulta IA de origen |
| `consulta_ocurrido_en` | TIMESTAMPTZ | NULL | Clave de particiÃ³n de la consulta |
| `tipo_reporte` | VARCHAR(100) | NOT NULL | Reporte solicitado |
| `formato` | VARCHAR(10) | NOT NULL, CHECK (`pdf`,`xlsx`,`csv`) | Formato exportado |
| `archivo_url` | VARCHAR(255) | NOT NULL | Archivo generado |
| `tamano_bytes` | BIGINT | NULL, CHECK `>= 0` | TamaÃ±o |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'generado'`, CHECK (`generado`,`fallido`,`eliminado`) | Estado |
| `generado_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | GeneraciÃ³n |
| `expira_en` | TIMESTAMPTZ | NULL | RetenciÃ³n del archivo |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, id)`; FK compuesta `(consulta_ia_log_id, consulta_ocurrido_en)` con `ON DELETE SET NULL`; `CHECK (expira_en IS NULL OR expira_en > generado_en)`.

#### 53. `avatar_cliente`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-36.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Cliente |
| `nombre` | VARCHAR(80) | NOT NULL, DEFAULT `'Mi avatar'` | Nombre del avatar |
| `modelo_url` | VARCHAR(255) | NULL | Modelo 3D del avatar |
| `altura_cm` | NUMERIC(5,2) | NULL, CHECK `> 0` | Altura |
| `peso_kg` | NUMERIC(5,2) | NULL, CHECK `> 0` | Peso |
| `tono_piel` | VARCHAR(30) | NULL | Tono de piel |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |
| `deleted_at` | TIMESTAMPTZ | NULL | Soft delete |

**Restricciones:** `UNIQUE(empresa_id, id)`; un cliente puede tener varios avatares.

#### 54. `medida_corporal`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-36.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `avatar_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Avatar |
| `tipo` | VARCHAR(30) | NOT NULL, CHECK (`busto`,`cintura`,`cadera`,`hombro`,`cuello`,`largo_manga`,`largo_pierna`,`muslo`,`rodilla`) | Medida |
| `valor_cm` | NUMERIC(6,2) | NOT NULL, CHECK `> 0` | Valor en centÃ­metros |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, avatar_id, tipo)`; `UNIQUE(empresa_id, id)`.

#### 55. `prenda_ar`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-36.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `prenda_id` | UUID | FK compuesta, ON DELETE CASCADE, NOT NULL | Prenda |
| `variante_id` | UUID | FK compuesta, ON DELETE CASCADE, NULL | Variante especÃ­fica |
| `modelo_url` | VARCHAR(255) | NOT NULL | Modelo 3D de la prenda |
| `textura_url` | VARCHAR(255) | NULL | Textura |
| `puntos_ajuste` | JSONB | NULL | Puntos de anclaje/ajuste |
| `talla_referencia` | VARCHAR(10) | NULL | Talla del modelo |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Disponible |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Ãšltima modificaciÃ³n |

**Restricciones:** `UNIQUE(empresa_id, id)`; Ã­ndice parcial `(empresa_id, prenda_id) WHERE activo`.

#### 56. `sesion_prueba_virtual`

**Ãmbito:** tenant. **PK:** `id`. **Caso de uso:** CU-36.

| Columna | Tipo | Restricciones | DescripciÃ³n |
|---|---|---|---|
| `id` | UUID | PK, `DEFAULT gen_random_uuid()` | Identificador |
| `empresa_id` | UUID | FK `empresa(id)`, NOT NULL | Tenant |
| `usuario_id` | UUID | FK compuesta, NOT NULL | Cliente |
| `avatar_id` | UUID | FK compuesta, NOT NULL | Avatar usado |
| `prenda_id` | UUID | FK compuesta, NOT NULL | Prenda probada |
| `variante_id` | UUID | FK compuesta, NULL | Variante probada |
| `estado` | VARCHAR(20) | NOT NULL, DEFAULT `'iniciada'`, CHECK (`iniciada`,`completada`,`abandonada`,`fallida`) | Estado |
| `resultado_url` | VARCHAR(255) | NULL | Imagen o video del resultado |
| `iniciada_en` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Inicio |
| `finalizada_en` | TIMESTAMPTZ | NULL | Fin |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | Alta |

**Restricciones:** `UNIQUE(empresa_id, id)`; `CHECK (finalizada_en IS NULL OR finalizada_en >= iniciada_en)`.

---

## 5. Relaciones principales

- `empresa` 1:N `suscripcion`, `pago_suscripcion`, `rol`, `usuario`, `sucursal`, `categoria`, `temporada`, `proveedor`, `prenda`, `variante`, `inventario`, `venta`, `dispositivo`, `cupon`, `consulta_ia_log`.
- `plan` 1:N `plan_limite`, `suscripcion`.
- `rol` N:M `permiso` mediante `rol_permiso`.
- `usuario` 1:N `sesion`, `verificacion_correo`, `direccion_cliente`, `carrito`, `reserva`, `venta` (como cliente), `venta` (como cajero), `consulta_ia_log`, `reporte_exportado`, `segmento_cliente`, `avatar_cliente`, `sesion_prueba_virtual`.
- `sucursal` 1:N `usuario`, `inventario`, `movimiento_inventario`, `reserva`, `venta`, `dispositivo`, `transferencia_inventario` (origen/destino).
- `categoria` 1:N `prenda`, `prediccion_demanda`.
- `temporada` 1:N `coleccion`, `prenda`.
- `coleccion` 1:N `prenda`.
- `proveedor` 1:N `prenda`.
- `prenda` 1:N `variante`, `prenda_recurso`, `prenda_ar`, `sesion_prueba_virtual`.
- `variante` 1:N `precio_historial`, `inventario`, `movimiento_inventario`, `reserva_detalle`, `carrito_detalle`, `venta_detalle`, `cambio_detalle`, `transferencia_detalle`, `prenda_ar`, `sesion_prueba_virtual`.
- `reserva` 1:N `reserva_detalle`, `reserva_estado_historial`; N:1 `dispositivo` (opcional).
- `empresa` 1:1 `catalogo_version`.
- `consulta_ia_log` 1:N `reporte_exportado` (opcional, con `ON DELETE SET NULL`).
- `avatar_cliente` 1:N `medida_corporal`, `sesion_prueba_virtual`.
- `carrito` 1:N `carrito_detalle`.
- `venta` 1:N `venta_detalle`, `pago`, `envio`, `cambio_prenda`, `venta_estado_historial`.
- `cambio_prenda` 1:N `cambio_detalle`.
- `transferencia_inventario` 1:N `transferencia_detalle`.
- `operacion_pendiente` 1:0..1 `resolucion_conflicto`.
- `modelo_ml` 1:N `prediccion_demanda`, `segmento_cliente`.
- `cupon` 1:N `cupon_uso`.
- `direccion_cliente` 1:N `envio`.

---

## 6. Aislamiento multitenant y RLS

### Regla de tenant

Toda tabla de negocio tiene `empresa_id UUID NOT NULL` y FK a `empresa(id)`. Las tablas padre incluyen `UNIQUE(empresa_id, id)`. Las tablas hijas usan FK compuesta:

```sql
FOREIGN KEY (empresa_id, variante_id)
  REFERENCES variante (empresa_id, id)
```

Esto impide que una fila apunte a un registro de otra empresa, incluso si el `id` existe.

### PolÃ­ticas RLS

Para cada tabla de tenant:

```sql
ALTER TABLE nombre_tabla ENABLE ROW LEVEL SECURITY;
ALTER TABLE nombre_tabla FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON nombre_tabla
  USING (empresa_id = current_setting('app.empresa_id', true)::uuid);
```

- La aplicaciÃ³n establece `SET LOCAL app.empresa_id = '<uuid>'` al inicio de cada transacciÃ³n.
- El rol de aplicaciÃ³n `fashion_app` no tiene `BYPASSRLS`.
- El Superadmin usa un rol separado `fashion_superadmin` o la variable `app.is_superadmin`; toda acciÃ³n queda en auditorÃ­a con `empresa_afectada_id`.
- `empresa` se filtra por `id`.
- `plan`, `ciudad`, `color`, `talla` y `permiso` son de lectura global; escritura solo Superadmin.
- `modelo_ml` permite modelos globales (`empresa_id IS NULL`) y modelos del tenant.
- `bitacora_auditoria` se lee por tenant; el Superadmin puede leer todo; la escritura se hace mediante funciÃ³n `SECURITY DEFINER`.
- Las nueve tablas nuevas (`verificacion_correo`, `prenda_recurso`, `catalogo_version`, `reserva_estado_historial`, `reporte_exportado`, `avatar_cliente`, `medida_corporal`, `prenda_ar`, `sesion_prueba_virtual`) estÃ¡n incluidas en el arreglo RLS con polÃ­tica `FOR ALL` por `empresa_id`.
- El DDL aplica **52 polÃ­ticas RLS** y **48 triggers** no internos.

### Reglas de autenticaciÃ³n

- Login por tenant: se resuelve `empresa.slug`, luego se busca `usuario` por `(empresa_id, correo)`.
- Superadmin tiene `empresa_id NULL`, rol global y ruta de acceso separada.
- El refresh token se guarda hasheado en `sesion`; nunca en texto plano.
- La verificaciÃ³n de correo usa `verificacion_correo.token_hash` con expiraciÃ³n; al confirmar se actualiza `usuario.email_verificado` y `email_verificado_en`.
- Bloqueo temporal por `intentos_fallidos` y `bloqueado_hasta`.

---

## 7. Reglas de integridad y triggers

| Regla | ImplementaciÃ³n |
|---|---|
| `updated_at` automÃ¡tico | Trigger `fn_set_updated_at` en tablas mutables |
| Stock no negativo | CHECK en `inventario` y validaciÃ³n atÃ³mica en la capa de servicio |
| Venta descuenta stock | TransacciÃ³n que actualiza `inventario`, incrementa `version` y crea `movimiento_inventario` |
| Reserva aparta stock | Trigger `fn_actualizar_stock_reservado` sobre `reserva_detalle`; bloquea cambios si la reserva ya estÃ¡ cerrada |
| LiberaciÃ³n de stock de reserva | Trigger `fn_liberar_stock_reserva` antes de cambiar a `cancelada`, `expirada`, `convertida` o `completada`; idempotente por `liberada_en` |
| Historial de reserva | Trigger `fn_registrar_historial_reserva` que inserta en `reserva_estado_historial` |
| ExpiraciÃ³n de reservas | FunciÃ³n `fn_expirar_reservas()` ejecutable por job programado (`pg_cron` o worker); libera stock y registra historial |
| VersiÃ³n de catÃ¡logo | Trigger `fn_bump_catalogo_version` sobre prenda, variante, categorÃ­a, temporada, colecciÃ³n, proveedor, precio y recursos |
| Transferencia genera movimientos | Dos movimientos enlazados por `transferencia_id` (`TRANSFERENCIA_SALIDA` y `TRANSFERENCIA_ENTRADA`) |
| Total de venta | Trigger sobre `venta_detalle` que recalcula `subtotal`, `descuento`, `impuesto` y `total` |
| Suma de pagos | Trigger sobre `pago` que impide superar `venta.total` con pagos completados |
| Cambio/devoluciÃ³n | Trigger que valida cantidad acumulada contra `venta_detalle.cantidad` |
| CupÃ³n | Trigger que valida vigencia, monto mÃ­nimo, usos totales y usos por usuario |
| LÃ­mite de sucursales | Trigger sobre `sucursal` que consulta `plan_limite` de la suscripciÃ³n activa |
| Rol de usuario | Trigger que valida rol global o del mismo tenant, y sucursal del mismo tenant |
| AuditorÃ­a inmutable | `REVOKE UPDATE, DELETE`; trigger append-only; inserciÃ³n vÃ­a funciÃ³n |
| AuditorÃ­a sin secretos | `fn_audit_row` excluye `password_hash` y `refresh_token_hash` de `datos_antes` y `datos_despues` |
| Idempotencia offline | `UNIQUE(empresa_id, idempotency_key)` en `operacion_pendiente` y `venta` |
| Anti-replay QR | `qr_nonce` Ãºnico por dispositivo y ventana de vigencia |
| Precio offline desactualizado | ComparaciÃ³n contra `precio_historial` vigente; si excede tolerancia, genera conflicto |

### Orden transaccional de una venta

1. Validar tenant, usuario, sucursal y permisos.
2. Bloquear `inventario` con `SELECT ... FOR UPDATE`.
3. Verificar `stock_disponible >= cantidad`.
4. Insertar `venta` y `venta_detalle`.
5. Descontar stock y crear `movimiento_inventario`.
6. Registrar `pago`.
7. Registrar `venta_estado_historial`.
8. Auditar la operaciÃ³n.

Todo ocurre en una sola transacciÃ³n; si falla un paso, se revierte completo.

### ResoluciÃ³n de conflictos offline

Estados de `operacion_pendiente`:

```text
pendiente -> procesando -> confirmada
                       -> conflicto -> resolucion_conflicto
                       -> rechazada
```

- Si no hay stock, la operaciÃ³n pasa a `conflicto`; no se crea venta.
- La resoluciÃ³n aplica una estrategia y deja `resultado_json` con el efecto exacto.
- Si la estrategia es `REINTENTO`, se vuelve a encolar con backoff.
- La venta solo se enlaza cuando la operaciÃ³n queda `confirmada`.

---

## 8. Estados y dominios

| Tabla | Campo | Valores |
|---|---|---|
| `empresa` | `estado` | `activa`, `suspendida`, `inactiva` |
| `suscripcion` | `estado` | `activa`, `vencida`, `suspendida`, `cancelada` |
| `pago_suscripcion` | `estado` | `pendiente`, `completado`, `fallido`, `reembolsado` |
| `usuario` | `activo` | booleano |
| `movimiento_inventario` | `tipo` | `INGRESO`, `MERMA`, `TRANSFERENCIA_SALIDA`, `TRANSFERENCIA_ENTRADA`, `VENTA`, `AJUSTE`, `DEVOLUCION`, `RESERVA`, `LIBERACION_RESERVA` |
| `transferencia_inventario` | `estado` | `pendiente`, `en_transito`, `recibida`, `cancelada` |
| `reserva` | `estado` | `activa`, `confirmada`, `expirada`, `cancelada`, `convertida` |
| `carrito` | `estado` | `activo`, `convertido`, `abandonado` |
| `venta` | `canal` | `POS`, `WEB`, `OFFLINE` |
| `venta` | `estado` | `pendiente_pago`, `pagada`, `preparando`, `enviada`, `entregada`, `completada`, `anulada`, `devuelta`, `pendiente_sync` |
| `pago` | `metodo` | `efectivo`, `tarjeta`, `qr`, `pasarela`, `transferencia`, `vale` |
| `pago` | `estado` | `pendiente`, `completado`, `fallido`, `reembolsado` |
| `cambio_prenda` | `tipo` | `CAMBIO`, `DEVOLUCION` |
| `cambio_prenda` | `estado` | `registrado`, `aprobado`, `rechazado`, `completado` |
| `envio` | `estado` | `pendiente`, `preparando`, `en_transito`, `entregado`, `fallido`, `devuelto`, `cancelado` |
| `cupon` | `tipo` | `PORCENTAJE`, `MONTO_FIJO` |
| `operacion_pendiente` | `estado` | `pendiente`, `procesando`, `confirmada`, `conflicto`, `rechazada` |
| `resolucion_conflicto` | `estrategia` | `AJUSTE_MANUAL`, `TRANSFERENCIA_SUCURSAL`, `VALE_CREDITO`, `DESCARTE`, `REINTENTO` |
| `modelo_ml` | `estado` | `entrenando`, `activo`, `retirado`, `fallido` |
| `consulta_ia_log` | `estado` | `exitoso`, `fallido`, `rechazado` |
| `consulta_ia_log` | `canal` | `texto`, `voz` |
| `reporte_exportado` | `formato` | `pdf`, `xlsx`, `csv` |
| `reporte_exportado` | `estado` | `generado`, `fallido`, `eliminado` |
| `sesion_prueba_virtual` | `estado` | `iniciada`, `completada`, `abandonada`, `fallida` |

---

## 9. Ãndices y particiones

### Ãndices obligatorios

- `usuario (empresa_id, correo)` Ãºnico.
- `variante (empresa_id, sku)` Ãºnico.
- `inventario (empresa_id, sucursal_id, variante_id)` Ãºnico.
- `movimiento_inventario (empresa_id, variante_id, ocurrido_en DESC)`.
- `venta (empresa_id, fecha_hora DESC)`.
- `venta (empresa_id, estado)`.
- `venta (empresa_id, usuario_id)`.
- `venta (empresa_id, numero)` Ãºnico.
- `pago (empresa_id, venta_id)`.
- `operacion_pendiente (empresa_id, estado, fecha_recepcion)`.
- `reserva (empresa_id, expira_en)` parcial para `activa`/`confirmada`.
- `reserva (empresa_id, dispositivo_id, estado)` parcial cuando hay dispositivo.
- `reserva_estado_historial (empresa_id, reserva_id, ocurrido_en DESC)`.
- `envio (empresa_id, estado)`.
- `cupon (empresa_id, codigo)` Ãºnico.
- `precio_historial (empresa_id, variante_id, vigente_desde DESC)`.
- `consulta_ia_log (empresa_id, ocurrido_en DESC)`.
- `verificacion_correo (empresa_id, usuario_id, expira_en DESC)` parcial sin verificar.
- `prenda_recurso (empresa_id, prenda_id, tipo, orden)` parcial sin soft delete.
- `avatar_cliente (empresa_id, usuario_id)` parcial sin soft delete.
- `medida_corporal (empresa_id, avatar_id)`.
- `prenda_ar (empresa_id, prenda_id)` parcial activos.
- `sesion_prueba_virtual (empresa_id, usuario_id, iniciada_en DESC)`.
- `reporte_exportado (empresa_id, generado_en DESC)`.

### Ãndices parciales

- SuscripciÃ³n activa Ãºnica por empresa.
- Carrito activo Ãºnico por usuario.
- DirecciÃ³n principal Ãºnica por usuario.
- `pasarela_id` Ãºnico cuando no es NULL.
- `tracking` Ãºnico cuando no es NULL.
- `venta_id` Ãºnico en `operacion_pendiente` cuando no es NULL.
- Un solo `prenda_recurso` principal por `(empresa_id, prenda_id, tipo)`.
- `verificacion_correo` indexada solo mientras `verificado_en IS NULL`.

### Ãndices JSONB

- GIN sobre `operacion_pendiente.payload_json`.
- GIN sobre `consulta_ia_log.parametros_json`.
- GIN sobre `bitacora_auditoria.datos_antes` y `datos_despues` si se consultan.
- GIN sobre `prenda_ar.puntos_ajuste` si se consultan ajustes por regiÃ³n.

### Particiones

| Tabla | Clave | Frecuencia |
|---|---|---|
| `bitacora_auditoria` | `RANGE(ocurrido_en)` | Mensual |
| `movimiento_inventario` | `RANGE(ocurrido_en)` | Mensual o anual |
| `consulta_ia_log` | `RANGE(ocurrido_en)` | Mensual |

En tablas particionadas, la PK es compuesta `(id, ocurrido_en)` porque PostgreSQL exige incluir la clave de particiÃ³n en las restricciones Ãºnicas.

---

## 10. Cambios respecto a las 32 tablas originales

### Tablas nuevas (24)

Respecto del modelo original de 32 tablas:

`plan_limite`, `pago_suscripcion`, `permiso`, `rol_permiso`, `sesion`, `precio_historial`, `transferencia_inventario`, `transferencia_detalle`, `cambio_detalle`, `dispositivo`, `direccion_cliente`, `envio`, `cupon`, `cupon_uso`, `venta_estado_historial`, `verificacion_correo`, `prenda_recurso`, `catalogo_version`, `reserva_estado_historial`, `reporte_exportado`, `avatar_cliente`, `medida_corporal`, `prenda_ar`, `sesion_prueba_virtual`.

### Tablas modificadas de forma relevante

- `empresa`: `slug`, moneda, zona horaria, logo y soft delete.
- `plan`: cÃ³digo, moneda y lÃ­mites externalizados.
- `suscripcion`: precio pactado, moneda, ciclo, renovaciÃ³n y unicidad activa.
- `rol` y `usuario`: soporte de rol global de Superadmin, RBAC granular, `email_verificado` y `email_verificado_en`.
- `sesion`: `refresh_token_hash`, `ip_origen`, `created_at` y `revocado_en`; alineada con autenticaciÃ³n real.
- `prenda`: `precio_base`, `moneda`, `modelo_3d_url` e `imagen_url`.
- `variante`: `empresa_id` y SKU Ãºnico por tenant.
- `inventario`: stock mÃ­nimo, versiÃ³n y checks.
- `movimiento_inventario`: documento origen, usuario, costo y saldo anterior.
- `reserva`: `fecha_visita`, `expira_en`, `dispositivo_id`, `liberada_en`, `motivo_cierre` y estados `activa`/`confirmada`/`convertida`.
- `dispositivo`: `serial`, `catalogo_version`, `ultima_sync` y estados `activo`/`revocado`.
- `carrito`: unicidad de carrito activo.
- `venta`: canal, estados de pedido, totales desglosados, idempotencia y firma QR.
- `pago`: idempotencia, moneda y control de suma.
- `cambio_prenda`: encabezado con detalle y soporte de devoluciÃ³n.
- `operacion_pendiente`: tenant, dispositivo, reintentos, error y vÃ­nculo con venta.
- `resolucion_conflicto`: tenant, detalle y resultado.
- `modelo_ml`: versiÃ³n, estado, dataset y mÃ©tricas.
- `prediccion_demanda` y `segmento_cliente`: tenant, unicidad y vigencia.
- `consulta_ia_log`: respuesta, modelo, tokens, costo, latencia, estado, `audio_url`, `audio_mime`, `tts_modelo`, `tts_voz` y `duracion_audio_ms`.

### Cambios para cobertura de los 36 casos de uso

| Caso de uso | Cambio aplicado |
|---|---|
| CU-02 VerificaciÃ³n de correo | `usuario.email_verificado_en` y tabla `verificacion_correo` con token hash, expiraciÃ³n y confirmaciÃ³n |
| CU-20/CU-27 Reservas | LiberaciÃ³n automÃ¡tica de stock, `liberada_en`, `motivo_cierre`, historial de estados y job `fn_expirar_reservas()` |
| CU-25 CatÃ¡logo | `prenda_recurso`, `catalogo_version`, `dispositivo.catalogo_version` y triggers de incremento |
| CU-34 Reportes | `reporte_exportado` con formato, archivo, tamaÃ±o, estado y retenciÃ³n |
| CU-35 Audio/TTS | Campos de audio, MIME, modelo, voz y duraciÃ³n en `consulta_ia_log` |
| CU-36 Probador virtual | `avatar_cliente`, `medida_corporal`, `prenda_ar` y `sesion_prueba_virtual` |

La validaciÃ³n automatizada de estas coberturas estÃ¡ en `tests/07_cobertura_36.sql`, incluida en `tests/run_tests.sql`.

### Tablas que se mantienen como catÃ¡logos globales

`plan`, `ciudad`, `color`, `talla`, `permiso`. Si una empresa necesita colores o tallas propias, se puede agregar `empresa_id` o una tabla puente; no es necesario para el alcance actual.

---

## 11. Pruebas de validaciÃ³n

1. **Aislamiento:** Tenant A no puede leer ni referenciar filas de Tenant B; las FK compuestas y RLS lo bloquean.
2. **Stock concurrente:** dos ventas simultÃ¡neas por la Ãºltima unidad; solo una confirma.
3. **Idempotencia offline:** reintento con la misma `idempotency_key` no duplica la venta.
4. **Conflicto offline:** venta sin stock genera `operacion_pendiente.estado = 'conflicto'` y una resoluciÃ³n.
5. **QR:** firma invÃ¡lida, nonce reutilizado o comprobante vencido se rechazan.
6. **Pagos:** webhook duplicado no duplica el pago; la suma de pagos no supera el total.
7. **Devoluciones:** no se puede devolver mÃ¡s cantidad que la vendida.
8. **Cupones:** no se exceden usos totales ni usos por usuario.
9. **SuscripciÃ³n:** no puede haber dos suscripciones activas para la misma empresa.
10. **LÃ­mite de plan:** no se puede crear una sucursal por encima del lÃ­mite.
11. **AuditorÃ­a:** UPDATE/DELETE sobre `bitacora_auditoria` falla; toda acciÃ³n sensible queda registrada.
12. **Superadmin:** las acciones globales quedan con `empresa_afectada_id` y `actor_tipo = 'superadmin'`.
13. **VerificaciÃ³n de correo (CU-02):** se registra token, expiraciÃ³n y `email_verificado_en`.
14. **LiberaciÃ³n de reserva (CU-20):** cancelar libera `stock_reservado`, registra `liberada_en` e historial y bloquea cambios posteriores al detalle.
15. **ExpiraciÃ³n de reserva (CU-27):** `fn_expirar_reservas()` pasa a `expirada`, libera stock y deja historial.
16. **VersiÃ³n de catÃ¡logo (CU-25):** un cambio en `prenda` incrementa `catalogo_version.version`.
17. **Reporte y audio (CU-34/CU-35):** se registran `reporte_exportado` y metadatos de audio/TTS en `consulta_ia_log`.
18. **Probador virtual (CU-36):** se crean avatar, medidas, prenda AR y sesiÃ³n de prueba virtual.

La suite completa se ejecutÃ³ con `ON_ERROR_STOP=1` y terminÃ³ con cÃ³digo de salida `0` sobre PostgreSQL 16. VerificaciÃ³n estructural: **56 tablas**, **3 particionadas**, **52 polÃ­ticas RLS** y **48 triggers**.

---

## 12. ImplementaciÃ³n

1. DDL modular en `db/`, ejecutable con `db/run_all.sql`.
2. Seeds de planes, lÃ­mites, ciudades, colores, tallas, roles, permisos y tenant demo en `db/16_seeds.sql`.
3. RLS, triggers e Ã­ndices en `db/13_funciones_triggers.sql`, `db/14_rls.sql` y `db/15_indices.sql`; AR en `db/17_ar.sql`.
4. Pruebas ejecutables en `tests/run_tests.sql`; validan aislamiento, stock, idempotencia offline, pagos, devoluciones, RLS, auditorÃ­a, lÃ­mites de plan y cobertura de los 36 casos de uso (`tests/07_cobertura_36.sql`).
5. Pendiente fuera del alcance CU-01..CU-05: diagrama ER definitivo y protocolo offline detallado.
6. Ajustes de CU-01 a CU-05 en `db/18_ajustes_cu01_05.sql`: columna `es_accion_superadmin`, metadatos HTTP de auditoria, rol `encargado`, funciones `SECURITY DEFINER` para login y verificacion de correo, y verificacion de los usuarios demo.
7. Backend FastAPI en `backend/` con capa RLS multitenant (`SET LOCAL ROLE fashion_app` + `app.empresa_id`), JWT con `sid` revocable, registro con verificacion de correo, perfil y middleware de auditoria.
8. Frontend Angular en `frontend/` con `AuthService`, interceptor Bearer, guards, login, registro, verificacion de correo y perfil.
9. Documentacion de robustez, secuencias, clases e interfaces de CU-01 a CU-05 en `docs/CU01_CU05_ICONIX.md`.

---

**Nota:** este documento define el modelo final acordado. El DDL, los seeds, las polÃ­ticas RLS y las pruebas se encuentran en `db/` y `tests/`.


