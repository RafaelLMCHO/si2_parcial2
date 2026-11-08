-- ============================================================================
-- Seeder de datos demo para revisar todas las funcionalidades de FashionStore.
-- Solo afecta al tenant "demo" (11111111-1111-1111-1111-111111111111).
-- Es idempotente: puede ejecutarse varias veces sin duplicar informacion.
-- NO forma parte de db/run_all.sql para no romper las pruebas de aislamiento.
-- Uso: scripts/seed_demo.ps1  (o psql -f db/25_seed_demo.sql)
-- ============================================================================
\set ON_ERROR_STOP on
BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Sucursales adicionales
-- ---------------------------------------------------------------------------
INSERT INTO sucursal (id, empresa_id, ciudad_id, nombre, direccion, telefono, es_matriz, estado)
VALUES
    ('11111111-1111-1111-1111-111111112101', '11111111-1111-1111-1111-111111111111', 2,
     'Sucursal Norte', 'Av. 6 de Agosto 2100, Sopocachi', '+591 71234567', false, 'activa'),
    ('11111111-1111-1111-1111-111111112102', '11111111-1111-1111-1111-111111111111', 3,
     'Sucursal Sur', 'Av. America 450, Queru Queru', '+591 72345678', false, 'activa')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 2. Usuarios: clientes adicionales y un cajero para otra sucursal
-- ---------------------------------------------------------------------------
INSERT INTO usuario (id, empresa_id, rol_id, sucursal_id, nombre, correo, password_hash,
                     telefono, email_verificado, email_verificado_en, estado)
VALUES
    ('11111111-1111-1111-1111-111111111305', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Valeria Rojas', 'cliente1@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000001', true, now() - interval '120 days', 'activo'),
    ('11111111-1111-1111-1111-111111111306', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Diego Vargas', 'cliente2@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000002', true, now() - interval '110 days', 'activo'),
    ('11111111-1111-1111-1111-111111111307', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Camila Quispe', 'cliente3@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000003', true, now() - interval '100 days', 'activo'),
    ('11111111-1111-1111-1111-111111111308', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Mateo Flores', 'cliente4@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000004', true, now() - interval '90 days', 'activo'),
    ('11111111-1111-1111-1111-111111111309', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Isabella Cruz', 'cliente5@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000005', true, now() - interval '80 days', 'activo'),
    ('11111111-1111-1111-1111-111111111310', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Sebastian Paz', 'cliente6@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000006', true, now() - interval '70 days', 'activo'),
    ('11111111-1111-1111-1111-111111111311', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Renata Suarez', 'cliente7@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000007', true, now() - interval '60 days', 'activo'),
    ('11111111-1111-1111-1111-111111111312', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Andres Molina', 'cliente8@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000008', true, now() - interval '50 days', 'activo'),
    ('11111111-1111-1111-1111-111111111313', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Lucia Herrera', 'cliente9@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000009', true, now() - interval '40 days', 'activo'),
    ('11111111-1111-1111-1111-111111111314', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111203', NULL, 'Gabriel Ortiz', 'cliente10@demo.test',
     crypt('Cliente123!', gen_salt('bf', 10)), '+591 71000010', true, now() - interval '30 days', 'activo'),
    ('11111111-1111-1111-1111-111111111316', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111202', '11111111-1111-1111-1111-111111112101',
     'Cajero Norte', 'cajero2@demo.test', crypt('Cajero123!', gen_salt('bf', 10)),
     '+591 71000020', true, now() - interval '20 days', 'activo')
ON CONFLICT DO NOTHING;

UPDATE usuario SET email_verificado = true,
                   email_verificado_en = COALESCE(email_verificado_en, now())
WHERE empresa_id = '11111111-1111-1111-1111-111111111111' AND email_verificado = false;

-- ---------------------------------------------------------------------------
-- 3. Catalogo: categorias, temporadas, colecciones y proveedores
-- ---------------------------------------------------------------------------
INSERT INTO categoria (id, empresa_id, nombre) VALUES
    ('11111111-1111-1111-1111-111111111405', '11111111-1111-1111-1111-111111111111', 'Camisas y Blusas'),
    ('11111111-1111-1111-1111-111111111406', '11111111-1111-1111-1111-111111111111', 'Pantalones'),
    ('11111111-1111-1111-1111-111111111407', '11111111-1111-1111-1111-111111111111', 'Chaquetas'),
    ('11111111-1111-1111-1111-111111111408', '11111111-1111-1111-1111-111111111111', 'Calzado'),
    ('11111111-1111-1111-1111-111111111409', '11111111-1111-1111-1111-111111111111', 'Accesorios'),
    ('11111111-1111-1111-1111-111111111410', '11111111-1111-1111-1111-111111111111', 'Deportivo'),
    ('11111111-1111-1111-1111-111111111411', '11111111-1111-1111-1111-111111111111', 'Ropa Interior')
ON CONFLICT DO NOTHING;

INSERT INTO temporada (id, empresa_id, nombre, fecha_inicio, fecha_fin) VALUES
    ('11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111111', 'Otono 2026', DATE '2026-03-01', DATE '2026-06-30'),
    ('11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111111', 'Verano 2026', DATE '2026-11-01', DATE '2027-02-28')
ON CONFLICT DO NOTHING;

INSERT INTO coleccion (id, empresa_id, nombre, anio) VALUES
    ('11111111-1111-1111-1111-111111111433', '11111111-1111-1111-1111-111111111111', 'Denim 2026', 2026),
    ('11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111111', 'Urbana 2026', 2026),
    ('11111111-1111-1111-1111-111111111435', '11111111-1111-1111-1111-111111111111', 'Fiesta 2026', 2026)
ON CONFLICT DO NOTHING;

INSERT INTO proveedor (id, empresa_id, nombre, nit, correo, telefono) VALUES
    ('11111111-1111-1111-1111-111111111444', '11111111-1111-1111-1111-111111111111', 'Textiles Andinos SRL', 'PROV-002', 'ventas@textilesandinos.test', '+591 33344455'),
    ('11111111-1111-1111-1111-111111111445', '11111111-1111-1111-1111-111111111111', 'Importadora Moda Global', 'PROV-003', 'contacto@modaglobal.test', '+591 22255566')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 4. Prendas
-- ---------------------------------------------------------------------------
UPDATE prenda SET precio_base = 180.00, imagen_url = 'https://cdn.fashionstore.test/demo/vestido-midi.jpg'
WHERE id = '11111111-1111-1111-1111-111111111501' AND empresa_id = '11111111-1111-1111-1111-111111111111';

INSERT INTO prenda (id, empresa_id, categoria_id, temporada_id, coleccion_id, proveedor_id,
                    codigo, nombre, descripcion, marca, genero, precio_base, imagen_url, estado)
VALUES
    ('11111111-1111-1111-1111-111111111502', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111405', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111444', 'FS-CAM-001', 'Camisa de lino', 'Camisa fresca de lino para uso diario', 'FashionStore', 'hombre', 160.00, 'https://cdn.fashionstore.test/demo/camisa-lino.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111503', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111405', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111435', '11111111-1111-1111-1111-111111111444', 'FS-BLU-001', 'Blusa de saten', 'Blusa de saten con caida fluida', 'FashionStore', 'mujer', 190.00, 'https://cdn.fashionstore.test/demo/blusa-saten.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111504', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111405', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111445', 'FS-CAM-002', 'Camiseta basica', 'Camiseta de algodon peinado', 'FashionStore', 'unisex', 90.00, 'https://cdn.fashionstore.test/demo/camiseta-basica.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111505', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111406', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111433', '11111111-1111-1111-1111-111111111444', 'FS-PAN-001', 'Jean recto', 'Jean recto de denim rigido', 'FashionStore', 'hombre', 240.00, 'https://cdn.fashionstore.test/demo/jean-recto.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111506', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111406', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111445', 'FS-PAN-002', 'Pantalon chino', 'Pantalon chino de algodon stretch', 'FashionStore', 'hombre', 210.00, 'https://cdn.fashionstore.test/demo/pantalon-chino.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111507', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111406', '11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111444', 'FS-PAN-003', 'Jogger urbano', 'Jogger con punos elasticos', 'FashionStore', 'unisex', 170.00, 'https://cdn.fashionstore.test/demo/jogger.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111508', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111407', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111433', '11111111-1111-1111-1111-111111111445', 'FS-CHA-001', 'Chaqueta denim', 'Chaqueta denim oversize', 'FashionStore', 'unisex', 320.00, 'https://cdn.fashionstore.test/demo/chaqueta-denim.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111509', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111407', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111435', '11111111-1111-1111-1111-111111111444', 'FS-BLZ-001', 'Blazer estructurado', 'Blazer de corte recto para oficina', 'FashionStore', 'mujer', 380.00, 'https://cdn.fashionstore.test/demo/blazer.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111510', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111408', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111445', 'FS-CAL-001', 'Zapato casual', 'Zapato casual de cuero sintetico', 'FashionStore', 'hombre', 290.00, 'https://cdn.fashionstore.test/demo/zapato-casual.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111511', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111408', '11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111444', 'FS-CAL-002', 'Zapatilla urbana', 'Zapatilla liviana para uso diario', 'FashionStore', 'unisex', 330.00, 'https://cdn.fashionstore.test/demo/zapatilla-urbana.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111512', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111409', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111435', '11111111-1111-1111-1111-111111111445', 'FS-ACC-001', 'Bolso tote', 'Bolso tote de lona reforzada', 'FashionStore', 'mujer', 220.00, 'https://cdn.fashionstore.test/demo/bolso-tote.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111513', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111409', '11111111-1111-1111-1111-111111111422', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111444', 'FS-ACC-002', 'Cinturon de cuero', 'Cinturon de cuero con hebilla metalica', 'FashionStore', 'unisex', 120.00, 'https://cdn.fashionstore.test/demo/cinturon.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111514', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111410', '11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111445', 'FS-DEP-001', 'Conjunto deportivo', 'Conjunto de top y leggings deportivos', 'FashionStore', 'mujer', 260.00, 'https://cdn.fashionstore.test/demo/conjunto-deportivo.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111515', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111410', '11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111444', 'FS-DEP-002', 'Leggings de entrenamiento', 'Leggings de compresion media', 'FashionStore', 'mujer', 150.00, 'https://cdn.fashionstore.test/demo/leggings.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111516', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111401', '11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111435', '11111111-1111-1111-1111-111111111444', 'FS-VES-002', 'Vestido de fiesta', 'Vestido largo de fiesta con abertura', 'FashionStore', 'mujer', 460.00, 'https://cdn.fashionstore.test/demo/vestido-fiesta.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111517', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111411', '11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111435', '11111111-1111-1111-1111-111111111444', 'FS-INT-001', 'Body de encaje', 'Body de encaje con espalda abierta', 'FashionStore', 'mujer', 130.00, 'https://cdn.fashionstore.test/demo/body-encaje.jpg', 'activa'),
    ('11111111-1111-1111-1111-111111111518', '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111411', '11111111-1111-1111-1111-111111111423', '11111111-1111-1111-1111-111111111434', '11111111-1111-1111-1111-111111111445', 'FS-INT-002', 'Pijama de algodon', 'Pijama de dos piezas de algodon', 'FashionStore', 'unisex', 180.00, 'https://cdn.fashionstore.test/demo/pijama.jpg', 'activa')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 5. Recursos de prendas
-- ---------------------------------------------------------------------------
INSERT INTO prenda_recurso (id, empresa_id, prenda_id, tipo, url, mime_type, orden, es_principal)
SELECT md5('fs25-img-' || p.codigo)::uuid,
       p.empresa_id, p.id, 'imagen', p.imagen_url, 'image/jpeg', 0, true
FROM prenda p
WHERE p.empresa_id = '11111111-1111-1111-1111-111111111111'
  AND p.imagen_url IS NOT NULL
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 6. Variantes (3 colores x 3 tallas por prenda)
-- ---------------------------------------------------------------------------
WITH p AS (
    SELECT id, codigo, precio_base,
           row_number() OVER (ORDER BY codigo) AS seq
    FROM prenda
    WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
      AND deleted_at IS NULL
), c AS (
    SELECT p.id AS prenda_id, p.codigo, p.precio_base, p.seq,
           unnest(CASE WHEN p.seq % 2 = 0
                       THEN ARRAY['Negro', 'Blanco', 'Rojo']
                       ELSE ARRAY['Azul Marino', 'Beige', 'Gris']
                  END) AS color_nombre
    FROM p
), t AS (
    SELECT c.*,
           unnest(CASE WHEN c.codigo LIKE 'FS-CAL%'
                       THEN ARRAY['36', '38', '40']
                       ELSE ARRAY['XS', 'S', 'M']
                  END) AS talla_nombre
    FROM c
)
INSERT INTO variante (id, empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras,
                      precio_venta, costo, estado)
SELECT md5('fs25-var-' || t.codigo || '-' || t.color_nombre || '-' || t.talla_nombre)::uuid,
       '11111111-1111-1111-1111-111111111111',
       t.prenda_id, co.id, ta.id,
       t.codigo || '-' || upper(left(replace(t.color_nombre, ' ', ''), 3)) || '-' || t.talla_nombre,
       'FS' || lpad((abs(hashtext(t.codigo || t.color_nombre || t.talla_nombre)) % 100000)::text, 5, '0'),
       t.precio_base,
       round(t.precio_base * 0.45, 2),
       'activa'
FROM t
JOIN color co ON co.nombre = t.color_nombre
JOIN talla ta ON ta.nombre = t.talla_nombre
ON CONFLICT DO NOTHING;

UPDATE variante SET precio_venta = 180.00, costo = 80.00
WHERE id = '11111111-1111-1111-1111-111111111601';

-- ---------------------------------------------------------------------------
-- 7. Inventario en las tres sucursales
-- ---------------------------------------------------------------------------
INSERT INTO inventario (id, empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado,
                        stock_minimo, ubicacion)
SELECT md5('fs25-inv-' || v.id || '-' || s.id)::uuid,
       '11111111-1111-1111-1111-111111111111',
       v.id, s.id,
       CASE WHEN abs(hashtext(v.sku || s.id::text)) % 17 = 0
            THEN 2 + (abs(hashtext(v.sku || s.id::text)) % 8)
            ELSE 40 + (abs(hashtext(v.sku || s.id::text)) % 120)
       END,
       0,
       5 + (abs(hashtext(v.sku || s.id::text)) % 10),
       'Pasillo ' || (abs(hashtext(v.sku)) % 8 + 1)
FROM variante v
CROSS JOIN sucursal s
WHERE v.empresa_id = '11111111-1111-1111-1111-111111111111'
  AND s.empresa_id = '11111111-1111-1111-1111-111111111111'
  AND s.estado = 'activa'
  AND v.deleted_at IS NULL
ON CONFLICT (empresa_id, variante_id, sucursal_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 8. Direcciones de clientes
-- ---------------------------------------------------------------------------
INSERT INTO direccion_cliente (id, empresa_id, usuario_id, etiqueta, destinatario, telefono,
                               linea1, linea2, ciudad_id, codigo_postal, referencia, es_principal)
SELECT md5('fs25-dir-' || u.id || '-' || n.n)::uuid,
       u.empresa_id, u.id,
       CASE n.n WHEN 1 THEN 'Casa' ELSE 'Trabajo' END,
       u.nombre,
       '+591 7' || lpad((abs(hashtext(u.id::text || n.n)) % 10000000)::text, 7, '0'),
       CASE n.n WHEN 1 THEN 'Av. Los Andes ' || (100 + abs(hashtext(u.id::text)) % 800)
                ELSE 'Calle Comercio ' || (10 + abs(hashtext(u.id::text)) % 90)
       END,
       CASE n.n WHEN 1 THEN 'Zona residencial' ELSE 'Edificio corporativo' END,
       1 + (abs(hashtext(u.id::text || n.n)) % 3),
       'CP' || lpad((abs(hashtext(u.id::text || n.n)) % 9999)::text, 4, '0'),
       'Referencia de entrega ' || n.n,
       (n.n = 1)
FROM usuario u
CROSS JOIN (VALUES (1), (2)) AS n(n)
WHERE u.empresa_id = '11111111-1111-1111-1111-111111111111'
  AND u.id <> '11111111-1111-1111-1111-111111111302'
  AND u.rol_id = '11111111-1111-1111-1111-111111111203'
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 9. Cupones
-- ---------------------------------------------------------------------------
INSERT INTO cupon (id, empresa_id, codigo, descripcion, tipo, valor, monto_minimo,
                   usos_maximos, usos_por_usuario, fecha_inicio, fecha_fin, activo)
VALUES
    ('11111111-1111-1111-1111-111111111a02', '11111111-1111-1111-1111-111111111111',
     'VERANO20', '20% de descuento en la coleccion de verano', 'porcentaje', 20.00, 150.00,
     100, 2, now() - interval '30 days', now() + interval '60 days', true),
    ('11111111-1111-1111-1111-111111111a03', '11111111-1111-1111-1111-111111111111',
     'ENVIOGRATIS', 'Envio gratis en compras mayores a Bs. 100', 'envio_gratis', 0.00, 100.00,
     200, 3, now() - interval '60 days', now() + interval '90 days', true)
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 10. Ventas WEB (una por categoria y por mes durante 8 meses)
-- ---------------------------------------------------------------------------
DO $seed$
DECLARE
    v_emp uuid := '11111111-1111-1111-1111-111111111111';
    v_suc_centro uuid := '11111111-1111-1111-1111-111111111101';
    v_rol_cli uuid := '11111111-1111-1111-1111-111111111203';
    v_cupon uuid := '11111111-1111-1111-1111-111111111a01';
    m int;
    cat record;
    var record;
    cli record;
    v_dir uuid;
    v_venta uuid;
    v_sub numeric(12,2);
    v_desc numeric(12,2);
    v_imp numeric(12,2);
    v_total numeric(12,2);
    v_fecha timestamptz;
    v_estado varchar(30);
    v_metodo varchar(20);
    v_num varchar(40);
    v_idem varchar(80);
    v_idx int;
    v_qty int;
BEGIN
    FOR m IN 0..7 LOOP
        FOR cat IN
            SELECT id, nombre, row_number() OVER (ORDER BY nombre) AS seq
            FROM categoria
            WHERE empresa_id = v_emp
        LOOP
            v_fecha := now() - make_interval(days => (m * 30 + ((cat.seq * 3) % 20))::int,
                                             hours => (cat.seq % 9)::int);
            SELECT u.id, u.nombre INTO cli
            FROM usuario u
            WHERE u.empresa_id = v_emp AND u.rol_id = v_rol_cli
            ORDER BY md5(u.id::text || m::text || cat.seq::text)
            LIMIT 1;

            SELECT d.id INTO v_dir
            FROM direccion_cliente d
            WHERE d.empresa_id = v_emp AND d.usuario_id = cli.id
            ORDER BY d.es_principal DESC, d.created_at
            LIMIT 1;

            v_venta := md5('fs25-venta-web-' || m || '-' || cat.seq)::uuid;
            v_num := 'WEB-' || to_char(v_fecha, 'YYYYMM') || '-' ||
                     lpad(((m * 10 + cat.seq))::text, 3, '0');
            v_idem := 'seed25-web-' || m || '-' || cat.seq;
            v_estado := CASE WHEN m = 0 THEN 'pagada'
                             WHEN m = 1 THEN 'enviada'
                             ELSE 'completada' END;

            INSERT INTO venta (id, empresa_id, numero, sucursal_id, usuario_id, canal,
                               fecha_hora, fecha_hora_cliente, fecha_recepcion_servidor,
                               moneda, subtotal, descuento, impuesto, total, estado,
                               direccion_id, idempotency_key, cliente_nombre, cliente_documento,
                               created_at, updated_at)
            VALUES (v_venta, v_emp, v_num, v_suc_centro, cli.id, 'WEB',
                    v_fecha, v_fecha + interval '1 minute', v_fecha + interval '2 minutes',
                    'BOB', 0, 0, 0, 0, v_estado,
                    v_dir, v_idem, cli.nombre,
                    'CI-' || lpad((abs(hashtext(cli.id::text)) % 9999999)::text, 7, '0'),
                    v_fecha, v_fecha)
            ON CONFLICT DO NOTHING;

            IF NOT FOUND THEN
                CONTINUE;
            END IF;

            v_idx := 0;
            FOR var IN
                SELECT v.id, v.precio_venta
                FROM variante v
                JOIN prenda p ON p.id = v.prenda_id AND p.empresa_id = v.empresa_id
                WHERE v.empresa_id = v_emp AND p.categoria_id = cat.id
                ORDER BY md5(v.id::text || m::text || cat.seq::text)
                LIMIT (1 + (m % 2))
            LOOP
                v_idx := v_idx + 1;
                v_qty := 1 + ((m + v_idx) % 2);
                INSERT INTO venta_detalle (id, empresa_id, venta_id, variante_id, cantidad,
                                           precio_lista, precio_unitario, descuento_linea, subtotal)
                VALUES (md5('fs25-vd-web-' || m || '-' || cat.seq || '-' || v_idx)::uuid,
                        v_emp, v_venta, var.id, v_qty,
                        var.precio_venta, var.precio_venta, 0, v_qty * var.precio_venta)
                ON CONFLICT DO NOTHING;
            END LOOP;

            SELECT subtotal INTO v_sub FROM venta WHERE id = v_venta;
            v_desc := CASE WHEN m % 4 = 0 THEN round(v_sub * 0.05, 2) ELSE 0 END;
            v_imp := round(v_sub * 0.13, 2);
            v_total := v_sub - v_desc + v_imp;
            UPDATE venta
               SET descuento = v_desc,
                   impuesto = v_imp,
                   total = v_total,
                   updated_at = v_fecha + interval '10 minutes'
             WHERE id = v_venta;

            v_metodo := (ARRAY['tarjeta', 'qr', 'pasarela', 'transferencia'])[1 + (m % 4)];
            INSERT INTO pago (id, empresa_id, venta_id, monto, metodo, idempotency_key,
                              estado, referencia, pagado_en)
            VALUES (md5('fs25-pago-web-' || m || '-' || cat.seq)::uuid, v_emp, v_venta,
                    v_total, v_metodo, 'seed25-pago-web-' || m || '-' || cat.seq,
                    'completado', 'SEED25-' || m || '-' || cat.seq,
                    v_fecha + interval '5 minutes')
            ON CONFLICT DO NOTHING;

            IF NOT EXISTS (SELECT 1 FROM venta_estado_historial h
                           WHERE h.empresa_id = v_emp AND h.venta_id = v_venta
                             AND h.estado_nuevo = 'pendiente_pago') THEN
                INSERT INTO venta_estado_historial (empresa_id, venta_id, estado_anterior,
                                                    estado_nuevo, motivo, usuario_id, ocurrido_en)
                VALUES (v_emp, v_venta, NULL, 'pendiente_pago', 'Creacion de orden',
                        cli.id, v_fecha);
            END IF;

            IF NOT EXISTS (SELECT 1 FROM venta_estado_historial h
                           WHERE h.empresa_id = v_emp AND h.venta_id = v_venta
                             AND h.estado_nuevo = v_estado) THEN
                INSERT INTO venta_estado_historial (empresa_id, venta_id, estado_anterior,
                                                    estado_nuevo, motivo, usuario_id, ocurrido_en)
                VALUES (v_emp, v_venta, 'pendiente_pago', v_estado, 'Pago confirmado',
                        cli.id, v_fecha + interval '5 minutes');
            END IF;

            IF v_dir IS NOT NULL AND ((m + cat.seq) % 3) <> 0 THEN
                v_estado := CASE WHEN m >= 3 THEN 'entregado'
                                 WHEN m = 2 THEN 'en_transito'
                                 ELSE 'enviado' END;
                INSERT INTO envio (id, empresa_id, venta_id, direccion_id, transportista,
                                   tracking, estado, costo, fecha_estimada, enviado_en,
                                   entregado_en, created_at, updated_at)
                VALUES (md5('fs25-envio-web-' || m || '-' || cat.seq)::uuid, v_emp, v_venta,
                        v_dir, 'Transportes Andinos',
                        'TRK-' || to_char(v_fecha, 'YYYYMMDD') || '-' || m || cat.seq,
                        v_estado, 15.00, (v_fecha + interval '5 days')::date,
                        CASE WHEN v_estado IN ('en_transito', 'entregado')
                             THEN v_fecha + interval '1 day' END,
                        CASE WHEN v_estado = 'entregado'
                             THEN v_fecha + interval '4 days' END,
                        v_fecha, v_fecha + interval '1 day')
                ON CONFLICT DO NOTHING;
            END IF;

            IF m = 1 AND cat.seq <= 3 THEN
                UPDATE venta SET cupon_id = v_cupon WHERE id = v_venta AND cupon_id IS NULL;
                INSERT INTO cupon_uso (id, empresa_id, cupon_id, venta_id, usuario_id, usado_en)
                VALUES (md5('fs25-cupon-web-' || m || '-' || cat.seq)::uuid, v_emp, v_cupon,
                        v_venta, cli.id, v_fecha + interval '3 minutes')
                ON CONFLICT (empresa_id, cupon_id, venta_id) DO NOTHING;
            END IF;
        END LOOP;
    END LOOP;
END
$seed$;

-- ---------------------------------------------------------------------------
-- 11. Ventas POS (una por categoria principal y por mes durante 8 meses)
-- ---------------------------------------------------------------------------
DO $seed$
DECLARE
    v_emp uuid := '11111111-1111-1111-1111-111111111111';
    v_suc uuid;
    v_cajero uuid := '11111111-1111-1111-1111-111111111304';
    m int;
    cat record;
    var record;
    v_venta uuid;
    v_sub numeric(12,2);
    v_imp numeric(12,2);
    v_fecha timestamptz;
    v_num varchar(40);
    v_idx int;
    v_qty int;
BEGIN
    FOR m IN 0..7 LOOP
        SELECT s.id INTO v_suc
        FROM sucursal s
        WHERE s.empresa_id = v_emp AND s.estado = 'activa'
        ORDER BY md5(s.id::text || m::text)
        LIMIT 1;

        FOR cat IN
            SELECT id, nombre, row_number() OVER (ORDER BY nombre) AS seq
            FROM categoria
            WHERE empresa_id = v_emp
            ORDER BY nombre
            LIMIT 3
        LOOP
            v_fecha := now() - make_interval(days => m * 30 + 4,
                                             hours => (10 + (cat.seq % 8))::int);
            v_venta := md5('fs25-venta-pos-' || m || '-' || cat.seq)::uuid;
            v_num := 'POS-' || to_char(v_fecha, 'YYYYMM') || '-' ||
                     lpad((m * 10 + cat.seq)::text, 3, '0');

            INSERT INTO venta (id, empresa_id, numero, sucursal_id, cajero_id, canal,
                               fecha_hora, fecha_hora_cliente, fecha_recepcion_servidor,
                               moneda, subtotal, descuento, impuesto, total, estado,
                               idempotency_key, cliente_nombre, created_at, updated_at)
            VALUES (v_venta, v_emp, v_num, v_suc, v_cajero, 'POS',
                    v_fecha, v_fecha, v_fecha + interval '1 second',
                    'BOB', 0, 0, 0, 0, 'completada',
                    'seed25-pos-' || m || '-' || cat.seq, 'Cliente de mostrador',
                    v_fecha, v_fecha)
            ON CONFLICT DO NOTHING;

            IF NOT FOUND THEN
                CONTINUE;
            END IF;

            v_idx := 0;
            FOR var IN
                SELECT v.id, v.precio_venta
                FROM variante v
                JOIN prenda p ON p.id = v.prenda_id AND p.empresa_id = v.empresa_id
                WHERE v.empresa_id = v_emp AND p.categoria_id = cat.id
                ORDER BY md5(v.id::text || 'pos' || m::text || cat.seq::text)
                LIMIT 2
            LOOP
                v_idx := v_idx + 1;
                v_qty := 1 + ((m + v_idx) % 3);
                INSERT INTO venta_detalle (id, empresa_id, venta_id, variante_id, cantidad,
                                           precio_lista, precio_unitario, descuento_linea, subtotal)
                VALUES (md5('fs25-vd-pos-' || m || '-' || cat.seq || '-' || v_idx)::uuid,
                        v_emp, v_venta, var.id, v_qty,
                        var.precio_venta, var.precio_venta, 0, v_qty * var.precio_venta)
                ON CONFLICT DO NOTHING;
            END LOOP;

            SELECT subtotal INTO v_sub FROM venta WHERE id = v_venta;
            v_imp := round(v_sub * 0.13, 2);
            UPDATE venta
               SET impuesto = v_imp,
                   total = v_sub + v_imp,
                   updated_at = v_fecha + interval '2 minutes'
             WHERE id = v_venta;

            INSERT INTO pago (id, empresa_id, venta_id, monto, metodo, idempotency_key,
                              estado, referencia, pagado_en)
            VALUES (md5('fs25-pago-pos-' || m || '-' || cat.seq)::uuid, v_emp, v_venta,
                    v_sub + v_imp, (ARRAY['efectivo', 'tarjeta', 'qr'])[1 + (m % 3)],
                    'seed25-pago-pos-' || m || '-' || cat.seq, 'completado',
                    'SEED25-POS-' || m || '-' || cat.seq, v_fecha)
            ON CONFLICT DO NOTHING;

            IF NOT EXISTS (SELECT 1 FROM venta_estado_historial h
                           WHERE h.empresa_id = v_emp AND h.venta_id = v_venta
                             AND h.estado_nuevo = 'completada') THEN
                INSERT INTO venta_estado_historial (empresa_id, venta_id, estado_anterior,
                                                    estado_nuevo, motivo, usuario_id, ocurrido_en)
                VALUES (v_emp, v_venta, NULL, 'completada', 'Venta de mostrador',
                        v_cajero, v_fecha);
            END IF;
        END LOOP;
    END LOOP;
END
$seed$;

-- ---------------------------------------------------------------------------
-- 12. Reservas en todos los estados
-- ---------------------------------------------------------------------------
DO $seed$
DECLARE
    v_emp uuid := '11111111-1111-1111-1111-111111111111';
    v_rol_cli uuid := '11111111-1111-1111-1111-111111111203';
    v_suc uuid;
    v_estados text[] := ARRAY['pendiente_preparacion', 'pendiente_preparacion', 'preparada',
                              'incidencia_stock', 'activa', 'activa', 'confirmada',
                              'expirada', 'cancelada', 'convertida'];
    i int;
    v_res uuid;
    v_cli uuid;
    v_var uuid;
    v_ini timestamptz;
    v_precio numeric(12,2);
BEGIN
    SELECT s.id INTO v_suc FROM sucursal s
    WHERE s.empresa_id = v_emp AND s.estado = 'activa'
    ORDER BY s.es_matriz DESC, s.nombre LIMIT 1;

    FOR i IN 1..10 LOOP
        SELECT u.id INTO v_cli FROM usuario u
        WHERE u.empresa_id = v_emp AND u.rol_id = v_rol_cli
        ORDER BY md5(u.id::text || 'res' || i::text) LIMIT 1;

        SELECT v.id, v.precio_venta INTO v_var, v_precio
        FROM variante v
        WHERE v.empresa_id = v_emp
        ORDER BY md5(v.id::text || 'res' || i::text) LIMIT 1;

        v_res := md5('fs25-reserva-' || i)::uuid;
        v_ini := now() - make_interval(days => 20 - i * 2);

        INSERT INTO reserva (id, empresa_id, codigo, usuario_id, sucursal_id, estado,
                             fecha_visita, expira_en, created_at, updated_at)
        VALUES (v_res, v_emp, 'RES-25-' || lpad(i::text, 3, '0'), v_cli, v_suc,
                'pendiente_preparacion', v_ini + interval '1 day',
                v_ini + interval '2 days', v_ini, v_ini)
        ON CONFLICT DO NOTHING;

        IF NOT FOUND THEN
            CONTINUE;
        END IF;

        INSERT INTO reserva_detalle (id, empresa_id, reserva_id, variante_id, cantidad)
        VALUES (md5('fs25-resdet-' || i)::uuid, v_emp, v_res, v_var, 1)
        ON CONFLICT DO NOTHING;

        UPDATE reserva SET estado = 'activa', updated_at = v_ini + interval '1 hour'
        WHERE id = v_res;

        IF v_estados[i] NOT IN ('pendiente_preparacion', 'activa') THEN
            UPDATE reserva
               SET estado = v_estados[i],
                   liberada_en = v_ini + interval '3 hours',
                   updated_at = v_ini + interval '3 hours'
             WHERE id = v_res;
        END IF;
    END LOOP;
END
$seed$;

-- ---------------------------------------------------------------------------
-- 13. Carritos (activo, abandonado, convertido y anonimo)
-- ---------------------------------------------------------------------------
INSERT INTO carrito (id, empresa_id, usuario_id, sesion_anonima, estado, created_at, updated_at)
VALUES
    ('11111111-1111-1111-1111-111111113001', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111302', NULL, 'activo', now() - interval '2 hours', now() - interval '1 hour'),
    ('11111111-1111-1111-1111-111111113002', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111305', NULL, 'abandonado', now() - interval '5 days', now() - interval '5 days'),
    ('11111111-1111-1111-1111-111111113003', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111306', NULL, 'convertido', now() - interval '10 days', now() - interval '9 days'),
    ('11111111-1111-1111-1111-111111113004', '11111111-1111-1111-1111-111111111111',
     NULL, 'anon-seed-25', 'activo', now() - interval '30 minutes', now() - interval '30 minutes')
ON CONFLICT DO NOTHING;

INSERT INTO carrito_detalle (id, empresa_id, carrito_id, variante_id, cantidad, precio_unitario)
SELECT md5('fs25-cartdet-' || c.id || '-' || v.id)::uuid,
       c.empresa_id, c.id, v.id, 1 + (abs(hashtext(c.id::text || v.id::text)) % 2), v.precio_venta
FROM carrito c
JOIN LATERAL (
    SELECT v.id, v.precio_venta
    FROM variante v
    WHERE v.empresa_id = c.empresa_id
    ORDER BY md5(v.id::text || c.id::text)
    LIMIT 2
) v ON true
WHERE c.empresa_id = '11111111-1111-1111-1111-111111111111'
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 14. Movimientos de inventario (kardex)
-- ---------------------------------------------------------------------------
DO $seed$
DECLARE
    v_emp uuid := '11111111-1111-1111-1111-111111111111';
    v_suc uuid := '11111111-1111-1111-1111-111111111101';
    v_admin uuid := '11111111-1111-1111-1111-111111111301';
    var record;
    v_stock int;
    i int := 0;
BEGIN
    FOR var IN
        SELECT v.id, i.stock_fisico
        FROM variante v
        JOIN inventario i ON i.variante_id = v.id AND i.empresa_id = v.empresa_id
        WHERE v.empresa_id = v_emp AND i.sucursal_id = v_suc
        ORDER BY v.sku
        LIMIT 8
    LOOP
        i := i + 1;
        v_stock := var.stock_fisico;

        IF NOT EXISTS (SELECT 1 FROM movimiento_inventario m
                       WHERE m.empresa_id = v_emp AND m.variante_id = var.id
                         AND m.motivo = 'Carga inicial seed 25') THEN
            INSERT INTO movimiento_inventario (empresa_id, variante_id, sucursal_id, tipo,
                                               cantidad, stock_anterior, stock_nuevo,
                                               referencia_tipo, motivo, usuario_id, ocurrido_en)
            VALUES (v_emp, var.id, v_suc, 'entrada',
                    50, v_stock, v_stock + 50,
                    'seed', 'Carga inicial seed 25', v_admin,
                    now() - interval '150 days' + make_interval(days => i));
        END IF;

        IF NOT EXISTS (SELECT 1 FROM movimiento_inventario m
                       WHERE m.empresa_id = v_emp AND m.variante_id = var.id
                         AND m.motivo = 'Ajuste por conteo fisico seed 25') THEN
            INSERT INTO movimiento_inventario (empresa_id, variante_id, sucursal_id, tipo,
                                               cantidad, stock_anterior, stock_nuevo,
                                               referencia_tipo, motivo, usuario_id, ocurrido_en)
            VALUES (v_emp, var.id, v_suc, 'ajuste',
                    -2, v_stock + 50, v_stock + 48,
                    'seed', 'Ajuste por conteo fisico seed 25', v_admin,
                    now() - interval '60 days' + make_interval(days => i));
        END IF;
    END LOOP;
END
$seed$;

-- ---------------------------------------------------------------------------
-- 15. Transferencias entre sucursales
-- ---------------------------------------------------------------------------
INSERT INTO transferencia_inventario (id, empresa_id, origen_id, destino_id, estado,
                                      solicitada_por, aprobada_por, created_at, updated_at)
VALUES
    ('11111111-1111-1111-1111-111111114001', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111101', '11111111-1111-1111-1111-111111112101',
     'en_transito', '11111111-1111-1111-1111-111111111301',
     '11111111-1111-1111-1111-111111111304', now() - interval '4 days', now() - interval '2 days'),
    ('11111111-1111-1111-1111-111111114002', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111101', '11111111-1111-1111-1111-111111112102',
     'recibida', '11111111-1111-1111-1111-111111111301',
     '11111111-1111-1111-1111-111111111304', now() - interval '15 days', now() - interval '10 days')
ON CONFLICT DO NOTHING;

INSERT INTO transferencia_detalle (id, empresa_id, transferencia_id, variante_id,
                                   cantidad, cantidad_recibida)
SELECT md5('fs25-trferdet-' || t.id || '-' || v.id)::uuid,
       t.empresa_id, t.id, v.id, 10,
       CASE WHEN t.estado = 'recibida' THEN 10 ELSE 0 END
FROM transferencia_inventario t
JOIN LATERAL (
    SELECT v.id
    FROM variante v
    WHERE v.empresa_id = t.empresa_id
    ORDER BY md5(v.id::text || t.id::text)
    LIMIT 4
) v ON true
WHERE t.empresa_id = '11111111-1111-1111-1111-111111111111'
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 16. Operaciones offline, conflictos e idempotencia
-- ---------------------------------------------------------------------------
INSERT INTO dispositivo (id, empresa_id, sucursal_id, nombre, serial, clave_publica,
                         ultima_sync, catalogo_version, estado)
VALUES
    ('11111111-1111-1111-1111-111111114101', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111112101', 'POS Norte', 'POS-NORTE-01',
     'seed-clave-publica-pos-norte', now() - interval '10 minutes', 12, 'activo'),
    ('11111111-1111-1111-1111-111111114102', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111112102', 'Tablet Sur', 'TABLET-SUR-01',
     'seed-clave-publica-tablet-sur', now() - interval '2 hours', 11, 'activo')
ON CONFLICT DO NOTHING;

INSERT INTO soft_lock (id, empresa_id, sucursal_id, variante_id, dispositivo_id,
                       cantidad, expira_en, creado_en)
SELECT md5('fs25-lock-' || v.id)::uuid,
       '11111111-1111-1111-1111-111111111111',
       '11111111-1111-1111-1111-111111112101',
       v.id, 'POS-NORTE-01', 1 + (abs(hashtext(v.id::text)) % 2),
       now() + interval '30 minutes', now() - interval '15 minutes'
FROM variante v
WHERE v.empresa_id = '11111111-1111-1111-1111-111111111111'
ORDER BY v.id
LIMIT 3
ON CONFLICT DO NOTHING;

INSERT INTO operacion_pendiente (id, empresa_id, dispositivo_id, sucursal_id, usuario_id,
                                 venta_id, tipo, payload, firma, nonce, idempotency_key,
                                 estado, intentos, ultimo_error, creada_en, procesada_en)
VALUES
    ('11111111-1111-1111-1111-111111114201', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111114101', '11111111-1111-1111-1111-111111112101',
     '11111111-1111-1111-1111-111111111304', NULL, 'venta_offline',
     '{"total": 450.00, "items": 2}'::jsonb, 'firma-seed-1', 'nonce-seed-1', 'seed25-off-1',
     'pendiente', 0, NULL, now() - interval '1 day', NULL),
    ('11111111-1111-1111-1111-111111114202', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111114101', '11111111-1111-1111-1111-111111112101',
     '11111111-1111-1111-1111-111111111304', NULL, 'pago_offline',
     '{"monto": 450.00, "metodo": "efectivo"}'::jsonb, 'firma-seed-2', 'nonce-seed-2', 'seed25-off-2',
     'procesando', 2, 'Reintento programado', now() - interval '20 hours', NULL),
    ('11111111-1111-1111-1111-111111114203', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111114102', '11111111-1111-1111-1111-111111112102',
     '11111111-1111-1111-1111-111111111304', NULL, 'ajuste_stock',
     '{"variante": "seed", "cantidad": -1}'::jsonb, 'firma-seed-3', 'nonce-seed-3', 'seed25-off-3',
     'conflicto', 3, 'Stock insuficiente en sucursal', now() - interval '18 hours', NULL),
    ('11111111-1111-1111-1111-111111114204', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111114102', '11111111-1111-1111-1111-111111112102',
     '11111111-1111-1111-1111-111111111304', NULL, 'devolucion_offline',
     '{"venta": "seed", "monto": 190.00}'::jsonb, 'firma-seed-4', 'nonce-seed-4', 'seed25-off-4',
     'aplicada', 1, NULL, now() - interval '12 hours', now() - interval '11 hours'),
    ('11111111-1111-1111-1111-111111114205', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111114101', '11111111-1111-1111-1111-111111112101',
     '11111111-1111-1111-1111-111111111304', NULL, 'reserva_offline',
     '{"reserva": "seed", "estado": "resuelta"}'::jsonb, 'firma-seed-5', 'nonce-seed-5', 'seed25-off-5',
     'resuelta', 2, NULL, now() - interval '8 hours', now() - interval '7 hours')
ON CONFLICT DO NOTHING;

INSERT INTO resolucion_conflicto (id, empresa_id, operacion_id, tipo, decision, detalle,
                                  resuelto_por, resuelto_en)
VALUES
    ('11111111-1111-1111-1111-111111114301', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111114203', 'stock_insuficiente', 'rechazar',
     '{"accion": "rechazar operacion por falta de stock"}'::jsonb,
     '11111111-1111-1111-1111-111111111301', now() - interval '17 hours'),
    ('11111111-1111-1111-1111-111111114302', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111114205', 'otro', 'aceptar',
     '{"accion": "reserva aplicada manualmente"}'::jsonb,
     '11111111-1111-1111-1111-111111111301', now() - interval '7 hours')
ON CONFLICT DO NOTHING;

INSERT INTO sync_registro_idempotencia (id, empresa_id, idempotency_key, tipo_operacion,
                                        resultado_json, procesado_en)
VALUES
    ('11111111-1111-1111-1111-111111114401', '11111111-1111-1111-1111-111111111111',
     'seed25-sync-1', 'venta_offline', '{"estado": "aplicada", "venta": "seed"}'::jsonb,
     now() - interval '10 hours'),
    ('11111111-1111-1111-1111-111111114402', '11111111-1111-1111-1111-111111111111',
     'seed25-sync-2', 'pago_offline', '{"estado": "aplicada", "pago": "seed"}'::jsonb,
     now() - interval '9 hours'),
    ('11111111-1111-1111-1111-111111114403', '11111111-1111-1111-1111-111111111111',
     'seed25-sync-3', 'ajuste_stock', '{"estado": "conflicto"}'::jsonb,
     now() - interval '8 hours')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 17. Cambio de prenda y nota de cambio (CU-29)
-- ---------------------------------------------------------------------------
INSERT INTO cambio_prenda (id, empresa_id, venta_id, sucursal_id, usuario_id, motivo,
                           estado, diferencia, created_at, updated_at)
VALUES ('11111111-1111-1111-1111-111111115001', '11111111-1111-1111-1111-111111111111',
        md5('fs25-venta-web-1-1')::uuid, '11111111-1111-1111-1111-111111111101',
        '11111111-1111-1111-1111-111111111302', 'Talla incorrecta',
        'completado', 0, now() - interval '20 days', now() - interval '19 days')
ON CONFLICT DO NOTHING;

INSERT INTO cambio_detalle (id, empresa_id, cambio_id, venta_detalle_id, variante_nueva_id,
                            cantidad, diferencia_precio)
SELECT '11111111-1111-1111-1111-111111115002'::uuid, vd.empresa_id,
       '11111111-1111-1111-1111-111111115001', vd.id,
       (SELECT v2.id FROM variante v2
        WHERE v2.empresa_id = vd.empresa_id AND v2.id <> vd.variante_id
          AND v2.prenda_id = (SELECT variante.prenda_id FROM variante WHERE variante.id = vd.variante_id)
        ORDER BY v2.id LIMIT 1),
       1, 0
FROM venta_detalle vd
WHERE vd.id = md5('fs25-vd-web-1-1-1')::uuid
  AND vd.empresa_id = '11111111-1111-1111-1111-111111111111'
ON CONFLICT DO NOTHING;

INSERT INTO nota_cambio (id, empresa_id, sucursal_id, venta_origen_id, variante_devuelta_id,
                         variante_nueva_id, cantidad, diferencia_monto, motivo, cajero_id,
                         qr_firma, created_at)
SELECT '11111111-1111-1111-1111-111111115003'::uuid, cd.empresa_id,
       '11111111-1111-1111-1111-111111111101', vd.venta_id, vd.variante_id,
       cd.variante_nueva_id, cd.cantidad, cd.diferencia_precio,
       'Cambio por talla', '11111111-1111-1111-1111-111111111304',
       'seed-qr-firma-cambio-1', now() - interval '19 days'
FROM cambio_detalle cd
JOIN venta_detalle vd ON vd.id = cd.venta_detalle_id AND vd.empresa_id = cd.empresa_id
WHERE cd.id = '11111111-1111-1111-1111-111111115002'
  AND cd.empresa_id = '11111111-1111-1111-1111-111111111111'
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 18. Modelos ML, predicciones y segmentos
-- ---------------------------------------------------------------------------
INSERT INTO modelo_ml (id, empresa_id, nombre, version, tipo, metricas, activo, entrenado_en)
VALUES
    ('11111111-1111-1111-1111-111111115001', '11111111-1111-1111-1111-111111111111',
     'Demanda Mensual', '2.0', 'demanda',
     '{"mae": 4.2, "rmse": 6.8, "r2": 0.81}'::jsonb, true, now() - interval '5 days'),
    ('11111111-1111-1111-1111-111111115002', '11111111-1111-1111-1111-111111111111',
     'Segmentacion RFM', '1.5', 'segmentacion',
     '{"silhouette": 0.64, "clusters": 4}'::jsonb, true, now() - interval '10 days'),
    ('11111111-1111-1111-1111-111111115003', '11111111-1111-1111-1111-111111111111',
     'Recomendacion Productos', '1.0', 'recomendacion',
     '{"precision_at_5": 0.37, "recall_at_5": 0.52}'::jsonb, true, now() - interval '15 days')
ON CONFLICT DO NOTHING;

INSERT INTO prediccion_demanda (id, empresa_id, modelo_ml_id, categoria_id, periodo,
                                demanda_estimada, intervalo_inferior, intervalo_superior)
SELECT md5('fs25-pred-' || c.id || '-' || o.m)::uuid,
       c.empresa_id, '11111111-1111-1111-1111-111111115001', c.id,
       (date_trunc('month', now()) + make_interval(months => o.m))::date,
       20 + (abs(hashtext(c.id::text || o.m::text)) % 60),
       15 + (abs(hashtext(c.id::text || o.m::text)) % 40),
       35 + (abs(hashtext(c.id::text || o.m::text)) % 40) + (abs(hashtext(c.id::text || o.m::text)) % 40)
FROM categoria c
CROSS JOIN (VALUES (0), (1), (2)) AS o(m)
WHERE c.empresa_id = '11111111-1111-1111-1111-111111111111'
ON CONFLICT DO NOTHING;

INSERT INTO segmento_cliente (id, empresa_id, modelo_ml_id, usuario_id, etiqueta, score,
                              vigente_desde, created_at)
SELECT md5('fs25-seg-' || u.id)::uuid, u.empresa_id,
       '11111111-1111-1111-1111-111111115002', u.id,
       (ARRAY['VIP', 'Frecuente', 'Ocasional', 'En riesgo'])[1 + (abs(hashtext(u.id::text)) % 4)],
       round((20 + (abs(hashtext(u.id::text)) % 80))::numeric / 100, 4),
       now() - interval '15 days', now() - interval '15 days'
FROM usuario u
WHERE u.empresa_id = '11111111-1111-1111-1111-111111111111'
  AND u.rol_id = '11111111-1111-1111-1111-111111111203'
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 19. Consultas IA y reportes exportados
-- ---------------------------------------------------------------------------
INSERT INTO consulta_ia_log (id, empresa_id, usuario_id, prompt, respuesta, modelo_llm,
                             canal, reporte_tipo, parametros_json, tokens_entrada,
                             tokens_salida, costo, latencia_ms, estado, ocurrido_en)
VALUES
    ('11111111-1111-1111-1111-111111115101', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', 'Cuales fueron las ventas del ultimo mes?',
     'Las ventas del ultimo mes sumaron Bs. 18.450 con 42 ordenes.', 'seed-llm',
     'texto', 'ventas_resumen', '{"periodo": "ultimo_mes"}'::jsonb, 120, 80, 0.0012, 950,
     'exitoso', now() - interval '6 days'),
    ('11111111-1111-1111-1111-111111115102', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', 'Que productos tienen bajo stock?',
     'Hay 7 variantes por debajo del minimo configurado.', 'seed-llm',
     'texto', 'stock_bajo', '{"limite": 10}'::jsonb, 90, 60, 0.0009, 720,
     'exitoso', now() - interval '5 days'),
    ('11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', 'Dame la prediccion de demanda por categoria',
     'La categoria Vestidos lidera con 74 unidades estimadas.', 'seed-llm',
     'voz', 'prediccion_demanda', '{"horizonte": 3}'::jsonb, 140, 100, 0.0016, 1200,
     'exitoso', now() - interval '4 days'),
    ('11111111-1111-1111-1111-111111115104', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', 'Cuales son los clientes VIP?',
     'Hay 3 clientes en el segmento VIP.', 'seed-llm',
     'texto', 'segmentos', '{"etiqueta": "VIP"}'::jsonb, 70, 45, 0.0007, 610,
     'exitoso', now() - interval '3 days'),
    ('11111111-1111-1111-1111-111111115105', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', 'Resumen de reservas activas',
     'Actualmente hay 2 reservas activas y 1 confirmada.', 'seed-llm',
     'texto', 'reservas_resumen', '{"estado": "activas"}'::jsonb, 60, 50, 0.0006, 580,
     'fallido', now() - interval '2 days'),
    ('11111111-1111-1111-1111-111111115106', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', 'Exporta el reporte de ventas por sucursal',
     'Reporte generado en formato PDF.', 'seed-llm',
     'texto', 'ventas_sucursal', '{"formato": "pdf"}'::jsonb, 80, 55, 0.0008, 840,
     'exitoso', now() - interval '1 day')
ON CONFLICT DO NOTHING;

INSERT INTO reporte_exportado (id, empresa_id, usuario_id, consulta_ia_log_id,
                               consulta_ocurrido_en, tipo_reporte, formato, archivo_url,
                               tamano_bytes, estado, generado_en, expira_en)
VALUES
    ('11111111-1111-1111-1111-111111115201', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', '11111111-1111-1111-1111-111111115101',
     now() - interval '6 days', 'ventas_resumen', 'pdf',
     'https://cdn.fashionstore.test/reportes/seed-ventas.pdf', 245760,
     'generado', now() - interval '6 days', now() + interval '24 days'),
    ('11111111-1111-1111-1111-111111115202', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', '11111111-1111-1111-1111-111111115102',
     now() - interval '5 days', 'stock_bajo', 'xlsx',
     'https://cdn.fashionstore.test/reportes/seed-stock.xlsx', 98304,
     'generado', now() - interval '5 days', now() + interval '25 days'),
    ('11111111-1111-1111-1111-111111115203', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111301', '11111111-1111-1111-1111-111111115106',
     now() - interval '1 day', 'ventas_sucursal', 'csv',
     'https://cdn.fashionstore.test/reportes/seed-sucursal.csv', 4096,
     'generado', now() - interval '1 day', now() + interval '29 days')
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 20. Realidad aumentada: avatares, medidas y prendas
-- ---------------------------------------------------------------------------
INSERT INTO avatar_cliente (id, empresa_id, usuario_id, nombre, modelo_url, altura_cm,
                            peso_kg, tono_piel)
VALUES
    ('11111111-1111-1111-1111-111111116001', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111302', 'Avatar de Cliente Demo',
     'https://cdn.fashionstore.test/avatares/seed-cliente.glb', 168.00, 62.00, 'medio'),
    ('11111111-1111-1111-1111-111111116002', '11111111-1111-1111-1111-111111111111',
     '11111111-1111-1111-1111-111111111305', 'Avatar de Valeria',
     'https://cdn.fashionstore.test/avatares/seed-valeria.glb', 160.00, 55.00, 'claro')
ON CONFLICT DO NOTHING;

INSERT INTO medida_corporal (id, empresa_id, avatar_id, tipo, valor_cm)
SELECT md5('fs25-med-' || m.avatar_id || '-' || m.tipo)::uuid, m.empresa_id, m.avatar_id,
       m.tipo, m.valor
FROM (
    VALUES
        ('11111111-1111-1111-1111-111111116001'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'busto', 88.00),
        ('11111111-1111-1111-1111-111111116001'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'cintura', 70.00),
        ('11111111-1111-1111-1111-111111116001'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'cadera', 96.00),
        ('11111111-1111-1111-1111-111111116001'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'hombro', 40.00),
        ('11111111-1111-1111-1111-111111116001'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'largo_pierna', 100.00),
        ('11111111-1111-1111-1111-111111116002'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'busto', 84.00),
        ('11111111-1111-1111-1111-111111116002'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'cintura', 66.00),
        ('11111111-1111-1111-1111-111111116002'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'cadera', 92.00),
        ('11111111-1111-1111-1111-111111116002'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'hombro', 38.00),
        ('11111111-1111-1111-1111-111111116002'::uuid,
         '11111111-1111-1111-1111-111111111111'::uuid, 'largo_pierna', 96.00)
) AS m(avatar_id, empresa_id, tipo, valor)
ON CONFLICT DO NOTHING;

INSERT INTO prenda_ar (id, empresa_id, prenda_id, variante_id, modelo_url, textura_url,
                       puntos_ajuste, talla_referencia, activo)
SELECT md5('fs25-ar-' || p.id)::uuid, p.empresa_id, p.id,
       (SELECT v.id FROM variante v WHERE v.prenda_id = p.id AND v.empresa_id = p.empresa_id
        ORDER BY v.id LIMIT 1),
       'https://cdn.fashionstore.test/ar/' || lower(p.codigo) || '.glb',
       'https://cdn.fashionstore.test/ar/' || lower(p.codigo) || '-textura.jpg',
       '{"hombros": [0.0, 1.0, 0.0], "cintura": [0.0, 0.0, 0.0]}'::jsonb,
       'M', true
FROM prenda p
WHERE p.empresa_id = '11111111-1111-1111-1111-111111111111'
ORDER BY p.codigo
LIMIT 10
ON CONFLICT DO NOTHING;

INSERT INTO sesion_prueba_virtual (id, empresa_id, usuario_id, avatar_id, prenda_id,
                                   variante_id, estado, resultado_url, iniciada_en,
                                   finalizada_en, created_at)
SELECT md5('fs25-sesion-ar-' || p.id)::uuid, p.empresa_id,
       '11111111-1111-1111-1111-111111111302',
       '11111111-1111-1111-1111-111111116001', p.id,
       (SELECT v.id FROM variante v WHERE v.prenda_id = p.id AND v.empresa_id = p.empresa_id
        ORDER BY v.id LIMIT 1),
       (ARRAY['completada', 'iniciada', 'abandonada'])[1 + (abs(hashtext(p.id::text)) % 3)],
       CASE WHEN abs(hashtext(p.id::text)) % 3 = 0
            THEN 'https://cdn.fashionstore.test/ar/resultado-' || lower(p.codigo) || '.png' END,
       now() - interval '10 days', now() - interval '10 days' + interval '2 minutes',
       now() - interval '10 days'
FROM prenda p
WHERE p.empresa_id = '11111111-1111-1111-1111-111111111111'
ORDER BY p.codigo
LIMIT 5
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 21. Verificacion rapida
-- ---------------------------------------------------------------------------
SELECT 'sucursales' AS entidad, count(*) AS total FROM sucursal WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'usuarios', count(*) FROM usuario WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'categorias', count(*) FROM categoria WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'prendas', count(*) FROM prenda WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'variantes', count(*) FROM variante WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'inventario', count(*) FROM inventario WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'ventas', count(*) FROM venta WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'venta_detalle', count(*) FROM venta_detalle WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'pagos', count(*) FROM pago WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'reservas', count(*) FROM reserva WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'carritos', count(*) FROM carrito WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'movimientos', count(*) FROM movimiento_inventario WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'transferencias', count(*) FROM transferencia_inventario WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'operaciones_offline', count(*) FROM operacion_pendiente WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'predicciones', count(*) FROM prediccion_demanda WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'segmentos', count(*) FROM segmento_cliente WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'consultas_ia', count(*) FROM consulta_ia_log WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'avatares', count(*) FROM avatar_cliente WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'prendas_ar', count(*) FROM prenda_ar WHERE empresa_id = '11111111-1111-1111-1111-111111111111'
UNION ALL SELECT 'sesiones_ar', count(*) FROM sesion_prueba_virtual WHERE empresa_id = '11111111-1111-1111-1111-111111111111';

COMMIT;





