BEGIN;

SET LOCAL ROLE fashion_app;
SET LOCAL app.empresa_id = '11111111-1111-1111-1111-111111111111';

DO $$
DECLARE
    v_count integer;
BEGIN
    UPDATE inventario
       SET stock_minimo = stock_minimo + 1
     WHERE id = '11111111-1111-1111-1111-111111111701';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se pudo actualizar el inventario del tenant';
    END IF;

    SELECT count(*)
      INTO v_count
      FROM bitacora_auditoria
     WHERE entidad = 'inventario'
       AND entidad_id = '11111111-1111-1111-1111-111111111701'
       AND accion = 'update';

    IF v_count < 1 THEN
        RAISE EXCEPTION 'La auditoría no registró la actualización';
    END IF;

    BEGIN
        DELETE FROM bitacora_auditoria
         WHERE entidad = 'inventario'
           AND entidad_id = '11111111-1111-1111-1111-111111111701';

        GET DIAGNOSTICS v_count = ROW_COUNT;
        IF v_count <> 0 THEN
            RAISE EXCEPTION 'La auditoría permitió eliminar registros';
        END IF;
    EXCEPTION WHEN insufficient_privilege THEN
        NULL;
    END;

    SELECT count(*)
      INTO v_count
      FROM bitacora_auditoria
     WHERE entidad = 'usuario'
       AND entidad_id = '11111111-1111-1111-1111-111111111301'
       AND (
           datos_antes ? 'password_hash'
           OR datos_despues ? 'password_hash'
       );

    IF v_count <> 0 THEN
        RAISE EXCEPTION 'La auditoría expuso password_hash';
    END IF;

    INSERT INTO consulta_ia_log (
        empresa_id,
        usuario_id,
        prompt,
        reporte_tipo,
        parametros_json
    ) VALUES (
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111301',
        'Ventas del mes',
        'ventas',
        '{}'::jsonb
    );

    BEGIN
        PERFORM 1 FROM consulta_ia_log_2026_10 LIMIT 1;
        RAISE EXCEPTION 'Se permitió el acceso directo a una partición';
    EXCEPTION WHEN insufficient_privilege THEN
        NULL;
    END;

    PERFORM set_config('app.empresa_id', '22222222-2222-2222-2222-222222222222', true);

    SELECT count(*) INTO v_count FROM venta;
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'RLS no aisló las ventas del otro tenant: %', v_count;
    END IF;
END $$;

RESET ROLE;
ROLLBACK;
