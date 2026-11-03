BEGIN;

-- Empresa demo
INSERT INTO empresa (nombre, slug, nit, correo, telefono, estado)
VALUES ('FashionStore Demo S.R.L.', 'demo', '1234567890', 'contacto@demo.test', '+59170000000', 'activa')
ON CONFLICT (slug) DO UPDATE SET nombre = EXCLUDED.nombre, estado = 'activa', updated_at = now();

-- Plan profesional
INSERT INTO plan (codigo, nombre, precio_mensual, moneda, activo)
VALUES ('profesional', 'Profesional', 499.00, 'BOB', true)
ON CONFLICT (codigo) DO UPDATE SET activo = true;

-- Suscripcion activa
INSERT INTO suscripcion (empresa_id, plan_id, estado, fecha_inicio, fecha_fin)
SELECT e.id, p.id, 'activa', CURRENT_DATE, CURRENT_DATE + INTERVAL '365 days'
FROM empresa e, plan p
WHERE e.slug = 'demo' AND p.codigo = 'profesional'
ON CONFLICT DO NOTHING;

-- Sucursal
INSERT INTO sucursal (empresa_id, nombre, direccion, ciudad_id, estado)
SELECT e.id, 'Sucursal Central', 'Av. Demo 123', c.id, 'activa'
FROM empresa e, ciudad c
WHERE e.slug = 'demo'
ORDER BY c.id
LIMIT 1
ON CONFLICT DO NOTHING;

-- Roles
INSERT INTO rol (empresa_id, nombre, descripcion)
SELECT e.id, r.nombre, r.descripcion
FROM empresa e
CROSS JOIN (VALUES
    ('administrador', 'Administrador de tienda'),
    ('encargado', 'Encargado de tienda'),
    ('cajero', 'Cajero'),
    ('cliente', 'Cliente')
) AS r(nombre, descripcion)
WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

-- Permisos basicos
INSERT INTO permiso (codigo, descripcion, modulo)
VALUES
    ('ventas.ver', 'Ver ventas', 'ventas'),
    ('ventas.crear', 'Crear ventas', 'ventas'),
    ('inventario.ver', 'Ver inventario', 'inventario'),
    ('inventario.gestion', 'Gestionar inventario', 'inventario'),
    ('catalogo.gestion', 'Gestionar catalogo', 'catalogo'),
    ('usuarios.gestion', 'Gestionar usuarios', 'usuarios'),
    ('reportes.ver', 'Ver reportes', 'reportes')
ON CONFLICT (codigo) DO NOTHING;

-- Asignar permisos a administrador
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id
FROM rol r
JOIN empresa e ON e.id = r.empresa_id
JOIN permiso p ON p.codigo IN ('ventas.ver','ventas.crear','inventario.ver','inventario.gestion','catalogo.gestion','usuarios.gestion','reportes.ver')
WHERE e.slug = 'demo' AND r.nombre = 'administrador'
ON CONFLICT DO NOTHING;

-- Usuarios demo (password: Admin123! / Cliente123! / Encargado123!)
-- Hash bcrypt para Admin123!
WITH admin_hash AS (
    SELECT '$2b$12$eV7M1JZq7Tq2U7fWm4pXEu3k9JkRr2n8vFqL0oZyHcU6tYpWbN1dS' AS h
)
INSERT INTO usuario (empresa_id, rol_id, nombre, correo, password_hash, telefono, email_verificado, estado)
SELECT e.id, r.id, 'Admin Demo', 'admin@demo.test', a.h, '+59170000001', true, 'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'administrador'
CROSS JOIN admin_hash a
WHERE e.slug = 'demo'
ON CONFLICT (empresa_id, correo) DO UPDATE SET email_verificado = true, estado = 'activo', password_hash = EXCLUDED.password_hash;

WITH cli_hash AS (
    SELECT '$2b$12$kQz8gT2vYhN1wR6uFjC4oP0bXeL9mK3sA7tH5dVnJ8qZyIrBpUcG' AS h
)
INSERT INTO usuario (empresa_id, rol_id, nombre, correo, password_hash, telefono, email_verificado, estado)
SELECT e.id, r.id, 'Cliente Demo', 'cliente@demo.test', c.h, '+59170000002', true, 'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'cliente'
CROSS JOIN cli_hash c
WHERE e.slug = 'demo'
ON CONFLICT (empresa_id, correo) DO UPDATE SET email_verificado = true, estado = 'activo', password_hash = EXCLUDED.password_hash;

WITH enc_hash AS (
    SELECT '$2b$12$hB6vT9nF4pK2rYjM8cLzWqE1aXoUdG5sHtR0iN7kPbV3yCxJeAfU' AS h
)
INSERT INTO usuario (empresa_id, rol_id, nombre, correo, password_hash, telefono, email_verificado, estado)
SELECT e.id, r.id, 'Encargado Demo', 'encargado@demo.test', en.h, '+59170000003', true, 'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'encargado'
CROSS JOIN enc_hash en
WHERE e.slug = 'demo'
ON CONFLICT (empresa_id, correo) DO UPDATE SET email_verificado = true, estado = 'activo', password_hash = EXCLUDED.password_hash;

-- Categorias
INSERT INTO categoria (empresa_id, nombre)
SELECT e.id, c.nombre
FROM empresa e
CROSS JOIN (VALUES
    ('Camisetas'),
    ('Pantalones'),
    ('Vestidos'),
    ('Calzado'),
    ('Accesorios')
) AS c(nombre)
WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

-- Colores y tallas
INSERT INTO color (nombre, hex)
VALUES
    ('Negro','#000000'),
    ('Blanco','#FFFFFF'),
    ('Azul','#1E3A8A'),
    ('Rojo','#DC2626'),
    ('Beige','#D9B75B')
ON CONFLICT DO NOTHING;

INSERT INTO talla (nombre, orden)
VALUES ('XS',1),('S',2),('M',3),('L',4),('XL',5),('XXL',6)
ON CONFLICT DO NOTHING;

-- Prendas
INSERT INTO prenda (empresa_id, categoria_id, codigo, nombre, descripcion, precio_base, estado)
SELECT e.id, cat.id, 'CAM-001', 'Camiseta Básica', 'Camiseta de algodón', 89.90, 'activa'
FROM empresa e JOIN categoria cat ON cat.empresa_id = e.id AND cat.nombre = 'Camisetas' WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

INSERT INTO prenda (empresa_id, categoria_id, codigo, nombre, descripcion, precio_base, estado)
SELECT e.id, cat.id, 'PAN-001', 'Pantalón Jean', 'Jean recto', 249.90, 'activa'
FROM empresa e JOIN categoria cat ON cat.empresa_id = e.id AND cat.nombre = 'Pantalones' WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

INSERT INTO prenda (empresa_id, categoria_id, codigo, nombre, descripcion, precio_base, estado)
SELECT e.id, cat.id, 'VES-001', 'Vestido Casual', 'Vestido para verano', 299.90, 'activa'
FROM empresa e JOIN categoria cat ON cat.empresa_id = e.id AND cat.nombre = 'Vestidos' WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

-- Variantes e inventario
INSERT INTO variante (empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, estado)
SELECT e.id, p.id, col.id, t.id, 'CAM-001-NEG-M', '7501234567890', 89.90, 'activa'
FROM empresa e
JOIN prenda p ON p.empresa_id = e.id AND p.codigo = 'CAM-001'
JOIN color col ON col.nombre = 'Negro'
JOIN talla t ON t.nombre = 'M'
WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

INSERT INTO variante (empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, estado)
SELECT e.id, p.id, col.id, t.id, 'PAN-001-AZU-L', '7501234567891', 249.90, 'activa'
FROM empresa e
JOIN prenda p ON p.empresa_id = e.id AND p.codigo = 'PAN-001'
JOIN color col ON col.nombre = 'Azul'
JOIN talla t ON t.nombre = 'L'
WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

INSERT INTO variante (empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, estado)
SELECT e.id, p.id, col.id, t.id, 'VES-001-BEI-S', '7501234567892', 299.90, 'activa'
FROM empresa e
JOIN prenda p ON p.empresa_id = e.id AND p.codigo = 'VES-001'
JOIN color col ON col.nombre = 'Beige'
JOIN talla t ON t.nombre = 'S'
WHERE e.slug = 'demo'
ON CONFLICT DO NOTHING;

-- Inventario
INSERT INTO inventario (empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado, stock_minimo)
SELECT e.id, v.id, s.id, 50, 0, 5
FROM empresa e
JOIN variante v ON v.empresa_id = e.id AND v.sku = 'CAM-001-NEG-M'
JOIN sucursal s ON s.empresa_id = e.id
WHERE e.slug = 'demo'
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO inventario (empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado, stock_minimo)
SELECT e.id, v.id, s.id, 30, 0, 5
FROM empresa e
JOIN variante v ON v.empresa_id = e.id AND v.sku = 'PAN-001-AZU-L'
JOIN sucursal s ON s.empresa_id = e.id
WHERE e.slug = 'demo'
LIMIT 1
ON CONFLICT DO NOTHING;

INSERT INTO inventario (empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado, stock_minimo)
SELECT e.id, v.id, s.id, 20, 0, 3
FROM empresa e
JOIN variante v ON v.empresa_id = e.id AND v.sku = 'VES-001-BEI-S'
JOIN sucursal s ON s.empresa_id = e.id
WHERE e.slug = 'demo'
LIMIT 1
ON CONFLICT DO NOTHING;

COMMIT;

-- Verificacion
SELECT e.slug, e.nombre, e.estado, u.correo, r.nombre as rol, u.email_verificado, u.estado as usuario_estado
FROM empresa e
LEFT JOIN usuario u ON u.empresa_id = e.id
LEFT JOIN rol r ON r.id = u.rol_id
WHERE e.slug = 'demo'
ORDER BY r.nombre;
