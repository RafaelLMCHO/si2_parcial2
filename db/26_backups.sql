-- 26_backups.sql: Tablas y RLS para el subsistema de Backups (Personalizado, Automático y Manual)
CREATE TABLE IF NOT EXISTS backup_registro (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuario(id) ON DELETE SET NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('manual', 'automatico')),
    alcance VARCHAR(20) NOT NULL CHECK (alcance IN ('global', 'empresa')),
    formato VARCHAR(10) NOT NULL DEFAULT 'json' CHECK (formato IN ('json', 'sql')),
    tablas_seleccionadas JSONB NOT NULL DEFAULT '[]'::jsonb,
    tamano_bytes BIGINT NOT NULL DEFAULT 0,
    tamano_legible VARCHAR(30) NOT NULL DEFAULT '0 KB',
    total_registros INT NOT NULL DEFAULT 0,
    checksum_sha256 VARCHAR(64),
    guardado_local BOOLEAN NOT NULL DEFAULT true,
    ruta_local TEXT,
    guardado_nube BOOLEAN NOT NULL DEFAULT true,
    url_nube TEXT,
    proveedor_nube VARCHAR(60) NOT NULL DEFAULT 'AWS S3 (sa-east-1)',
    estado VARCHAR(20) NOT NULL DEFAULT 'completado' CHECK (estado IN ('completado', 'fallido', 'en_progreso')),
    error_mensaje TEXT,
    detalles_tablas JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS backup_configuracion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID UNIQUE REFERENCES empresa(id) ON DELETE CASCADE,
    activo BOOLEAN NOT NULL DEFAULT false,
    frecuencia VARCHAR(30) NOT NULL DEFAULT 'diario' CHECK (frecuencia IN ('cada_hora', 'cada_2_horas', 'cada_4_horas', 'cada_6_horas', 'cada_12_horas', 'diario', 'semanal', 'mensual', 'fecha_especifica')),
    fecha_inicio DATE,
    fecha_especifica DATE,
    hora_ejecucion VARCHAR(10) NOT NULL DEFAULT '02:00',
    dia_semana INT NOT NULL DEFAULT 0 CHECK (dia_semana BETWEEN 0 AND 6),
    dia_mes INT DEFAULT 1 CHECK (dia_mes BETWEEN 1 AND 31),
    destino VARCHAR(20) NOT NULL DEFAULT 'ambos' CHECK (destino IN ('local', 'nube', 'ambos')),
    formato VARCHAR(10) NOT NULL DEFAULT 'json' CHECK (formato IN ('json', 'sql')),
    tablas JSONB NOT NULL DEFAULT '["catalogo", "inventario", "ventas", "reservas", "clientes"]'::jsonb,
    retencion_dias INT NOT NULL DEFAULT 30,
    ultima_ejecucion TIMESTAMPTZ,
    proxima_ejecucion TIMESTAMPTZ,
    estado_ultima_ejecucion VARCHAR(20),
    error_ultima_ejecucion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_backup_config_global ON backup_configuracion ((1)) WHERE empresa_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_backup_reg_empresa ON backup_registro(empresa_id);
CREATE INDEX IF NOT EXISTS idx_backup_reg_created ON backup_registro(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backup_reg_tipo ON backup_registro(tipo);

GRANT SELECT, INSERT, UPDATE, DELETE ON backup_registro, backup_configuracion TO fashion_app, fashion_superadmin;

ALTER TABLE backup_registro ENABLE ROW LEVEL SECURITY;
ALTER TABLE backup_registro FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS p_backup_registro_select ON backup_registro;
CREATE POLICY p_backup_registro_select ON backup_registro
    FOR SELECT
    USING (
        empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid
    );

DROP POLICY IF EXISTS p_backup_registro_insert ON backup_registro;
CREATE POLICY p_backup_registro_insert ON backup_registro
    FOR INSERT
    WITH CHECK (
        empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid
    );

DROP POLICY IF EXISTS p_backup_registro_mod ON backup_registro;
CREATE POLICY p_backup_registro_mod ON backup_registro
    FOR UPDATE
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid)
    WITH CHECK (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

DROP POLICY IF EXISTS p_backup_registro_del ON backup_registro;
CREATE POLICY p_backup_registro_del ON backup_registro
    FOR DELETE
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

ALTER TABLE backup_configuracion ENABLE ROW LEVEL SECURITY;
ALTER TABLE backup_configuracion FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS p_backup_config_select ON backup_configuracion;
CREATE POLICY p_backup_config_select ON backup_configuracion
    FOR SELECT
    USING (
        empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid
    );

DROP POLICY IF EXISTS p_backup_config_all ON backup_configuracion;
CREATE POLICY p_backup_config_all ON backup_configuracion
    FOR ALL
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid)
    WITH CHECK (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

