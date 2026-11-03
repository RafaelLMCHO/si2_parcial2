CREATE TABLE rol (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    nombre varchar(50) NOT NULL,
    descripcion text,
    es_global boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, nombre),
    CHECK ((es_global AND empresa_id IS NULL) OR ((NOT es_global) AND empresa_id IS NOT NULL))
);

CREATE TABLE permiso (
    id smallserial PRIMARY KEY,
    codigo varchar(80) NOT NULL UNIQUE,
    descripcion text NOT NULL,
    modulo varchar(40) NOT NULL
);

CREATE TABLE rol_permiso (
    rol_id uuid NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
    permiso_id smallint NOT NULL REFERENCES permiso(id) ON DELETE CASCADE,
    PRIMARY KEY (rol_id, permiso_id)
);

CREATE TABLE usuario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    rol_id uuid NOT NULL REFERENCES rol(id),
    sucursal_id uuid,
    nombre varchar(120) NOT NULL,
    correo citext NOT NULL,
    password_hash text NOT NULL,
    telefono varchar(20),
    email_verificado boolean NOT NULL DEFAULT false,
    email_verificado_en timestamptz,
    estado varchar(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    ultimo_acceso timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, correo),
    FOREIGN KEY (empresa_id, sucursal_id)
        REFERENCES sucursal(empresa_id, id)
);

CREATE TABLE sesion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    refresh_token_hash text NOT NULL UNIQUE,
    ip_origen inet,
    user_agent text,
    created_at timestamptz NOT NULL DEFAULT now(),
    expira_en timestamptz NOT NULL,
    revocado_en timestamptz,
    CHECK (expira_en > created_at)
);

CREATE TABLE verificacion_correo (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    token_hash text NOT NULL UNIQUE,
    expira_en timestamptz NOT NULL,
    verificado_en timestamptz,
    creado_en timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id) ON DELETE CASCADE,
    CHECK (expira_en > creado_en)
);
