ALTER TABLE empresa
    ADD COLUMN IF NOT EXISTS direccion varchar(200);

ALTER TABLE empresa
    DROP CONSTRAINT IF EXISTS empresa_estado_check;

ALTER TABLE empresa
    ADD CONSTRAINT empresa_estado_check
    CHECK (estado IN ('pendiente_plan', 'activa', 'suspendida', 'cancelada'));

CREATE INDEX IF NOT EXISTS ix_empresa_saas_estado
    ON empresa (estado, created_at DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_suscripcion_empresa_fecha
    ON suscripcion (empresa_id, fecha_inicio DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_suscripcion_vencimiento
    ON suscripcion (fecha_fin)
    WHERE estado IN ('prueba', 'activa', 'mora');

CREATE INDEX IF NOT EXISTS ix_venta_empresa_fecha_completada
    ON venta (empresa_id, fecha_hora DESC)
    WHERE estado = 'completada' AND deleted_at IS NULL;
