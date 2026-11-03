BEGIN;

UPDATE inventario
   SET stock_fisico = 1,
       stock_reservado = 0
 WHERE id = '11111111-1111-1111-1111-111111111701';

INSERT INTO reserva (
    id, empresa_id, usuario_id, sucursal_id, estado, expira_en
) VALUES (
    '11111111-1111-1111-1111-111111111c11',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111302',
    '11111111-1111-1111-1111-111111111101',
    'activa',
    now() + interval '1 hour'
);

INSERT INTO reserva_detalle (
    id, empresa_id, reserva_id, variante_id, cantidad
) VALUES (
    '11111111-1111-1111-1111-111111111c12',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111c11',
    '11111111-1111-1111-1111-111111111601',
    1
);

DO $$
DECLARE
    v_filas integer;
BEGIN
    IF (SELECT stock_reservado FROM inventario WHERE id = '11111111-1111-1111-1111-111111111701') <> 1 THEN
        RAISE EXCEPTION 'La reserva no incrementó stock_reservado';
    END IF;

    IF (SELECT stock_disponible FROM inventario WHERE id = '11111111-1111-1111-1111-111111111701') <> 0 THEN
        RAISE EXCEPTION 'El stock disponible no quedó en cero';
    END IF;

    INSERT INTO reserva (
        id, empresa_id, usuario_id, sucursal_id, estado, expira_en
    ) VALUES (
        '11111111-1111-1111-1111-111111111c13',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111302',
        '11111111-1111-1111-1111-111111111101',
        'activa',
        now() + interval '1 hour'
    );

    BEGIN
        INSERT INTO reserva_detalle (
            id, empresa_id, reserva_id, variante_id, cantidad
        ) VALUES (
            gen_random_uuid(),
            '11111111-1111-1111-1111-111111111111',
            '11111111-1111-1111-1111-111111111c13',
            '11111111-1111-1111-1111-111111111601',
            1
        );
        RAISE EXCEPTION 'Se permitió reservar más unidades que el stock físico';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;

    UPDATE inventario
       SET stock_fisico = stock_fisico - 1
     WHERE id = '11111111-1111-1111-1111-111111111701'
       AND stock_fisico - stock_reservado >= 1;

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> 0 THEN
        RAISE EXCEPTION 'La actualización atómica descontó stock reservado';
    END IF;
END $$;

ROLLBACK;
