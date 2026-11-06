-- Migración cu17_cu24_ajustes
-- a) Ampliar CHECK de reserva.estado
ALTER TABLE reserva DROP CONSTRAINT IF EXISTS reserva_estado_check;
ALTER TABLE reserva ALTER COLUMN estado SET DEFAULT 'pendiente_preparacion';
ALTER TABLE reserva ADD CONSTRAINT reserva_estado_check
    CHECK (estado IN (
        'pendiente_preparacion','preparada','incidencia_stock',
        'activa','confirmada','expirada','cancelada','convertida'
    ));

-- b) Agregar campos a reserva
ALTER TABLE reserva ADD COLUMN IF NOT EXISTS codigo varchar(20);
ALTER TABLE reserva ADD COLUMN IF NOT EXISTS fecha_visita timestamptz;
ALTER TABLE reserva ADD COLUMN IF NOT EXISTS probador varchar(30);
ALTER TABLE reserva ADD COLUMN IF NOT EXISTS cliente_uuid uuid;

-- Actualizar existing rows con codigo y fecha_visita provisional
UPDATE reserva SET codigo = 'LEGACY-' || substring(id::text, 1, 6) WHERE codigo IS NULL;
UPDATE reserva SET fecha_visita = created_at WHERE fecha_visita IS NULL;

ALTER TABLE reserva ALTER COLUMN codigo SET NOT NULL;
ALTER TABLE reserva ALTER COLUMN fecha_visita SET NOT NULL;  -- para nuevas reservas

-- Intentar quitar NOT NULL si ya existe (puede fallar si no hay datos legacy)
-- Para rows existentes sin fecha_visita, se usa el default
-- (No se puede hacer esto atómico sin conocer si hay datos, dejamos la restricción a nivel de servicio)

CREATE UNIQUE INDEX IF NOT EXISTS uq_reserva_empresa_codigo ON reserva (empresa_id, codigo);
CREATE UNIQUE INDEX IF NOT EXISTS uq_reserva_empresa_cliente_uuid ON reserva (empresa_id, cliente_uuid) WHERE cliente_uuid IS NOT NULL;

-- c) Agregar ubicacion a inventario
ALTER TABLE inventario ADD COLUMN IF NOT EXISTS ubicacion varchar(60);

-- d) Ampliar CHECK de venta.estado  
ALTER TABLE venta DROP CONSTRAINT IF EXISTS venta_estado_check;
ALTER TABLE venta ADD CONSTRAINT venta_estado_check
    CHECK (estado IN (
        'pendiente_pago', 'pagada', 'preparando', 'enviada', 'entregada',
        'completada', 'anulada', 'devuelta', 'pendiente_sync', 'pago_fallido'
    ));

-- e) Agregar campos de cliente y sucursal a venta
ALTER TABLE venta ADD COLUMN IF NOT EXISTS cliente_nombre varchar(120);
ALTER TABLE venta ADD COLUMN IF NOT EXISTS cliente_documento varchar(30);

-- f) Tabla stripe_evento
CREATE TABLE IF NOT EXISTS stripe_evento (
    id varchar(100) PRIMARY KEY,
    tipo varchar(60) NOT NULL,
    procesado_en timestamptz NOT NULL DEFAULT now()
);

-- g) Verificar/crear particiones futuras de movimiento_inventario
DO $$
DECLARE
    d date := DATE '2026-01-01';
BEGIN
    WHILE d < DATE '2029-01-01' LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF movimiento_inventario FOR VALUES FROM (%L) TO (%L)',
            'movimiento_inventario_' || to_char(d, 'YYYY_MM'),
            d,
            d + interval '1 month'
        );
        d := d + interval '1 month';
    END LOOP;
END $$;

-- h) Nuevos permisos
INSERT INTO permiso (codigo, descripcion, modulo) VALUES
    ('stock.ajustar', 'Ajustar stock de inventario', 'inventario'),
    ('stock.transferir', 'Transferir stock entre sucursales', 'inventario'),
    ('reservas.crear', 'Crear reservas', 'reservas'),
    ('reservas.ver', 'Consultar reservas', 'reservas'),
    ('reservas.cancelar', 'Cancelar reservas', 'reservas'),
    ('reservas.preparar', 'Preparar reservas en sucursal', 'reservas'),
    ('carrito.gestionar', 'Gestionar carrito de compras', 'carrito'),
    ('pagos.procesar', 'Procesar pagos', 'pagos')
ON CONFLICT (codigo) DO NOTHING;

-- Asignar permisos a rol administrador (empresa demo)
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111201', p.id
FROM permiso p
WHERE p.codigo IN (
    'inventario.ver', 'stock.ajustar', 'stock.transferir',
    'reservas.ver'
)
ON CONFLICT DO NOTHING;

-- Asignar permisos a rol cajero (empresa demo)
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111202', p.id
FROM permiso p
WHERE p.codigo IN (
    'inventario.ver', 'ventas.crear', 'pagos.procesar'
)
ON CONFLICT DO NOTHING;

-- Asignar permisos a rol cliente (empresa demo)
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111203', p.id
FROM permiso p
WHERE p.codigo IN (
    'reservas.crear', 'reservas.ver', 'reservas.cancelar',
    'carrito.gestionar', 'pagos.procesar'
)
ON CONFLICT DO NOTHING;

-- Rol encargado (crear si no existe)
INSERT INTO rol (id, empresa_id, nombre, descripcion, es_global)
VALUES (
    '11111111-1111-1111-1111-111111111204',
    '11111111-1111-1111-1111-111111111111',
    'encargado',
    'Encargado de sucursal',
    false
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111204', p.id
FROM permiso p
WHERE p.codigo IN (
    'inventario.ver', 'stock.ajustar', 'stock.transferir',
    'reservas.ver', 'reservas.cancelar', 'reservas.preparar'
)
ON CONFLICT DO NOTHING;

-- Usuario encargado demo
INSERT INTO usuario (
    id, empresa_id, rol_id, sucursal_id,
    nombre, correo, password_hash, estado, email_verificado
)
VALUES (
    '11111111-1111-1111-1111-111111111303',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111204',
    '11111111-1111-1111-1111-111111111101',
    'Encargado Demo',
    'encargado@demo.test',
    crypt('Encargado123!', gen_salt('bf', 10)),
    'activo',
    true
)
ON CONFLICT (id) DO NOTHING;

-- Cajero usuario demo
INSERT INTO usuario (
    id, empresa_id, rol_id, sucursal_id,
    nombre, correo, password_hash, estado, email_verificado
)
VALUES (
    '11111111-1111-1111-1111-111111111304',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111202',
    '11111111-1111-1111-1111-111111111101',
    'Cajero Demo',
    'cajero@demo.test',
    crypt('Cajero123!', gen_salt('bf', 10)),
    'activo',
    true
)
ON CONFLICT (id) DO NOTHING;

-- Marcar email_verificado en usuarios demo existentes
UPDATE usuario SET email_verificado = true 
WHERE id IN (
    '11111111-1111-1111-1111-111111111301',
    '11111111-1111-1111-1111-111111111302'
);

-- Tabla envio (si no existe)
CREATE TABLE IF NOT EXISTS envio (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    venta_id uuid NOT NULL,
    direccion_id uuid,
    tipo varchar(20) NOT NULL DEFAULT 'envio'
        CHECK (tipo IN ('envio', 'recojo')),
    costo numeric(12,2) NOT NULL DEFAULT 0 CHECK (costo >= 0),
    estado varchar(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'preparando', 'enviado', 'entregado', 'cancelado')),
    sucursal_recojo_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, id),
    UNIQUE (empresa_id, venta_id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id) ON DELETE CASCADE
);

-- cupon_uso (si no existe)
CREATE TABLE IF NOT EXISTS cupon_uso (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    cupon_id uuid NOT NULL,
    usuario_id uuid NOT NULL,
    venta_id uuid NOT NULL,
    descuento_aplicado numeric(12,2) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (empresa_id, cupon_id, usuario_id),
    UNIQUE (empresa_id, id),
    FOREIGN KEY (empresa_id, cupon_id)
        REFERENCES cupon(empresa_id, id),
    FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuario(empresa_id, id),
    FOREIGN KEY (empresa_id, venta_id)
        REFERENCES venta(empresa_id, id)
);
