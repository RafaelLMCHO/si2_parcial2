CREATE TABLE categoria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(100) NOT NULL,
    categoria_padre_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre),
    FOREIGN KEY (empresa_id, categoria_padre_id)
        REFERENCES categoria(empresa_id, id)
);

CREATE TABLE temporada (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(80) NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre),
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin > fecha_inicio)
);

CREATE TABLE coleccion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(80) NOT NULL,
    anio smallint CHECK (anio IS NULL OR anio BETWEEN 1900 AND 2200),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre)
);

CREATE TABLE proveedor (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(120) NOT NULL,
    nit varchar(20) NOT NULL,
    correo citext,
    telefono varchar(20),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nit)
);

CREATE TABLE color (
    id smallserial PRIMARY KEY,
    nombre varchar(40) NOT NULL UNIQUE,
    hex char(7)
);

CREATE TABLE talla (
    id smallserial PRIMARY KEY,
    nombre varchar(20) NOT NULL UNIQUE,
    orden smallint
);

CREATE TABLE prenda (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    categoria_id uuid NOT NULL,
    temporada_id uuid,
    coleccion_id uuid,
    proveedor_id uuid,
    codigo varchar(50) NOT NULL,
    nombre varchar(160) NOT NULL,
    descripcion text,
    marca varchar(80),
    genero varchar(20) NOT NULL DEFAULT 'unisex'
        CHECK (genero IN ('mujer', 'hombre', 'nino', 'unisex')),
    precio_base numeric(12,2) NOT NULL DEFAULT 0 CHECK (precio_base >= 0),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    modelo_3d_url varchar(255),
    imagen_url varchar(255),
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'inactiva', 'descontinuada')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, codigo),
    FOREIGN KEY (empresa_id, categoria_id)
        REFERENCES categoria(empresa_id, id),
    FOREIGN KEY (empresa_id, temporada_id)
        REFERENCES temporada(empresa_id, id),
    FOREIGN KEY (empresa_id, coleccion_id)
        REFERENCES coleccion(empresa_id, id),
    FOREIGN KEY (empresa_id, proveedor_id)
        REFERENCES proveedor(empresa_id, id)
);

CREATE TABLE prenda_recurso (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    prenda_id uuid NOT NULL,
    tipo varchar(20) NOT NULL
        CHECK (tipo IN ('imagen', 'modelo_3d', 'textura', 'video')),
    url varchar(255) NOT NULL,
    mime_type varchar(80),
    orden smallint NOT NULL DEFAULT 0,
    es_principal boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id) ON DELETE CASCADE
);

CREATE TABLE catalogo_version (
    empresa_id uuid PRIMARY KEY REFERENCES empresa(id) ON DELETE CASCADE,
    version bigint NOT NULL DEFAULT 1 CHECK (version > 0),
    actualizado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE variante (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    prenda_id uuid NOT NULL,
    color_id smallint NOT NULL REFERENCES color(id),
    talla_id smallint NOT NULL REFERENCES talla(id),
    sku varchar(60) NOT NULL,
    codigo_barras varchar(80),
    precio_venta numeric(12,2) NOT NULL CHECK (precio_venta >= 0),
    costo numeric(12,2) NOT NULL DEFAULT 0 CHECK (costo >= 0),
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'inactiva')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, sku),
    UNIQUE (empresa_id, prenda_id, color_id, talla_id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id) ON DELETE CASCADE
);

CREATE TABLE precio_historial (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    variante_id uuid NOT NULL,
    sucursal_id uuid,
    precio_anterior numeric(12,2) NOT NULL CHECK (precio_anterior >= 0),
    precio_nuevo numeric(12,2) NOT NULL CHECK (precio_nuevo >= 0),
    motivo varchar(120),
    creado_por uuid NOT NULL,
    vigente_desde timestamptz NOT NULL DEFAULT now(),
    vigente_hasta timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id),
    FOREIGN KEY (empresa_id, creado_por)
        REFERENCES usuario(empresa_id, id),
    CHECK (vigente_hasta IS NULL OR vigente_hasta > vigente_desde)
);
