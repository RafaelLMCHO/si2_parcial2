BEGIN;

INSERT INTO empresa (id, nombre, slug, nit, correo)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    'Empresa C',
    'empresa-c',
    'C-001',
    'c@test.local'
);

INSERT INTO suscripcion (id, empresa_id, plan_id, estado, fecha_inicio)
SELECT
    '33333333-3333-3333-3333-333333333c01',
    '33333333-3333-3333-3333-333333333333',
    p.id,
    'activa',
    CURRENT_DATE
FROM plan p
WHERE p.codigo = 'basico';

INSERT INTO sucursal (id, empresa_id, ciudad_id, nombre, direccion, estado)
SELECT
    '33333333-3333-3333-3333-333333333101',
    '33333333-3333-3333-3333-333333333333',
    c.id,
    'Sucursal C1',
    'Calle 1',
    'activa'
FROM ciudad c
WHERE c.nombre = 'Santa Cruz de la Sierra'
  AND c.departamento = 'Santa Cruz';

INSERT INTO sucursal (id, empresa_id, ciudad_id, nombre, direccion, estado)
SELECT
    '33333333-3333-3333-3333-333333333102',
    '33333333-3333-3333-3333-333333333333',
    c.id,
    'Sucursal C2',
    'Calle 2',
    'activa'
FROM ciudad c
WHERE c.nombre = 'Santa Cruz de la Sierra'
  AND c.departamento = 'Santa Cruz';

DO $$
BEGIN
    INSERT INTO sucursal (id, empresa_id, ciudad_id, nombre, direccion, estado)
    SELECT
        '33333333-3333-3333-3333-333333333103',
        '33333333-3333-3333-3333-333333333333',
        c.id,
        'Sucursal C3',
        'Calle 3',
        'activa'
    FROM ciudad c
    WHERE c.nombre = 'Santa Cruz de la Sierra'
      AND c.departamento = 'Santa Cruz';

    RAISE EXCEPTION 'Se permitió superar el límite de sucursales del plan';
EXCEPTION WHEN others THEN
    IF SQLERRM NOT LIKE '%sucursales%' THEN
        RAISE;
    END IF;
END $$;

ROLLBACK;
