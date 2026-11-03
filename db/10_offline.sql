CREATE TABLE operacion_pendiente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    dispositivo_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    venta_id uuid,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN ('venta_offline', 'pago_offline', 'devolucion_offline', 'ajuste_stock')),
    payload jsonb NOT NULL,
    firma varchar(255),
    nonce varchar(100) NOT NULL,
    idempotency_key varchar(100) NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'procesando', 'aplicada', 'rechazada', 'conflicto')),
    intentos integer NOT NULL DEFAULT 0 CHECK (intentos >= 0),
    ultimo_error text,
    creada_en timestamptz NOT NULL DEFAULT now(),
    procesada_en timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, idempotency_key),
    FOREIGN KEY (empresa_id, dispositivo_id)
        REFERENCES dispositivo(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id)
);

CREATE TABLE resolucion_conflicto (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    operacion_id uuid NOT NULL,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN ('stock_insuficiente', 'precio_cambiado', 'duplicado', 'otro')),
    decision varchar(30) NOT NULL
        CHECK (decision IN ('rechazar', 'ajustar', 'aceptar', 'revision')),
    detalle jsonb,
    resuelto_por uuid NOT NULL,
    resuelto_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, operacion_id)
        REFERENCES operacion_pendiente(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, resuelto_por)
        REFERENCES usuario(empresa_id, id)
);
