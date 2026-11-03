INSERT INTO plan (codigo, nombre, precio_mensual)
VALUES
    ('basico', 'Básico', 199.00),
    ('profesional', 'Profesional', 499.00)
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO plan_limite (plan_id, recurso, limite)
SELECT p.id, v.recurso, v.limite
FROM plan p
JOIN (VALUES
    ('basico', 'sucursales', 2),
    ('basico', 'usuarios', 5),
    ('basico', 'productos', 500),
    ('basico', 'consultas_ia_mes', 0),
    ('profesional', 'sucursales', 10),
    ('profesional', 'usuarios', 50),
    ('profesional', 'productos', 5000),
    ('profesional', 'consultas_ia_mes', 1000)
) AS v(codigo, recurso, limite) ON v.codigo = p.codigo
ON CONFLICT (plan_id, recurso) DO NOTHING;

INSERT INTO permiso (codigo, descripcion, modulo)
VALUES
    ('ventas.crear', 'Crear ventas', 'ventas'),
    ('ventas.ver', 'Consultar ventas', 'ventas'),
    ('ventas.anular', 'Anular ventas', 'ventas'),
    ('ventas.devolver', 'Registrar devoluciones y cambios', 'ventas'),
    ('inventario.ver', 'Consultar inventario', 'inventario'),
    ('inventario.ajustar', 'Ajustar inventario', 'inventario'),
    ('inventario.transferir', 'Transferir inventario entre sucursales', 'inventario'),
    ('catalogo.ver', 'Consultar catálogo', 'catalogo'),
    ('catalogo.crear', 'Crear productos y variantes', 'catalogo'),
    ('catalogo.editar', 'Editar productos y variantes', 'catalogo'),
    ('catalogo.eliminar', 'Desactivar productos y variantes', 'catalogo'),
    ('usuarios.ver', 'Consultar usuarios', 'usuarios'),
    ('usuarios.crear', 'Crear usuarios', 'usuarios'),
    ('usuarios.editar', 'Editar usuarios', 'usuarios'),
    ('usuarios.desactivar', 'Desactivar usuarios', 'usuarios'),
    ('reportes.ver', 'Consultar reportes', 'reportes'),
    ('ia.consultar', 'Consultar asistente de IA', 'ia'),
    ('configuracion.editar', 'Editar configuración del tenant', 'configuracion'),
    ('suscripcion.gestionar', 'Gestionar suscripción y plan', 'suscripcion'),
    ('auditoria.ver', 'Consultar auditoría', 'auditoria')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO empresa (id, nombre, slug, nit, correo, telefono)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'FashionStore Demo',
    'demo',
    'DEMO-001',
    'demo@fashionstore.test',
    '+591 70000000'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO rol (id, empresa_id, nombre, descripcion, es_global)
VALUES
    ('00000000-0000-0000-0000-000000000001', NULL, 'superadmin', 'Administrador global de la plataforma', true),
    ('11111111-1111-1111-1111-111111111201', '11111111-1111-1111-1111-111111111111', 'administrador', 'Acceso total al tenant', false),
    ('11111111-1111-1111-1111-111111111202', '11111111-1111-1111-1111-111111111111', 'cajero', 'Operación de ventas', false),
    ('11111111-1111-1111-1111-111111111203', '11111111-1111-1111-1111-111111111111', 'cliente', 'Cliente de la tienda en línea', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111201', id
FROM permiso
ON CONFLICT DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111202', id
FROM permiso
WHERE codigo IN ('ventas.crear', 'ventas.ver', 'inventario.ver', 'catalogo.ver')
ON CONFLICT DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT '11111111-1111-1111-1111-111111111203', id
FROM permiso
WHERE codigo IN ('catalogo.ver', 'ventas.ver')
ON CONFLICT DO NOTHING;

INSERT INTO ciudad (nombre, departamento)
VALUES
    ('Santa Cruz de la Sierra', 'Santa Cruz'),
    ('La Paz', 'La Paz'),
    ('Cochabamba', 'Cochabamba'),
    ('Sucre', 'Chuquisaca'),
    ('Oruro', 'Oruro'),
    ('Tarija', 'Tarija'),
    ('Potosí', 'Potosí'),
    ('Trinidad', 'Beni')
ON CONFLICT (nombre, departamento) DO NOTHING;

INSERT INTO color (nombre, hex)
VALUES
    ('Negro', '#000000'),
    ('Blanco', '#FFFFFF'),
    ('Azul Marino', '#1B2A4A'),
    ('Rojo', '#C0392B'),
    ('Beige', '#D9C7A7'),
    ('Gris', '#7F8C8D'),
    ('Verde Oliva', '#6B7A3A'),
    ('Rosado', '#E8A0B4')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO talla (nombre, orden)
VALUES
    ('XS', 1),
    ('S', 2),
    ('M', 3),
    ('L', 4),
    ('XL', 5),
    ('XXL', 6),
    ('36', 7),
    ('38', 8),
    ('40', 9),
    ('42', 10)
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO suscripcion (id, empresa_id, plan_id, estado, fecha_inicio)
SELECT
    '11111111-1111-1111-1111-111111111c01',
    '11111111-1111-1111-1111-111111111111',
    p.id,
    'activa',
    CURRENT_DATE
FROM plan p
WHERE p.codigo = 'profesional'
ON CONFLICT (id) DO NOTHING;

INSERT INTO sucursal (
    id,
    empresa_id,
    ciudad_id,
    nombre,
    direccion,
    telefono,
    es_matriz,
    estado
)
SELECT
    '11111111-1111-1111-1111-111111111101',
    '11111111-1111-1111-1111-111111111111',
    c.id,
    'Sucursal Centro',
    'Av. Monseñor Rivero 100',
    '+591 70000000',
    true,
    'activa'
FROM ciudad c
WHERE c.nombre = 'Santa Cruz de la Sierra'
  AND c.departamento = 'Santa Cruz'
ON CONFLICT (id) DO NOTHING;

INSERT INTO usuario (
    id,
    empresa_id,
    rol_id,
    sucursal_id,
    nombre,
    correo,
    password_hash,
    estado
)
VALUES
    (
        '00000000-0000-0000-0000-000000000002',
        NULL,
        '00000000-0000-0000-0000-000000000001',
        NULL,
        'Superadmin',
        'superadmin@fashionstore.test',
        crypt('Superadmin123!', gen_salt('bf', 10)),
        'activo'
    ),
    (
        '11111111-1111-1111-1111-111111111301',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111201',
        '11111111-1111-1111-1111-111111111101',
        'Administrador Demo',
        'admin@demo.test',
        crypt('Admin123!', gen_salt('bf', 10)),
        'activo'
    ),
    (
        '11111111-1111-1111-1111-111111111302',
        '11111111-1111-1111-1111-111111111111',
        '11111111-1111-1111-1111-111111111203',
        '11111111-1111-1111-1111-111111111101',
        'Cliente Demo',
        'cliente@demo.test',
        crypt('Cliente123!', gen_salt('bf', 10)),
        'activo'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO categoria (id, empresa_id, nombre)
VALUES (
    '11111111-1111-1111-1111-111111111401',
    '11111111-1111-1111-1111-111111111111',
    'Vestidos'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO temporada (id, empresa_id, nombre, fecha_inicio, fecha_fin)
VALUES (
    '11111111-1111-1111-1111-111111111402',
    '11111111-1111-1111-1111-111111111111',
    'Primavera 2026',
    DATE '2026-01-01',
    DATE '2026-12-31'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO coleccion (id, empresa_id, nombre, anio)
VALUES (
    '11111111-1111-1111-1111-111111111403',
    '11111111-1111-1111-1111-111111111111',
    'Esenciales',
    2026
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO proveedor (id, empresa_id, nombre, nit, correo, telefono)
VALUES (
    '11111111-1111-1111-1111-111111111404',
    '11111111-1111-1111-1111-111111111111',
    'Proveedor Demo',
    'PROV-001',
    'proveedor@demo.test',
    '+591 72222222'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO prenda (
    id,
    empresa_id,
    categoria_id,
    temporada_id,
    coleccion_id,
    proveedor_id,
    codigo,
    nombre,
    descripcion,
    marca,
    genero,
    estado
)
VALUES (
    '11111111-1111-1111-1111-111111111501',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111401',
    '11111111-1111-1111-1111-111111111402',
    '11111111-1111-1111-1111-111111111403',
    '11111111-1111-1111-1111-111111111404',
    'FS-VES-001',
    'Vestido midi',
    'Vestido midi de lino',
    'FashionStore',
    'mujer',
    'activa'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO prenda_recurso (
    id,
    empresa_id,
    prenda_id,
    tipo,
    url,
    mime_type,
    orden,
    es_principal
)
VALUES (
    '11111111-1111-1111-1111-111111111502',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111501',
    'imagen',
    'https://cdn.fashionstore.test/demo/vestido-midi.jpg',
    'image/jpeg',
    0,
    true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO variante (
    id,
    empresa_id,
    prenda_id,
    color_id,
    talla_id,
    sku,
    codigo_barras,
    precio_venta,
    costo,
    estado
)
SELECT
    '11111111-1111-1111-1111-111111111601',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111501',
    c.id,
    t.id,
    'FS-VES-001-NEG-M',
    'FS0001',
    100.00,
    50.00,
    'activa'
FROM color c
CROSS JOIN talla t
WHERE c.nombre = 'Negro'
  AND t.nombre = 'M'
ON CONFLICT (id) DO NOTHING;

INSERT INTO inventario (
    id,
    empresa_id,
    variante_id,
    sucursal_id,
    stock_fisico,
    stock_reservado,
    stock_minimo
)
VALUES (
    '11111111-1111-1111-1111-111111111701',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111601',
    '11111111-1111-1111-1111-111111111101',
    10,
    0,
    2
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO dispositivo (
    id,
    empresa_id,
    sucursal_id,
    nombre,
    serial,
    estado
)
VALUES (
    '11111111-1111-1111-1111-111111111801',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111101',
    'POS Demo',
    'POS-DEMO-01',
    'activo'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO direccion_cliente (
    id,
    empresa_id,
    usuario_id,
    etiqueta,
    destinatario,
    telefono,
    linea1,
    ciudad_id,
    es_principal
)
SELECT
    '11111111-1111-1111-1111-111111111901',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111302',
    'Casa',
    'Cliente Demo',
    '+591 71111111',
    'Calle Los Pitones 123',
    c.id,
    true
FROM ciudad c
WHERE c.nombre = 'Santa Cruz de la Sierra'
  AND c.departamento = 'Santa Cruz'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cupon (
    id,
    empresa_id,
    codigo,
    descripcion,
    tipo,
    valor,
    monto_minimo,
    usos_maximos,
    usos_por_usuario,
    fecha_inicio,
    fecha_fin,
    activo
)
VALUES (
    '11111111-1111-1111-1111-111111111a01',
    '11111111-1111-1111-1111-111111111111',
    'BIENVENIDO10',
    '10% de descuento en la primera compra',
    'porcentaje',
    10.00,
    0.00,
    100,
    1,
    now() - interval '1 day',
    now() + interval '30 days',
    true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO venta (
    id,
    empresa_id,
    numero,
    usuario_id,
    canal,
    estado,
    direccion_id,
    idempotency_key,
    moneda
)
VALUES (
    '11111111-1111-1111-1111-111111111b01',
    '11111111-1111-1111-1111-111111111111',
    'V-0001',
    '11111111-1111-1111-1111-111111111302',
    'WEB',
    'pagada',
    '11111111-1111-1111-1111-111111111901',
    'seed-venta-1',
    'BOB'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO venta_detalle (
    id,
    empresa_id,
    venta_id,
    variante_id,
    cantidad,
    precio_lista,
    precio_unitario,
    descuento_linea,
    subtotal
)
VALUES (
    '11111111-1111-1111-1111-111111111b02',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111b01',
    '11111111-1111-1111-1111-111111111601',
    2,
    100.00,
    100.00,
    0.00,
    200.00
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO pago (
    id,
    empresa_id,
    venta_id,
    monto,
    metodo,
    idempotency_key,
    estado,
    referencia
)
VALUES (
    '11111111-1111-1111-1111-111111111b03',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111b01',
    200.00,
    'tarjeta',
    'seed-pago-1',
    'completado',
    'SEED-001'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO modelo_ml (
    id,
    empresa_id,
    nombre,
    version,
    tipo,
    metricas,
    activo
)
VALUES (
    '11111111-1111-1111-1111-111111111e01',
    NULL,
    'demanda',
    '1.0',
    'demanda',
    '{"mae": 5.2}'::jsonb,
    true
)
ON CONFLICT (id) DO NOTHING;
