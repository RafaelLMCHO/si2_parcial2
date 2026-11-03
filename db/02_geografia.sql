CREATE TABLE ciudad (
    id smallserial PRIMARY KEY,
    nombre varchar(80) NOT NULL,
    departamento varchar(80) NOT NULL,
    pais char(2) NOT NULL DEFAULT 'BO',
    UNIQUE (nombre, departamento)
);

CREATE TABLE sucursal (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    ciudad_id smallint NOT NULL REFERENCES ciudad(id),
    nombre varchar(120) NOT NULL,
    direccion varchar(200) NOT NULL,
    telefono varchar(20),
    es_matriz boolean NOT NULL DEFAULT false,
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('activa', 'inactiva')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, nombre)
);
