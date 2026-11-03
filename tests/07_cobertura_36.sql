BEGIN;

DO $$
DECLARE
    v_version bigint;
    v_stock integer;
    v_reserva_id uuid := '11111111-1111-1111-1111-111111111c21';
    v_reserva_exp_id uuid := '11111111-1111-1111-1111-111111111c22';
    v_consulta_id uuid;
    v_consulta_ocurrido timestamptz;
    v_avatar_id uuid := '11111111-1111-1111-1111-111111111f01';
BEGIN
    INSERT INTO verificacion_correo (
        id, empresa_id, usuario_id, token_hash, expira_en
    ) VALUES (
        '11111111-1111-1111-1111-111111111e11',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111301',
        'token-verificacion-demo',
        now() + interval '1 hour'
    );

    UPDATE usuario
       SET email_verificado = true,
           email_verificado_en = now()
     WHERE id = '11111111-1111-1111-1111-111111111301';

    IF NOT (SELECT email_verificado FROM usuario WHERE id = '11111111-1111-1111-1111-111111111301') THEN
        RAISE EXCEPTION 'CU-02: no se registró la verificación de correo';
    END IF;

    SELECT version INTO v_version
      FROM catalogo_version
     WHERE empresa_id = '11111111-1111-1111-1111-111111111111';

    IF v_version IS NULL THEN
        RAISE EXCEPTION 'CU-25: no existe la versión de catálogo del tenant';
    END IF;

    UPDATE prenda
       SET nombre = nombre || ' actualizada'
     WHERE id = '11111111-1111-1111-1111-111111111501';

    IF (SELECT version FROM catalogo_version WHERE empresa_id = '11111111-1111-1111-1111-111111111111') <> v_version + 1 THEN
        RAISE EXCEPTION 'CU-25: el cambio de catálogo no incrementó la versión';
    END IF;

    UPDATE inventario
       SET stock_fisico = 5,
           stock_reservado = 0
     WHERE id = '11111111-1111-1111-1111-111111111701';

    INSERT INTO reserva (
        id, empresa_id, usuario_id, sucursal_id, estado,
        expira_en, fecha_visita, dispositivo_id
    ) VALUES (
        v_reserva_id,
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111302',
        '11111111-1111-1111-1111-111111111101',
        'activa',
        now() + interval '1 hour',
        now() + interval '1 day',
        '11111111-1111-1111-1111-111111111801'
    );

    INSERT INTO reserva_detalle (
        id, empresa_id, reserva_id, variante_id, cantidad
    ) VALUES (
        '11111111-1111-1111-1111-111111111c23',
        '11111111-1111-1111-1111-111111111111',
        v_reserva_id,
        '11111111-1111-1111-1111-111111111601',
        2
    );

    SELECT stock_reservado INTO v_stock
      FROM inventario
     WHERE id = '11111111-1111-1111-1111-111111111701';

    IF v_stock <> 2 THEN
        RAISE EXCEPTION 'CU-20: la reserva no apartó stock, stock_reservado=%', v_stock;
    END IF;

    UPDATE reserva
       SET estado = 'cancelada',
           motivo_cierre = 'Cancelación de prueba'
     WHERE id = v_reserva_id;

    SELECT stock_reservado INTO v_stock
      FROM inventario
     WHERE id = '11111111-1111-1111-1111-111111111701';

    IF v_stock <> 0 THEN
        RAISE EXCEPTION 'CU-20: la cancelación no liberó el stock, stock_reservado=%', v_stock;
    END IF;

    IF (SELECT liberada_en FROM reserva WHERE id = v_reserva_id) IS NULL THEN
        RAISE EXCEPTION 'CU-20: no se registró la liberación de la reserva';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM reserva_estado_historial
         WHERE reserva_id = v_reserva_id
           AND estado_anterior = 'activa'
           AND estado_nuevo = 'cancelada'
    ) THEN
        RAISE EXCEPTION 'CU-20: no se registró el historial de la reserva';
    END IF;

    BEGIN
        UPDATE reserva_detalle
           SET cantidad = 3
         WHERE reserva_id = v_reserva_id;
        RAISE EXCEPTION 'CU-20: se permitió modificar una reserva cerrada';
    EXCEPTION WHEN others THEN
        IF SQLERRM NOT LIKE '%reserva cerrada%' THEN
            RAISE;
        END IF;
    END;

    INSERT INTO reserva (
        id, empresa_id, usuario_id, sucursal_id, estado, expira_en
    ) VALUES (
        v_reserva_exp_id,
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111302',
        '11111111-1111-1111-1111-111111111101',
        'activa',
        now() + interval '1 hour'
    );

    INSERT INTO reserva_detalle (
        id, empresa_id, reserva_id, variante_id, cantidad
    ) VALUES (
        '11111111-1111-1111-1111-111111111c24',
        '11111111-1111-1111-1111-111111111111',
        v_reserva_exp_id,
        '11111111-1111-1111-1111-111111111601',
        1
    );

    UPDATE reserva
       SET created_at = now() - interval '2 hours',
           expira_en = now() - interval '1 hour'
     WHERE id = v_reserva_exp_id;

    PERFORM fn_expirar_reservas();

    IF (SELECT estado FROM reserva WHERE id = v_reserva_exp_id) <> 'expirada' THEN
        RAISE EXCEPTION 'CU-27: la reserva vencida no fue expirada';
    END IF;

    SELECT stock_reservado INTO v_stock
      FROM inventario
     WHERE id = '11111111-1111-1111-1111-111111111701';

    IF v_stock <> 0 THEN
        RAISE EXCEPTION 'CU-27: la expiración no liberó el stock, stock_reservado=%', v_stock;
    END IF;

    INSERT INTO consulta_ia_log (
        empresa_id,
        usuario_id,
        prompt,
        respuesta,
        canal,
        reporte_tipo,
        parametros_json,
        estado,
        audio_url,
        audio_mime,
        tts_modelo,
        tts_voz,
        duracion_audio_ms
    ) VALUES (
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111301',
        'Resumen de ventas del mes',
        'Las ventas crecieron 12%.',
        'voz',
        'ventas',
        '{}'::jsonb,
        'exitoso',
        'https://cdn.fashionstore.test/audio/resumen.mp3',
        'audio/mpeg',
        'tts-demo',
        'es-BO',
        1200
    )
    RETURNING id, ocurrido_en INTO v_consulta_id, v_consulta_ocurrido;

    INSERT INTO reporte_exportado (
        empresa_id,
        usuario_id,
        consulta_ia_log_id,
        consulta_ocurrido_en,
        tipo_reporte,
        formato,
        archivo_url,
        tamano_bytes
    ) VALUES (
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111301',
        v_consulta_id,
        v_consulta_ocurrido,
        'ventas',
        'pdf',
        'https://cdn.fashionstore.test/reportes/ventas.pdf',
        2048
    );

    INSERT INTO avatar_cliente (
        id, empresa_id, usuario_id, nombre, altura_cm, peso_kg, tono_piel
    ) VALUES (
        v_avatar_id,
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111302',
        'Avatar demo',
        165.00,
        58.00,
        'medio'
    );

    INSERT INTO medida_corporal (
        id, empresa_id, avatar_id, tipo, valor_cm
    ) VALUES (
        '11111111-1111-1111-1111-111111111f02',
        '11111111-1111-1111-1111-111111111111',
        v_avatar_id,
        'cintura',
        70.00
    );

    INSERT INTO prenda_ar (
        id, empresa_id, prenda_id, variante_id,
        modelo_url, textura_url, puntos_ajuste, talla_referencia
    ) VALUES (
        '11111111-1111-1111-1111-111111111f03',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111501',
        '11111111-1111-1111-1111-111111111601',
        'https://cdn.fashionstore.test/ar/vestido-midi.glb',
        'https://cdn.fashionstore.test/ar/vestido-midi.png',
        '{"hombro": [0, 1.2, 0]}'::jsonb,
        'M'
    );

    INSERT INTO sesion_prueba_virtual (
        id, empresa_id, usuario_id, avatar_id, prenda_id, variante_id,
        estado, iniciada_en, finalizada_en
    ) VALUES (
        '11111111-1111-1111-1111-111111111f04',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111302',
        v_avatar_id,
        '11111111-1111-1111-1111-111111111501',
        '11111111-1111-1111-1111-111111111601',
        'completada',
        now() - interval '5 minutes',
        now()
    );

    IF NOT EXISTS (
        SELECT 1
          FROM sesion_prueba_virtual
         WHERE id = '11111111-1111-1111-1111-111111111f04'
           AND estado = 'completada'
    ) THEN
        RAISE EXCEPTION 'CU-36: no se registró la sesión de prueba virtual';
    END IF;
END $$;

ROLLBACK;
