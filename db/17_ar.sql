CREATE TABLE avatar_cliente (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    nombre varchar(80) NOT NULL DEFAULT 'Mi avatar',
    modelo_url varchar(255),
    altura_cm numeric(5,2) CHECK (altura_cm IS NULL OR altura_cm > 0),
    peso_kg numeric(5,2) CHECK (peso_kg IS NULL OR peso_kg > 0),
    tono_piel varchar(30),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id) ON DELETE CASCADE
);

CREATE TABLE medida_corporal (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    avatar_id uuid NOT NULL,
    tipo varchar(30) NOT NULL
        CHECK (tipo IN (
            'busto', 'cintura', 'cadera', 'hombro', 'cuello',
            'largo_manga', 'largo_pierna', 'muslo', 'rodilla'
        )),
    valor_cm numeric(6,2) NOT NULL CHECK (valor_cm > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, avatar_id, tipo),
    FOREIGN KEY (empresa_id, avatar_id)
        REFERENCES avatar_cliente(empresa_id, id) ON DELETE CASCADE
);

CREATE TABLE prenda_ar (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    prenda_id uuid NOT NULL,
    variante_id uuid,
    modelo_url varchar(255) NOT NULL,
    textura_url varchar(255),
    puntos_ajuste jsonb,
    talla_referencia varchar(10),
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id) ON DELETE CASCADE
);

CREATE TABLE sesion_prueba_virtual (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL,
    avatar_id uuid NOT NULL,
    prenda_id uuid NOT NULL,
    variante_id uuid,
    estado varchar(20) NOT NULL DEFAULT 'iniciada'
        CHECK (estado IN ('iniciada', 'completada', 'abandonada', 'fallida')),
    resultado_url varchar(255),
    iniciada_en timestamptz NOT NULL DEFAULT now(),
    finalizada_en timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, avatar_id)
        REFERENCES avatar_cliente(empresa_id, id),
    FOREIGN KEY (empresa_id, prenda_id)
        REFERENCES prenda(empresa_id, id),
    FOREIGN KEY (empresa_id, variante_id)
        REFERENCES variante(empresa_id, id),
    CHECK (finalizada_en IS NULL OR finalizada_en >= iniciada_en)
);
