-- ============================================================================
-- GUÍA Y DICCIONARIO UNIFICADO DE TABLAS - SISTEMA SAAS FASHION STORE
-- ============================================================================
-- Proyecto: Sistema Web / Móvil Multi-Tenant de Gestión Boutique y E-Commerce
-- Base de Datos: PostgreSQL 16+
-- Total de Tablas: 62 tablas distribuidas en 16 módulos funcionales
-- Propósito: Documento de referencia arquitectónica y guía para docencia / defensa.
-- NOTA: Este archivo es puramente documental / guía de referencia estructural.
-- ============================================================================

-- EXTENSIONES REQUERIDAS DE POSTGRESQL
-- ----------------------------------------------------------------------------
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- CREATE EXTENSION IF NOT EXISTS citext;

-- ============================================================================
-- ÍNDICE DE MÓDULOS Y TABLAS (62 TABLAS)
-- ============================================================================
-- MÓDULO 01: CORE SAAS & MULTI-TENANCY (5 tablas)
--   1. empresa
--   2. plan
--   3. plan_limite
--   4. suscripcion
--   5. pago_suscripcion
--
-- MÓDULO 02: GEOGRAFÍA Y ESTRUCTURA ORGANIZACIONAL (2 tablas)
--   6. ciudad
--   7. sucursal
--
-- MÓDULO 03: SEGURIDAD, RBAC Y AUTENTICACIÓN (6 tablas)
--   8. rol
--   9. permiso
--  10. rol_permiso
--  11. usuario
--  12. sesion
--  13. verificacion_correo
--
-- MÓDULO 04: AUDITORÍA Y TRAZABILIDAD (PARTICIONADA) (1 tabla)
--  14. bitacora_auditoria
--
-- MÓDULO 05: CATÁLOGO DE PRODUCTOS Y PRENDAS (11 tablas)
--  15. categoria
--  16. temporada
--  17. coleccion
--  18. proveedor
--  19. color
--  20. talla
--  21. prenda
--  22. prenda_recurso
--  23. catalogo_version
--  24. variante
--  25. precio_historial
--
-- MÓDULO 06: INVENTARIO, KÁRDEX Y TRANSFERENCIAS (4 tablas)
--  26. inventario
--  27. movimiento_inventario
--  28. transferencia_inventario
--  29. transferencia_detalle
--
-- MÓDULO 07: RESERVAS DE PROBADOR Y CARRITO (5 tablas)
--  30. reserva
--  31. reserva_detalle
--  32. reserva_estado_historial
--  33. carrito
--  34. carrito_detalle
--
-- MÓDULO 08: E-COMMERCE BASE (DIRECCIONES, CUPONES, DISPOSITIVOS) (3 tablas)
--  35. direccion_cliente
--  36. cupon
--  37. dispositivo
--
-- MÓDULO 09: VENTAS, FACTURACIÓN, PAGOS Y CAMBIOS (6 tablas)
--  38. venta
--  39. venta_detalle
--  40. pago
--  41. cambio_prenda
--  42. cambio_detalle
--  43. venta_estado_historial
--
-- MÓDULO 10: CONTINGENCIA OFFLINE Y RESOLUCIÓN DE CONFLICTOS (2 tablas)
--  44. operacion_pendiente
--  45. resolucion_conflicto
--
-- MÓDULO 11: ENVÍOS Y DERIVADOS DE E-COMMERCE (2 tablas)
--  46. envio
--  47. cupon_uso
--
-- MÓDULO 12: MACHINE LEARNING, IA Y ANALÍTICA (5 tablas)
--  48. modelo_ml
--  49. prediccion_demanda
--  50. segmento_cliente
--  51. consulta_ia_log
--  52. reporte_exportado
--
-- MÓDULO 13: REALIDAD AUMENTADA (AR) Y VESTIDOR VIRTUAL (4 tablas)
--  53. avatar_cliente
--  54. medida_corporal
--  55. prenda_ar
--  56. sesion_prueba_virtual
--
-- MÓDULO 14: PASARELA DE PAGOS Y WEBHOOKS (1 tabla)
--  57. stripe_evento
--
-- MÓDULO 15: SOFT-LOCKS, DEVOLUCIONES QR Y REPLICACIÓN (3 tablas)
--  58. soft_lock
--  59. nota_cambio
--  60. sync_registro_idempotencia
--
-- MÓDULO 16: BACKUPS Y RESTAURACIÓN (2 tablas)
--  61. backup_registro
--  62. backup_configuracion
-- ============================================================================


-- ============================================================================
-- MÓDULO 01: CORE SAAS & MULTI-TENANCY
-- ============================================================================

-- 1. Tenants / Empresas suscritas a la plataforma SaaS
CREATE TABLE empresa (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre varchar(120) NOT NULL,
    slug citext NOT NULL UNIQUE,
    nit varchar(20) NOT NULL UNIQUE,
    correo citext NOT NULL,
    telefono varchar(20),
    direccion varchar(200),
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('pendiente_plan', 'activa', 'suspendida', 'cancelada')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

-- 2. Catálogo de planes de suscripción (Básico, Profesional, Enterprise)
CREATE TABLE plan (
    id smallserial PRIMARY KEY,
    codigo varchar(20) NOT NULL UNIQUE,
    nombre varchar(60) NOT NULL,
    precio_mensual numeric(12,2) NOT NULL DEFAULT 0 CHECK (precio_mensual >= 0),
    periodo varchar(20) NOT NULL DEFAULT 'mensual' CHECK (periodo IN ('mensual', 'anual')),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 3. Cuotas y límites máximos por recurso de cada plan (usuarios, sucursales, productos)
CREATE TABLE plan_limite (
    id bigserial PRIMARY KEY,
    plan_id smallint NOT NULL REFERENCES plan(id) ON DELETE CASCADE,
    recurso varchar(40) NOT NULL,
    limite integer CHECK (limite IS NULL OR limite >= 0),
    UNIQUE (plan_id, recurso)
);

-- 4. Contratos de suscripción activa/prueba entre una Empresa y un Plan
CREATE TABLE suscripcion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    plan_id smallint NOT NULL REFERENCES plan(id),
    estado varchar(20) NOT NULL DEFAULT 'prueba'
        CHECK (estado IN ('prueba', 'activa', 'mora', 'suspendida', 'cancelada')),
    fecha_inicio date NOT NULL,
    fecha_fin date,
    renovacion_auto boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    CHECK (fecha_fin IS NULL OR fecha_fin > fecha_inicio)
);

-- 5. Registro de cobros y pagos de membresía SaaS mensual/anual
CREATE TABLE pago_suscripcion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    suscripcion_id uuid NOT NULL,
    monto numeric(12,2) NOT NULL CHECK (monto > 0),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    metodo varchar(30) NOT NULL
        CHECK (metodo IN ('efectivo', 'tarjeta', 'qr', 'pasarela', 'transferencia')),
    referencia varchar(100),
    estado varchar(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'completado', 'fallido', 'reembolsado')),
    pagado_en timestamptz,
    periodo_inicio date NOT NULL,
    periodo_fin date NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, suscripcion_id)
        REFERENCES suscripcion(empresa_id, id) ON DELETE CASCADE,
    CHECK (periodo_fin > periodo_inicio)
);


-- ============================================================================
-- MÓDULO 02: GEOGRAFÍA Y ESTRUCTURA ORGANIZACIONAL
-- ============================================================================

-- 6. Ciudades y divisiones territoriales para sucursales y envíos
CREATE TABLE ciudad (
    id smallserial PRIMARY KEY,
    nombre varchar(80) NOT NULL,
    departamento varchar(80) NOT NULL,
    pais char(2) NOT NULL DEFAULT 'BO',
    UNIQUE (nombre, departamento)
);

-- 7. Puntos físicos de venta / Boutiques de cada Empresa (multi-sucursal)
CREATE TABLE sucursal (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    ciudad_id smallint NOT NULL REFERENCES ciudad(id),
    nombre varchar(120) NOT NULL,
    direccion varchar(200) NOT NULL,
    telefono varchar(20),
    es_matriz boolean NOT NULL DEFAULT false,
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'inactiva')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre)
);


-- ============================================================================
-- MÓDULO 03: SEGURIDAD, RBAC Y AUTENTICACIÓN
-- ============================================================================

-- 8. Roles del sistema (superadmin, admin, encargado, cajero, cliente)
CREATE TABLE rol (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(50) NOT NULL,
    descripcion text,
    es_global boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, nombre),
    CHECK ((es_global AND empresa_id IS NULL) OR ((NOT es_global) AND empresa_id IS NOT NULL))
);

-- 9. Catálogo granular de privilegios y permisos de sistema
CREATE TABLE permiso (
    id smallserial PRIMARY KEY,
    codigo varchar(80) NOT NULL UNIQUE,
    descripcion text NOT NULL,
    modulo varchar(40) NOT NULL
);

-- 10. Matriz asociativa Muchos a Muchos entre Roles y Permisos
CREATE TABLE rol_permiso (
    rol_id uuid NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
    permiso_id smallint NOT NULL REFERENCES permiso(id) ON DELETE CASCADE,
    PRIMARY KEY (rol_id, permiso_id)
);

-- 11. Cuentas de usuario pertenecientes a una empresa o superadministradores
CREATE TABLE usuario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    rol_id uuid NOT NULL REFERENCES rol(id),
    sucursal_id uuid,
    nombre varchar(120) NOT NULL,
    correo citext NOT NULL,
    password_hash text NOT NULL,
    telefono varchar(20),
    email_verificado boolean NOT NULL DEFAULT false,
    email_verificado_en timestamptz,
    estado varchar(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    ultimo_acceso timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, correo),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id)
);

-- 12. Sesiones activas con tokens JWT y Refresh Tokens criptográficos
CREATE TABLE sesion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    refresh_token_hash text NOT NULL UNIQUE,
    ip_origen inet,
    user_agent text,
    created_at timestamptz NOT NULL DEFAULT now(),
    expira_en timestamptz NOT NULL,
    revocado_en timestamptz,
    CHECK (expira_en > created_at)
);

-- 13. Tokens de activación y verificación de correo electrónico
CREATE TABLE verificacion_correo (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    token_hash text NOT NULL UNIQUE,
    expira_en timestamptz NOT NULL,
    verificado_en timestamptz,
    creado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id) ON DELETE CASCADE,
    CHECK (expira_en > creado_en)
);


-- ============================================================================
-- MÓDULO 04: AUDITORÍA Y TRAZABILIDAD (PARTICIONADA)
-- ============================================================================

-- 14. Registro inmutable de eventos, accesos y cambios en los datos (particionada por fecha)
CREATE TABLE bitacora_auditoria (
    id bigserial,
    empresa_id uuid REFERENCES empresa(id) ON DELETE SET NULL,
    empresa_afectada_id uuid REFERENCES empresa(id) ON DELETE SET NULL,
    usuario_id uuid REFERENCES usuario(id) ON DELETE SET NULL,
    actor_tipo varchar(20) NOT NULL DEFAULT 'usuario'
        CHECK (actor_tipo IN ('usuario', 'sistema', 'superadmin')),
    accion varchar(20) NOT NULL
        CHECK (accion IN ('insert', 'update', 'delete', 'login', 'logout', 'export', 'access', 'sync')),
    entidad varchar(60) NOT NULL,
    entidad_id uuid,
    datos_antes jsonb,
    datos_despues jsonb,
    ip inet,
    es_accion_superadmin boolean NOT NULL DEFAULT false,
    metodo varchar(10),
    endpoint varchar(255),
    parametros jsonb,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, ocurrido_en)
) PARTITION BY RANGE (ocurrido_en);


-- ============================================================================
-- MÓDULO 05: CATÁLOGO DE PRODUCTOS Y PRENDAS
-- ============================================================================

-- 15. Jerarquía de categorías de prendas (recursiva con categoría padre)
CREATE TABLE categoria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(100) NOT NULL,
    categoria_padre_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre),
    FOREIGN KEY (empresa_id, categoria_padre_id)
        REFERENCES categoria(empresa_id, id)
);

-- 16. Temporadas de moda (Otoño-Invierno, Primavera-Verano, etc.)
CREATE TABLE temporada (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(80) NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre),
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin > fecha_inicio)
);

-- 17. Colecciones exclusivas por año o lanzamiento de la marca
CREATE TABLE coleccion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(80) NOT NULL,
    anio smallint CHECK (anio IS NULL OR anio BETWEEN 1900 AND 2200),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre)
);

-- 18. Proveedores o fabricantes de prendas textiles
CREATE TABLE proveedor (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(120) NOT NULL,
    nit varchar(20) NOT NULL,
    correo citext,
    telefono varchar(20),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nit)
);

-- 19. Catálogo normalizado de colores con código Hexadecimal
CREATE TABLE color (
    id smallserial PRIMARY KEY,
    nombre varchar(40) NOT NULL UNIQUE,
    hex char(7)
);

-- 20. Catálogo normalizado de tallas (XS, S, M, L, XL, etc.) con orden visual
CREATE TABLE talla (
    id smallserial PRIMARY KEY,
    nombre varchar(20) NOT NULL UNIQUE,
    orden smallint
);

-- 21. Prenda / Producto matriz de la boutique
CREATE TABLE prenda (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    categoria_id uuid NOT NULL,
    temporada_id uuid,
    coleccion_id uuid,
    proveedor_id uuid,
    codigo varchar(50) NOT NULL,
    nombre varchar(160) NOT NULL,
    descripcion text,
    marca varchar(80),
    genero varchar(20) NOT NULL DEFAULT 'unisex'
        CHECK (genero IN ('mujer', 'hombre', 'nino', 'unisex')),
    precio_base numeric(12,2) NOT NULL DEFAULT 0 CHECK (precio_base >= 0),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    modelo_3d_url varchar(255),
    imagen_url varchar(255),
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'inactiva', 'descontinuada')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, codigo),
    FOREIGN KEY (empresa_id, categoria_id)
        REFERENCES categoria(empresa_id, id),
    FOREIGN KEY (empresa_id, temporada_id)
        REFERENCES temporada(empresa_id, id),
    FOREIGN KEY (empresa_id, coleccion_id)
        REFERENCES coleccion(empresa_id, id),
    FOREIGN KEY (empresa_id, proveedor_id)
        REFERENCES proveedor(empresa_id, id)
);

-- 22. Recursos multimedia asociados a la prenda (galería de fotos, video, modelos 3D)
CREATE TABLE prenda_recurso (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    prenda_id uuid NOT NULL,
    tipo varchar(20) NOT NULL
        CHECK (tipo IN ('imagen', 'modelo_3d', 'textura', 'video')),
    url varchar(255) NOT NULL,
    mime_type varchar(80),
    orden smallint NOT NULL DEFAULT 0,
    es_principal boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id) ON DELETE CASCADE
);

-- 23. Versión incremental del catálogo por Tenant para invalidación de caché offline (CU-13)
CREATE TABLE catalogo_version (
    empresa_id uuid PRIMARY KEY REFERENCES empresa(id) ON DELETE CASCADE,
    version bigint NOT NULL DEFAULT 1 CHECK (version > 0),
    actualizado_en timestamptz NOT NULL DEFAULT now()
);

-- 24. Variante específica de prenda según SKU, Color y Talla
CREATE TABLE variante (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    prenda_id uuid NOT NULL,
    color_id smallint NOT NULL REFERENCES color(id),
    talla_id smallint NOT NULL REFERENCES talla(id),
    sku varchar(60) NOT NULL,
    codigo_barras varchar(80),
    precio_venta numeric(12,2) NOT NULL CHECK (precio_venta >= 0),
    costo numeric(12,2) NOT NULL DEFAULT 0 CHECK (costo >= 0),
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'inactiva')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, sku),
    UNIQUE (empresa_id, prenda_id, color_id, talla_id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id) ON DELETE CASCADE
);

-- 25. Historial de variaciones de precio por variante o sucursal
CREATE TABLE precio_historial (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    variante_id uuid NOT NULL,
    sucursal_id uuid,
    precio_anterior numeric(12,2) NOT NULL CHECK (precio_anterior >= 0),
    precio_nuevo numeric(12,2) NOT NULL CHECK (precio_nuevo >= 0),
    motivo varchar(120),
    creado_por uuid NOT NULL,
    vigente_desde timestamptz NOT NULL DEFAULT now(),
    vigente_hasta timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, creado_por)
        REFERENCES usuario(empresa_id, id),
    CHECK (vigente_hasta IS NULL OR vigente_hasta > vigente_desde)
);


-- ============================================================================
-- MÓDULO 06: INVENTARIO, KÁRDEX Y TRANSFERENCIAS
-- ============================================================================

-- 26. Stock físico, reservado y disponible por sucursal y variante
CREATE TABLE inventario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    variante_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    stock_fisico integer NOT NULL DEFAULT 0 CHECK (stock_fisico >= 0),
    stock_reservado integer NOT NULL DEFAULT 0 CHECK (stock_reservado >= 0),
    stock_disponible integer GENERATED ALWAYS AS (stock_fisico - stock_reservado) STORED,
    stock_minimo integer NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),
    ubicacion varchar(60),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, variante_id, sucursal_id),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id) ON DELETE CASCADE,
    CHECK (stock_reservado <= stock_fisico)
);

-- 27. Kárdex inmutable de movimientos de stock (particionado por fecha)
CREATE TABLE movimiento_inventario (
    id bigserial,
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    variante_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN (
            'entrada', 'salida', 'ajuste', 'venta', 'devolucion',
            'transferencia_salida', 'transferencia_entrada', 'reserva_liberada'
        )),
    cantidad integer NOT NULL CHECK (cantidad <> 0),
    stock_anterior integer NOT NULL CHECK (stock_anterior >= 0),
    stock_nuevo integer NOT NULL CHECK (stock_nuevo >= 0),
    referencia_tipo varchar(40),
    referencia_id uuid,
    motivo varchar(200),
    usuario_id uuid,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, ocurrido_en),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    CHECK (stock_nuevo = stock_anterior + cantidad)
) PARTITION BY RANGE (ocurrido_en);

-- 28. Cabecera de transferencias de inventario entre sucursales
CREATE TABLE transferencia_inventario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    origen_id uuid NOT NULL,
    destino_id uuid NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'borrador'
        CHECK (estado IN ('borrador', 'solicitada', 'aprobada', 'en_transito', 'recibida', 'cancelada')),
    solicitada_por uuid NOT NULL,
    aprobada_por uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, origen_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, destino_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, solicitada_por)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, aprobada_por)
        REFERENCES usuario(empresa_id, id),
    CHECK (origen_id <> destino_id)
);

-- 29. Ítems y cantidades transferidas y recibidas
CREATE TABLE transferencia_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    transferencia_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    cantidad_recibida integer NOT NULL DEFAULT 0 CHECK (cantidad_recibida >= 0),
    UNIQUE (empresa_id, transferencia_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, transferencia_id)
        REFERENCES transferencia_inventario(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    CHECK (cantidad_recibida <= cantidad)
);


-- ============================================================================
-- MÓDULO 07: RESERVAS DE PROBADOR Y CARRITO
-- ============================================================================

-- 30. Reservas de prendas en probador o para recojo en tienda física
CREATE TABLE reserva (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    codigo varchar(20) NOT NULL,
    estado varchar(30) NOT NULL DEFAULT 'pendiente_preparacion'
        CHECK (estado IN (
            'pendiente_preparacion', 'preparada', 'incidencia_stock',
            'activa', 'confirmada', 'expirada', 'cancelada', 'convertida', 'completada'
        )),
    fecha_visita timestamptz NOT NULL,
    expira_en timestamptz NOT NULL,
    probador varchar(30),
    cliente_uuid uuid,
    dispositivo_id uuid,
    liberada_en timestamptz,
    motivo_cierre varchar(200),
    observacion text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    CHECK (expira_en > created_at)
);

-- 31. Variantes y prendas incluidas en una reserva
CREATE TABLE reserva_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    reserva_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    UNIQUE (empresa_id, reserva_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, reserva_id)
        REFERENCES reserva(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id)
);

-- 32. Historial de transiciones de estados de una reserva
CREATE TABLE reserva_estado_historial (
    id bigserial PRIMARY KEY,
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    reserva_id uuid NOT NULL,
    estado_anterior varchar(30),
    estado_nuevo varchar(30) NOT NULL,
    motivo varchar(200),
    usuario_id uuid,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (empresa_id, reserva_id)
        REFERENCES reserva(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
);

-- 33. Carrito de compras web o móvil
CREATE TABLE carrito (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid,
    sesion_anonima varchar(100),
    estado varchar(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'convertido', 'abandonado')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    CHECK (usuario_id IS NOT NULL OR sesion_anonima IS NOT NULL)
);

-- 34. Artículos en el carrito con precio congelado temporalmente
CREATE TABLE carrito_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    carrito_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    precio_unitario numeric(12,2) NOT NULL CHECK (precio_unitario >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, carrito_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, carrito_id)
        REFERENCES carrito(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id)
);


-- ============================================================================
-- MÓDULO 08: E-COMMERCE BASE (DIRECCIONES, CUPONES, DISPOSITIVOS)
-- ============================================================================

-- 35. Direcciones de entrega de los clientes
CREATE TABLE direccion_cliente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    etiqueta varchar(40),
    destinatario varchar(120) NOT NULL,
    telefono varchar(20) NOT NULL,
    linea1 varchar(200) NOT NULL,
    linea2 varchar(200),
    ciudad_id smallint NOT NULL REFERENCES ciudad(id),
    codigo_postal varchar(20),
    referencia text,
    es_principal boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id) ON DELETE CASCADE
);

-- 36. Cupones promocionales de descuento
CREATE TABLE cupon (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    codigo varchar(40) NOT NULL,
    descripcion text,
    tipo varchar(20) NOT NULL
        CHECK (tipo IN ('porcentaje', 'monto_fijo', 'envio_gratis')),
    valor numeric(12,2) NOT NULL CHECK (valor >= 0),
    monto_minimo numeric(12,2) NOT NULL DEFAULT 0 CHECK (monto_minimo >= 0),
    usos_maximos integer CHECK (usos_maximos IS NULL OR usos_maximos > 0),
    usos_por_usuario integer CHECK (usos_por_usuario IS NULL OR usos_por_usuario > 0),
    fecha_inicio timestamptz NOT NULL,
    fecha_fin timestamptz NOT NULL,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, codigo),
    UNIQUE (empresa_id, id),
    CHECK (fecha_fin > fecha_inicio),
    CHECK (tipo <> 'porcentaje' OR valor <= 100)
);

-- 37. Dispositivos POS físicos autorizados para operar online/offline
CREATE TABLE dispositivo (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    sucursal_id uuid NOT NULL,
    nombre varchar(100) NOT NULL,
    serial varchar(100) NOT NULL,
    clave_publica text,
    ultima_sync timestamptz,
    catalogo_version bigint NOT NULL DEFAULT 0 CHECK (catalogo_version >= 0),
    estado varchar(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'revocado')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, serial),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id)
);

-- Vinculación de FK para dispositivo en tabla reserva (declarada previamente)
ALTER TABLE reserva DROP CONSTRAINT IF EXISTS fk_reserva_dispositivo;
ALTER TABLE reserva
    ADD CONSTRAINT fk_reserva_dispositivo
    FOREIGN KEY (empresa_id, dispositivo_id)
    REFERENCES dispositivo(empresa_id, id);


-- ============================================================================
-- MÓDULO 09: VENTAS, FACTURACIÓN, PAGOS Y CAMBIOS
-- ============================================================================

-- 38. Transacciones de venta (POS, WEB y OFFLINE sincronizadas)
CREATE TABLE venta (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    numero varchar(30) NOT NULL,
    sucursal_id uuid,
    usuario_id uuid,
    cajero_id uuid,
    cliente_nombre varchar(120),
    cliente_documento varchar(30),
    canal varchar(20) NOT NULL
        CHECK (canal IN ('POS', 'WEB', 'OFFLINE')),
    fecha_hora timestamptz NOT NULL DEFAULT now(),
    fecha_hora_cliente timestamptz,
    fecha_recepcion_servidor timestamptz NOT NULL DEFAULT now(),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    subtotal numeric(12,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    descuento numeric(12,2) NOT NULL DEFAULT 0 CHECK (descuento >= 0),
    impuesto numeric(12,2) NOT NULL DEFAULT 0 CHECK (impuesto >= 0),
    total numeric(12,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    estado varchar(30) NOT NULL DEFAULT 'pendiente_pago'
        CHECK (estado IN (
            'pendiente_pago', 'pagada', 'preparando', 'enviada', 'entregada',
            'completada', 'anulada', 'devuelta', 'pendiente_sync', 'pago_fallido'
        )),
    direccion_id uuid,
    cupon_id uuid,
    idempotency_key varchar(100) NOT NULL,
    firma_qr varchar(255),
    qr_nonce varchar(100),
    firma_algoritmo varchar(20)
        CHECK (firma_algoritmo IS NULL OR firma_algoritmo IN ('HMAC-SHA256', 'Ed25519')),
    firma_version smallint NOT NULL DEFAULT 1,
    firmado_en timestamptz,
    dispositivo_id uuid,
    notas text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, numero),
    UNIQUE (empresa_id, idempotency_key),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, cajero_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, direccion_id)
        REFERENCES direccion_cliente(empresa_id, id),
    FOREIGN KEY (empresa_id, cupon_id)
        REFERENCES cupon(empresa_id, id),
    FOREIGN KEY (empresa_id, dispositivo_id)
        REFERENCES dispositivo(empresa_id, id),
    CHECK (total = subtotal - descuento + impuesto),
    CHECK (descuento <= subtotal),
    CHECK (canal <> 'POS' OR sucursal_id IS NOT NULL),
    CHECK (canal <> 'POS' OR cajero_id IS NOT NULL)
);

-- 39. Líneas de detalle de la venta (artículos, cantidades y descuentos)
CREATE TABLE venta_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    precio_lista numeric(12,2) NOT NULL CHECK (precio_lista >= 0),
    precio_unitario numeric(12,2) NOT NULL CHECK (precio_unitario >= 0),
    descuento_linea numeric(12,2) NOT NULL DEFAULT 0 CHECK (descuento_linea >= 0),
    subtotal numeric(12,2) NOT NULL CHECK (subtotal >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, venta_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    CHECK (subtotal = (cantidad * precio_unitario) - descuento_linea)
);

-- 40. Registro de pagos realizados sobre una venta
CREATE TABLE pago (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    monto numeric(12,2) NOT NULL CHECK (monto > 0),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    metodo varchar(30) NOT NULL
        CHECK (metodo IN ('efectivo', 'tarjeta', 'qr', 'pasarela', 'transferencia', 'vale')),
    pasarela_id varchar(100),
    idempotency_key varchar(100) NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'completado'
        CHECK (estado IN ('pendiente', 'completado', 'fallido', 'reembolsado')),
    referencia varchar(100),
    pagado_en timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, idempotency_key),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE
);

-- 41. Solicitudes de cambio de prendas post-venta
CREATE TABLE cambio_prenda (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    motivo varchar(200) NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'solicitado'
        CHECK (estado IN ('solicitado', 'aprobado', 'rechazado', 'completado', 'cancelado')),
    diferencia numeric(12,2) NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
);

-- 42. Detalle de variantes devueltas y recibidas en un cambio
CREATE TABLE cambio_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    cambio_id uuid NOT NULL,
    venta_detalle_id uuid NOT NULL,
    variante_nueva_id uuid,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    diferencia_precio numeric(12,2) NOT NULL DEFAULT 0,
    UNIQUE (empresa_id, cambio_id, venta_detalle_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, cambio_id)
        REFERENCES cambio_prenda(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, venta_detalle_id)
        REFERENCES venta_detalle(empresa_id, id),
    FOREIGN KEY (empresa_id, variante_nueva_id)
        REFERENCES variante(empresa_id, id)
);

-- 43. Histórico de estados de la venta (trazabilidad de orden)
CREATE TABLE venta_estado_historial (
    id bigserial PRIMARY KEY,
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    estado_anterior varchar(30),
    estado_nuevo varchar(30) NOT NULL,
    motivo varchar(200),
    usuario_id uuid,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
);


-- ============================================================================
-- MÓDULO 10: CONTINGENCIA OFFLINE Y RESOLUCIÓN DE CONFLICTOS
-- ============================================================================

-- 44. Cola de operaciones generadas offline por los dispositivos POS
CREATE TABLE operacion_pendiente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    dispositivo_id uuid,
    sucursal_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    venta_id uuid,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN ('venta_offline', 'pago_offline', 'devolucion_offline', 'reserva_offline', 'cambio_offline', 'ajuste_stock')),
    payload jsonb NOT NULL,
    firma varchar(255),
    nonce varchar(100),
    idempotency_key varchar(100) NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'procesando', 'aplicada', 'rechazada', 'conflicto', 'resuelta')),
    intentos integer NOT NULL DEFAULT 0 CHECK (intentos >= 0),
    ultimo_error text,
    creada_en timestamptz NOT NULL DEFAULT now(),
    procesada_en timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, idempotency_key),
    FOREIGN KEY (empresa_id, dispositivo_id)
        REFERENCES dispositivo(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id)
);

-- 45. Registro de discrepancias y resolución manual o automática de conflictos
CREATE TABLE resolucion_conflicto (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    operacion_id uuid NOT NULL,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN ('stock_insuficiente', 'precio_cambiado', 'duplicado', 'otro')),
    decision varchar(30) NOT NULL
        CHECK (decision IN ('rechazar', 'ajustar', 'aceptar', 'revision')),
    detalle jsonb,
    resuelto_por uuid NOT NULL,
    resuelto_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, operacion_id)
        REFERENCES operacion_pendiente(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, resuelto_por)
        REFERENCES usuario(empresa_id, id)
);


-- ============================================================================
-- MÓDULO 11: ENVÍOS Y DERIVADOS DE E-COMMERCE
-- ============================================================================

-- 46. Gestión de despachos y logística de envíos a domicilio o recojo
CREATE TABLE envio (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    direccion_id uuid,
    tipo varchar(20) NOT NULL DEFAULT 'envio'
        CHECK (tipo IN ('envio', 'recojo')),
    transportista varchar(100),
    tracking varchar(100),
    costo numeric(12,2) NOT NULL DEFAULT 0 CHECK (costo >= 0),
    estado varchar(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'preparando', 'enviado', 'en_transito', 'entregado', 'devuelto', 'cancelado')),
    sucursal_recojo_id uuid,
    fecha_estimada date,
    enviado_en timestamptz,
    entregado_en timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, venta_id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, direccion_id)
        REFERENCES direccion_cliente(empresa_id, id),
    CHECK (entregado_en IS NULL OR enviado_en IS NULL OR entregado_en >= enviado_en)
);

-- 47. Trazabilidad de cupones canjeados por usuario y compra
CREATE TABLE cupon_uso (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    cupon_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    venta_id uuid NOT NULL,
    descuento_aplicado numeric(12,2) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, cupon_id, usuario_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, cupon_id)
        REFERENCES cupon(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id)
);


-- ============================================================================
-- MÓDULO 12: MACHINE LEARNING, IA Y ANALÍTICA
-- ============================================================================

-- 48. Metadatos y versiones de modelos de Machine Learning entrenados
CREATE TABLE modelo_ml (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(100) NOT NULL,
    version varchar(30) NOT NULL,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN ('demanda', 'segmentacion', 'recomendacion')),
    metricas jsonb,
    activo boolean NOT NULL DEFAULT true,
    entrenado_en timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, nombre, version)
);

-- 49. Predicciones estadísticas de demanda futura por categoría de prenda
CREATE TABLE prediccion_demanda (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    modelo_ml_id uuid NOT NULL REFERENCES modelo_ml(id),
    categoria_id uuid NOT NULL,
    periodo date NOT NULL,
    demanda_estimada numeric(12,2) NOT NULL CHECK (demanda_estimada >= 0),
    intervalo_inferior numeric(12,2),
    intervalo_superior numeric(12,2),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, modelo_ml_id, categoria_id, periodo),
    FOREIGN KEY (empresa_id, categoria_id)
        REFERENCES categoria(empresa_id, id),
    CHECK (periodo = date_trunc('month', periodo)::date),
    CHECK (intervalo_superior IS NULL OR intervalo_inferior IS NULL OR intervalo_superior >= intervalo_inferior)
);

-- 50. Segmentación analítica de clientes (VIP, frecuente, nuevo, inactivo)
CREATE TABLE segmento_cliente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    modelo_ml_id uuid NOT NULL REFERENCES modelo_ml(id),
    usuario_id uuid NOT NULL,
    etiqueta varchar(50) NOT NULL,
    score numeric(5,4) CHECK (score IS NULL OR (score >= 0 AND score <= 1)),
    vigente_desde timestamptz NOT NULL DEFAULT now(),
    vigente_hasta timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, modelo_ml_id, usuario_id, vigente_desde),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    CHECK (vigente_hasta IS NULL OR vigente_hasta > vigente_desde)
);

-- 51. Registro de prompts, consultas en lenguaje natural y síntesis de voz LLM
CREATE TABLE consulta_ia_log (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    prompt text NOT NULL,
    respuesta text,
    modelo_llm varchar(80),
    canal varchar(20) NOT NULL DEFAULT 'texto'
        CHECK (canal IN ('texto', 'voz')),
    reporte_tipo varchar(100) NOT NULL,
    parametros_json jsonb NOT NULL,
    tokens_entrada integer CHECK (tokens_entrada IS NULL OR tokens_entrada >= 0),
    tokens_salida integer CHECK (tokens_salida IS NULL OR tokens_salida >= 0),
    costo numeric(12,6) CHECK (costo IS NULL OR costo >= 0),
    latencia_ms integer CHECK (latencia_ms IS NULL OR latencia_ms >= 0),
    estado varchar(20) NOT NULL DEFAULT 'exitoso'
        CHECK (estado IN ('exitoso', 'fallido', 'rechazado')),
    cache_key varchar(100),
    audio_url varchar(255),
    audio_mime varchar(40),
    tts_modelo varchar(80),
    tts_voz varchar(80),
    duracion_audio_ms integer CHECK (duracion_audio_ms IS NULL OR duracion_audio_ms >= 0),
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, ocurrido_en),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
) PARTITION BY RANGE (ocurrido_en);

-- 52. Reportes PDF/Excel/CSV generados bajo demanda o por el asistente IA
CREATE TABLE reporte_exportado (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    consulta_ia_log_id uuid,
    consulta_ocurrido_en timestamptz,
    tipo_reporte varchar(100) NOT NULL,
    formato varchar(10) NOT NULL
        CHECK (formato IN ('pdf', 'xlsx', 'csv')),
    archivo_url varchar(255) NOT NULL,
    tamano_bytes bigint CHECK (tamano_bytes IS NULL OR tamano_bytes >= 0),
    estado varchar(20) NOT NULL DEFAULT 'generado'
        CHECK (estado IN ('generado', 'fallido', 'eliminado')),
    generado_en timestamptz NOT NULL DEFAULT now(),
    expira_en timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (consulta_ia_log_id, consulta_ocurrido_en)
        REFERENCES consulta_ia_log(id, ocurrido_en) ON DELETE SET NULL,
    CHECK (expira_en IS NULL OR expira_en > generado_en)
);


-- ============================================================================
-- MÓDULO 13: REALIDAD AUMENTADA (AR) Y VESTIDOR VIRTUAL
-- ============================================================================

-- 53. Perfil de avatar 3D del cliente
CREATE TABLE avatar_cliente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    nombre varchar(80) NOT NULL DEFAULT 'Mi avatar',
    modelo_url varchar(255),
    altura_cm numeric(5,2) CHECK (altura_cm IS NULL OR altura_cm > 0),
    peso_kg numeric(5,2) CHECK (peso_kg IS NULL OR peso_kg > 0),
    tono_piel varchar(30),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id) ON DELETE CASCADE
);

-- 54. Medidas antropométricas del avatar para entalle virtual preciso
CREATE TABLE medida_corporal (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    avatar_id uuid NOT NULL,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN (
            'busto', 'cintura', 'cadera', 'hombro', 'cuello',
            'largo_manga', 'largo_pierna', 'muslo', 'rodilla'
        )),
    valor_cm numeric(6,2) NOT NULL CHECK (valor_cm > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, avatar_id, tipo),
    FOREIGN KEY (empresa_id, avatar_id)
        REFERENCES avatar_cliente(empresa_id, id) ON DELETE CASCADE
);

-- 55. Mapeo del modelo 3D GLB y texturas de prendas para Realidad Aumentada
CREATE TABLE prenda_ar (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    prenda_id uuid NOT NULL,
    variante_id uuid,
    modelo_url varchar(255) NOT NULL,
    textura_url varchar(255),
    puntos_ajuste jsonb,
    talla_referencia varchar(10),
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id) ON DELETE CASCADE
);

-- 56. Sesión interactiva de probador virtual en tiempo real (WebGL / WebXR)
CREATE TABLE sesion_prueba_virtual (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    avatar_id uuid NOT NULL,
    prenda_id uuid NOT NULL,
    variante_id uuid,
    estado varchar(20) NOT NULL DEFAULT 'iniciada'
        CHECK (estado IN ('iniciada', 'completada', 'abandonada', 'fallida')),
    resultado_url varchar(255),
    iniciada_en timestamptz NOT NULL DEFAULT now(),
    finalizada_en timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, avatar_id)
        REFERENCES avatar_cliente(empresa_id, id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    CHECK (finalizada_en IS NULL OR finalizada_en >= iniciada_en)
);


-- ============================================================================
-- MÓDULO 14: PASARELA DE PAGOS Y WEBHOOKS
-- ============================================================================

-- 57. Registro y deduplicación de eventos Webhook de Stripe (CU-24)
CREATE TABLE stripe_evento (
    id varchar(100) PRIMARY KEY,
    tipo varchar(60) NOT NULL,
    procesado_en timestamptz NOT NULL DEFAULT now()
);


-- ============================================================================
-- MÓDULO 15: SOFT-LOCKS, DEVOLUCIONES QR Y REPLICACIÓN
-- ============================================================================

-- 58. Bloqueo temporal optimista de stock con TTL de 45 min para probadores (CU-27)
CREATE TABLE soft_lock (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    sucursal_id uuid NOT NULL REFERENCES sucursal(id) ON DELETE CASCADE,
    variante_id uuid NOT NULL REFERENCES variante(id) ON DELETE CASCADE,
    dispositivo_id varchar(100) NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    expira_en timestamptz NOT NULL,
    creado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id)
);

-- 59. Notas de cambio y sustitución de prendas validadas mediante QR (CU-29)
CREATE TABLE nota_cambio (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    sucursal_id uuid NOT NULL REFERENCES sucursal(id) ON DELETE CASCADE,
    venta_origen_id uuid REFERENCES venta(id),
    variante_devuelta_id uuid NOT NULL REFERENCES variante(id),
    variante_nueva_id uuid NOT NULL REFERENCES variante(id),
    cantidad integer NOT NULL DEFAULT 1,
    diferencia_monto numeric(10, 2) NOT NULL DEFAULT 0,
    motivo text,
    cajero_id uuid NOT NULL REFERENCES usuario(id),
    qr_firma varchar(255),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id)
);

-- 60. Control de idempotencia de lotes sincronizados desde dispositivos remotos (CU-31 / RNF05)
CREATE TABLE sync_registro_idempotencia (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    idempotency_key varchar(100) NOT NULL,
    tipo_operacion varchar(40) NOT NULL,
    resultado_json jsonb NOT NULL,
    procesado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, idempotency_key)
);


-- ============================================================================
-- MÓDULO 16: BACKUPS Y RESTAURACIÓN
-- ============================================================================

-- 61. Registro y auditoría de copias de seguridad generadas (Manual / Automático)
CREATE TABLE backup_registro (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid REFERENCES usuario(id) ON DELETE SET NULL,
    nombre varchar(150) NOT NULL,
    descripcion text,
    tipo varchar(20) NOT NULL CHECK (tipo IN ('manual', 'automatico')),
    alcance varchar(20) NOT NULL CHECK (alcance IN ('global', 'empresa')),
    formato varchar(10) NOT NULL DEFAULT 'json' CHECK (formato IN ('json', 'sql')),
    tablas_seleccionadas jsonb NOT NULL DEFAULT '[]'::jsonb,
    tamano_bytes bigint NOT NULL DEFAULT 0,
    tamano_legible varchar(30) NOT NULL DEFAULT '0 KB',
    total_registros integer NOT NULL DEFAULT 0,
    checksum_sha256 varchar(64),
    guardado_local boolean NOT NULL DEFAULT true,
    ruta_local text,
    guardado_nube boolean NOT NULL DEFAULT true,
    url_nube text,
    proveedor_nube varchar(60) NOT NULL DEFAULT 'AWS S3 (sa-east-1)',
    estado varchar(20) NOT NULL DEFAULT 'completado' CHECK (estado IN ('completado', 'fallido', 'en_progreso')),
    error_mensaje text,
    detalles_tablas jsonb DEFAULT '{}'::jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 62. Programación recurrente y configuración de políticas de backup automático
CREATE TABLE backup_configuracion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid UNIQUE REFERENCES empresa(id) ON DELETE CASCADE,
    activo boolean NOT NULL DEFAULT false,
    frecuencia varchar(30) NOT NULL DEFAULT 'diario'
        CHECK (frecuencia IN ('cada_hora', 'cada_2_horas', 'cada_4_horas', 'cada_6_horas', 'cada_12_horas', 'diario', 'semanal', 'mensual', 'fecha_especifica')),
    fecha_inicio date,
    fecha_especifica date,
    hora_ejecucion varchar(10) NOT NULL DEFAULT '02:00',
    dia_semana integer NOT NULL DEFAULT 0 CHECK (dia_semana BETWEEN 0 AND 6),
    dia_mes integer DEFAULT 1 CHECK (dia_mes BETWEEN 1 AND 31),
    destino varchar(20) NOT NULL DEFAULT 'ambos' CHECK (destino IN ('local', 'nube', 'ambos')),
    formato varchar(10) NOT NULL DEFAULT 'json' CHECK (formato IN ('json', 'sql')),
    tablas jsonb NOT NULL DEFAULT '["catalogo", "inventario", "ventas", "reservas", "clientes"]'::jsonb,
    retencion_dias integer NOT NULL DEFAULT 30,
    ultima_ejecucion timestamptz,
    proxima_ejecucion timestamptz,
    estado_ultima_ejecucion varchar(20),
    error_ultima_ejecucion text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- FIN DEL SCRIPT GUÍA CONSOLIDADO (62 TABLAS DEL SISTEMA)
-- ============================================================================
