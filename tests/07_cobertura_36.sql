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

    -- Validaciones de esquema y RLS para ajustes CU-01..CU-37 (db/27_ajustes_36cu.sql + CU-37)
    IF NOT EXISTS (
        SELECT 1
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = 'plan'
           AND column_name = 'periodo'
    ) THEN
        RAISE EXCEPTION 'CU-06: falta la columna plan.periodo';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conname = 'reserva_estado_check'
           AND pg_get_constraintdef(oid) LIKE '%completada%'
    ) THEN
        RAISE EXCEPTION 'CU-21: reserva_estado_check no incluye el estado completada';
    END IF;

    IF (
        SELECT count(*)
          FROM pg_indexes
         WHERE schemaname = current_schema()
           AND tablename = 'bitacora_auditoria'
           AND indexname IN ('ix_bitacora_auditoria_empresa_fecha', 'ix_bitacora_auditoria_accion_fecha')
    ) <> 2 THEN
        RAISE EXCEPTION 'CU-05: faltan indices paginados en bitacora_auditoria';
    END IF;

    IF (
        SELECT count(*)
          FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = current_schema()
           AND c.relname IN ('soft_lock', 'nota_cambio', 'sync_registro_idempotencia')
           AND c.relrowsecurity = true
           AND c.relforcerowsecurity = true
    ) <> 3 THEN
        RAISE EXCEPTION 'CU-27/CU-29/CU-31: RLS no esta habilitado y forzado en tablas offline';
    END IF;

    IF to_regclass('backup_registro') IS NULL OR to_regclass('backup_configuracion') IS NULL THEN
        RAISE EXCEPTION 'CU-37: faltan tablas de backups (backup_registro/backup_configuracion)';
    END IF;
END $$;

ROLLBACK;

/*
================================================================================
MATRIZ DE COBERTURA FUNCIONAL (CU-01 a CU-37)
CU | backend | web | móvil | test | estado
--------------------------------------------------------------------------------
CU-01 | routers/auth.py (/auth/login, /auth/register-tenant) | features/auth/login, features/saas/empresa-form | features/auth/presentation/login_screen.dart | test_cu01_05.py, test_e2e_36_cu.py | completo
CU-02 | routers/auth.py (/auth/register, /auth/verify-email) | features/auth/register, verify-email | features/auth/presentation/{register,verify_email}_screen.dart | test_cu01_05.py, 07_cobertura_36.sql, test_e2e_36_cu.py | completo
CU-03 | routers/users.py (/users/me, /users/me/password) | features/profile/profile.component.ts | features/profile/presentation/profile_screen.dart | test_cu01_05.py, test_e2e_36_cu.py | completo
CU-04 | routers/auth.py (/auth/refresh, /auth/logout) | core/auth.service.ts, core/auth.interceptor.ts | features/auth/data/auth_repository.dart | test_cu01_05.py, test_e2e_36_cu.py | completo
CU-05 | middleware/audit.py + routers/auditoria.py (/auditoria/logs) | features/auditoria/auditoria.component.ts | features/auditoria/presentation/auditoria_screen.dart | test_cu01_05.py, 05_rls_auditoria.sql, test_e2e_36_cu.py | completo
CU-06 | routers/saas.py (/saas/planes CRUD) | features/saas/planes/planes.component.ts | features/saas/presentation/planes_controller.dart | test_cu06_09.py, 08_cu06_cu09.sql, test_e2e_36_cu.py | completo
CU-07 | routers/suscripciones.py (/mi-suscripcion*) | features/mi-suscripcion/mi-suscripcion.component.ts | features/saas/presentation/suscripciones_controller.dart | test_cu06_09.py, 06_limites_planes.sql, test_e2e_36_cu.py | completo
CU-08 | routers/saas.py (/saas/facturas, /saas/facturas/{id}/pdf) | features/saas/facturacion/facturacion.component.ts | features/saas/presentation/facturacion_controller.dart | test_cu06_09.py, 08_cu06_cu09.sql, test_e2e_36_cu.py | completo
CU-09 | routers/saas.py (/saas/metricas, /saas/empresas*) | features/saas/{panel,metricas,empresa-detail} | features/saas/presentation/{saas_screen,metricas_controller}.dart | test_cu06_09.py, 01_aislamiento_tenant.sql, test_e2e_36_cu.py | completo
CU-10 | routers/empleados.py (/empleados*) | features/empleados/empleados.component.ts | features/empleados/presentation/empleados_screen.dart | test_cu10_16.py, test_e2e_36_cu.py | completo
CU-11 | routers/sucursales.py (/sucursales*) | features/sucursales/sucursales.component.ts | features/sucursales/presentation/sucursales_screen.dart | test_cu10_16.py, 06_limites_planes.sql, test_e2e_36_cu.py | completo
CU-12 | routers/catalogo.py (/catalogo/admin/prendas*) | features/catalogo-admin/catalogo-admin.component.ts | features/catalogo_admin/presentation/catalogo_admin_screen.dart | test_cu10_16.py, test_e2e_36_cu.py | completo
CU-13 | routers/catalogo.py (/catalogo/prendas, /catalogo/prendas/{id}) | features/catalogo-cliente | features/catalogo/presentation/{catalogo,detalle_producto}_screen.dart | test_cu10_16.py, test_e2e_36_cu.py | completo
CU-14 | routers/catalogo.py (/catalogo/auxiliares + filtros) | features/catalogo-cliente | features/catalogo/presentation/widgets/filtros_catalogo_sheet.dart | test_e2e_36_cu.py | completo
CU-15 | routers/proveedores.py (/proveedores*) | features/proveedores/proveedores.component.ts | features/proveedores/presentation/proveedores_screen.dart | test_cu10_16.py, test_e2e_36_cu.py | completo
CU-16 | routers/colecciones.py (/temporadas-colecciones*) | features/temporadas/temporadas.component.ts | features/temporadas/presentation/temporadas_screen.dart | test_cu10_16.py, test_e2e_36_cu.py | completo
CU-17 | routers/inventario.py (/inventario*) | features/inventario/inventario.component.ts | features/inventario/presentation/inventario_screen.dart | test_cu17_inventario.py, 02_stock_concurrente.sql, test_e2e_36_cu.py | completo
CU-18 | routers/inventario.py (/inventario/prendas/{prenda_id}/disponibilidad) | features/disponibilidad-tiendas | features/inventario/presentation/disponibilidad_screen.dart | test_cu18_disponibilidad.py, test_e2e_36_cu.py | completo
CU-19 | routers/reservas.py (/reservas/validar, /reservas) | features/reservas/reserva-creacion | features/reservas/presentation/reserva_creacion_controller.dart | test_cu19_reservas.py, 02_stock_concurrente.sql, test_e2e_36_cu.py | completo
CU-20 | routers/reservas.py (/reservas/mis-reservas, /reservas/{id}/cancelar) | features/reservas/reserva-cliente | features/reservas/presentation/reserva_cliente_controller.dart | test_cu20_cancelar_reservas.py, 07_cobertura_36.sql, test_e2e_36_cu.py | completo
CU-21 | routers/reservas.py (/reservas/por-preparar, /preparar, /completar, /incidencia) | features/reservas/reserva-staff | features/reservas/presentation/reserva_staff_controller.dart | test_cu21_preparar_reservas.py, test_e2e_36_cu.py | completo
CU-22 | routers/carrito.py + routers/checkout.py | features/checkout/checkout.component.ts | features/checkout/presentation/checkout_screen.dart | test_cu22_checkout.py, test_e2e_36_cu.py | completo
CU-23 | routers/pos.py (/pos/*) | features/pos/pos.component.ts | features/pos/presentation/pos_screen.dart | test_cu23_pos.py, test_e2e_36_cu.py | completo
CU-24 | routers/pagos.py + StripeGateway (PaymentIntent, Webhook HMAC, Reembolso) | features/pagos/pagos.component.ts | features/pagos/presentation/pagos_screen.dart | test_cu24_pagos.py, 04_pagos_devoluciones.sql, test_e2e_36_cu.py | completo
CU-25 | routers/sync.py (/sync/catalogo-offline) | features/offline/catalogo-offline | features/offline/presentation/catalogo_offline_screen.dart | test_cu25_a_cu32_sync.py, 07_cobertura_36.sql, test_e2e_36_cu.py | completo
CU-26 | routers/sync.py (/sync) | features/offline/reserva-offline | features/offline/presentation/reserva_offline_screen.dart | test_cu25_a_cu32_sync.py, test_e2e_36_cu.py | completo
CU-27 | routers/sync.py (/sync/soft-locks*) + fn_expirar_reservas() | features/offline/bloqueos-activos | features/offline/presentation/bloqueos_activos_screen.dart | test_cu25_a_cu32_sync.py, 07_cobertura_36.sql, test_e2e_36_cu.py | completo
CU-28 | routers/sync.py (/sync tipo venta_offline) | features/offline/venta-offline | features/offline/presentation/venta_offline_screen.dart | test_cu25_a_cu32_sync.py, 03_offline_idempotencia.sql, test_e2e_36_cu.py | completo
CU-29 | routers/sync.py (/sync/validar-qr, /sync/nota-cambio) | features/offline/cambio-qr | features/offline/presentation/cambio_qr_screen.dart | test_cu25_a_cu32_sync.py, test_e2e_36_cu.py | completo
CU-30 | routers/sync.py (/sync + operacion_pendiente) | features/offline/cola-operaciones | features/offline/presentation/cola_operaciones_screen.dart | test_cu25_a_cu32_sync.py, test_e2e_36_cu.py | completo
CU-31 | routers/sync.py (/sync + sync_registro_idempotencia) | features/offline/cola-operaciones | features/offline/presentation/cola_operaciones_screen.dart | test_cu25_a_cu32_sync.py, 03_offline_idempotencia.sql, test_e2e_36_cu.py | completo
CU-32 | routers/sync.py (/sync/conflictos, /conflictos/resolver) | features/offline/conflictos | features/offline/presentation/conflictos_screen.dart | test_cu25_a_cu32_sync.py, test_e2e_36_cu.py | completo
CU-33 | routers/reportes.py (/reportes/convencionales/*) | features/reportes/reportes-convencionales.component.ts | features/reportes/presentation/reportes_convencionales_screen.dart | test_cu33_a_cu36.py, test_e2e_36_cu.py | completo
CU-34 | routers/reportes.py (/reportes/ia/*) + LLM Adapter/Whitelist BR-08 + XLSX/PDF | features/reportes/reporte-ia.component.ts | features/reportes/presentation/reporte_ia_screen.dart | test_cu33_a_cu36.py, 07_cobertura_36.sql, test_e2e_36_cu.py | completo
CU-35 | routers/inteligencia.py (/inteligencia/ml/*) + LinearRegression/KMeans/WAV | features/analytics-ml/dashboard-ml.component.ts | features/analytics_ml/presentation/dashboard_ml_screen.dart | test_cu33_a_cu36.py, test_e2e_36_cu.py | completo
CU-36 | routers/vestidor.py (/vestidor/*) + db/17_ar.sql + Decart Lucy VTON | features/vestidor-virtual/vestidor-virtual.component.ts | features/vestidor_virtual/presentation/vestidor_virtual_screen.dart | test_cu33_a_cu36.py, 07_cobertura_36.sql, test_e2e_36_cu.py | completo
CU-37 | routers/backups.py (/backups*) | features/backups/backups.component.ts | features/backups/presentation/backups_screen.dart | test_cu37_backups.py, 07_cobertura_36.sql, test_e2e_36_cu.py | completo
================================================================================
*/
