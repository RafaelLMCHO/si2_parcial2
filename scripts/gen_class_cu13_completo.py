import os
import shutil
import sys

# Ensure scripts directory is in path
sys.path.insert(0, os.path.dirname(__file__))
from generate_class_diagrams import UMLClassDiagram

def generate_unified_clases_cu13(output_dir):
    d = UMLClassDiagram(
        title="CU-13: CONSULTAR CATÁLOGO DE PRENDAS (DISEÑO UNIFICADO BCE)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Fronteras Web/Flutter, Controladores de Versión y Modelo de Dominio",
        width=24,
        height=15
    )

    # 1. Actor
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente', stereotype='actor',
        attributes=[
            '+ isOnline: boolean',
            '+ localVersion: int',
            '+ deviceStorage: str'
        ],
        methods=[
            '+ browseCatalog()',
            '+ filterByCriteria()',
            '+ viewProductDetails()'
        ]
    )

    # 2. Boundaries (UI & Cache)
    d.add_class(
        'ui_web', x=0.21, y_top=0.92, w=0.165,
        name='CatalogoWebUI', stereotype='boundary',
        attributes=[
            '- productos: Prenda[] = []',
            '- isOffline: boolean = false',
            '- isDataStale: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ fetchCatalogoOnline(): Promise<void>',
            '+ loadFromLocalStorage(): Promise<void>',
            '+ renderProducts(): void'
        ]
    )

    d.add_class(
        'ui_mob', x=0.21, y_top=0.64, w=0.165,
        name='CatalogoFlutterUI', stereotype='boundary',
        attributes=[
            '- items: List<Prenda> = []',
            '- isOffline: bool = false',
            '- cacheUpdatedAt: DateTime?'
        ],
        methods=[
            '+ cargarInicial(slug): Future<void>',
            '+ recargar(slug): Future<void>',
            '+ _cargarOnline(): Future<void>',
            '+ _cargarOffline(): Future<void>'
        ]
    )

    d.add_class(
        'ui_banner', x=0.21, y_top=0.36, w=0.165,
        name='BannerDesactualizadoView', stereotype='boundary',
        attributes=[
            '- visible: boolean = false',
            '- warningText: string',
            '- lastDownload: timestamp'
        ],
        methods=[
            '+ showStaleDataWarning(): void',
            '+ hideWarning(): void',
            '+ retryConnection(): void'
        ]
    )

    # 3. Controller
    d.add_class(
        'ctrl', x=0.43, y_top=0.92, w=0.22,
        name='CU13ConsultaCatalogoController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ list_prendas(filtros, slug): PrendaListResponse',
            '+ get_catalog_version(empresa_id): int',
            '+ get_prenda(prenda_id): PrendaOut',
            '+ get_auxiliares(slug): AuxiliaresResponse'
        ]
    )

    # 4. Local Storage / Cache
    d.add_class(
        'cache', x=0.43, y_top=0.58, w=0.20,
        name='CatalogoCacheLocal', stereotype='boundary',
        attributes=[
            '- db: SQLite | localStorage',
            '+ cacheKey: string = "fs_offline_catalog_cache"',
            '+ version: int = 1',
            '+ cachedAt: timestamp'
        ],
        methods=[
            '+ getLocalCatalog(): Promise<list>',
            '+ saveLocalCatalog(version, items): void',
            '+ isCacheStale(): boolean'
        ]
    )

    # 5. Multitenant Entity
    d.add_class(
        'empresa', x=0.43, y_top=0.26, w=0.20,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ slug: citext [UNIQUE]',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ findBySlug(slug): Empresa'
        ]
    )

    # 6. Category Entity
    d.add_class(
        'categoria', x=0.69, y_top=0.92, w=0.20,
        name='Categoria', stereotype='entity', table='categoria',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(100)',
            '+ categoria_padre_id: uuid [FK]'
        ],
        methods=[
            '+ getCategoriasByTenant(emp_id): list'
        ]
    )

    # 7. Garment Entity
    d.add_class(
        'prenda', x=0.69, y_top=0.58, w=0.20,
        name='Prenda', stereotype='entity', table='prenda',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# categoria_id: uuid [FK]',
            '+ codigo: varchar(50)',
            '+ nombre: varchar(160)',
            '+ precio_base: numeric(12,2)',
            '+ estado: varchar(20) = "activa"'
        ],
        methods=[
            '+ getActiveCatalogo(emp_id, filtros): list',
            '+ getGarmentDetails(id): dict'
        ]
    )

    # 8. Variant Entity
    d.add_class(
        'variante', x=0.91, y_top=0.58, w=0.15,
        name='PrendaVariante', stereotype='entity', table='variante',
        attributes=[
            '+ id: uuid [PK]',
            '# prenda_id: uuid [FK]',
            '+ sku: varchar(60) [UNIQUE]',
            '+ talla: varchar(20)',
            '+ color: varchar(40)',
            '+ precio_venta: numeric(12,2)'
        ],
        methods=[
            '+ getVariantsByPrenda(id): list'
        ]
    )

    # Connectors / Relationships
    d.add_connector('actor', 'ui_web', side1='right', side2='left', label="«interacts web»")
    d.add_connector('actor', 'ui_mob', side1='right', side2='left', label="«interacts mobile»", rad=-0.06)

    d.add_connector('ui_web', 'ui_banner', side1='bottom', side2='top', mult1="1", mult2="0..1", is_comp=True)
    d.add_connector('ui_mob', 'ui_banner', side1='bottom', side2='top', mult1="1", mult2="0..1", is_comp=True)

    d.add_connector('ui_web', 'ctrl', side1='right', side2='left', label="«HTTP online»", is_dep=True)
    d.add_connector('ui_mob', 'ctrl', side1='right', side2='left', label="«HTTP online»", is_dep=True, rad=-0.06)

    d.add_connector('ui_web', 'cache', side1='right', side2='left', label="«saves snapshot»", is_dep=True, rad=0.08)
    d.add_connector('ui_mob', 'cache', side1='right', side2='left', label="«reads local»", is_dep=True)

    d.add_connector('ctrl', 'empresa', side1='bottom', side2='top', label="«resolves slug»", is_dep=True)
    d.add_connector('ctrl', 'categoria', side1='right', side2='left', label="«queries tree»", is_dep=True)
    d.add_connector('ctrl', 'prenda', side1='right', side2='left', label="«queries catalog»", is_dep=True)

    d.add_connector('empresa', 'prenda', side1='right', side2='bottom', mult1="1", mult2="0..*", is_comp=True, rad=-0.08)
    d.add_connector('categoria', 'prenda', side1='bottom', side2='top', mult1="1", mult2="0..*")
    d.add_connector('prenda', 'variante', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)

    d.add_legend()

    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, "clases_cu13_consultar_catalogo.png")
    svg_path = os.path.join(output_dir, "clases_cu13_consultar_catalogo.svg")
    d.save(png_path, svg_path)
    print(f"Generado exitosamente:\n- {png_path}\n- {svg_path}")

    # Copy to artifacts directory
    artifact_dir = r"C:\Users\rafae\.gemini\antigravity\brain\a5d18367-c1c6-4259-a736-b6dd74b38e8d"
    if os.path.exists(artifact_dir):
        shutil.copy2(png_path, os.path.join(artifact_dir, "clases_cu13_consultar_catalogo.png"))
        print(f"- Copiado a artifact: {artifact_dir}\\clases_cu13_consultar_catalogo.png")

if __name__ == "__main__":
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "diagramas", "diagrama de clases"))
    generate_unified_clases_cu13(docs_dir)

