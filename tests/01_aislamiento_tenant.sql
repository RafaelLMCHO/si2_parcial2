BEGIN;

INSERT INTO empresa (id, nombre, slug, nit, correo)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'Empresa B',
    'empresa-b',
    'B-001',
    'b@test.local'
);

INSERT INTO categoria (id, empresa_id, nombre)
VALUES (
    '22222222-2222-2222-2222-222222222401',
    '22222222-2222-2222-2222-222222222222',
    'Categoría B'
);

INSERT INTO prenda (
    id, empresa_id, categoria_id, codigo, nombre, genero, estado
)
VALUES (
    '22222222-2222-2222-2222-222222222501',
    '22222222-2222-2222-2222-222222222222',
    '22222222-2222-2222-2222-222222222401',
    'B-001',
    'Prenda B',
    'unisex',
    'activa'
);

INSERT INTO variante (
    id, empresa_id, prenda_id, color_id, talla_id, sku, precio_venta, estado
)
SELECT
    '22222222-2222-2222-2222-222222222601',
    '22222222-2222-2222-2222-222222222222',
    '22222222-2222-2222-2222-222222222501',
    c.id,
    t.id,
    'B-SKU-001',
    100.00,
    'activa'
FROM color c
CROSS JOIN talla t
WHERE c.nombre = 'Negro'
  AND t.nombre = 'M';

SET LOCAL ROLE fashion_app;
SET LOCAL app.empresa_id = '11111111-1111-1111-1111-111111111111';

DO $$
DECLARE
    v_count integer;
BEGIN
    SELECT count(*) INTO v_count FROM empresa;
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'RLS empresa: se esperaban 1 fila, se obtuvieron %', v_count;
    END IF;

    SELECT count(*) INTO v_count FROM sucursal;
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'RLS sucursal: se esperaban 1 fila, se obtuvieron %', v_count;
    END IF;

    SELECT count(*) INTO v_count FROM venta;
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'RLS venta: se esperaban 1 fila, se obtuvieron %', v_count;
    END IF;

    BEGIN
        INSERT INTO venta_detalle (
            id,
            empresa_id,
            venta_id,
            variante_id,
            cantidad,
            precio_lista,
            precio_unitario,
            descuento_linea,
            subtotal
        ) VALUES (
            gen_random_uuid(),
            '11111111-1111-1111-1111-111111111111',
            '11111111-1111-1111-1111-111111111b01',
            '22222222-2222-2222-2222-222222222601',
            1,
            100.00,
            100.00,
            0.00,
            100.00
        );
        RAISE EXCEPTION 'La FK compuesta permitió mezclar dos tenants';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
END $$;

RESET ROLE;
SET LOCAL ROLE fashion_superadmin;

DO $$
DECLARE
    v_count integer;
BEGIN
    SELECT count(*) INTO v_count FROM empresa;
    IF v_count < 2 THEN
        RAISE EXCEPTION 'El superadmin no ve todos los tenants: %', v_count;
    END IF;
END $$;

RESET ROLE;
ROLLBACK;
