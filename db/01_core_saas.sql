CREATE TABLE empresa (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre varchar(120) NOT NULL,
    slug citext NOT NULL UNIQUE,
    nit varchar(20) NOT NULL UNIQUE,
    correo citext NOT NULL,
    telefono varchar(20),
    direccion varchar(200),
    estado varchar(20) NOT NULL DEFAULT 'activa'
        CHECK (estado IN ('pendiente_plan', 'activa', 'suspendida', 'cancelada')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE plan (
    id smallserial PRIMARY KEY,
    codigo varchar(20) NOT NULL UNIQUE,
    nombre varchar(60) NOT NULL,
    precio_mensual numeric(12,2) NOT NULL DEFAULT 0 CHECK (precio_mensual >= 0),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE plan_limite (
    id bigserial PRIMARY KEY,
    plan_id smallint NOT NULL REFERENCES plan(id) ON DELETE CASCADE,
    recurso varchar(40) NOT NULL,
    limite integer CHECK (limite IS NULL OR limite >= 0),
    UNIQUE (plan_id, recurso)
);

CREATE TABLE suscripcion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    plan_id smallint NOT NULL REFERENCES plan(id),
    estado varchar(20) NOT NULL DEFAULT 'prueba'
        CHECK (estado IN ('prueba', 'activa', 'mora', 'suspendida', 'cancelada')),
    fecha_inicio date NOT NULL,
    fecha_fin date,
    renovacion_auto boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    CHECK (fecha_fin IS NULL OR fecha_fin > fecha_inicio)
);

CREATE TABLE pago_suscripcion (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    suscripcion_id uuid NOT NULL,
    monto numeric(12,2) NOT NULL CHECK (monto > 0),
    moneda char(3) NOT NULL DEFAULT 'BOB',
    metodo varchar(30) NOT NULL
        CHECK (metodo IN ('efectivo', 'tarjeta', 'qr', 'pasarela', 'transferencia')),
    referencia varchar(100),
    estado varchar(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'completado', 'fallido', 'reembolsado')),
    pagado_en timestamptz,
    periodo_inicio date NOT NULL,
    periodo_fin date NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, suscripcion_id)
        REFERENCES suscripcion(empresa_id, id) ON DELETE CASCADE,
    CHECK (periodo_fin > periodo_inicio)
);
