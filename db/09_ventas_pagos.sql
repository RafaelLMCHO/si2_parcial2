CREATE TABLE venta (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    numero varchar(30) NOT NULL,
    sucursal_id uuid,
    usuario_id uuid,
    cajero_id uuid,
    canal varchar(20) NOT NULL
        CHECK (canal IN ('POS', 'WEB', 'OFFLINE')),
    fecha_hora timestamptz NOT NULL DEFAULT now(),
    fecha_hora_cliente timestamptz,
    fecha_recepcion_servidor timestamptz NOT NULL DEFAULT now(),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    subtotal numeric(12,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    descuento numeric(12,2) NOT NULL DEFAULT 0 CHECK (descuento >= 0),
    impuesto numeric(12,2) NOT NULL DEFAULT 0 CHECK (impuesto >= 0),
    total numeric(12,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    estado varchar(30) NOT NULL DEFAULT 'pendiente_pago'
        CHECK (estado IN (
            'pendiente_pago', 'pagada', 'preparando', 'enviada', 'entregada',
            'completada', 'anulada', 'devuelta', 'pendiente_sync'
        )),
    direccion_id uuid,
    cupon_id uuid,
    idempotency_key varchar(100) NOT NULL,
    firma_qr varchar(255),
    qr_nonce varchar(100),
    firma_algoritmo varchar(20)
        CHECK (firma_algoritmo IS NULL OR firma_algoritmo IN ('HMAC-SHA256', 'Ed25519')),
    firma_version smallint NOT NULL DEFAULT 1,
    firmado_en timestamptz,
    dispositivo_id uuid,
    notas text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, numero),
    UNIQUE (empresa_id, idempotency_key),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, cajero_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, direccion_id)
        REFERENCES direccion_cliente(empresa_id, id),
    FOREIGN KEY (empresa_id, cupon_id)
        REFERENCES cupon(empresa_id, id),
    FOREIGN KEY (empresa_id, dispositivo_id)
        REFERENCES dispositivo(empresa_id, id),
    CHECK (total = subtotal - descuento + impuesto),
    CHECK (descuento <= subtotal),
    CHECK (canal <> 'POS' OR sucursal_id IS NOT NULL),
    CHECK (canal <> 'POS' OR cajero_id IS NOT NULL)
);

CREATE TABLE venta_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    precio_lista numeric(12,2) NOT NULL CHECK (precio_lista >= 0),
    precio_unitario numeric(12,2) NOT NULL CHECK (precio_unitario >= 0),
    descuento_linea numeric(12,2) NOT NULL DEFAULT 0 CHECK (descuento_linea >= 0),
    subtotal numeric(12,2) NOT NULL CHECK (subtotal >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, venta_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    CHECK (subtotal = (cantidad * precio_unitario) - descuento_linea)
);

CREATE TABLE pago (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    monto numeric(12,2) NOT NULL CHECK (monto > 0),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    metodo varchar(30) NOT NULL
        CHECK (metodo IN ('efectivo', 'tarjeta', 'qr', 'pasarela', 'transferencia', 'vale')),
    pasarela_id varchar(100),
    idempotency_key varchar(100) NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'completado'
        CHECK (estado IN ('pendiente', 'completado', 'fallido', 'reembolsado')),
    referencia varchar(100),
    pagado_en timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, idempotency_key),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE
);

CREATE TABLE cambio_prenda (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    motivo varchar(200) NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'solicitado'
        CHECK (estado IN ('solicitado', 'aprobado', 'rechazado', 'completado', 'cancelado')),
    diferencia numeric(12,2) NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
);

CREATE TABLE cambio_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    cambio_id uuid NOT NULL,
    venta_detalle_id uuid NOT NULL,
    variante_nueva_id uuid,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    diferencia_precio numeric(12,2) NOT NULL DEFAULT 0,
    UNIQUE (empresa_id, cambio_id, venta_detalle_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, cambio_id)
        REFERENCES cambio_prenda(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, venta_detalle_id)
        REFERENCES venta_detalle(empresa_id, id),
    FOREIGN KEY (empresa_id, variante_nueva_id)
        REFERENCES variante(empresa_id, id)
);

CREATE TABLE venta_estado_historial (
    id bigserial PRIMARY KEY,
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    estado_anterior varchar(30),
    estado_nuevo varchar(30) NOT NULL,
    motivo varchar(200),
    usuario_id uuid,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
);
