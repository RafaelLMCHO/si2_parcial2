-- Ajustes para CU-01 a CU-05 (autenticacion, registro, perfil, logout y auditoria).
-- Este archivo se ejecuta despues de los seeds y antes de la verificacion estructural.

ALTER TABLE bitacora_auditoria
    ADD COLUMN IF NOT EXISTS es_accion_superadmin boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS metodo varchar(10),
    ADD COLUMN IF NOT EXISTS endpoint varchar(255),
    ADD COLUMN IF NOT EXISTS parametros jsonb;

ALTER TABLE bitacora_auditoria
    DROP CONSTRAINT IF EXISTS bitacora_auditoria_accion_check;

ALTER TABLE bitacora_auditoria
    ADD CONSTRAINT bitacora_auditoria_accion_check
    CHECK (accion IN ('insert', 'update', 'delete', 'login', 'logout', 'export', 'access', 'sync'));

-- Rol faltante para los actores del modelo de casos de uso.
INSERT INTO rol (id, empresa_id, nombre, descripcion, es_global)
VALUES (
    '11111111-1111-1111-1111-111111111204',
    '11111111-1111-1111-1111-111111111111',
    'encargado',
    'Encargado de sucursal',
    false
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111204', id
FROM permiso
WHERE codigo IN ('ventas.crear', 'ventas.ver', 'inventario.ver', 'inventario.ajustar', 'catalogo.ver')
ON CONFLICT DO NOTHING;

-- Los usuarios demo ya existen y no tienen correo verificado; sin esto no podrian
-- iniciar sesion con la regla de CU-02.
UPDATE usuario
   SET email_verificado = true,
       email_verificado_en = COALESCE(email_verificado_en, now())
 WHERE correo IN ('superadmin@fashionstore.test', 'admin@demo.test', 'cliente@demo.test')
   AND email_verificado = false;

CREATE OR REPLACE FUNCTION fn_empresa_por_slug(p_slug text)
RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT e.id
      FROM empresa e
     WHERE e.slug = p_slug
       AND e.deleted_at IS NULL
     LIMIT 1;
$$;

ALTER FUNCTION fn_empresa_por_slug(text) OWNER TO fashion_superadmin;

CREATE OR REPLACE FUNCTION fn_login_lookup(p_slug text, p_correo text)
RETURNS TABLE (
    usuario_id uuid,
    empresa_id uuid,
    nombre varchar,
    correo citext,
    password_hash text,
    usuario_estado varchar,
    email_verificado boolean,
    telefono varchar,
    sucursal_id uuid,
    ultimo_acceso timestamptz,
    created_at timestamptz,
    rol_id uuid,
    rol_nombre varchar,
    empresa_slug citext,
    empresa_estado varchar,
    suscripcion_estado varchar,
    suscripcion_fecha_fin date,
    plan_codigo varchar
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT u.id,
           u.empresa_id,
           u.nombre,
           u.correo,
           u.password_hash,
           u.estado,
           u.email_verificado,
           u.telefono,
           u.sucursal_id,
           u.ultimo_acceso,
           u.created_at,
           r.id,
           r.nombre,
           e.slug,
           e.estado,
           s.estado,
           s.fecha_fin,
           p.codigo
      FROM usuario u
      JOIN rol r ON r.id = u.rol_id
      LEFT JOIN empresa e ON e.id = u.empresa_id
      LEFT JOIN LATERAL (
          SELECT s2.estado, s2.fecha_fin, s2.plan_id
            FROM suscripcion s2
           WHERE s2.empresa_id = u.empresa_id
             AND s2.estado IN ('prueba', 'activa', 'mora')
           ORDER BY s2.fecha_inicio DESC
           LIMIT 1
      ) s ON true
      LEFT JOIN plan p ON p.id = s.plan_id
     WHERE u.deleted_at IS NULL
       AND u.correo = p_correo
       AND (
           (p_slug IS NOT NULL AND u.empresa_id = fn_empresa_por_slug(p_slug))
           OR (p_slug IS NULL AND u.empresa_id IS NULL)
       )
     LIMIT 1;
$$;

ALTER FUNCTION fn_login_lookup(text, text) OWNER TO fashion_superadmin;

CREATE OR REPLACE FUNCTION fn_verificar_correo(p_slug text, p_token_hash text)
RETURNS TABLE (usuario_id uuid, empresa_id uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_empresa uuid;
    v_usuario uuid;
BEGIN
    SELECT fn_empresa_por_slug(p_slug) INTO v_empresa;
    IF v_empresa IS NULL THEN
        RETURN;
    END IF;

    UPDATE verificacion_correo vc
       SET verificado_en = now()
     WHERE vc.empresa_id = v_empresa
       AND vc.token_hash = p_token_hash
       AND vc.verificado_en IS NULL
       AND vc.expira_en > now()
    RETURNING vc.usuario_id INTO v_usuario;

    IF v_usuario IS NULL THEN
        RETURN;
    END IF;

    UPDATE usuario u
       SET email_verificado = true,
           email_verificado_en = COALESCE(u.email_verificado_en, now()),
           estado = CASE WHEN u.estado IN ('inactivo', 'pendiente') THEN 'activo' ELSE u.estado END
     WHERE u.empresa_id = v_empresa
       AND u.id = v_usuario;

    RETURN QUERY SELECT v_usuario, v_empresa;
END;
$$;

ALTER FUNCTION fn_verificar_correo(text, text) OWNER TO fashion_superadmin;

CREATE OR REPLACE FUNCTION fn_registrar_auditoria(
    p_empresa_id uuid,
    p_empresa_afectada_id uuid,
    p_usuario_id uuid,
    p_actor_tipo varchar,
    p_accion varchar,
    p_entidad varchar,
    p_entidad_id uuid,
    p_datos_antes jsonb,
    p_datos_despues jsonb,
    p_ip inet,
    p_es_accion_superadmin boolean,
    p_metodo varchar,
    p_endpoint varchar,
    p_parametros jsonb
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_id bigint;
BEGIN
    INSERT INTO bitacora_auditoria (
        empresa_id,
        empresa_afectada_id,
        usuario_id,
        actor_tipo,
        accion,
        entidad,
        entidad_id,
        datos_antes,
        datos_despues,
        ip,
        es_accion_superadmin,
        metodo,
        endpoint,
        parametros
    ) VALUES (
        p_empresa_id,
        p_empresa_afectada_id,
        p_usuario_id,
        COALESCE(p_actor_tipo, 'usuario'),
        p_accion,
        p_entidad,
        p_entidad_id,
        p_datos_antes,
        p_datos_despues,
        p_ip,
        COALESCE(p_es_accion_superadmin, false),
        p_metodo,
        p_endpoint,
        p_parametros
    )
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$;

ALTER FUNCTION fn_registrar_auditoria(
    uuid, uuid, uuid, varchar, varchar, varchar, uuid, jsonb, jsonb,
    inet, boolean, varchar, varchar, jsonb
) OWNER TO fashion_superadmin;

GRANT EXECUTE ON FUNCTION fn_empresa_por_slug(text) TO fashion_app, fashion_superadmin;
GRANT EXECUTE ON FUNCTION fn_login_lookup(text, text) TO fashion_app, fashion_superadmin;
GRANT EXECUTE ON FUNCTION fn_verificar_correo(text, text) TO fashion_app, fashion_superadmin;
GRANT EXECUTE ON FUNCTION fn_registrar_auditoria(
    uuid, uuid, uuid, varchar, varchar, varchar, uuid, jsonb, jsonb,
    inet, boolean, varchar, varchar, jsonb
) TO fashion_app, fashion_superadmin;
