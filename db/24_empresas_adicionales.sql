-- ============================================================================
-- 24_empresas_adicionales.sql
-- Creación de 5 empresas completas con suscripciones, sucursales, roles,
-- usuarios, catálogo, existencias y configuración multitenant.
-- ============================================================================

-- 1. Inserción de las 5 Empresas
INSERT INTO empresa (nombre, slug, nit, correo, telefono, estado)
VALUES
    ('Zara Bolivia S.A.', 'zara', '1029384751', 'contacto@zara.bo', '+591 3 3456781', 'activa'),
    ('Mango Urban Fashion S.R.L.', 'mango', '2039485762', 'contacto@mango.bo', '+591 2 2789012', 'activa'),
    ('H&M Bolivia Retail S.A.', 'hm', '3049586773', 'contacto@hm.bo', '+591 4 4123453', 'activa'),
    ('Pull&Bear Streetwear S.R.L.', 'pullbear', '4059687784', 'contacto@pullbear.bo', '+591 3 3678904', 'activa'),
    ('Bershka Teens Bolivia S.A.', 'bershka', '5069788795', 'contacto@bershka.bo', '+591 2 2345675', 'activa')
ON CONFLICT (slug) DO UPDATE 
    SET nombre = EXCLUDED.nombre,
        nit = EXCLUDED.nit,
        correo = EXCLUDED.correo,
        telefono = EXCLUDED.telefono,
        estado = 'activa',
        updated_at = now();

-- 2. Asignar Suscripción Profesional Activa a cada empresa
INSERT INTO suscripcion (empresa_id, plan_id, estado, fecha_inicio, fecha_fin)
SELECT e.id, p.id, 'activa', CURRENT_DATE, CURRENT_DATE + INTERVAL '365 days'
FROM empresa e
CROSS JOIN plan p
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND p.codigo = 'profesional'
ON CONFLICT DO NOTHING;

-- 3. Crear Sucursales Principales
INSERT INTO sucursal (empresa_id, ciudad_id, nombre, direccion, telefono, es_matriz, estado)
SELECT e.id, c.id, s.nombre, s.direccion, s.telefono, true, 'activa'
FROM (
    VALUES
        ('zara', 'Santa Cruz de la Sierra', 'Zara Ventura Mall', '4to Anillo y Av. San Martín, Ventura Mall', '+591 3 3456781'),
        ('mango', 'La Paz', 'Mango San Miguel', 'Av. Montenegro esq. Claudio Aliaga, San Miguel', '+591 2 2789012'),
        ('hm', 'Cochabamba', 'H&M Hupermall', 'Av. Pando #1055, Hupermall Nivel 2', '+591 4 4123453'),
        ('pullbear', 'Santa Cruz de la Sierra', 'Pull&Bear Las Brisas', '4to Anillo esq. Banzer, Mall Las Brisas', '+591 3 3678904'),
        ('bershka', 'La Paz', 'Bershka Megacenter', 'Av. Rafael Pabón, Megacenter Irpavi', '+591 2 2345675')
) AS s(slug, ciudad_nombre, nombre, direccion, telefono)
JOIN empresa e ON e.slug = s.slug
JOIN ciudad c ON c.nombre = s.ciudad_nombre
ON CONFLICT DO NOTHING;

-- 4. Crear Roles para cada una de las 5 Empresas
INSERT INTO rol (empresa_id, nombre, descripcion, es_global)
SELECT e.id, r.nombre, r.descripcion, false
FROM empresa e
CROSS JOIN (
    VALUES
        ('administrador', 'Administrador total de la tienda'),
        ('encargado', 'Encargado de tienda y probadores'),
        ('cajero', 'Cajero punto de venta POS'),
        ('cliente', 'Cliente ecommerce y catálogo')
) AS r(nombre, descripcion)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT DO NOTHING;

-- 5. Asignar Permisos a los Roles de cada Empresa
-- Permisos para Administrador
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id
FROM rol r
JOIN empresa e ON e.id = r.empresa_id
CROSS JOIN permiso p
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND r.nombre = 'administrador'
ON CONFLICT DO NOTHING;

-- Permisos para Encargado
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id
FROM rol r
JOIN empresa e ON e.id = r.empresa_id
JOIN permiso p ON p.codigo IN (
    'ventas.ver', 'inventario.ver', 'inventario.ajustar', 'inventario.transferir',
    'catalogo.ver', 'reportes.ver', 'reservas.ver', 'reservas.preparar', 'reservas.cancelar'
)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND r.nombre = 'encargado'
ON CONFLICT DO NOTHING;

-- Permisos para Cajero
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id
FROM rol r
JOIN empresa e ON e.id = r.empresa_id
JOIN permiso p ON p.codigo IN (
    'ventas.crear', 'ventas.ver', 'ventas.devolver', 'inventario.ver',
    'catalogo.ver', 'pagos.procesar'
)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND r.nombre = 'cajero'
ON CONFLICT DO NOTHING;

-- Permisos para Cliente
INSERT INTO rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id
FROM rol r
JOIN empresa e ON e.id = r.empresa_id
JOIN permiso p ON p.codigo IN (
    'catalogo.ver', 'ventas.ver', 'reservas.crear', 'reservas.ver', 'reservas.cancelar',
    'carrito.gestionar', 'pagos.procesar'
)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND r.nombre = 'cliente'
ON CONFLICT DO NOTHING;

-- 6. Crear Usuarios para cada Empresa
-- Admin: admin@<slug>.bo / Admin123!
INSERT INTO usuario (empresa_id, rol_id, sucursal_id, nombre, correo, password_hash, telefono, email_verificado, estado)
SELECT 
    e.id, 
    r.id, 
    s.id, 
    'Admin ' || e.nombre, 
    'admin@' || e.slug || '.bo', 
    crypt('Admin123!', gen_salt('bf', 10)), 
    e.telefono, 
    true, 
    'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'administrador'
JOIN sucursal s ON s.empresa_id = e.id AND s.es_matriz = true
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, correo) DO UPDATE 
    SET password_hash = crypt('Admin123!', gen_salt('bf', 10)),
        email_verificado = true,
        estado = 'activo';

-- Encargado: encargado@<slug>.bo / Encargado123!
INSERT INTO usuario (empresa_id, rol_id, sucursal_id, nombre, correo, password_hash, telefono, email_verificado, estado)
SELECT 
    e.id, 
    r.id, 
    s.id, 
    'Encargado ' || e.nombre, 
    'encargado@' || e.slug || '.bo', 
    crypt('Encargado123!', gen_salt('bf', 10)), 
    e.telefono, 
    true, 
    'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'encargado'
JOIN sucursal s ON s.empresa_id = e.id AND s.es_matriz = true
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, correo) DO UPDATE 
    SET password_hash = crypt('Encargado123!', gen_salt('bf', 10)),
        email_verificado = true,
        estado = 'activo';

-- Cajero: cajero@<slug>.bo / Cajero123!
INSERT INTO usuario (empresa_id, rol_id, sucursal_id, nombre, correo, password_hash, telefono, email_verificado, estado)
SELECT 
    e.id, 
    r.id, 
    s.id, 
    'Cajero ' || e.nombre, 
    'cajero@' || e.slug || '.bo', 
    crypt('Cajero123!', gen_salt('bf', 10)), 
    e.telefono, 
    true, 
    'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'cajero'
JOIN sucursal s ON s.empresa_id = e.id AND s.es_matriz = true
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, correo) DO UPDATE 
    SET password_hash = crypt('Cajero123!', gen_salt('bf', 10)),
        email_verificado = true,
        estado = 'activo';

-- Cliente: cliente@<slug>.bo / Cliente123!
INSERT INTO usuario (empresa_id, rol_id, sucursal_id, nombre, correo, password_hash, telefono, email_verificado, estado)
SELECT 
    e.id, 
    r.id, 
    NULL, 
    'Cliente VIP ' || e.nombre, 
    'cliente@' || e.slug || '.bo', 
    crypt('Cliente123!', gen_salt('bf', 10)), 
    e.telefono, 
    true, 
    'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'cliente'
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, correo) DO UPDATE 
    SET password_hash = crypt('Cliente123!', gen_salt('bf', 10)),
        email_verificado = true,
        estado = 'activo';

-- 7. Categorías para cada Empresa
INSERT INTO categoria (empresa_id, nombre)
SELECT e.id, cat.nombre
FROM empresa e
CROSS JOIN (
    VALUES
        ('Camisas & Polos'),
        ('Pantalones & Jeans'),
        ('Vestidos & Faldas'),
        ('Chaquetas & Abrigos'),
        ('Calzado & Accesorios')
) AS cat(nombre)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT DO NOTHING;

-- 8. Prendas de Muestra para cada Empresa
INSERT INTO prenda (empresa_id, categoria_id, codigo, nombre, descripcion, precio_base, estado, genero)
SELECT 
    e.id, 
    c.id, 
    UPPER(e.slug) || '-' || p.codigo,
    p.nombre,
    p.descripcion,
    p.precio,
    'activa',
    p.genero
FROM empresa e
JOIN categoria c ON c.empresa_id = e.id AND c.nombre = 'Camisas & Polos'
CROSS JOIN (
    VALUES
        ('01', 'Camisa Lino Premium', 'Camisa de lino 100% transpirable de corte regular', 249.00, 'unisex'),
        ('02', 'Polo Piqué Clásico', 'Polo de algodón peinado con cuello en ribete', 149.00, 'hombre'),
        ('03', 'Blusa Satén Elegance', 'Blusa con caída suave y botones aperlados', 199.00, 'mujer')
) AS p(codigo, nombre, descripcion, precio, genero)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT DO NOTHING;

-- 9. Variantes de las Prendas
INSERT INTO variante (empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, costo, estado)
SELECT 
    pr.empresa_id,
    pr.id,
    col.id,
    tal.id,
    pr.codigo || '-' || tal.nombre || '-' || UPPER(SUBSTRING(col.nombre, 1, 3)),
    '777' || LPAD(CAST(ABS(HASHTEXT(pr.codigo || tal.nombre || col.nombre)) % 1000000000 AS text), 9, '0'),
    pr.precio_base,
    pr.precio_base * 0.45,
    'activa'
FROM prenda pr
JOIN empresa e ON e.id = pr.empresa_id
CROSS JOIN (SELECT id, nombre FROM color WHERE nombre IN ('Blanco', 'Negro', 'Azul Marino') LIMIT 3) col
CROSS JOIN (SELECT id, nombre FROM talla WHERE nombre IN ('S', 'M', 'L') LIMIT 3) tal
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, sku) DO NOTHING;

-- 10. Inventario Inicial (250 unidades físicas por variante en la sucursal matriz)
INSERT INTO inventario (empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado, stock_minimo, ubicacion)
SELECT 
    v.empresa_id,
    v.id,
    s.id,
    250,
    0,
    10,
    'Sección A - Mostrador Principal'
FROM variante v
JOIN sucursal s ON s.empresa_id = v.empresa_id AND s.es_matriz = true
JOIN empresa e ON e.id = v.empresa_id
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, variante_id, sucursal_id) DO UPDATE
    SET stock_fisico = 250,
        stock_reservado = 0,
        actualizado_en = now();
