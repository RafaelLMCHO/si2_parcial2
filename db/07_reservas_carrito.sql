CREATE TABLE reserva (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    sucursal_id uuid NOT NULL,
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'confirmada', 'expirada', 'cancelada', 'convertida')),
    fecha_visita timestamptz,
    expira_en timestamptz NOT NULL,
    dispositivo_id uuid,
    liberada_en timestamptz,
    motivo_cierre varchar(200),
    observacion text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    CHECK (expira_en > created_at)
);

CREATE TABLE reserva_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    reserva_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    UNIQUE (empresa_id, reserva_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, reserva_id)
        REFERENCES reserva(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id)
);

CREATE TABLE reserva_estado_historial (
    id bigserial PRIMARY KEY,
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    reserva_id uuid NOT NULL,
    estado_anterior varchar(20),
    estado_nuevo varchar(20) NOT NULL,
    motivo varchar(200),
    usuario_id uuid,
    ocurrido_en timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (empresa_id, reserva_id)
        REFERENCES reserva(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id)
);

CREATE TABLE carrito (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid,
    sesion_anonima varchar(100),
    estado varchar(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'convertido', 'abandonado')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    CHECK (usuario_id IS NOT NULL OR sesion_anonima IS NOT NULL)
);

CREATE TABLE carrito_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    carrito_id uuid NOT NULL,
    variante_id uuid NOT NULL,
    cantidad integer NOT NULL CHECK (cantidad > 0),
    precio_unitario numeric(12,2) NOT NULL CHECK (precio_unitario >= 0),
    UNIQUE (empresa_id, carrito_id, variante_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, carrito_id)
        REFERENCES carrito(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id)
);
