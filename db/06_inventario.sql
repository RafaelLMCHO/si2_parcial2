CREATE TABLE inventario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    variante_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    stock_fisico integer NOT NULL DEFAULT 0 CHECK (stock_fisico >= 0),
    stock_reservado integer NOT NULL DEFAULT 0 CHECK (stock_reservado >= 0),
    stock_disponible integer GENERATED ALWAYS AS (stock_fisico - stock_reservado) STORED,
    stock_minimo integer NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),
    actualizado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, variante_id, sucursal_id),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id) ON DELETE CASCADE,
    CHECK (stock_reservado <= stock_fisico)
);

CREATE TABLE movimiento_inventario (
    id bigserial,
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    variante_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN (
            'entrada', 'salida', 'ajuste', 'venta', 'devolucion',
            'transferencia_salida', 'transferencia_entrada', 'reserva_liberada'
        )),
    cantidad integer NOT NULL CHECK (cantidad <> 0),
    stock_anterior integer NOT NULL CHECK (stock_anterior >= 0),
    stock_nuevo integer NOT NULL CHECK (stock_nuevo >= 0),
    referencia_tipo varchar(40),
    referencia_id uuid,
    motivo varchar(200),
    usuario_id uuid,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, ocurrido_en),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    CHECK (stock_nuevo = stock_anterior + cantidad)
) PARTITION BY RANGE (ocurrido_en);

DO $$
DECLARE
    d date := DATE '2026-01-01';
BEGIN
    WHILE d < DATE '2028-01-01' LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF movimiento_inventario FOR VALUES FROM (%L) TO (%L)',
            'movimiento_inventario_' || to_char(d, 'YYYY_MM'),
            d,
            d + interval '1 month'
        );
        d := d + interval '1 month';
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS movimiento_inventario_default
    PARTITION OF movimiento_inventario DEFAULT;

CREATE TABLE transferencia_inventario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    origen_id uuid NOT NULL,
    destino_id uuid NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'borrador'
        CHECK (estado IN ('borrador', 'solicitada', 'aprobada', 'en_transito', 'recibida', 'cancelada')),
    solicitada_por uuid NOT NULL,
    aprobada_por uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, origen_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, destino_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, solicitada_por)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, aprobada_por)
        REFERENCES usuario(empresa_id, id),
    CHECK (origen_id <> destino_id)
);

CREATE TABLE transferencia_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    transferencia_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    cantidad_recibida integer NOT NULL DEFAULT 0 CHECK (cantidad_recibida >= 0),
    UNIQUE (empresa_id, transferencia_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, transferencia_id)
        REFERENCES transferencia_inventario(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    CHECK (cantidad_recibida <= cantidad)
);
