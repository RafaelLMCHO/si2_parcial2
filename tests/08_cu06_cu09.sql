BEGIN;

INSERT INTO empresa (id, nombre, slug, nit, correo, telefono, direccion, estado)
VALUES (
    '66666666-6666-6666-6666-666666666666',
    'Empresa SaaS Prueba',
    'empresa-saas-prueba',
    'SAAS-SQL-001',
    'saas-sql@test.local',
    '70000066',
    'Av. SaaS 123',
    'pendiente_plan'
);

DO $$
BEGIN
    INSERT INTO empresa (id, nombre, slug, nit, correo)
    VALUES (
        '66666666-6666-6666-6666-666666666667',
        'Empresa SaaS Duplicada',
        'empresa-saas-duplicada',
        'SAAS-SQL-001',
        'saas-sql-2@test.local'
    );
    RAISE EXCEPTION 'Se permitio registrar un NIT duplicado';
EXCEPTION WHEN unique_violation THEN
    NULL;
END $$;

UPDATE empresa
   SET estado = 'activa'
 WHERE id = '66666666-6666-6666-6666-666666666666';

INSERT INTO suscripcion (id, empresa_id, plan_id, estado, fecha_inicio, fecha_fin)
SELECT
    '66666666-6666-6666-6666-666666666c01',
    '66666666-6666-6666-6666-666666666666',
    p.id,
    'activa',
    CURRENT_DATE,
    CURRENT_DATE + 30
FROM plan p
WHERE p.codigo = 'basico';

DO $$
BEGIN
    INSERT INTO suscripcion (id, empresa_id, plan_id, estado, fecha_inicio, fecha_fin)
    SELECT
        '66666666-6666-6666-6666-666666666c02',
        '66666666-6666-6666-6666-666666666666',
        p.id,
        'activa',
        CURRENT_DATE,
        CURRENT_DATE + 30
    FROM plan p
    WHERE p.codigo = 'profesional';
    RAISE EXCEPTION 'Se permitio mas de una suscripcion activa por empresa';
EXCEPTION WHEN unique_violation THEN
    NULL;
END $$;

UPDATE suscripcion
   SET estado = 'cancelada',
       updated_at = now()
 WHERE id = '66666666-6666-6666-6666-666666666c01';

INSERT INTO suscripcion (id, empresa_id, plan_id, estado, fecha_inicio, fecha_fin)
SELECT
    '66666666-6666-6666-6666-666666666c03',
    '66666666-6666-6666-6666-666666666666',
    p.id,
    'activa',
    CURRENT_DATE + 1,
    CURRENT_DATE + 31
FROM plan p
WHERE p.codigo = 'profesional';

DO $$
DECLARE
    v_activas integer;
BEGIN
    SELECT count(*)
      INTO v_activas
      FROM suscripcion
     WHERE empresa_id = '66666666-6666-6666-6666-666666666666'
       AND estado IN ('prueba', 'activa', 'mora');

    IF v_activas <> 1 THEN
        RAISE EXCEPTION 'El historial de suscripciones dejo % suscripciones activas', v_activas;
    END IF;
END $$;

ROLLBACK;
