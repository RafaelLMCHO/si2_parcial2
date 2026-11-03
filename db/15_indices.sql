CREATE UNIQUE INDEX ux_suscripcion_activa
    ON suscripcion (empresa_id)
    WHERE estado IN ('prueba', 'activa', 'mora');

CREATE UNIQUE INDEX ux_rol_global_nombre
    ON rol (nombre)
    WHERE empresa_id IS NULL;

CREATE UNIQUE INDEX ux_usuario_correo_global
    ON usuario (correo)
    WHERE empresa_id IS NULL;

CREATE UNIQUE INDEX ux_sucursal_matriz
    ON sucursal (empresa_id)
    WHERE es_matriz AND deleted_at IS NULL;

CREATE INDEX ix_usuario_empresa_estado
    ON usuario (empresa_id, estado)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_sesion_usuario_expira
    ON sesion (usuario_id, expira_en DESC);

CREATE INDEX ix_bitacora_empresa_fecha
    ON bitacora_auditoria (empresa_id, ocurrido_en DESC);

CREATE INDEX ix_bitacora_entidad
    ON bitacora_auditoria (entidad, entidad_id);

CREATE INDEX ix_bitacora_datos_gin
    ON bitacora_auditoria USING gin (datos_despues jsonb_path_ops);

CREATE INDEX ix_prenda_empresa_categoria
    ON prenda (empresa_id, categoria_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_prenda_empresa_estado
    ON prenda (empresa_id, estado)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX ux_variante_barras
    ON variante (empresa_id, codigo_barras)
    WHERE codigo_barras IS NOT NULL;

CREATE INDEX ix_variante_prenda
    ON variante (empresa_id, prenda_id);

CREATE INDEX ix_precio_historial_variante_fecha
    ON precio_historial (empresa_id, variante_id, vigente_desde DESC);

CREATE INDEX ix_inventario_sucursal
    ON inventario (empresa_id, sucursal_id);

CREATE INDEX ix_inventario_bajo_minimo
    ON inventario (empresa_id, sucursal_id)
    WHERE stock_disponible <= stock_minimo;

CREATE INDEX ix_movimiento_variante_fecha
    ON movimiento_inventario (empresa_id, variante_id, ocurrido_en DESC);

CREATE INDEX ix_movimiento_sucursal_fecha
    ON movimiento_inventario (empresa_id, sucursal_id, ocurrido_en DESC);

CREATE INDEX ix_transferencia_estado
    ON transferencia_inventario (empresa_id, estado);

CREATE INDEX ix_reserva_usuario_estado
    ON reserva (empresa_id, usuario_id, estado);

CREATE UNIQUE INDEX ux_carrito_activo_usuario
    ON carrito (empresa_id, usuario_id)
    WHERE estado = 'activo' AND usuario_id IS NOT NULL;

CREATE UNIQUE INDEX ux_carrito_activo_sesion
    ON carrito (empresa_id, sesion_anonima)
    WHERE estado = 'activo' AND sesion_anonima IS NOT NULL;

CREATE INDEX ix_venta_empresa_fecha
    ON venta (empresa_id, fecha_hora DESC);

CREATE INDEX ix_venta_empresa_estado
    ON venta (empresa_id, estado);

CREATE INDEX ix_venta_usuario
    ON venta (empresa_id, usuario_id);

CREATE INDEX ix_venta_sucursal_fecha
    ON venta (empresa_id, sucursal_id, fecha_hora DESC);

CREATE UNIQUE INDEX ux_venta_qr_nonce
    ON venta (empresa_id, qr_nonce)
    WHERE qr_nonce IS NOT NULL;

CREATE INDEX ix_venta_detalle_variante
    ON venta_detalle (empresa_id, variante_id);

CREATE INDEX ix_pago_venta_estado
    ON pago (empresa_id, venta_id, estado);

CREATE INDEX ix_cambio_venta
    ON cambio_prenda (empresa_id, venta_id);

CREATE INDEX ix_cambio_detalle_venta_detalle
    ON cambio_detalle (empresa_id, venta_detalle_id);

CREATE INDEX ix_dispositivo_sucursal
    ON dispositivo (empresa_id, sucursal_id);

CREATE UNIQUE INDEX ux_operacion_nonce
    ON operacion_pendiente (empresa_id, dispositivo_id, nonce);

CREATE INDEX ix_operacion_estado
    ON operacion_pendiente (empresa_id, estado, creada_en);

CREATE INDEX ix_operacion_dispositivo
    ON operacion_pendiente (empresa_id, dispositivo_id, creada_en DESC);

CREATE UNIQUE INDEX ux_operacion_venta
    ON operacion_pendiente (empresa_id, venta_id)
    WHERE venta_id IS NOT NULL;

CREATE INDEX ix_resolucion_operacion
    ON resolucion_conflicto (empresa_id, operacion_id);

CREATE INDEX ix_direccion_usuario
    ON direccion_cliente (empresa_id, usuario_id)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX ux_direccion_principal
    ON direccion_cliente (empresa_id, usuario_id)
    WHERE es_principal AND deleted_at IS NULL;

CREATE INDEX ix_envio_venta
    ON envio (empresa_id, venta_id);

CREATE UNIQUE INDEX ux_envio_tracking
    ON envio (empresa_id, tracking)
    WHERE tracking IS NOT NULL;

CREATE INDEX ix_cupon_uso_cupon
    ON cupon_uso (empresa_id, cupon_id);

CREATE INDEX ix_cupon_uso_usuario
    ON cupon_uso (empresa_id, usuario_id, usado_en DESC);

CREATE INDEX ix_venta_historial_venta
    ON venta_estado_historial (empresa_id, venta_id, ocurrido_en DESC);

CREATE INDEX ix_prediccion_categoria_periodo
    ON prediccion_demanda (empresa_id, categoria_id, periodo);

CREATE INDEX ix_segmento_usuario
    ON segmento_cliente (empresa_id, usuario_id);

CREATE UNIQUE INDEX ux_modelo_global
    ON modelo_ml (nombre, version)
    WHERE empresa_id IS NULL;

CREATE INDEX ix_consulta_empresa_fecha
    ON consulta_ia_log (empresa_id, ocurrido_en DESC);

CREATE INDEX ix_consulta_parametros_gin
    ON consulta_ia_log USING gin (parametros_json);

CREATE INDEX ix_verificacion_correo_usuario
    ON verificacion_correo (empresa_id, usuario_id, expira_en DESC)
    WHERE verificado_en IS NULL;

CREATE INDEX ix_prenda_recurso_prenda
    ON prenda_recurso (empresa_id, prenda_id, tipo, orden)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX ux_prenda_recurso_principal
    ON prenda_recurso (empresa_id, prenda_id, tipo)
    WHERE es_principal AND deleted_at IS NULL;

CREATE INDEX ix_avatar_cliente_usuario
    ON avatar_cliente (empresa_id, usuario_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_medida_corporal_avatar
    ON medida_corporal (empresa_id, avatar_id);

CREATE INDEX ix_prenda_ar_prenda
    ON prenda_ar (empresa_id, prenda_id)
    WHERE activo;

CREATE INDEX ix_sesion_prueba_virtual_usuario
    ON sesion_prueba_virtual (empresa_id, usuario_id, iniciada_en DESC);

CREATE INDEX ix_reporte_exportado_empresa_fecha
    ON reporte_exportado (empresa_id, generado_en DESC);

CREATE INDEX ix_reserva_expiracion
    ON reserva (empresa_id, expira_en)
    WHERE estado IN ('activa', 'confirmada');

CREATE INDEX ix_reserva_dispositivo_estado
    ON reserva (empresa_id, dispositivo_id, estado)
    WHERE dispositivo_id IS NOT NULL;

CREATE INDEX ix_reserva_historial
    ON reserva_estado_historial (empresa_id, reserva_id, ocurrido_en DESC);
