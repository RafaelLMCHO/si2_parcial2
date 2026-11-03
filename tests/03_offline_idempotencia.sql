BEGIN;

DO $$
BEGIN
    INSERT INTO operacion_pendiente (
        id,
        empresa_id,
        dispositivo_id,
        sucursal_id,
        usuario_id,
        tipo,
        payload,
        nonce,
        idempotency_key
    ) VALUES (
        gen_random_uuid(),
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111801',
        '11111111-1111-1111-1111-111111111101',
        '11111111-1111-1111-1111-111111111301',
        'venta_offline',
        '{"total": 100}'::jsonb,
        'nonce-1',
        'op-key-1'
    );

    BEGIN
        INSERT INTO operacion_pendiente (
            id, empresa_id, dispositivo_id, sucursal_id, usuario_id,
            tipo, payload, nonce, idempotency_key
        ) VALUES (
            gen_random_uuid(),
            '11111111-1111-1111-1111-111111111111',
            '11111111-1111-1111-1111-111111111801',
            '11111111-1111-1111-1111-111111111101',
            '11111111-1111-1111-1111-111111111301',
            'venta_offline',
            '{"total": 100}'::jsonb,
            'nonce-2',
            'op-key-1'
        );
        RAISE EXCEPTION 'La idempotencia de la operación no bloqueó el duplicado';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;

    BEGIN
        INSERT INTO operacion_pendiente (
            id, empresa_id, dispositivo_id, sucursal_id, usuario_id,
            tipo, payload, nonce, idempotency_key
        ) VALUES (
            gen_random_uuid(),
            '11111111-1111-1111-1111-111111111111',
            '11111111-1111-1111-1111-111111111801',
            '11111111-1111-1111-1111-111111111101',
            '11111111-1111-1111-1111-111111111301',
            'venta_offline',
            '{"total": 100}'::jsonb,
            'nonce-1',
            'op-key-2'
        );
        RAISE EXCEPTION 'El nonce no bloqueó el replay';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

DO $$
BEGIN
    INSERT INTO venta (
        id, empresa_id, numero, canal, estado, idempotency_key
    ) VALUES (
        gen_random_uuid(),
        '11111111-1111-1111-1111-111111111111',
        'V-DUP',
        'WEB',
        'pendiente_pago',
        'seed-venta-1'
    );
    RAISE EXCEPTION 'La idempotencia de la venta no bloqueó el duplicado';
EXCEPTION WHEN unique_violation THEN
    NULL;
END $$;

ROLLBACK;
