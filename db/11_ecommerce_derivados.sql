CREATE TABLE envio (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    direccion_id uuid NOT NULL,
    transportista varchar(100),
    tracking varchar(100),
    estado varchar(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'preparando', 'enviado', 'en_transito', 'entregado', 'devuelto', 'cancelado')),
    costo numeric(12,2) NOT NULL DEFAULT 0 CHECK (costo >= 0),
    fecha_estimada date,
    enviado_en timestamptz,
    entregado_en timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, direccion_id)
        REFERENCES direccion_cliente(empresa_id, id),
    CHECK (entregado_en IS NULL OR enviado_en IS NULL OR entregado_en >= enviado_en)
);

CREATE TABLE cupon_uso (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    cupon_id uuid NOT NULL,
    venta_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    usado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, cupon_id, venta_id),
    FOREIGN KEY (empresa_id, cupon_id)
        REFERENCES cupon(empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
);
