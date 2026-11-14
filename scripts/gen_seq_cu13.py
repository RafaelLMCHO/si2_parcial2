import os
import shutil
import sys

# Ensure scripts dir is on sys.path
sys.path.insert(0, os.path.dirname(__file__))
from generate_sequence_diagrams import SequenceDiagram

def generate_seq_cu13(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-13: CONSULTAR CATÁLOGO DE PRENDAS",
        "Exploración de Productos, Filtrado Multidimensional, Sincronización de Versión y Modo Offline | Metodología ICONIX",
        width=19,
        height=14
    )

    # Participants based on Robustness Diagram
    d.add_participant('actor', 'Cliente / Visitante', 'actor', 0.05, 'Web / App', w=0.082)
    d.add_participant('ui_web', 'CatalogoWebUI', 'boundary', 0.16, 'features/catalogo-cliente', w=0.088)
    d.add_participant('ui_mob', 'CatalogoFlutter', 'boundary', 0.28, 'features/catalogo (Mobile)', w=0.092)
    d.add_participant('ver', 'get_catalog_version()', 'control', 0.41, 'catalogo_service.py', w=0.096)
    d.add_participant('ctrl', 'list_prendas()', 'control', 0.54, 'catalogo_service.py', w=0.088)
    d.add_participant('cat', 'Categoriadb', 'entity', 0.66, 'db / categoria', w=0.082)
    d.add_participant('pnd', 'Prenda', 'entity', 0.77, 'db / prenda', w=0.082)
    d.add_participant('var', 'Variante', 'entity', 0.87, 'db / variante', w=0.082)
    d.add_participant('cache', 'CatalogoCacheLocal', 'entity', 0.96, 'localStorage / SQLite', w=0.082)

    # 1. Trigger
    d.add_message('actor', 'ui_web', 0.84, "1. Solicitar catálogo con filtros (categoría, talla, precio)")

    # Frame alt: Online vs Offline
    d.add_frame(
        "alt", "[Modo Online: Hay conexión a Internet]",
        0.02, 0.99, 0.81, 0.05,
        divider_y=0.33,
        else_guard="[else: Modo Offline / Pérdida de red (Falla de conexión)]"
    )

    # Online flow
    d.add_message('ui_web', 'ver', 0.77, "2. VersionOffline() (verificar versión de catálogo)")
    d.add_message('ver', 'cache', 0.73, "3. GET: comparar version_catalogo con cache")
    d.add_message('cache', 'ver', 0.69, "4. version_cache_local (ej. v3)", is_return=True)
    d.add_message('ver', 'ui_web', 0.65, "5. version_remota (ej. v4: requiere refresco)", is_return=True)
    d.add_message('ui_web', 'ctrl', 0.61, "6. GET /api/v1/catalogo/prendas (filtros, empresa_slug)")
    d.add_message('ctrl', 'cat', 0.57, "7. GET: árbol de categorías activas del tenant")
    d.add_message('ctrl', 'pnd', 0.53, "8. GET: consultar prendas activas tenant (p.estado='activa')")
    d.add_message('ctrl', 'var', 0.49, "9. GET: obtener variantes y precios (talla, color, SKU)")
    d.add_message('ctrl', 'cache', 0.45, "10. PUT: actualizar cache local / stale banner (snapshot + version)")
    d.add_message('ctrl', 'ui_web', 0.40, "11. Response 200 OK: PrendaListResponse (items, version_catalogo, total)", is_return=True)
    d.add_message('ui_web', 'actor', 0.36, "12. Renderizar grilla de prendas boutique y filtros", is_return=True)

    # Offline flow
    d.add_message('actor', 'ui_mob', 0.29, "13. Abrir catálogo sin conexión / evento offline")
    d.add_message('ui_mob', 'cache', 0.24, "14. leerCacheLocalSiOffline() (readCatalogoSnapshot)")
    d.add_message('cache', 'ui_mob', 0.19, "15. Retornar snapshot local (prendas, variantes, updatedAt)", is_return=True)
    d.add_message('ui_mob', 'ui_mob', 0.14, "16. Mostrar Stale Banner ('Modo sin conexión: datos desactualizados')", self_call=True)
    d.add_message('ui_mob', 'actor', 0.08, "17. Renderizar catálogo en modo contingencia con advertencia", is_return=True)

    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, "secuencia_cu13_consultar_catalogo.png")
    svg_path = os.path.join(output_dir, "secuencia_cu13_consultar_catalogo.svg")
    d.save(png_path, svg_path)
    print(f"Generado exitosamente:\n- {png_path}\n- {svg_path}")

    # Copy to artifact directory
    artifact_dir = r"C:\Users\rafae\.gemini\antigravity\brain\a5d18367-c1c6-4259-a736-b6dd74b38e8d"
    if os.path.exists(artifact_dir):
        shutil.copy2(png_path, os.path.join(artifact_dir, "secuencia_cu13_consultar_catalogo.png"))
        print(f"- Copiado a artifact: {artifact_dir}\\secuencia_cu13_consultar_catalogo.png")

if __name__ == "__main__":
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "diagramas"))
    generate_seq_cu13(docs_dir)

