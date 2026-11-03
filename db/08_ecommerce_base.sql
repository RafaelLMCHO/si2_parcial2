CREATE TABLE direccion_cliente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    etiqueta varchar(40),
    destinatario varchar(120) NOT NULL,
    telefono varchar(20) NOT NULL,
    linea1 varchar(200) NOT NULL,
    linea2 varchar(200),
    ciudad_id smallint NOT NULL REFERENCES ciudad(id),
    codigo_postal varchar(20),
    referencia text,
    es_principal boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id) ON DELETE CASCADE
);

CREATE TABLE cupon (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    codigo varchar(40) NOT NULL,
    descripcion text,
    tipo varchar(20) NOT NULL
        CHECK (tipo IN ('porcentaje', 'monto_fijo', 'envio_gratis')),
    valor numeric(12,2) NOT NULL CHECK (valor >= 0),
    monto_minimo numeric(12,2) NOT NULL DEFAULT 0 CHECK (monto_minimo >= 0),
    usos_maximos integer CHECK (usos_maximos IS NULL OR usos_maximos > 0),
    usos_por_usuario integer CHECK (usos_por_usuario IS NULL OR usos_por_usuario > 0),
    fecha_inicio timestamptz NOT NULL,
    fecha_fin timestamptz NOT NULL,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, codigo),
    UNIQUE (empresa_id, id),
    CHECK (fecha_fin > fecha_inicio),
    CHECK (tipo <> 'porcentaje' OR valor <= 100)
);

CREATE TABLE dispositivo (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    sucursal_id uuid NOT NULL,
    nombre varchar(100) NOT NULL,
    serial varchar(100) NOT NULL,
    clave_publica text,
    ultima_sync timestamptz,
    catalogo_version bigint NOT NULL DEFAULT 0 CHECK (catalogo_version >= 0),
    estado varchar(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'revocado')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, serial),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id)
);

ALTER TABLE reserva
    ADD CONSTRAINT fk_reserva_dispositivo
    FOREIGN KEY (empresa_id, dispositivo_id)
    REFERENCES dispositivo(empresa_id, id);
