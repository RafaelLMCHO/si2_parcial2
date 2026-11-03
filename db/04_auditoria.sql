CREATE TABLE bitacora_auditoria (
    id bigserial,
    empresa_id uuid REFERENCES empresa(id) ON DELETE SET NULL,
    empresa_afectada_id uuid REFERENCES empresa(id) ON DELETE SET NULL,
    usuario_id uuid REFERENCES usuario(id) ON DELETE SET NULL,
    actor_tipo varchar(20) NOT NULL DEFAULT 'usuario'
        CHECK (actor_tipo IN ('usuario', 'sistema', 'superadmin')),
    accion varchar(20) NOT NULL
        CHECK (accion IN ('insert', 'update', 'delete', 'login', 'logout', 'export')),
    entidad varchar(60) NOT NULL,
    entidad_id uuid,
    datos_antes jsonb,
    datos_despues jsonb,
    ip inet,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, ocurrido_en)
) PARTITION BY RANGE (ocurrido_en);

DO $$
DECLARE
    d date := DATE '2026-01-01';
BEGIN
    WHILE d < DATE '2028-01-01' LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF bitacora_auditoria FOR VALUES FROM (%L) TO (%L)',
            'bitacora_auditoria_' || to_char(d, 'YYYY_MM'),
            d,
            d + interval '1 month'
        );
        d := d + interval '1 month';
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS bitacora_auditoria_default
    PARTITION OF bitacora_auditoria DEFAULT;
