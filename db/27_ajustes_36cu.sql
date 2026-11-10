-- 27_ajustes_36cu.sql: Ajustes finales para completar los 36 Casos de Uso (CU-01 a CU-36)

-- 0. Agregar columna periodo en plan para CRUD CU-06
ALTER TABLE plan
    ADD COLUMN IF NOT EXISTS periodo varchar(20) NOT NULL DEFAULT 'mensual'
    CHECK (periodo IN ('mensual', 'anual'));

-- 1. Ampliar CHECK de reserva.estado para soportar estado 'completada' (CU-21)
ALTER TABLE reserva DROP CONSTRAINT IF EXISTS reserva_estado_check;
ALTER TABLE reserva ADD CONSTRAINT reserva_estado_check
    CHECK (estado IN (
        'pendiente_preparacion',
        'preparada',
        'incidencia_stock',
        'activa',
        'confirmada',
        'expirada',
        'cancelada',
        'convertida',
        'completada'
    ));

-- 2. Índices de bitacora_auditoria para consultas paginadas y filtradas (CU-05)
CREATE INDEX IF NOT EXISTS ix_bitacora_auditoria_empresa_fecha
    ON bitacora_auditoria (empresa_id, ocurrido_en DESC);
CREATE INDEX IF NOT EXISTS ix_bitacora_auditoria_accion_fecha
    ON bitacora_auditoria (accion, ocurrido_en DESC);

-- 3. Permisos y RLS para tablas creadas en 22_ajustes_cu25_cu32.sql despues de 14_rls.sql
GRANT SELECT, INSERT, UPDATE, DELETE
   ON soft_lock, nota_cambio, sync_registro_idempotencia
   TO fashion_app, fashion_superadmin;

DO $$
DECLARE
    t text;
    v_pred text := 'empresa_id = NULLIF(current_setting(''app.empresa_id'', true), '''')::uuid';
BEGIN
    FOREACH t IN ARRAY ARRAY['soft_lock', 'nota_cambio', 'sync_registro_idempotencia']
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', 'p_' || t || '_tenant', t);
        EXECUTE format(
            'CREATE POLICY %I ON %I FOR ALL USING (%s) WITH CHECK (%s)',
            'p_' || t || '_tenant',
            t,
            v_pred,
            v_pred
        );
    END LOOP;
END $$;
