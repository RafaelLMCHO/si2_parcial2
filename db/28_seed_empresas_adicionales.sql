-- ============================================================================
-- 28_seed_empresas_adicionales.sql
-- Seeder completo e idempotente para las 5 empresas adicionales:
--   zara, mango, hm, pullbear, bershka
-- Agrega sucursales, clientes, empleados, temporadas, colecciones,
-- proveedores, prendas en todas las categorias, variantes, inventario,
-- ventas WEB/POS de 8 meses (para Reportes CU-33 y ML CU-35), reservas,
-- carritos, movimientos, transferencias, offline, IA y vestidor AR.
-- NO forma parte de db/run_all.sql para no afectar las pruebas de aislamiento.
-- Uso: .\scripts\seed_empresas.ps1
-- ============================================================================
\set ON_ERROR_STOP on
BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Sucursales adicionales (2 por empresa -> 3 sucursales activas c/u)
-- ---------------------------------------------------------------------------
INSERT INTO sucursal (id, empresa_id, ciudad_id, nombre, direccion, telefono, es_matriz, estado)
SELECT
    md5('fs28-suc-' || e.slug || '-' || extra.suf)::uuid,
    e.id,
    c.id,
    initcap(e.slug) || ' ' || extra.nombre,
    extra.direccion,
    extra.telefono,
    false,
    'activa'
FROM empresa e
CROSS JOIN (
    VALUES
        ('norte', 'La Paz', 'Sucursal Norte', 'Av. 6 de Agosto #2240, Sopocachi', '+591 2 2441100'),
        ('sur', 'Cochabamba', 'Sucursal Sur', 'Av. America #620, Queru Queru', '+591 4 4452200')
) AS extra(suf, ciudad_nombre, nombre, direccion, telefono)
JOIN ciudad c ON c.nombre = extra.ciudad_nombre
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND NOT EXISTS (
      SELECT 1 FROM sucursal s
      WHERE s.empresa_id = e.id AND s.nombre = initcap(e.slug) || ' ' || extra.nombre
  )
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 2. Empleados y clientes adicionales por empresa (>= 7 clientes para K-Means)
-- ---------------------------------------------------------------------------
-- Cajero extra en Sucursal Norte
INSERT INTO usuario (id, empresa_id, rol_id, sucursal_id, nombre, correo, password_hash,
                     telefono, email_verificado, email_verificado_en, estado)
SELECT
    md5('fs28-usr-' || e.slug || '-cajero2')::uuid,
    e.id,
    r.id,
    s.id,
    'Cajero Norte ' || initcap(e.slug),
    'cajero2@' || e.slug || '.bo',
    crypt('Cajero123!', gen_salt('bf', 10)),
    '+591 7200' || lpad((abs(hashtext(e.slug)) % 9000 + 1000)::text, 4, '0'),
    true,
    now() - interval '60 days',
    'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'cajero'
JOIN sucursal s ON s.empresa_id = e.id AND s.nombre = initcap(e.slug) || ' Sucursal Norte'
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, correo) DO UPDATE
    SET email_verificado = true,
        estado = 'activo';

-- Encargado extra en Sucursal Sur
INSERT INTO usuario (id, empresa_id, rol_id, sucursal_id, nombre, correo, password_hash,
                     telefono, email_verificado, email_verificado_en, estado)
SELECT
    md5('fs28-usr-' || e.slug || '-encargado2')::uuid,
    e.id,
    r.id,
    s.id,
    'Encargado Sur ' || initcap(e.slug),
    'encargado2@' || e.slug || '.bo',
    crypt('Encargado123!', gen_salt('bf', 10)),
    '+591 7300' || lpad((abs(hashtext(e.slug)) % 9000 + 1000)::text, 4, '0'),
    true,
    now() - interval '60 days',
    'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'encargado'
JOIN sucursal s ON s.empresa_id = e.id AND s.nombre = initcap(e.slug) || ' Sucursal Sur'
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, correo) DO UPDATE
    SET email_verificado = true,
        estado = 'activo';

-- 6 clientes adicionales por empresa (cliente1..cliente6@<slug>.bo / Cliente123!)
INSERT INTO usuario (id, empresa_id, rol_id, sucursal_id, nombre, correo, password_hash,
                     telefono, email_verificado, email_verificado_en, estado)
SELECT
    md5('fs28-usr-' || e.slug || '-cli-' || c.num)::uuid,
    e.id,
    r.id,
    NULL,
    c.nombre || ' (' || upper(e.slug) || ')',
    'cliente' || c.num || '@' || e.slug || '.bo',
    crypt('Cliente123!', gen_salt('bf', 10)),
    '+591 7' || c.num || lpad((abs(hashtext(e.slug || c.num)) % 1000000)::text, 6, '0'),
    true,
    now() - make_interval(days => 100 - c.num * 10),
    'activo'
FROM empresa e
JOIN rol r ON r.empresa_id = e.id AND r.nombre = 'cliente'
CROSS JOIN (
    VALUES
        (1, 'Valeria Rojas'),
        (2, 'Diego Vargas'),
        (3, 'Camila Quispe'),
        (4, 'Mateo Flores'),
        (5, 'Isabella Cruz'),
        (6, 'Sebastian Paz')
) AS c(num, nombre)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, correo) DO UPDATE
    SET email_verificado = true,
        estado = 'activo';

-- Asegurar email_verificado en todos los usuarios de las 5 empresas
UPDATE usuario u
   SET email_verificado = true,
       email_verificado_en = COALESCE(u.email_verificado_en, now())
  FROM empresa e
 WHERE u.empresa_id = e.id
   AND e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
   AND u.email_verificado = false;

-- ---------------------------------------------------------------------------
-- 3. Temporadas, colecciones y proveedores
-- ---------------------------------------------------------------------------
INSERT INTO temporada (id, empresa_id, nombre, fecha_inicio, fecha_fin)
SELECT
    md5('fs28-temp-' || e.slug || '-' || t.codigo)::uuid,
    e.id,
    t.nombre,
    t.f_ini,
    t.f_fin
FROM empresa e
CROSS JOIN (
    VALUES
        ('pri26', 'Primavera 2026', DATE '2026-01-01', DATE '2026-06-30'),
        ('oto26', 'Otono - Invierno 2026', DATE '2026-07-01', DATE '2026-12-31')
) AS t(codigo, nombre, f_ini, f_fin)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, nombre) DO NOTHING;

INSERT INTO coleccion (id, empresa_id, nombre, anio)
SELECT
    md5('fs28-col-' || e.slug || '-' || col.codigo)::uuid,
    e.id,
    col.nombre,
    2026
FROM empresa e
CROSS JOIN (
    VALUES
        ('esenciales', 'Esenciales 2026'),
        ('urbana', 'Urbana Signature 2026')
) AS col(codigo, nombre)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, nombre) DO NOTHING;

INSERT INTO proveedor (id, empresa_id, nombre, nit, correo, telefono)
SELECT
    md5('fs28-prov-' || e.slug || '-' || p.suf)::uuid,
    e.id,
    p.prefijo || ' ' || initcap(e.slug),
    'NIT-' || upper(left(e.slug, 6)) || '-' || p.suf,
    'proveedores+' || p.suf || '@' || e.slug || '.bo',
    e.telefono
FROM empresa e
CROSS JOIN (
    VALUES
        ('01', 'Textiles Andinos'),
        ('02', 'Importadora Moda Global')
) AS p(suf, prefijo)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, nit) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 4. Catalogo completo: completar camisas existentes y agregar 8 prendas mas
-- ---------------------------------------------------------------------------
UPDATE prenda p
   SET temporada_id = COALESCE(p.temporada_id, (SELECT t.id FROM temporada t WHERE t.empresa_id = p.empresa_id ORDER BY t.nombre LIMIT 1)),
       coleccion_id = COALESCE(p.coleccion_id, (SELECT c.id FROM coleccion c WHERE c.empresa_id = p.empresa_id ORDER BY c.nombre LIMIT 1)),
       proveedor_id = COALESCE(p.proveedor_id, (SELECT pr.id FROM proveedor pr WHERE pr.empresa_id = p.empresa_id ORDER BY pr.nit LIMIT 1)),
       marca = COALESCE(p.marca, initcap(e.slug)),
       imagen_url = COALESCE(p.imagen_url, 'https://cdn.fashionstore.test/' || e.slug || '/' || lower(p.codigo) || '.jpg')
  FROM empresa e
 WHERE p.empresa_id = e.id
   AND e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka');

INSERT INTO prenda (
    id, empresa_id, categoria_id, temporada_id, coleccion_id, proveedor_id,
    codigo, nombre, descripcion, marca, genero, precio_base, imagen_url, estado
)
SELECT
    md5('fs28-prenda-' || e.slug || '-' || pr.cod)::uuid,
    e.id,
    cat.id,
    t.id,
    col.id,
    prov.id,
    upper(e.slug) || '-' || pr.cod,
    pr.nombre,
    pr.descripcion,
    initcap(e.slug),
    pr.genero,
    pr.precio,
    'https://cdn.fashionstore.test/' || e.slug || '/' || lower(pr.cod) || '.jpg',
    'activa'
FROM empresa e
CROSS JOIN (
    VALUES
        ('04', 'Pantalones & Jeans', 'Jean Recto Clasico', 'Jean denim stretch de tiro medio y corte recto', 'unisex', 269.00),
        ('05', 'Pantalones & Jeans', 'Pantalon Chino Slim', 'Pantalon chino de gabardina ligera elastizada', 'hombre', 229.00),
        ('06', 'Vestidos & Faldas', 'Vestido Midi Floral', 'Vestido fluido largo midi con cintura entallada', 'mujer', 319.00),
        ('07', 'Vestidos & Faldas', 'Falda Plisada Satin', 'Falda midi plisada de tela satinada', 'mujer', 219.00),
        ('08', 'Chaquetas & Abrigos', 'Chaqueta Denim Urbana', 'Chaqueta denim lavada con bolsillos frontales', 'unisex', 359.00),
        ('09', 'Chaquetas & Abrigos', 'Blazer Sastrero Fit', 'Blazer estructurado con forro respirable', 'mujer', 429.00),
        ('10', 'Calzado & Accesorios', 'Zapatilla Urbana Blanca', 'Zapatilla minimalista suela ultraligera', 'unisex', 349.00),
        ('11', 'Calzado & Accesorios', 'Botin Cuero Casual', 'Botin clasico acabado mate de alta resistencia', 'hombre', 449.00)
) AS pr(cod, cat_nombre, nombre, descripcion, genero, precio)
JOIN categoria cat ON cat.empresa_id = e.id AND cat.nombre = pr.cat_nombre
JOIN LATERAL (SELECT id FROM temporada WHERE empresa_id = e.id ORDER BY nombre LIMIT 1) t ON true
JOIN LATERAL (SELECT id FROM coleccion WHERE empresa_id = e.id ORDER BY nombre LIMIT 1) col ON true
JOIN LATERAL (SELECT id FROM proveedor WHERE empresa_id = e.id ORDER BY nit LIMIT 1) prov ON true
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, codigo) DO NOTHING;

-- Imagenes principales en prenda_recurso
INSERT INTO prenda_recurso (id, empresa_id, prenda_id, tipo, url, mime_type, orden, es_principal)
SELECT
    md5('fs28-img-' || p.id)::uuid,
    p.empresa_id,
    p.id,
    'imagen',
    p.imagen_url,
    'image/jpeg',
    0,
    true
FROM prenda p
JOIN empresa e ON e.id = p.empresa_id
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND p.imagen_url IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM prenda_recurso r WHERE r.empresa_id = p.empresa_id AND r.prenda_id = p.id
  )
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 5. Variantes para las 8 prendas nuevas (3 colores x 3 tallas)
-- ---------------------------------------------------------------------------
WITH nuevas AS (
    SELECT p.id AS prenda_id, p.empresa_id, p.codigo, p.precio_base, cat.nombre AS cat_nombre
    FROM prenda p
    JOIN empresa e ON e.id = p.empresa_id
    JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
    WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
      AND right(p.codigo, 2) IN ('04','05','06','07','08','09','10','11')
), colores AS (
    SELECT n.*,
           unnest(ARRAY['Negro', 'Beige', 'Azul Marino']) AS color_nombre
    FROM nuevas n
), tallas AS (
    SELECT c.*,
           unnest(CASE WHEN c.cat_nombre = 'Calzado & Accesorios'
                       THEN ARRAY['36', '38', '40']
                       ELSE ARRAY['XS', 'S', 'M']
                  END) AS talla_nombre
    FROM colores c
)
INSERT INTO variante (
    id, empresa_id, prenda_id, color_id, talla_id, sku, codigo_barras, precio_venta, costo, estado
)
SELECT
    md5('fs28-var-' || t.empresa_id || '-' || t.codigo || '-' || t.color_nombre || '-' || t.talla_nombre)::uuid,
    t.empresa_id,
    t.prenda_id,
    co.id,
    ta.id,
    t.codigo || '-' || upper(left(replace(t.color_nombre, ' ', ''), 3)) || '-' || t.talla_nombre,
    '778' || lpad((abs(hashtext(t.codigo || t.color_nombre || t.talla_nombre)) % 1000000000)::text, 9, '0'),
    t.precio_base,
    round(t.precio_base * 0.45, 2),
    'activa'
FROM tallas t
JOIN color co ON co.nombre = t.color_nombre
JOIN talla ta ON ta.nombre = t.talla_nombre
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- 6. Inventario completo en las 3 sucursales de cada empresa
-- ---------------------------------------------------------------------------
INSERT INTO inventario (id, empresa_id, variante_id, sucursal_id, stock_fisico, stock_reservado, stock_minimo, ubicacion)
SELECT
    md5('fs28-inv-' || v.id || '-' || s.id)::uuid,
    e.id,
    v.id,
    s.id,
    CASE WHEN abs(hashtext(v.sku || s.id::text)) % 15 = 0
         THEN 3 + (abs(hashtext(v.sku || s.id::text)) % 5)
         ELSE 35 + (abs(hashtext(v.sku || s.id::text)) % 110)
    END,
    0,
    10,
    'Estanteria ' || chr(65 + (abs(hashtext(v.sku)) % 6))
FROM empresa e
JOIN variante v ON v.empresa_id = e.id AND v.deleted_at IS NULL
JOIN sucursal s ON s.empresa_id = e.id AND s.estado = 'activa' AND s.deleted_at IS NULL
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, variante_id, sucursal_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 7. Direcciones de clientes y Cupones por empresa
-- ---------------------------------------------------------------------------
INSERT INTO direccion_cliente (
    id, empresa_id, usuario_id, etiqueta, destinatario, telefono,
    linea1, linea2, ciudad_id, codigo_postal, referencia, es_principal
)
SELECT
    md5('fs28-dir-' || u.id)::uuid,
    u.empresa_id,
    u.id,
    'Casa',
    u.nombre,
    COALESCE(u.telefono, '+591 70000001'),
    'Av. Principal #' || (100 + abs(hashtext(u.id::text)) % 800),
    'Zona Central',
    (SELECT id FROM ciudad ORDER BY abs(hashtext(u.id::text || id::text)) LIMIT 1),
    'CP' || lpad((abs(hashtext(u.id::text)) % 9000 + 1000)::text, 4, '0'),
    'Porton negro, timbre 2',
    true
FROM usuario u
JOIN empresa e ON e.id = u.empresa_id
JOIN rol r ON r.id = u.rol_id
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
  AND r.nombre = 'cliente'
ON CONFLICT DO NOTHING;

INSERT INTO cupon (
    id, empresa_id, codigo, descripcion, tipo, valor, monto_minimo,
    usos_maximos, usos_por_usuario, fecha_inicio, fecha_fin, activo
)
SELECT
    md5('fs28-cupon-' || e.slug || '-' || cp.codigo)::uuid,
    e.id,
    cp.codigo,
    cp.descripcion,
    cp.tipo,
    cp.valor,
    cp.monto_min,
    500,
    10,
    now() - interval '60 days',
    now() + interval '120 days',
    true
FROM empresa e
CROSS JOIN (
    VALUES
        ('BIENVENIDO10', '10% de descuento de bienvenida', 'porcentaje', 10.00, 0.00),
        ('VERANO20', '20% de descuento temporada 2026', 'porcentaje', 20.00, 150.00)
) AS cp(codigo, descripcion, tipo, valor, monto_min)
WHERE e.slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
ON CONFLICT (empresa_id, codigo) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 8. Ventas WEB y POS durante 8 meses por cada categoria + Reservas + Movs + AR/IA/ML
-- ---------------------------------------------------------------------------
DO $seed28$
DECLARE
    emp record;
    m int;
    cat record;
    var record;
    cli record;
    v_dir uuid;
    v_suc_matriz uuid;
    v_suc uuid;
    v_admin uuid;
    v_cajero uuid;
    v_cupon uuid;
    v_venta uuid;
    v_sub numeric(12,2);
    v_desc numeric(12,2);
    v_imp numeric(12,2);
    v_total numeric(12,2);
    v_mes_base timestamptz;
    v_fecha timestamptz;
    v_estado varchar(30);
    v_env_estado varchar(20);
    v_metodo varchar(20);
    v_num varchar(30);
    v_idem varchar(80);
    v_idx int;
    v_qty int;

    -- Reservas
    i int;
    v_res uuid;
    v_var_res uuid;
    v_res_estados text[] := ARRAY['pendiente_preparacion', 'preparada', 'activa', 'confirmada', 'completada', 'cancelada'];
    v_ini timestamptz;

    -- Transferencias y Offline
    v_suc_norte uuid;
    v_suc_sur uuid;
    v_disp1 uuid;
    v_disp2 uuid;
    v_trf1 uuid;
    v_trf2 uuid;
    v_op1 uuid;
    v_op2 uuid;
    v_op3 uuid;

    -- ML / IA / AR
    v_ml_dem uuid;
    v_ml_seg uuid;
    v_ml_rec uuid;
    v_cia_1 uuid;
    v_cia_2 uuid;
    v_av_idx int;
    v_av_id uuid;
    med text;
    v_pa_idx int;
BEGIN
    FOR emp IN
        SELECT id, slug, nombre
        FROM empresa
        WHERE slug IN ('zara', 'mango', 'hm', 'pullbear', 'bershka')
    LOOP
        SELECT id INTO v_suc_matriz FROM sucursal WHERE empresa_id = emp.id AND es_matriz = true LIMIT 1;
        SELECT id INTO v_suc_norte  FROM sucursal WHERE empresa_id = emp.id AND nombre LIKE '%Sucursal Norte%' LIMIT 1;
        SELECT id INTO v_suc_sur    FROM sucursal WHERE empresa_id = emp.id AND nombre LIKE '%Sucursal Sur%' LIMIT 1;
        SELECT u.id INTO v_admin    FROM usuario u JOIN rol r ON r.id = u.rol_id WHERE u.empresa_id = emp.id AND r.nombre = 'administrador' LIMIT 1;
        SELECT id INTO v_cupon      FROM cupon WHERE empresa_id = emp.id AND codigo = 'BIENVENIDO10' LIMIT 1;

        -- A. Ventas WEB (8 meses x 5 categorias)
        FOR m IN 0..7 LOOP
            v_mes_base := date_trunc('month', now()) - make_interval(months => m);

            FOR cat IN
                SELECT id, nombre, row_number() OVER (ORDER BY nombre) AS seq
                FROM categoria
                WHERE empresa_id = emp.id
            LOOP
                IF m = 0 AND cat.seq = 1 THEN
                    v_fecha := now() - interval '2 hours';
                ELSE
                    v_fecha := LEAST(
                        now() - interval '3 hours',
                        v_mes_base + make_interval(days => ((cat.seq * 4) % 24)::int, hours => (10 + cat.seq)::int)
                    );
                END IF;

                SELECT u.id, u.nombre INTO cli
                FROM usuario u
                JOIN rol r ON r.id = u.rol_id
                WHERE u.empresa_id = emp.id AND r.nombre = 'cliente'
                ORDER BY u.correo
                OFFSET ((m * 3 + cat.seq - 1) % 7)
                LIMIT 1;

                SELECT d.id INTO v_dir
                FROM direccion_cliente d
                WHERE d.empresa_id = emp.id AND d.usuario_id = cli.id
                LIMIT 1;

                v_venta := md5('fs28-venta-web-' || emp.slug || '-' || m || '-' || cat.seq)::uuid;
                v_num := 'WEB-' || to_char(v_fecha, 'YYYYMM') || '-' || lpad((m * 10 + cat.seq)::text, 3, '0');
                v_idem := 'fs28-web-' || emp.slug || '-' || m || '-' || cat.seq;
                v_estado := CASE WHEN m = 0 THEN 'pagada' WHEN m = 1 THEN 'enviada' ELSE 'completada' END;

                INSERT INTO venta (
                    id, empresa_id, numero, sucursal_id, usuario_id, canal,
                    fecha_hora, fecha_hora_cliente, fecha_recepcion_servidor,
                    moneda, subtotal, descuento, impuesto, total, estado,
                    direccion_id, idempotency_key, cliente_nombre, cliente_documento,
                    created_at, updated_at
                )
                VALUES (
                    v_venta, emp.id, v_num, v_suc_matriz, cli.id, 'WEB',
                    v_fecha, v_fecha + interval '1 minute', v_fecha + interval '2 minutes',
                    'BOB', 0, 0, 0, 0, v_estado,
                    v_dir, v_idem, cli.nombre,
                    'CI-' || lpad((abs(hashtext(cli.id::text)) % 9000000 + 1000000)::text, 7, '0'),
                    v_fecha, v_fecha
                )
                ON CONFLICT DO NOTHING;

                IF FOUND THEN
                    v_idx := 0;
                    FOR var IN
                        SELECT v.id, v.precio_venta
                        FROM variante v
                        JOIN prenda p ON p.id = v.prenda_id AND p.empresa_id = v.empresa_id
                        WHERE v.empresa_id = emp.id AND p.categoria_id = cat.id
                        ORDER BY md5(v.id::text || m::text || cat.seq::text)
                        LIMIT (1 + ((m + cat.seq) % 2))
                    LOOP
                        v_idx := v_idx + 1;
                        -- Variacion creciente hacia los meses recientes para R2/MSE reales en scikit-learn
                        v_qty := 1 + (((7 - m) + v_idx + cat.seq) % 4);
                        INSERT INTO venta_detalle (
                            id, empresa_id, venta_id, variante_id, cantidad,
                            precio_lista, precio_unitario, descuento_linea, subtotal
                        )
                        VALUES (
                            md5('fs28-vd-web-' || emp.slug || '-' || m || '-' || cat.seq || '-' || v_idx)::uuid,
                            emp.id, v_venta, var.id, v_qty,
                            var.precio_venta, var.precio_venta, 0, v_qty * var.precio_venta
                        )
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
                    INSERT INTO pago (
                        id, empresa_id, venta_id, monto, metodo, idempotency_key,
                        estado, referencia, pagado_en
                    )
                    VALUES (
                        md5('fs28-pago-web-' || emp.slug || '-' || m || '-' || cat.seq)::uuid,
                        emp.id, v_venta, v_total, v_metodo,
                        'fs28-pago-web-' || emp.slug || '-' || m || '-' || cat.seq,
                        'completado', 'FS28-' || upper(emp.slug) || '-' || m || '-' || cat.seq,
                        v_fecha + interval '5 minutes'
                    )
                    ON CONFLICT DO NOTHING;

                    IF NOT EXISTS (SELECT 1 FROM venta_estado_historial h WHERE h.empresa_id = emp.id AND h.venta_id = v_venta AND h.estado_nuevo = 'pendiente_pago') THEN
                        INSERT INTO venta_estado_historial (empresa_id, venta_id, estado_anterior, estado_nuevo, motivo, usuario_id, ocurrido_en)
                        VALUES (emp.id, v_venta, NULL, 'pendiente_pago', 'Creacion orden web', cli.id, v_fecha);
                    END IF;

                    IF NOT EXISTS (SELECT 1 FROM venta_estado_historial h WHERE h.empresa_id = emp.id AND h.venta_id = v_venta AND h.estado_nuevo = v_estado) THEN
                        INSERT INTO venta_estado_historial (empresa_id, venta_id, estado_anterior, estado_nuevo, motivo, usuario_id, ocurrido_en)
                        VALUES (emp.id, v_venta, 'pendiente_pago', v_estado, 'Pago confirmado', cli.id, v_fecha + interval '5 minutes');
                    END IF;

                    IF v_dir IS NOT NULL AND ((m + cat.seq) % 2 = 0) THEN
                        v_env_estado := CASE WHEN m >= 2 THEN 'entregado' WHEN m = 1 THEN 'en_transito' ELSE 'enviado' END;
                        INSERT INTO envio (
                            id, empresa_id, venta_id, direccion_id, transportista, tracking,
                            estado, costo, fecha_estimada, enviado_en, entregado_en, created_at, updated_at
                        )
                        VALUES (
                            md5('fs28-env-web-' || emp.slug || '-' || m || '-' || cat.seq)::uuid,
                            emp.id, v_venta, v_dir, 'Courier Bolivia Express',
                            'TRK-' || upper(emp.slug) || '-' || to_char(v_fecha, 'YYMM') || '-' || m || cat.seq,
                            v_env_estado, 15.00, (v_fecha + interval '4 days')::date,
                            v_fecha + interval '1 day',
                            CASE WHEN v_env_estado = 'entregado' THEN v_fecha + interval '3 days' END,
                            v_fecha, v_fecha + interval '1 day'
                        )
                        ON CONFLICT DO NOTHING;
                    END IF;

                    IF m = 1 AND cat.seq <= 2 AND v_cupon IS NOT NULL THEN
                        UPDATE venta SET cupon_id = v_cupon WHERE id = v_venta AND cupon_id IS NULL;
                        INSERT INTO cupon_uso (id, empresa_id, cupon_id, venta_id, usuario_id, usado_en)
                        VALUES (md5('fs28-cupuso-' || emp.slug || '-' || m || '-' || cat.seq)::uuid, emp.id, v_cupon, v_venta, cli.id, v_fecha + interval '3 minutes')
                        ON CONFLICT (empresa_id, cupon_id, venta_id) DO NOTHING;
                    END IF;
                END IF;

                -- B. Venta POS en las primeras 3 categorias (distribuidas en las 3 sucursales)
                IF cat.seq <= 3 THEN
                    IF m = 0 AND cat.seq = 1 THEN
                        v_fecha := now() - interval '1 hour';
                    ELSE
                        v_fecha := LEAST(
                            now() - interval '4 hours',
                            v_mes_base + make_interval(days => (1 + (cat.seq * 5) % 22)::int, hours => 16)
                        );
                    END IF;

                    SELECT s.id INTO v_suc
                    FROM sucursal s
                    WHERE s.empresa_id = emp.id AND s.estado = 'activa'
                    ORDER BY s.es_matriz DESC, s.nombre
                    OFFSET ((m + cat.seq) % 3)
                    LIMIT 1;

                    SELECT u.id INTO v_cajero
                    FROM usuario u
                    JOIN rol r ON r.id = u.rol_id
                    WHERE u.empresa_id = emp.id AND r.nombre = 'cajero'
                    ORDER BY u.correo
                    OFFSET (m % 2)
                    LIMIT 1;

                    v_venta := md5('fs28-venta-pos-' || emp.slug || '-' || m || '-' || cat.seq)::uuid;
                    v_num := 'POS-' || to_char(v_fecha, 'YYYYMM') || '-' || lpad((m * 10 + cat.seq)::text, 3, '0');

                    INSERT INTO venta (
                        id, empresa_id, numero, sucursal_id, cajero_id, canal,
                        fecha_hora, fecha_hora_cliente, fecha_recepcion_servidor,
                        moneda, subtotal, descuento, impuesto, total, estado,
                        idempotency_key, cliente_nombre, created_at, updated_at
                    )
                    VALUES (
                        v_venta, emp.id, v_num, v_suc, v_cajero, 'POS',
                        v_fecha, v_fecha, v_fecha + interval '2 seconds',
                        'BOB', 0, 0, 0, 0, 'completada',
                        'fs28-pos-' || emp.slug || '-' || m || '-' || cat.seq,
                        'Cliente de Mostrador',
                        v_fecha, v_fecha
                    )
                    ON CONFLICT DO NOTHING;

                    IF FOUND THEN
                        v_idx := 0;
                        FOR var IN
                            SELECT v.id, v.precio_venta
                            FROM variante v
                            JOIN prenda p ON p.id = v.prenda_id AND p.empresa_id = v.empresa_id
                            WHERE v.empresa_id = emp.id AND p.categoria_id = cat.id
                            ORDER BY md5(v.id::text || 'pos' || m::text || cat.seq::text)
                            LIMIT 2
                        LOOP
                            v_idx := v_idx + 1;
                            v_qty := 1 + (((7 - m) + v_idx) % 3);
                            INSERT INTO venta_detalle (
                                id, empresa_id, venta_id, variante_id, cantidad,
                                precio_lista, precio_unitario, descuento_linea, subtotal
                            )
                            VALUES (
                                md5('fs28-vd-pos-' || emp.slug || '-' || m || '-' || cat.seq || '-' || v_idx)::uuid,
                                emp.id, v_venta, var.id, v_qty,
                                var.precio_venta, var.precio_venta, 0, v_qty * var.precio_venta
                            )
                            ON CONFLICT DO NOTHING;
                        END LOOP;

                        SELECT subtotal INTO v_sub FROM venta WHERE id = v_venta;
                        v_imp := round(v_sub * 0.13, 2);
                        UPDATE venta
                           SET impuesto = v_imp,
                               total = v_sub + v_imp,
                               updated_at = v_fecha + interval '2 minutes'
                         WHERE id = v_venta;

                        INSERT INTO pago (
                            id, empresa_id, venta_id, monto, metodo, idempotency_key,
                            estado, referencia, pagado_en
                        )
                        VALUES (
                            md5('fs28-pago-pos-' || emp.slug || '-' || m || '-' || cat.seq)::uuid,
                            emp.id, v_venta, v_sub + v_imp,
                            (ARRAY['efectivo', 'tarjeta', 'qr'])[1 + (m % 3)],
                            'fs28-pago-pos-' || emp.slug || '-' || m || '-' || cat.seq,
                            'completado', 'FS28-POS-' || upper(emp.slug) || '-' || m || '-' || cat.seq,
                            v_fecha
                        )
                        ON CONFLICT DO NOTHING;

                        IF NOT EXISTS (SELECT 1 FROM venta_estado_historial h WHERE h.empresa_id = emp.id AND h.venta_id = v_venta AND h.estado_nuevo = 'completada') THEN
                            INSERT INTO venta_estado_historial (empresa_id, venta_id, estado_anterior, estado_nuevo, motivo, usuario_id, ocurrido_en)
                            VALUES (emp.id, v_venta, NULL, 'completada', 'Venta en caja POS', v_cajero, v_fecha);
                        END IF;
                    END IF;
                END IF;
            END LOOP;
        END LOOP;

        -- C. Reservas (6 por empresa en distintos estados)
        FOR i IN 1..6 LOOP
            SELECT u.id INTO cli
            FROM usuario u
            JOIN rol r ON r.id = u.rol_id
            WHERE u.empresa_id = emp.id AND r.nombre = 'cliente'
            ORDER BY md5(u.id::text || i::text)
            LIMIT 1;

            SELECT v.id INTO v_var_res
            FROM variante v
            WHERE v.empresa_id = emp.id
            ORDER BY md5(v.id::text || 'res' || i::text)
            LIMIT 1;

            v_res := md5('fs28-res-' || emp.slug || '-' || i)::uuid;
            v_ini := now() - make_interval(days => 12 - i * 2);

            INSERT INTO reserva (
                id, empresa_id, codigo, usuario_id, sucursal_id, estado,
                fecha_visita, expira_en, probador, created_at, updated_at
            )
            VALUES (
                v_res, emp.id, 'RES-' || upper(left(emp.slug, 4)) || '-' || lpad(i::text, 3, '0'),
                cli.id, v_suc_matriz, 'pendiente_preparacion',
                v_ini + interval '1 day', now() + interval '5 days',
                'Probador ' || i, v_ini, v_ini
            )
            ON CONFLICT DO NOTHING;

            IF FOUND THEN
                INSERT INTO reserva_detalle (id, empresa_id, reserva_id, variante_id, cantidad)
                VALUES (md5('fs28-resdet-' || emp.slug || '-' || i)::uuid, emp.id, v_res, v_var_res, 1)
                ON CONFLICT DO NOTHING;

                UPDATE reserva SET estado = 'activa', updated_at = v_ini + interval '1 hour' WHERE id = v_res;

                IF v_res_estados[i] NOT IN ('pendiente_preparacion', 'activa') THEN
                    -- Si es completada o cancelada, fn_liberar_stock_reserva descuenta stock_reservado y asigna liberada_en
                    UPDATE reserva
                       SET estado = v_res_estados[i],
                           motivo_cierre = CASE WHEN v_res_estados[i] IN ('cancelada', 'completada') THEN 'Cierre demo seed' END,
                           updated_at = v_ini + interval '2 hours'
                     WHERE id = v_res;
                END IF;
            END IF;
        END LOOP;

        -- D. Carritos de muestra
        INSERT INTO carrito (id, empresa_id, usuario_id, sesion_anonima, estado, created_at, updated_at)
        SELECT
            md5('fs28-cart-' || emp.slug || '-1')::uuid,
            emp.id,
            u.id,
            NULL,
            'activo',
            now() - interval '2 hours',
            now() - interval '1 hour'
        FROM usuario u
        JOIN rol r ON r.id = u.rol_id
        WHERE u.empresa_id = emp.id AND r.nombre = 'cliente'
        ORDER BY u.correo
        LIMIT 1
        ON CONFLICT DO NOTHING;

        INSERT INTO carrito_detalle (id, empresa_id, carrito_id, variante_id, cantidad, precio_unitario)
        SELECT
            md5('fs28-cartdet-' || emp.slug || '-' || v.id)::uuid,
            emp.id,
            md5('fs28-cart-' || emp.slug || '-1')::uuid,
            v.id,
            1,
            v.precio_venta
        FROM variante v
        WHERE v.empresa_id = emp.id
        ORDER BY v.sku
        LIMIT 2
        ON CONFLICT DO NOTHING;

        -- E. Movimientos de inventario y Transferencias entre sucursales
        FOR var IN
            SELECT v.id, i.stock_fisico
            FROM variante v
            JOIN inventario i ON i.variante_id = v.id AND i.empresa_id = v.empresa_id
            WHERE v.empresa_id = emp.id AND i.sucursal_id = v_suc_matriz
            ORDER BY v.sku
            LIMIT 4
        LOOP
            IF NOT EXISTS (SELECT 1 FROM movimiento_inventario m WHERE m.empresa_id = emp.id AND m.variante_id = var.id AND m.motivo = 'Carga inicial seed 28') THEN
                INSERT INTO movimiento_inventario (empresa_id, variante_id, sucursal_id, tipo, cantidad, stock_anterior, stock_nuevo, referencia_tipo, motivo, usuario_id, ocurrido_en)
                VALUES (emp.id, var.id, v_suc_matriz, 'entrada', 30, var.stock_fisico, var.stock_fisico + 30, 'seed', 'Carga inicial seed 28', v_admin, now() - interval '90 days');
            END IF;
        END LOOP;

        IF v_suc_norte IS NOT NULL AND v_suc_sur IS NOT NULL THEN
            v_trf1 := md5('fs28-trf1-' || emp.slug)::uuid;
            v_trf2 := md5('fs28-trf2-' || emp.slug)::uuid;

            INSERT INTO transferencia_inventario (id, empresa_id, origen_id, destino_id, estado, solicitada_por, aprobada_por, created_at, updated_at)
            VALUES
                (v_trf1, emp.id, v_suc_matriz, v_suc_norte, 'en_transito', v_admin, v_admin, now() - interval '3 days', now() - interval '1 day'),
                (v_trf2, emp.id, v_suc_matriz, v_suc_sur,   'recibida',    v_admin, v_admin, now() - interval '10 days', now() - interval '6 days')
            ON CONFLICT DO NOTHING;

            INSERT INTO transferencia_detalle (id, empresa_id, transferencia_id, variante_id, cantidad, cantidad_recibida)
            SELECT
                md5('fs28-trfdet-' || t.id || '-' || v.id)::uuid,
                emp.id, t.id, v.id, 8,
                CASE WHEN t.estado = 'recibida' THEN 8 ELSE 0 END
            FROM transferencia_inventario t
            JOIN LATERAL (SELECT id FROM variante WHERE empresa_id = emp.id ORDER BY sku LIMIT 3) v ON true
            WHERE t.id IN (v_trf1, v_trf2)
            ON CONFLICT DO NOTHING;
        END IF;

        -- F. Dispositivos, Soft Locks y Operaciones Offline
        v_disp1 := md5('fs28-disp1-' || emp.slug)::uuid;
        v_disp2 := md5('fs28-disp2-' || emp.slug)::uuid;

        INSERT INTO dispositivo (id, empresa_id, sucursal_id, nombre, serial, clave_publica, ultima_sync, catalogo_version, estado)
        VALUES
            (v_disp1, emp.id, v_suc_matriz, 'POS Caja Principal ' || upper(emp.slug), 'POS-' || upper(emp.slug) || '-01', 'pub-key-1', now() - interval '15 minutes', 10, 'activo'),
            (v_disp2, emp.id, COALESCE(v_suc_norte, v_suc_matriz), 'Tablet Inventario ' || upper(emp.slug), 'TAB-' || upper(emp.slug) || '-02', 'pub-key-2', now() - interval '2 hours', 10, 'activo')
        ON CONFLICT DO NOTHING;

        INSERT INTO soft_lock (id, empresa_id, sucursal_id, variante_id, dispositivo_id, cantidad, expira_en, creado_en)
        SELECT
            md5('fs28-lock-' || emp.slug || '-' || v.id)::uuid,
            emp.id, v_suc_matriz, v.id, 'POS-' || upper(emp.slug) || '-01', 1,
            now() + interval '40 minutes', now() - interval '5 minutes'
        FROM variante v
        WHERE v.empresa_id = emp.id
        ORDER BY v.sku
        LIMIT 2
        ON CONFLICT DO NOTHING;

        SELECT u.id INTO v_cajero FROM usuario u JOIN rol r ON r.id = u.rol_id WHERE u.empresa_id = emp.id AND r.nombre = 'cajero' LIMIT 1;

        v_op1 := md5('fs28-op1-' || emp.slug)::uuid;
        v_op2 := md5('fs28-op2-' || emp.slug)::uuid;
        v_op3 := md5('fs28-op3-' || emp.slug)::uuid;

        INSERT INTO operacion_pendiente (
            id, empresa_id, dispositivo_id, sucursal_id, usuario_id, tipo,
            payload, firma, nonce, idempotency_key, estado, intentos, ultimo_error, creada_en, procesada_en
        )
        VALUES
            (v_op1, emp.id, v_disp1, v_suc_matriz, v_cajero, 'venta_offline', '{"total": 350.00, "items": 2}'::jsonb, 'sig-1', 'n-1', 'fs28-off-' || emp.slug || '-1', 'pendiente', 0, NULL, now() - interval '6 hours', NULL),
            (v_op2, emp.id, v_disp2, COALESCE(v_suc_norte, v_suc_matriz), v_cajero, 'ajuste_stock', '{"variante": "offline", "cantidad": -2}'::jsonb, 'sig-2', 'n-2', 'fs28-off-' || emp.slug || '-2', 'conflicto', 2, 'Diferencia de conteo fisico', now() - interval '4 hours', NULL),
            (v_op3, emp.id, v_disp1, v_suc_matriz, v_cajero, 'pago_offline', '{"monto": 229.00, "metodo": "efectivo"}'::jsonb, 'sig-3', 'n-3', 'fs28-off-' || emp.slug || '-3', 'aplicada', 1, NULL, now() - interval '12 hours', now() - interval '11 hours')
        ON CONFLICT DO NOTHING;

        INSERT INTO resolucion_conflicto (id, empresa_id, operacion_id, tipo, decision, detalle, resuelto_por, resuelto_en)
        VALUES
            (md5('fs28-resconf-' || emp.slug)::uuid, emp.id, v_op2, 'stock_insuficiente', 'ajustar', '{"observacion": "Ajuste validado en sucursal"}'::jsonb, v_admin, now() - interval '2 hours')
        ON CONFLICT DO NOTHING;

        INSERT INTO sync_registro_idempotencia (id, empresa_id, idempotency_key, tipo_operacion, resultado_json, procesado_en)
        VALUES
            (md5('fs28-sync-' || emp.slug || '-1')::uuid, emp.id, 'fs28-sync-' || emp.slug || '-1', 'venta_offline', '{"estado": "aplicada"}'::jsonb, now() - interval '5 hours'),
            (md5('fs28-sync-' || emp.slug || '-2')::uuid, emp.id, 'fs28-sync-' || emp.slug || '-2', 'pago_offline', '{"estado": "aplicada"}'::jsonb, now() - interval '4 hours')
        ON CONFLICT DO NOTHING;

        -- G. Modelos ML, Predicciones, Segmentos y Consultas IA / Reportes
        v_ml_dem := md5('fs28-ml-dem-' || emp.slug)::uuid;
        v_ml_seg := md5('fs28-ml-seg-' || emp.slug)::uuid;
        v_ml_rec := md5('fs28-ml-rec-' || emp.slug)::uuid;

        INSERT INTO modelo_ml (id, empresa_id, nombre, version, tipo, metricas, activo, entrenado_en)
        VALUES
            (v_ml_dem, emp.id, 'Demanda Mensual', '2.0', 'demanda', '{"mae": 3.8, "rmse": 5.4, "r2": 0.84}'::jsonb, true, now() - interval '2 days'),
            (v_ml_seg, emp.id, 'Segmentacion RFM', '1.5', 'segmentacion', '{"silhouette": 0.68, "clusters": 4}'::jsonb, true, now() - interval '3 days'),
            (v_ml_rec, emp.id, 'Recomendacion Prendas', '1.0', 'recomendacion', '{"precision_at_5": 0.41}'::jsonb, true, now() - interval '4 days')
        ON CONFLICT (empresa_id, nombre, version) DO NOTHING;

        INSERT INTO prediccion_demanda (id, empresa_id, modelo_ml_id, categoria_id, periodo, demanda_estimada, intervalo_inferior, intervalo_superior)
        SELECT
            md5('fs28-pred-' || emp.slug || '-' || c.id || '-' || o.m)::uuid,
            emp.id, v_ml_dem, c.id,
            (date_trunc('month', now()) + make_interval(months => o.m))::date,
            25 + (abs(hashtext(c.id::text || o.m::text)) % 45),
            18 + (abs(hashtext(c.id::text || o.m::text)) % 30),
            45 + (abs(hashtext(c.id::text || o.m::text)) % 45)
        FROM categoria c
        CROSS JOIN (VALUES (0), (1), (2)) AS o(m)
        WHERE c.empresa_id = emp.id
        ON CONFLICT DO NOTHING;

        INSERT INTO segmento_cliente (id, empresa_id, modelo_ml_id, usuario_id, etiqueta, score, vigente_desde, created_at)
        SELECT
            md5('fs28-seg-' || emp.slug || '-' || u.id)::uuid,
            emp.id, v_ml_seg, u.id,
            (ARRAY['VIP', 'Frecuente', 'Ocasional', 'Nuevo'])[1 + (abs(hashtext(u.id::text)) % 4)],
            round((30 + (abs(hashtext(u.id::text)) % 69))::numeric / 100, 4),
            now() - interval '10 days', now() - interval '10 days'
        FROM usuario u
        JOIN rol r ON r.id = u.rol_id
        WHERE u.empresa_id = emp.id AND r.nombre = 'cliente'
        ON CONFLICT DO NOTHING;

        v_cia_1 := md5('fs28-cia1-' || emp.slug)::uuid;
        v_cia_2 := md5('fs28-cia2-' || emp.slug)::uuid;

        INSERT INTO consulta_ia_log (
            id, empresa_id, usuario_id, prompt, respuesta, modelo_llm, canal,
            reporte_tipo, parametros_json, tokens_entrada, tokens_salida, costo, latencia_ms, estado, ocurrido_en
        )
        VALUES
            (v_cia_1, emp.id, v_admin, 'Cuales fueron las ventas del ultimo mes en ' || emp.nombre || '?', 'El resumen mensual muestra crecimiento constante por sucursal.', 'seed-llm', 'texto', 'ventas_resumen', '{"periodo": "ultimo_mes"}'::jsonb, 95, 70, 0.0011, 780, 'exitoso', now() - interval '3 days'),
            (v_cia_2, emp.id, v_admin, 'Que prendas tienen bajo stock?', 'Se detectaron variantes por debajo del stock minimo configurado.', 'seed-llm', 'voz', 'stock_bajo', '{"limite": 10}'::jsonb, 85, 65, 0.0009, 890, 'exitoso', now() - interval '1 day')
        ON CONFLICT DO NOTHING;

        INSERT INTO reporte_exportado (
            id, empresa_id, usuario_id, consulta_ia_log_id, consulta_ocurrido_en,
            tipo_reporte, formato, archivo_url, tamano_bytes, estado, generado_en, expira_en
        )
        VALUES
            (md5('fs28-rep1-' || emp.slug)::uuid, emp.id, v_admin, v_cia_1, now() - interval '3 days', 'ventas_resumen', 'pdf', 'https://cdn.fashionstore.test/' || emp.slug || '/reporte-ventas.pdf', 184320, 'generado', now() - interval '3 days', now() + interval '27 days'),
            (md5('fs28-rep2-' || emp.slug)::uuid, emp.id, v_admin, v_cia_2, now() - interval '1 day', 'stock_bajo', 'xlsx', 'https://cdn.fashionstore.test/' || emp.slug || '/reporte-stock.xlsx', 73728, 'generado', now() - interval '1 day', now() + interval '29 days')
        ON CONFLICT DO NOTHING;

        -- H. Vestidor Virtual AR (avatares, medidas, prendas_ar y sesiones)
        v_av_idx := 0;
        FOR cli IN
            SELECT u.id, u.nombre
            FROM usuario u
            JOIN rol r ON r.id = u.rol_id
            WHERE u.empresa_id = emp.id AND r.nombre = 'cliente'
            ORDER BY u.correo
            LIMIT 2
        LOOP
            v_av_idx := v_av_idx + 1;
            v_av_id := md5('fs28-avatar-' || emp.slug || '-' || v_av_idx)::uuid;

            INSERT INTO avatar_cliente (id, empresa_id, usuario_id, nombre, modelo_url, altura_cm, peso_kg, tono_piel)
            VALUES (
                v_av_id, emp.id, cli.id,
                'Avatar ' || split_part(cli.nombre, ' ', 1),
                'https://cdn.fashionstore.test/avatares/' || emp.slug || '-' || v_av_idx || '.glb',
                165 + v_av_idx * 4, 58 + v_av_idx * 5,
                CASE WHEN v_av_idx = 1 THEN 'medio' ELSE 'claro' END
            )
            ON CONFLICT DO NOTHING;

            FOREACH med IN ARRAY ARRAY['busto', 'cintura', 'cadera', 'hombro', 'largo_pierna'] LOOP
                INSERT INTO medida_corporal (id, empresa_id, avatar_id, tipo, valor_cm)
                VALUES (
                    md5('fs28-med-' || v_av_id || '-' || med)::uuid,
                    emp.id, v_av_id, med,
                    CASE med
                        WHEN 'busto' THEN 86 + v_av_idx * 3
                        WHEN 'cintura' THEN 68 + v_av_idx * 3
                        WHEN 'cadera' THEN 94 + v_av_idx * 3
                        WHEN 'hombro' THEN 39 + v_av_idx * 2
                        ELSE 98 + v_av_idx * 2
                    END
                )
                ON CONFLICT DO NOTHING;
            END LOOP;
        END LOOP;

        INSERT INTO prenda_ar (id, empresa_id, prenda_id, variante_id, modelo_url, textura_url, puntos_ajuste, talla_referencia, activo)
        SELECT
            md5('fs28-ar-' || p.id)::uuid,
            p.empresa_id, p.id,
            (SELECT v.id FROM variante v WHERE v.prenda_id = p.id AND v.empresa_id = p.empresa_id ORDER BY v.id LIMIT 1),
            '/assets/models/ar/casual_tshirt.glb',
            '/assets/textures/ar/cotton_blue.png',
            '{"hombro_izq": [-0.25, 0.40, 0], "hombro_der": [0.25, 0.40, 0], "cintura": [0, -0.10, 0], "escala_base": 1.0}'::jsonb,
            'M',
            true
        FROM prenda p
        WHERE p.empresa_id = emp.id
        ORDER BY p.codigo
        LIMIT 6
        ON CONFLICT DO NOTHING;

        INSERT INTO sesion_prueba_virtual (
            id, empresa_id, usuario_id, avatar_id, prenda_id, variante_id,
            estado, resultado_url, iniciada_en, finalizada_en, created_at
        )
        SELECT
            md5('fs28-sesar-' || emp.slug || '-' || pa.id)::uuid,
            emp.id,
            (SELECT usuario_id FROM avatar_cliente WHERE empresa_id = emp.id LIMIT 1),
            (SELECT id FROM avatar_cliente WHERE empresa_id = emp.id LIMIT 1),
            pa.prenda_id,
            pa.variante_id,
            'completada',
            'https://cdn.fashionstore.test/ar/' || emp.slug || '-render.png',
            now() - interval '2 days',
            now() - interval '2 days' + interval '90 seconds',
            now() - interval '2 days'
        FROM prenda_ar pa
        WHERE pa.empresa_id = emp.id
        ORDER BY pa.id
        LIMIT 3
        ON CONFLICT DO NOTHING;
    END LOOP;
END
$seed28$;

-- Resumen de verificacion por empresa
SELECT
    e.slug,
    (SELECT count(*) FROM sucursal s WHERE s.empresa_id = e.id) AS sucursales,
    (SELECT count(*) FROM usuario u WHERE u.empresa_id = e.id) AS usuarios,
    (SELECT count(*) FROM prenda p WHERE p.empresa_id = e.id) AS prendas,
    (SELECT count(*) FROM variante v WHERE v.empresa_id = e.id) AS variantes,
    (SELECT count(*) FROM inventario i WHERE i.empresa_id = e.id) AS inventarios,
    (SELECT count(*) FROM venta ve WHERE ve.empresa_id = e.id) AS ventas,
    (SELECT count(*) FROM reserva r WHERE r.empresa_id = e.id) AS reservas,
    (SELECT count(*) FROM prenda_ar pa WHERE pa.empresa_id = e.id) AS prendas_ar
FROM empresa e
ORDER BY e.created_at;

COMMIT;

