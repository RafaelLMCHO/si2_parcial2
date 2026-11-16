import os
import shutil
import sys

# Ensure scripts directory is in path
sys.path.insert(0, os.path.dirname(__file__))
from generate_class_diagrams import UMLClassDiagram

def generate_unified_clases_cu13(output_dir):
    d = UMLClassDiagram(
        title="CU-13: CONSULTAR CATÁLOGO DE PRENDAS (DISEÑO ROBUSTEZ - CLASES)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - 2 Fronteras (Web y Flutter), Controladores de Robustez y Esquema Relacional de BD",
        width=25,
        height=16
    )

    # 1. Actor
    d.add_class(
        'actor', x=0.065, y_top=0.75, w=0.10,
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

    # 2. ÚNICAS 2 FRONTERAS (Boundary)
    d.add_class(
        'ui_web', x=0.22, y_top=0.92, w=0.17,
        name='CatalogoWebUI', stereotype='boundary',
        attributes=[
            '- productos: Prenda[] = []',
            '- isOffline: boolean = false',
            '- isDataStale: boolean = false',
            '- bannerVisible: boolean = false',
            '- warningText: string'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ checkVersionOffline(): Promise<void>',
            '+ fetchCatalogoOnline(): Promise<void>',
            '+ leerCacheLocalSiOffline(): Promise<void>',
            '+ mostrarAlertaDesactualizado(): void',
            '+ ocultarAlerta(): void',
            '+ reintentarSincronizacion(): void',
            '+ renderCatalogo(): void'
        ]
    )

    d.add_class(
        'ui_mob', x=0.22, y_top=0.50, w=0.17,
        name='CatalogoFlutterUI', stereotype='boundary',
        attributes=[
            '- items: List<Prenda> = []',
            '- isOffline: bool = false',
            '- isDataStale: bool = false',
            '- cacheUpdatedAt: DateTime?'
        ],
        methods=[
            '+ initState(): void',
            '+ cargarInicial(slug: String): Future<void>',
            '+ checkVersionOffline(): Future<void>',
            '+ leerCacheLocalSiOffline(): Future<void>',
            '+ mostrarAlertaDesactualizado(): void',
            '+ recargar(slug: String): Future<void>'
        ]
    )

    # 3. Controller (Coincidente con el Diagrama de Robustez)
    d.add_class(
        'ctrl', x=0.44, y_top=0.92, w=0.21,
        name='CU13ConsultaCatalogoController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ get_catalog_version(empresa_id: uuid): int',
            '+ list_prendas(slug: str, filtros: dict): list[Prenda]',
            '+ get_prenda(prenda_id: uuid): Prenda',
            '+ get_auxiliares(slug: str): dict'
        ]
    )

    # 4. Entidad de Cache Local (Offline / Sincronización)
    d.add_class(
        'cache', x=0.44, y_top=0.64, w=0.20,
        name='CatalogoCacheLocal', stereotype='entity',
        attributes=[
            '- db: IndexedDB | SQLite',
            '+ cacheKey: varchar(60) = "fs_offline_catalog"',
            '+ localVersion: bigint = 1',
            '+ cachedAt: timestamptz',
            '+ isStale: boolean = false'
        ],
        methods=[
            '+ leerCacheLocalSiOffline(): list',
            '+ actualizarCacheLocal(version: int, items: list): void',
            '+ isCacheStale(serverVersion: int): boolean'
        ]
    )

    # 5. Entidad BD: catalogo_version
    d.add_class(
        'cat_ver', x=0.44, y_top=0.36, w=0.20,
        name='CatalogoVersion', stereotype='entity', table='catalogo_version',
        attributes=[
            '+ empresa_id: uuid [PK, FK]',
            '+ version: bigint = 1',
            '+ actualizado_en: timestamptz = now()'
        ],
        methods=[
            '+ getCurrentVersion(emp_id: uuid): bigint'
        ]
    )

    # 6. Entidad BD: categoria
    d.add_class(
        'categoria', x=0.67, y_top=0.92, w=0.19,
        name='Categoria', stereotype='entity', table='categoria',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(100)',
            '# categoria_padre_id: uuid [FK]',
            '+ created_at: timestamptz',
            '+ updated_at: timestamptz'
        ],
        methods=[
            '+ getCategoriasByTenant(emp_id): list'
        ]
    )

    # 7. Entidad BD: empresa
    d.add_class(
        'empresa', x=0.67, y_top=0.58, w=0.19,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ slug: citext [UNIQUE]',
            '+ nit: varchar(20)',
            '+ correo: citext',
            '+ telefono: varchar(20)',
            '+ estado: varchar(20) = "activa"',
            '+ created_at: timestamptz'
        ],
        methods=[
            '+ findBySlug(slug: str): Empresa'
        ]
    )

    # 8. Entidad BD: prenda (Atributos 100% coincidentes con db/05_catalogo.sql)
    d.add_class(
        'prenda', x=0.89, y_top=0.92, w=0.20,
        name='Prenda', stereotype='entity', table='prenda',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# categoria_id: uuid [FK]',
            '# temporada_id: uuid [FK]',
            '# coleccion_id: uuid [FK]',
            '# proveedor_id: uuid [FK]',
            '+ codigo: varchar(50) [UNIQUE]',
            '+ nombre: varchar(160)',
            '+ descripcion: text',
            '+ marca: varchar(80)',
            '+ genero: varchar(20) = "unisex"',
            '+ precio_base: numeric(12,2)',
            '+ moneda: char(3) = "BOB"',
            '+ imagen_url: varchar(255)',
            '+ estado: varchar(20) = "activa"'
        ],
        methods=[
            '+ getActiveCatalogo(emp_id, filtros): list',
            '+ getGarmentDetails(id): dict'
        ]
    )

    # 9. Entidad BD: variante (Atributos 100% coincidentes con db/05_catalogo.sql)
    d.add_class(
        'variante', x=0.89, y_top=0.45, w=0.20,
        name='Variante', stereotype='entity', table='variante',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# prenda_id: uuid [FK]',
            '# color_id: smallint [FK]',
            '# talla_id: smallint [FK]',
            '+ sku: varchar(60) [UNIQUE]',
            '+ codigo_barras: varchar(80)',
            '+ precio_venta: numeric(12,2)',
            '+ costo: numeric(12,2)',
            '+ estado: varchar(20) = "activa"'
        ],
        methods=[
            '+ getVariantsByPrenda(id: uuid): list'
        ]
    )

    # Relaciones y Conectores
    # Actor -> Las únicas 2 Fronteras
    d.add_connector('actor', 'ui_web', side1='right', side2='left', label="«interacts web»")
    d.add_connector('actor', 'ui_mob', side1='right', side2='left', label="«interacts mobile»", rad=-0.04)

    # Fronteras -> Controlador (Llamadas robustez: checkVersionOffline, list_prendas)
    d.add_connector('ui_web', 'ctrl', side1='right', side2='left', label="«HTTP online»", is_dep=True)
    d.add_connector('ui_mob', 'ctrl', side1='right', side2='left', label="«HTTP online»", is_dep=True, rad=-0.06)

    # Fronteras -> Cache Local (Llamada robustez: leerCacheLocalSiOffline, stale banner)
    d.add_connector('ui_web', 'cache', side1='right', side2='left', label="«actualizar / leer»", is_dep=True, rad=0.06)
    d.add_connector('ui_mob', 'cache', side1='right', side2='left', label="«leerCacheLocalSiOffline»", is_dep=True)

    # Controlador -> Entidades (Llamadas robustez: get_catalog_version, list_prendas)
    d.add_connector('ctrl', 'cat_ver', side1='bottom', side2='top', label="«get_catalog_version»", is_dep=True)
    d.add_connector('ctrl', 'categoria', side1='right', side2='left', label="«get_auxiliares»", is_dep=True)
    d.add_connector('ctrl', 'prenda', side1='right', side2='left', label="«list_prendas»", is_dep=True)

    # Modelo Relacional BD
    d.add_connector('empresa', 'cat_ver', side1='left', side2='right', mult1="1", mult2="1", is_comp=True)
    d.add_connector('empresa', 'categoria', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'prenda', side1='right', side2='bottom', mult1="1", mult2="0..*", is_comp=True, rad=-0.08)
    d.add_connector('categoria', 'prenda', side1='right', side2='left', mult1="1", mult2="0..*")
    d.add_connector('prenda', 'variante', side1='bottom', side2='top', mult1="1", mult2="1..*", is_comp=True)

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
