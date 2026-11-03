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

DO $$
DECLARE
    d date := DATE '2026-01-01';
BEGIN
    WHILE d < DATE '2028-01-01' LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF consulta_ia_log FOR VALUES FROM (%L) TO (%L)',
            'consulta_ia_log_' || to_char(d, 'YYYY_MM'),
            d,
            d + interval '1 month'
        );
        d := d + interval '1 month';
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS consulta_ia_log_default
    PARTITION OF consulta_ia_log DEFAULT;

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
