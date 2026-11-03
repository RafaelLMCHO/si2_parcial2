DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fashion_app') THEN
        EXECUTE 'CREATE ROLE fashion_app NOLOGIN';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fashion_superadmin') THEN
        EXECUTE 'CREATE ROLE fashion_superadmin NOLOGIN BYPASSRLS';
    END IF;
END $$;

ALTER ROLE fashion_app NOBYPASSRLS;
ALTER ROLE fashion_superadmin BYPASSRLS;

GRANT USAGE ON SCHEMA public TO fashion_app, fashion_superadmin;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fashion_app, fashion_superadmin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fashion_app, fashion_superadmin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fashion_app, fashion_superadmin;

REVOKE INSERT, UPDATE, DELETE ON plan, plan_limite, permiso, ciudad, color, talla FROM fashion_app;
REVOKE INSERT, UPDATE, DELETE ON bitacora_auditoria FROM fashion_app;

DO $$
DECLARE
    r record;
BEGIN
    FOR r IN
        SELECT child.relname
          FROM pg_inherits i
          JOIN pg_class parent ON parent.oid = i.inhparent
          JOIN pg_class child ON child.oid = i.inhrelid
          JOIN pg_namespace n ON n.oid = parent.relnamespace
         WHERE n.nspname = 'public'
           AND parent.relname IN (
               'bitacora_auditoria',
               'movimiento_inventario',
               'consulta_ia_log'
           )
    LOOP
        EXECUTE format('REVOKE ALL ON TABLE %I FROM fashion_app', r.relname);
    END LOOP;
END $$;

ALTER TABLE empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresa FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_empresa_select ON empresa;
CREATE POLICY p_empresa_select ON empresa
    FOR SELECT
    USING (id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);
DROP POLICY IF EXISTS p_empresa_update ON empresa;
CREATE POLICY p_empresa_update ON empresa
    FOR UPDATE
    USING (id = NULLIF(current_setting('app.empresa_id', true), '')::uuid)
    WITH CHECK (id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

ALTER TABLE rol ENABLE ROW LEVEL SECURITY;
ALTER TABLE rol FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_rol_select ON rol;
CREATE POLICY p_rol_select ON rol
    FOR SELECT
    USING (
        empresa_id IS NULL
        OR empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid
    );
DROP POLICY IF EXISTS p_rol_mod ON rol;
CREATE POLICY p_rol_mod ON rol
    FOR ALL
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid)
    WITH CHECK (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

ALTER TABLE usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_usuario_tenant ON usuario;
CREATE POLICY p_usuario_tenant ON usuario
    FOR ALL
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid)
    WITH CHECK (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

ALTER TABLE sesion ENABLE ROW LEVEL SECURITY;
ALTER TABLE sesion FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_sesion_tenant ON sesion;
CREATE POLICY p_sesion_tenant ON sesion
    FOR ALL
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid)
    WITH CHECK (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

ALTER TABLE bitacora_auditoria ENABLE ROW LEVEL SECURITY;
ALTER TABLE bitacora_auditoria FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_bitacora_select ON bitacora_auditoria;
CREATE POLICY p_bitacora_select ON bitacora_auditoria
    FOR SELECT
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

ALTER TABLE modelo_ml ENABLE ROW LEVEL SECURITY;
ALTER TABLE modelo_ml FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_modelo_ml_select ON modelo_ml;
CREATE POLICY p_modelo_ml_select ON modelo_ml
    FOR SELECT
    USING (
        empresa_id IS NULL
        OR empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid
    );
DROP POLICY IF EXISTS p_modelo_ml_mod ON modelo_ml;
CREATE POLICY p_modelo_ml_mod ON modelo_ml
    FOR ALL
    USING (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid)
    WITH CHECK (empresa_id = NULLIF(current_setting('app.empresa_id', true), '')::uuid);

DO $$
DECLARE
    t text;
    v_pred text := 'empresa_id = NULLIF(current_setting(''app.empresa_id'', true), '''')::uuid';
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'suscripcion',
        'pago_suscripcion',
        'verificacion_correo',
        'sucursal',
        'categoria',
        'temporada',
        'coleccion',
        'proveedor',
        'prenda',
        'prenda_recurso',
        'catalogo_version',
        'variante',
        'precio_historial',
        'inventario',
        'movimiento_inventario',
        'transferencia_inventario',
        'transferencia_detalle',
        'reserva',
        'reserva_detalle',
        'reserva_estado_historial',
        'carrito',
        'carrito_detalle',
        'venta',
        'venta_detalle',
        'pago',
        'cambio_prenda',
        'cambio_detalle',
        'dispositivo',
        'operacion_pendiente',
        'resolucion_conflicto',
        'direccion_cliente',
        'envio',
        'cupon',
        'cupon_uso',
        'venta_estado_historial',
        'prediccion_demanda',
        'segmento_cliente',
        'consulta_ia_log',
        'reporte_exportado',
        'avatar_cliente',
        'medida_corporal',
        'prenda_ar',
        'sesion_prueba_virtual'
    ]
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
