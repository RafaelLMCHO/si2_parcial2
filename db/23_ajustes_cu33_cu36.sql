-- ============================================================================
-- 23_ajustes_cu33_cu36.sql
-- Módulo de Reportes, Inteligencia Artificial, Machine Learning y Vestidor RA
-- CU-33: Reportes y dashboards convencionales
-- CU-34: Reportes generativos con IA (Whitelist segura BR-08, PDF/Excel)
-- CU-35: Dashboard analítico ML con síntesis por audio TTS (scikit-learn)
-- CU-36: Vestidor virtual con Realidad Aumentada (RA)
-- ============================================================================

-- 1. Semillas de prendas AR para el Vestidor Virtual (CU-36)
INSERT INTO prenda_ar (
    id,
    empresa_id,
    prenda_id,
    modelo_url,
    textura_url,
    puntos_ajuste,
    talla_referencia,
    activo
)
SELECT
    '11111111-1111-1111-1111-111111111a01'::uuid,
    p.empresa_id,
    p.id,
    '/assets/models/ar/casual_tshirt.glb',
    '/assets/textures/ar/cotton_blue.png',
    jsonb_build_object(
        'hombro_izq', jsonb_build_array(-0.25, 0.40, 0),
        'hombro_der', jsonb_build_array(0.25, 0.40, 0),
        'cuello', jsonb_build_array(0, 0.45, 0),
        'pecho', jsonb_build_array(0, 0.25, 0.05),
        'cintura', jsonb_build_array(0, -0.10, 0),
        'escala_base', 1.0
    ),
    'M',
    true
FROM prenda p
WHERE p.id = '11111111-1111-1111-1111-111111111501'::uuid
ON CONFLICT (id) DO NOTHING;

-- Si la empresa demo tiene prendas, asociar modelo AR
INSERT INTO prenda_ar (
    empresa_id,
    prenda_id,
    modelo_url,
    textura_url,
    puntos_ajuste,
    talla_referencia,
    activo
)
SELECT
    p.empresa_id,
    p.id,
    '/assets/models/ar/demo_prenda.glb',
    '/assets/textures/ar/demo_fabric.png',
    jsonb_build_object(
        'hombro_izq', jsonb_build_array(-0.24, 0.38, 0),
        'hombro_der', jsonb_build_array(0.24, 0.38, 0),
        'cuello', jsonb_build_array(0, 0.42, 0),
        'escala_base', 1.0
    ),
    'M',
    true
FROM prenda p
JOIN empresa e ON e.id = p.empresa_id
WHERE e.slug = 'demo'
  AND NOT EXISTS (SELECT 1 FROM prenda_ar pa WHERE pa.prenda_id = p.id)
LIMIT 3;

-- 2. Índices de optimización para consultas analíticas de reportes (CU-33 y CU-34)
CREATE INDEX IF NOT EXISTS idx_venta_reportes_empresa_fecha 
    ON venta (empresa_id, fecha_hora DESC);

CREATE INDEX IF NOT EXISTS idx_venta_detalle_reportes_variante 
    ON venta_detalle (empresa_id, variante_id);

CREATE INDEX IF NOT EXISTS idx_mov_inventario_reportes 
    ON movimiento_inventario (empresa_id, ocurrido_en DESC);

CREATE INDEX IF NOT EXISTS idx_reporte_exportado_empresa_usuario 
    ON reporte_exportado (empresa_id, usuario_id, generado_en DESC);

