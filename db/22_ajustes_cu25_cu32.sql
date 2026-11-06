-- Migración cu25_cu32_ajustes: Operaciones Offline, Soft-Lock y Sincronización Idempotente

-- 1. Ampliar CHECK de operacion_pendiente.tipo y operacion_pendiente.estado
ALTER TABLE operacion_pendiente DROP CONSTRAINT IF EXISTS operacion_pendiente_tipo_check;
ALTER TABLE operacion_pendiente ADD CONSTRAINT operacion_pendiente_tipo_check
    CHECK (tipo IN ('venta_offline', 'pago_offline', 'devolucion_offline', 'reserva_offline', 'cambio_offline', 'ajuste_stock'));

ALTER TABLE operacion_pendiente DROP CONSTRAINT IF EXISTS operacion_pendiente_estado_check;
ALTER TABLE operacion_pendiente ADD CONSTRAINT operacion_pendiente_estado_check
    CHECK (estado IN ('pendiente', 'procesando', 'aplicada', 'rechazada', 'conflicto', 'resuelta'));

-- Permitir que dispositivo_id sea nullable o tenga default si no se registra previamente en tabla dispositivo
ALTER TABLE operacion_pendiente DROP CONSTRAINT IF EXISTS operacion_pendiente_empresa_id_dispositivo_id_fkey;
ALTER TABLE operacion_pendiente ALTER COLUMN dispositivo_id DROP NOT NULL;
ALTER TABLE operacion_pendiente ALTER COLUMN nonce DROP NOT NULL;

-- 2. Tabla de Soft-Lock temporal con TTL de 45 minutos (CU-27)
CREATE TABLE IF NOT EXISTS soft_lock (
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

CREATE INDEX IF NOT EXISTS idx_soft_lock_busqueda ON soft_lock (empresa_id, sucursal_id, variante_id, expira_en);

-- 3. Tabla de Nota de Cambio para Devolución/Sustitución por QR (CU-29)
CREATE TABLE IF NOT EXISTS nota_cambio (
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

-- 4. Registro de Idempotencia para Lotes de Sincronización (CU-31 / RNF05)
CREATE TABLE IF NOT EXISTS sync_registro_idempotencia (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    idempotency_key varchar(100) NOT NULL,
    tipo_operacion varchar(40) NOT NULL,
    resultado_json jsonb NOT NULL,
    procesado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, idempotency_key)
);

