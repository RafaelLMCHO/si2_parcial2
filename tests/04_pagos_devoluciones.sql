BEGIN;

DO $$
DECLARE
    v_cambio_id uuid;
    i integer;
BEGIN
    BEGIN
        INSERT INTO pago (
            id, empresa_id, venta_id, monto, metodo, idempotency_key, estado
        ) VALUES (
            gen_random_uuid(),
            '11111111-1111-1111-1111-111111111111',
            '11111111-1111-1111-1111-111111111b01',
            1.00,
            'efectivo',
            'pago-extra-1',
            'completado'
        );
        RAISE EXCEPTION 'Se permitió un pago que excede el total';
    EXCEPTION WHEN others THEN
        IF SQLERRM NOT LIKE '%excede el total%' THEN
            RAISE;
        END IF;
    END;

    FOR i IN 1..3 LOOP
        INSERT INTO cambio_prenda (
            id,
            empresa_id,
            venta_id,
            sucursal_id,
            usuario_id,
            motivo,
            estado
        ) VALUES (
            gen_random_uuid(),
            '11111111-1111-1111-1111-111111111111',
            '11111111-1111-1111-1111-111111111b01',
            '11111111-1111-1111-1111-111111111101',
            '11111111-1111-1111-1111-111111111302',
            'Cambio ' || i,
            'solicitado'
        )
        RETURNING id INTO v_cambio_id;

        IF i <= 2 THEN
            INSERT INTO cambio_detalle (
                id, empresa_id, cambio_id, venta_detalle_id, cantidad
            ) VALUES (
                gen_random_uuid(),
                '11111111-1111-1111-1111-111111111111',
                v_cambio_id,
                '11111111-1111-1111-1111-111111111b02',
                1
            );
        ELSE
            BEGIN
                INSERT INTO cambio_detalle (
                    id, empresa_id, cambio_id, venta_detalle_id, cantidad
                ) VALUES (
                    gen_random_uuid(),
                    '11111111-1111-1111-1111-111111111111',
                    v_cambio_id,
                    '11111111-1111-1111-1111-111111111b02',
                    1
                );
                RAISE EXCEPTION 'Se permitió devolver más unidades que las vendidas';
            EXCEPTION WHEN others THEN
                IF SQLERRM NOT LIKE '%excede la cantidad%' THEN
                    RAISE;
                END IF;
            END;
        END IF;
    END LOOP;
END $$;

INSERT INTO cupon_uso (
    id, empresa_id, cupon_id, venta_id, usuario_id
) VALUES (
    gen_random_uuid(),
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111a01',
    '11111111-1111-1111-1111-111111111b01',
    '11111111-1111-1111-1111-111111111302'
);

ROLLBACK;
