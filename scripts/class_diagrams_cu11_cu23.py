import os
from generate_class_diagrams import UMLClassDiagram

def generate_clases_cu11(output_dir):
    """CU-11: Administrar sucursales (Límite según Plan BR-02)"""
    d = UMLClassDiagram(
        title="CU-11: Administrar Sucursales (Límites por Plan BR-02)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Validación de cupo por suscripción y persistencia en PostgreSQL"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Administrador', stereotype='actor',
        attributes=[
            '+ tenantId: uuid',
            '+ adminRole: string',
            '+ sessionToken: str'
        ],
        methods=[
            '+ browseBranches()',
            '+ fillBranchForm()',
            '+ submitBranch()',
            '+ toggleStatus()'
        ]
    )
    d.add_class(
        'ui_list', x=0.21, y_top=0.91, w=0.165,
        name='GestionSucursalesComponent', stereotype='boundary',
        attributes=[
            '- sucursales: SucursalOut[] = []',
            '- planLimite: number = 2',
            '- activasCount: number = 0',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadBranches(): Promise<void>',
            '+ checkLimitReached(): boolean',
            '+ openCreateModal(): void',
            '+ onToggleBranch(id): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.54, w=0.165,
        name='ModalSucursalForm', stereotype='boundary',
        attributes=[
            '- nombre: string = ""',
            '- ciudad: string = ""',
            '- direccion: string = ""',
            '- telefono: string = ""',
            '- errorMessage: string | null'
        ],
        methods=[
            '+ submitForm(): Promise<void>',
            '+ validateInputs(): boolean',
            '+ showQuotaExceededError(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU11SucursalesController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listBranches(empresa_id: uuid): list',
            '+ createBranch(empresa_id, data): Sucursal',
            '+ countActiveBranches(empresa_id): int',
            '+ validateBranchQuotaBR02(emp_id): bool',
            '+ updateBranch(emp_id, id, data): Sucursal'
        ]
    )
    d.add_class(
        'dto', x=0.43, y_top=0.46, w=0.20,
        name='SucursalCreateDTO', stereotype='dto',
        attributes=[
            '+ nombre: str',
            '+ ciudad: str',
            '+ direccion: str',
            '+ telefono: str | None',
            '+ es_casa_matriz: bool = False'
        ],
        methods=[]
    )
    d.add_class(
        'sucursal', x=0.70, y_top=0.91, w=0.22,
        name='Sucursal', stereotype='entity', table='sucursal',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(100)',
            '+ ciudad: varchar(60)',
            '+ direccion: text',
            '+ telefono: varchar(20)',
            '+ es_casa_matriz: boolean',
            '+ estado: varchar(20) = "activo"',
            '+ created_at: timestamptz'
        ],
        methods=[
            '+ countActive(emp_id: uuid): int',
            '+ insertBranch(data: dict): Sucursal',
            '+ updateStatus(id, estado): void'
        ]
    )
    d.add_class(
        'suscripcion', x=0.91, y_top=0.91, w=0.15,
        name='Suscripcion', stereotype='entity', table='suscripcion',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# plan_id: smallint [FK]',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ getActivePlan(emp_id): Plan',
            '+ isWithinLimit(curr, lim): bool'
        ]
    )
    d.add_class(
        'plan', x=0.91, y_top=0.55, w=0.15,
        name='Plan', stereotype='entity', table='plan',
        attributes=[
            '+ id: smallint [PK]',
            '+ codigo: varchar(30)',
            '+ limite_sucursales: smallint'
        ],
        methods=[
            '+ getBranchLimit(code): int'
        ]
    )
    d.add_class(
        'empresa', x=0.70, y_top=0.50, w=0.22,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ estado: varchar(20)'
        ],
        methods=[]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.23, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20) = "crear_sucursal"',
            '+ entidad: varchar(60) = "sucursal"'
        ],
        methods=[
            '+ logBranchCreated(sucursal_id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_list', side1='right', side2='left', label="«manages branches»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«inputs data»", rad=-0.08)
    d.add_connector('ui_list', 'ctrl', side1='right', side2='left', label="«loads list»", is_dep=True)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='bottom', label="«submits form»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'dto', side1='bottom', side2='top', is_dep=True)
    d.add_connector('ctrl', 'sucursal', side1='right', side2='left', label="«counts & persists»", is_dep=True)
    d.add_connector('ctrl', 'suscripcion', side1='right', side2='left', label="«verifies BR-02»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'sucursal', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'suscripcion', side1='right', side2='bottom', mult1="1", mult2="1", is_comp=True)
    d.add_connector('plan', 'suscripcion', side1='top', side2='bottom', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu11_administrar_sucursales.png")
    svg_path = os.path.join(output_dir, "clases_cu11_administrar_sucursales.svg")
    d.save(png_path, svg_path)


def generate_clases_cu12(output_dir):
    """CU-12: Administrar catálogo de productos (CRUD de prendas, variantes SKU)"""
    d = UMLClassDiagram(
        title="CU-12: Administrar Catálogo de Productos (Prendas y SKU)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Catálogo multitenant con variantes de talla/color y SKU único"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Administrador', stereotype='actor',
        attributes=[
            '+ tenantId: uuid',
            '+ adminUserId: uuid'
        ],
        methods=[
            '+ browseCatalog()',
            '+ openCreatePrenda()',
            '+ addVariantRows()',
            '+ saveProductCatalog()'
        ]
    )
    d.add_class(
        'ui_cat', x=0.21, y_top=0.91, w=0.165,
        name='CatalogoPrendasComponent', stereotype='boundary',
        attributes=[
            '- prendas: PrendaItem[] = []',
            '- selectedCategoria: string',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadCatalog(): Promise<void>',
            '+ openCreateModal(): void',
            '+ deletePrenda(id): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.55, w=0.165,
        name='ModalPrendaForm', stereotype='boundary',
        attributes=[
            '- nombre: string = ""',
            '- precio_base: number = 0',
            '- categoria_id: string',
            '- variantes: VarianteRow[] = []'
        ],
        methods=[
            '+ addVariant(): void',
            '+ removeVariant(index): void',
            '+ submitPrenda(): Promise<void>',
            '+ validateSkuUniqueness(): bool'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU12CatalogoController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listProducts(empresa_id): list',
            '+ createProduct(empresa_id, data): Prenda',
            '+ validateUniqueSku(emp_id, sku): bool',
            '+ updateProduct(emp_id, id, data): Prenda',
            '+ softDeleteProduct(emp_id, id): void'
        ]
    )
    d.add_class(
        'prenda', x=0.70, y_top=0.91, w=0.22,
        name='Prenda', stereotype='entity', table='prenda',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# categoria_id: uuid [FK]',
            '# coleccion_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ descripcion: text',
            '+ precio_base: numeric(10,2)',
            '+ estado: varchar(20) = "activo"'
        ],
        methods=[
            '+ insertProduct(data): Prenda',
            '+ getCatalogByTenant(emp_id): list',
            '+ setInactive(id): void'
        ]
    )
    d.add_class(
        'variante', x=0.91, y_top=0.91, w=0.15,
        name='PrendaVariante', stereotype='entity', table='prenda_variante',
        attributes=[
            '+ id: uuid [PK]',
            '# prenda_id: uuid [FK]',
            '+ sku: varchar(50) [UNIQUE]',
            '+ talla: varchar(10)',
            '+ color: varchar(40)',
            '+ precio_adicional: numeric'
        ],
        methods=[
            '+ skuExists(emp_id, sku): bool',
            '+ insertVariants(items): void'
        ]
    )
    d.add_class(
        'categoria', x=0.70, y_top=0.52, w=0.22,
        name='Categoria', stereotype='entity', table='categoria',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(80)'
        ],
        methods=[
            '+ listActive(emp_id): list'
        ]
    )
    d.add_class(
        'coleccion', x=0.91, y_top=0.55, w=0.15,
        name='Coleccion', stereotype='entity', table='coleccion',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(100)'
        ],
        methods=[]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.25, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20) = "crear_prenda"'
        ],
        methods=[
            '+ logPrendaCreated(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_cat', side1='right', side2='left', label="«maintains products»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«configures SKU»", rad=-0.08)
    d.add_connector('ui_cat', 'ctrl', side1='right', side2='left', label="«loads catalog»", is_dep=True)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='bottom', label="«saves garment»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'prenda', side1='right', side2='left', label="«inserts garment»", is_dep=True)
    d.add_connector('ctrl', 'variante', side1='right', side2='left', label="«validates SKU»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits product»", is_dep=True, rad=-0.12)
    
    d.add_connector('prenda', 'variante', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    d.add_connector('categoria', 'prenda', side1='top', side2='bottom', mult1="1", mult2="0..*")
    d.add_connector('coleccion', 'prenda', side1='left', side2='bottom', mult1="0..1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu12_catalogo_productos.png")
    svg_path = os.path.join(output_dir, "clases_cu12_catalogo_productos.svg")
    d.save(png_path, svg_path)


def generate_clases_cu13(output_dir):
    """CU-13: Consultar catálogo de prendas (con alerta de datos desactualizados)"""
    d = UMLClassDiagram(
        title="CU-13: Consultar Catálogo de Prendas (Online / Offline)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Sincronización híbrida y banner de advertencia visual"
    )
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
            '+ checkOfflineBanner()',
            '+ viewProductDetails()'
        ]
    )
    d.add_class(
        'ui_pub', x=0.21, y_top=0.91, w=0.165,
        name='CatalogoPublicoComponent', stereotype='boundary',
        attributes=[
            '- productos: ProductoCard[] = []',
            '- isOffline: boolean = false',
            '- isDataStale: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ fetchCatalogOnline(): Promise<void>',
            '+ loadFromLocalStorage(): Promise<void>',
            '+ renderProducts(): void'
        ]
    )
    d.add_class(
        'ui_banner', x=0.21, y_top=0.55, w=0.165,
        name='BannerDesactualizadoView', stereotype='boundary',
        attributes=[
            '- visible: boolean = false',
            '- syncPendingCount: number = 0',
            '- warningText: string'
        ],
        methods=[
            '+ showStaleDataWarning(): void',
            '+ hideWarning(): void',
            '+ retryConnection(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU13ConsultaCatalogoController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getPublicCatalog(slug: str): list[dict]',
            '+ getCatalogVersion(slug: str): int',
            '+ checkConnectivity(): dict'
        ]
    )
    d.add_class(
        'cache', x=0.43, y_top=0.48, w=0.20,
        name='CatalogoCacheLocal', stereotype='boundary',
        attributes=[
            '- db: IDBDatabase | SQLite',
            '+ cacheKey: string = "catalog_data"',
            '+ version: number = 1',
            '+ cachedAt: timestamp'
        ],
        methods=[
            '+ getLocalCatalog(): Promise<list>',
            '+ saveLocalCatalog(data): Promise<void>',
            '+ isCacheStale(): boolean'
        ]
    )
    d.add_class(
        'prenda', x=0.70, y_top=0.91, w=0.22,
        name='Prenda', stereotype='entity', table='prenda',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ descripcion: text',
            '+ precio_base: numeric(10,2)',
            '+ imagen_url: text',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ getActiveCatalog(emp_id): list',
            '+ getGarmentDetails(id): dict'
        ]
    )
    d.add_class(
        'variante', x=0.91, y_top=0.91, w=0.15,
        name='PrendaVariante', stereotype='entity', table='prenda_variante',
        attributes=[
            '+ id: uuid [PK]',
            '# prenda_id: uuid [FK]',
            '+ sku: varchar(50)',
            '+ talla: varchar(10)',
            '+ color: varchar(40)'
        ],
        methods=[
            '+ getVariantsByPrenda(id): list'
        ]
    )
    d.add_class(
        'empresa', x=0.70, y_top=0.48, w=0.22,
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
    
    d.add_connector('actor', 'ui_pub', side1='right', side2='left', label="«views catalog»")
    d.add_connector('actor', 'ui_banner', side1='bottom', side2='left', label="«sees warning»", rad=-0.08)
    d.add_connector('ui_pub', 'ctrl', side1='right', side2='left', label="«queries API online»", is_dep=True)
    d.add_connector('ui_pub', 'cache', side1='bottom', side2='top', label="«falls back offline»", is_dep=True)
    d.add_connector('ctrl', 'prenda', side1='right', side2='left', label="«retrieves items»", is_dep=True)
    d.add_connector('ctrl', 'empresa', side1='right', side2='left', label="«identifies slug»", is_dep=True, rad=-0.08)
    
    d.add_connector('empresa', 'prenda', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('prenda', 'variante', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu13_consultar_catalogo.png")
    svg_path = os.path.join(output_dir, "clases_cu13_consultar_catalogo.svg")
    d.save(png_path, svg_path)


def generate_clases_cu14(output_dir):
    """CU-14: Filtrar productos (talla, color, categoría, temporada y precio)"""
    d = UMLClassDiagram(
        title="CU-14: Filtrar Productos (Multicriterio Híbrido)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Filtros dinámicos en servidor o motor SQL local"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente', stereotype='actor',
        attributes=[
            '+ selectedFilters: dict',
            '+ currentTenant: str'
        ],
        methods=[
            '+ selectTallaColor()',
            '+ setPriceRange()',
            '+ applyFilters()',
            '+ clearFilters()'
        ]
    )
    d.add_class(
        'ui_filter', x=0.21, y_top=0.91, w=0.165,
        name='FiltrosCatalogoComponent', stereotype='boundary',
        attributes=[
            '- tallas: string[] = []',
            '- colores: string[] = []',
            '- categorias: string[] = []',
            '- minPrice: number = 0',
            '- maxPrice: number = 1000'
        ],
        methods=[
            '+ onFilterChanged(): void',
            '+ buildFilterQuery(): FilterDTO',
            '+ resetAllFilters(): void'
        ]
    )
    d.add_class(
        'ui_results', x=0.21, y_top=0.52, w=0.165,
        name='ResultadosCatalogoView', stereotype='boundary',
        attributes=[
            '- items: ProductoItem[] = []',
            '- totalFound: number = 0',
            '- emptyMessage: string'
        ],
        methods=[
            '+ renderResults(): void',
            '+ showNoResultsPlaceholder(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU14FiltrosController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ filterCatalogOnline(emp_id, filter): list',
            '+ filterCatalogOffline(localDb, filter): list',
            '+ getFilterFacets(empresa_id): dict'
        ]
    )
    d.add_class(
        'dto', x=0.43, y_top=0.52, w=0.20,
        name='FilterCatalogDTO', stereotype='dto',
        attributes=[
            '+ categoria_id: uuid | None',
            '+ coleccion_id: uuid | None',
            '+ talla: str | None',
            '+ color: str | None',
            '+ precio_min: float | None',
            '+ precio_max: float | None'
        ],
        methods=[]
    )
    d.add_class(
        'prenda', x=0.70, y_top=0.91, w=0.22,
        name='Prenda', stereotype='entity', table='prenda',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# categoria_id: uuid [FK]',
            '# coleccion_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ precio_base: numeric(10,2)',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ filterByCriteria(params): list'
        ]
    )
    d.add_class(
        'variante', x=0.91, y_top=0.91, w=0.15,
        name='PrendaVariante', stereotype='entity', table='prenda_variante',
        attributes=[
            '+ id: uuid [PK]',
            '# prenda_id: uuid [FK]',
            '+ talla: varchar(10)',
            '+ color: varchar(40)',
            '+ sku: varchar(50)'
        ],
        methods=[
            '+ matchVariants(talla, color): list'
        ]
    )
    d.add_class(
        'categoria', x=0.70, y_top=0.48, w=0.22,
        name='Categoria', stereotype='entity', table='categoria',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(80)'
        ],
        methods=[]
    )
    d.add_class(
        'coleccion', x=0.91, y_top=0.52, w=0.15,
        name='Coleccion', stereotype='entity', table='coleccion',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(100)'
        ],
        methods=[]
    )
    
    d.add_connector('actor', 'ui_filter', side1='right', side2='left', label="«selects facets»")
    d.add_connector('ui_filter', 'ctrl', side1='right', side2='left', label="«dispatches filter»", is_dep=True)
    d.add_connector('ui_filter', 'ui_results', side1='bottom', side2='top', label="«updates view»")
    d.add_connector('ctrl', 'dto', side1='bottom', side2='top', is_dep=True)
    d.add_connector('ctrl', 'prenda', side1='right', side2='left', label="«dynamic SQL query»", is_dep=True)
    d.add_connector('ctrl', 'variante', side1='right', side2='left', label="«matches sizes»", is_dep=True, rad=0.08)
    
    d.add_connector('prenda', 'variante', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    d.add_connector('categoria', 'prenda', side1='top', side2='bottom', mult1="1", mult2="0..*")
    d.add_connector('coleccion', 'prenda', side1='left', side2='bottom', mult1="0..1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu14_filtrar_productos.png")
    svg_path = os.path.join(output_dir, "clases_cu14_filtrar_productos.svg")
    d.save(png_path, svg_path)


def generate_clases_cu15(output_dir):
    """CU-15: Administrar proveedores textiles"""
    d = UMLClassDiagram(
        title="CU-15: Administrar Proveedores Textiles",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Gestión de insumos, confección y abastecimiento tenant"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Administrador', stereotype='actor',
        attributes=[
            '+ tenantId: uuid',
            '+ adminPermissions: list'
        ],
        methods=[
            '+ browseSuppliers()',
            '+ openCreateModal()',
            '+ fillSupplierForm()',
            '+ saveSupplier()'
        ]
    )
    d.add_class(
        'ui_prov', x=0.21, y_top=0.91, w=0.165,
        name='ProveedoresComponent', stereotype='boundary',
        attributes=[
            '- proveedores: ProveedorRow[] = []',
            '- searchQuery: string = ""',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadSuppliers(): Promise<void>',
            '+ openCreateModal(): void',
            '+ deleteSupplier(id): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.55, w=0.165,
        name='ModalProveedorForm', stereotype='boundary',
        attributes=[
            '- razon_social: string = ""',
            '- nit: string = ""',
            '- contacto: string = ""',
            '- telefono: string = ""'
        ],
        methods=[
            '+ submitForm(): Promise<void>',
            '+ validateNit(): boolean',
            '+ showDuplicityError(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU15ProveedoresController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listSuppliers(empresa_id): list',
            '+ createSupplier(empresa_id, data): Proveedor',
            '+ checkNitDuplicity(emp_id, nit): bool',
            '+ updateSupplier(emp_id, id, data): Proveedor'
        ]
    )
    d.add_class(
        'proveedor', x=0.70, y_top=0.91, w=0.22,
        name='Proveedor', stereotype='entity', table='proveedor',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ razon_social: varchar(120)',
            '+ nit: varchar(20)',
            '+ contacto: varchar(100)',
            '+ telefono: varchar(20)',
            '+ direccion: text',
            '+ estado: varchar(20) = "activo"'
        ],
        methods=[
            '+ insertSupplier(data): Proveedor',
            '+ nitExists(emp_id, nit): bool',
            '+ updateData(id, data): void'
        ]
    )
    d.add_class(
        'empresa', x=0.91, y_top=0.91, w=0.15,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ estado: varchar(20)'
        ],
        methods=[]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.45, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20) = "crear_proveedor"',
            '+ entidad: varchar(60) = "proveedor"'
        ],
        methods=[
            '+ logSupplierCreated(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_prov', side1='right', side2='left', label="«manages vendors»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«inputs NIT & contact»", rad=-0.08)
    d.add_connector('ui_prov', 'ctrl', side1='right', side2='left', label="«lists vendors»", is_dep=True)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='bottom', label="«saves vendor»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'proveedor', side1='right', side2='left', label="«inserts vendor»", is_dep=True)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'proveedor', side1='left', side2='right', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu15_administrar_proveedores.png")
    svg_path = os.path.join(output_dir, "clases_cu15_administrar_proveedores.svg")
    d.save(png_path, svg_path)


def generate_clases_cu16(output_dir):
    """CU-16: Administrar temporadas y colecciones comerciales"""
    d = UMLClassDiagram(
        title="CU-16: Administrar Temporadas y Colecciones Comerciales",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Clasificación temporal de prendas y fechas de vigencia"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Administrador', stereotype='actor',
        attributes=[
            '+ tenantId: uuid',
            '+ activeRole: str'
        ],
        methods=[
            '+ viewCollections()',
            '+ openCreateModal()',
            '+ setCollectionDates()',
            '+ saveCollection()'
        ]
    )
    d.add_class(
        'ui_col', x=0.21, y_top=0.91, w=0.165,
        name='TemporadasColeccionesComponent', stereotype='boundary',
        attributes=[
            '- colecciones: ColeccionItem[] = []',
            '- vigentesOnly: boolean = false',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadCollections(): Promise<void>',
            '+ openCreateModal(): void',
            '+ toggleVigencia(id): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.55, w=0.165,
        name='ModalColeccionForm', stereotype='boundary',
        attributes=[
            '- nombre: string = ""',
            '- fecha_inicio: string = ""',
            '- fecha_fin: string = ""',
            '- errorFechas: string | null'
        ],
        methods=[
            '+ submitForm(): Promise<void>',
            '+ validateDates(): boolean',
            '+ showDateRangeError(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU16ColeccionesController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listCollections(empresa_id): list',
            '+ createCollection(empresa_id, data): Coleccion',
            '+ validateDateRange(ini, fin): bool',
            '+ updateCollection(emp_id, id, data): Coleccion'
        ]
    )
    d.add_class(
        'coleccion', x=0.70, y_top=0.91, w=0.22,
        name='Coleccion', stereotype='entity', table='coleccion',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(100)',
            '+ descripcion: text',
            '+ fecha_inicio: date',
            '+ fecha_fin: date',
            '+ estado: varchar(20) = "vigente"'
        ],
        methods=[
            '+ insertCollection(data): Coleccion',
            '+ isDateValid(ini, fin): bool',
            '+ getActiveCollections(emp_id): list'
        ]
    )
    d.add_class(
        'prenda', x=0.91, y_top=0.91, w=0.15,
        name='Prenda', stereotype='entity', table='prenda',
        attributes=[
            '+ id: uuid [PK]',
            '# coleccion_id: uuid [FK]',
            '+ nombre: varchar(120)'
        ],
        methods=[
            '+ countPrendasInColeccion(col_id): int'
        ]
    )
    d.add_class(
        'empresa', x=0.70, y_top=0.48, w=0.22,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)'
        ],
        methods=[]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '+ accion: varchar(20) = "crear_coleccion"'
        ],
        methods=[
            '+ logCollectionCreated(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_col', side1='right', side2='left', label="«manages seasons»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«configures dates»", rad=-0.08)
    d.add_connector('ui_col', 'ctrl', side1='right', side2='left', label="«loads collections»", is_dep=True)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='bottom', label="«validates & saves»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'coleccion', side1='right', side2='left', label="«inserts collection»", is_dep=True)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'coleccion', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('coleccion', 'prenda', side1='right', side2='left', mult1="0..1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu16_temporadas_colecciones.png")
    svg_path = os.path.join(output_dir, "clases_cu16_temporadas_colecciones.svg")
    d.save(png_path, svg_path)


def generate_clases_cu17(output_dir):
    """CU-17: Gestionar inventario global y local (ajustes y transferencias)"""
    d = UMLClassDiagram(
        title="CU-17: Gestionar Inventario Global y Local",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Control de existencias por sucursal, kardex y ajustes"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Encargado / Admin', stereotype='actor',
        attributes=[
            '+ sucursalId: uuid',
            '+ staffRole: string',
            '+ sessionToken: str'
        ],
        methods=[
            '+ viewStockMatrix()',
            '+ openAdjustmentModal()',
            '+ submitAdjustment()',
            '+ handleStockAlert()'
        ]
    )
    d.add_class(
        'ui_matriz', x=0.21, y_top=0.91, w=0.165,
        name='MatrizInventarioComponent', stereotype='boundary',
        attributes=[
            '- existencias: StockItem[] = []',
            '- sucursalSeleccionada: string',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadStock(): Promise<void>',
            '+ openAdjustmentModal(): void',
            '+ filterByLowStock(): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.55, w=0.165,
        name='FormularioAjusteModal', stereotype='boundary',
        attributes=[
            '- variante_id: string',
            '- tipo_ajuste: string = "merma"',
            '- cantidad: number = 0',
            '- motivo: string = ""'
        ],
        methods=[
            '+ submitAdjustment(): Promise<void>',
            '+ validateQuantity(): boolean',
            '+ showConflictToast(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU17InventarioController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listStock(emp_id, sucursal_id): list',
            '+ recordAdjustment(emp_id, data): MovimientoInventario',
            '+ transferStock(orig_id, dest_id, qty): void',
            '+ notifyStockError(msg): void'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.91, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '# sucursal_id: uuid [FK]',
            '# prenda_variante_id: uuid [FK]',
            '+ stock_actual: integer',
            '+ stock_minimo: integer',
            '+ stock_bloqueado: integer = 0'
        ],
        methods=[
            '+ updateStock(delta: int): void',
            '+ checkCriticalMin(): bool',
            '+ getStock(suc_id, var_id): Inventario'
        ]
    )
    d.add_class(
        'variante', x=0.91, y_top=0.91, w=0.15,
        name='PrendaVariante', stereotype='entity', table='prenda_variante',
        attributes=[
            '+ id: uuid [PK]',
            '+ sku: varchar(50)',
            '+ talla: varchar(10)',
            '+ color: varchar(40)'
        ],
        methods=[
            '+ findBySku(sku): PrendaVariante'
        ]
    )
    d.add_class(
        'movimiento', x=0.70, y_top=0.52, w=0.22,
        name='MovimientoInventario', stereotype='entity', table='movimiento_inventario',
        attributes=[
            '+ id: uuid [PK]',
            '# inventario_id: uuid [FK]',
            '+ tipo: varchar(30)',
            '+ cantidad: integer',
            '+ motivo: text',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ logMovement(data: dict): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20) = "ajuste_inventario"',
            '+ entidad: varchar(60) = "inventario"'
        ],
        methods=[
            '+ logStockAdjustment(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_matriz', side1='right', side2='left', label="«inspects stock»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«submits adjustment»", rad=-0.08)
    d.add_connector('ui_matriz', 'ctrl', side1='right', side2='left', label="«lists stock»", is_dep=True)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='bottom', label="«records movement»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«updates quantities»", is_dep=True)
    d.add_connector('ctrl', 'movimiento', side1='right', side2='left', label="«writes kardex»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('variante', 'inventario', side1='left', side2='right', mult1="1", mult2="0..*")
    d.add_connector('inventario', 'movimiento', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu17_gestion_inventario.png")
    svg_path = os.path.join(output_dir, "clases_cu17_gestion_inventario.svg")
    d.save(png_path, svg_path)


def generate_clases_cu18(output_dir):
    """CU-18: Consultar disponibilidad por sucursal (stock físico y local)"""
    d = UMLClassDiagram(
        title="CU-18: Consultar Disponibilidad por Sucursal",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Existencias en tiendas físicas para clientes y staff"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente', stereotype='actor',
        attributes=[
            '+ userLocation: str',
            '+ selectedSku: str'
        ],
        methods=[
            '+ selectGarmentSize()',
            '+ openStoreMapModal()',
            '+ selectStoreLocation()'
        ]
    )
    d.add_class(
        'ui_prod', x=0.21, y_top=0.91, w=0.165,
        name='CatalogoPrendaComponent', stereotype='boundary',
        attributes=[
            '- prendaId: string',
            '- selectedVarianteId: string',
            '- loading: boolean = false'
        ],
        methods=[
            '+ onSelectVariant(id): void',
            '+ openAvailabilityModal(): void'
        ]
    )
    d.add_class(
        'ui_mapa', x=0.21, y_top=0.55, w=0.165,
        name='MapaDisponibilidadModal', stereotype='boundary',
        attributes=[
            '- sucursalesStock: BranchStockDTO[] = []',
            '- selectedCity: string = "todas"'
        ],
        methods=[
            '+ filterByCity(city): void',
            '+ calculateDistance(): number',
            '+ highlightInStockStores(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU18DisponibilidadController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getAvailabilityByVariant(var_id): list',
            '+ filterBranchesWithStock(emp_id, var_id): list',
            '+ getStoreLocations(emp_id): list'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.91, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '# sucursal_id: uuid [FK]',
            '# prenda_variante_id: uuid [FK]',
            '+ stock_actual: integer'
        ],
        methods=[
            '+ getStockByVariantAcrossBranches(id): list'
        ]
    )
    d.add_class(
        'sucursal', x=0.91, y_top=0.91, w=0.15,
        name='Sucursal', stereotype='entity', table='sucursal',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(100)',
            '+ ciudad: varchar(60)',
            '+ direccion: text'
        ],
        methods=[
            '+ getActiveBranches(emp_id): list'
        ]
    )
    d.add_class(
        'variante', x=0.70, y_top=0.55, w=0.22,
        name='PrendaVariante', stereotype='entity', table='prenda_variante',
        attributes=[
            '+ id: uuid [PK]',
            '# prenda_id: uuid [FK]',
            '+ sku: varchar(50)',
            '+ talla: varchar(10)',
            '+ color: varchar(40)'
        ],
        methods=[]
    )
    d.add_class(
        'empresa', x=0.91, y_top=0.55, w=0.15,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)'
        ],
        methods=[]
    )
    
    d.add_connector('actor', 'ui_prod', side1='right', side2='left', label="«selects product»")
    d.add_connector('actor', 'ui_mapa', side1='bottom', side2='left', label="«locates stores»", rad=-0.08)
    d.add_connector('ui_prod', 'ctrl', side1='right', side2='left', label="«queries stock»", is_dep=True)
    d.add_connector('ui_mapa', 'ctrl', side1='right', side2='bottom', label="«fetches branches»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«reads stock»", is_dep=True)
    d.add_connector('ctrl', 'sucursal', side1='right', side2='left', label="«reads branches»", is_dep=True, rad=0.08)
    
    d.add_connector('sucursal', 'inventario', side1='left', side2='right', mult1="1", mult2="0..*")
    d.add_connector('variante', 'inventario', side1='top', side2='bottom', mult1="1", mult2="0..*")
    d.add_connector('empresa', 'sucursal', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu18_disponibilidad_tiendas.png")
    svg_path = os.path.join(output_dir, "clases_cu18_disponibilidad_tiendas.svg")
    d.save(png_path, svg_path)


def generate_clases_cu19(output_dir):
    """CU-19: Realizar reserva de múltiples prendas (modo en línea)"""
    d = UMLClassDiagram(
        title="CU-19: Realizar Reserva de Múltiples Prendas (Online)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Apartado provisional en sucursal con TTL para probador"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente', stereotype='actor',
        attributes=[
            '+ clienteId: uuid',
            '+ sessionToken: str'
        ],
        methods=[
            '+ addToReservationCart()',
            '+ chooseBranchAndSlot()',
            '+ submitReservation()',
            '+ viewVoucherQR()'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.91, w=0.165,
        name='ModalReservaProbador', stereotype='boundary',
        attributes=[
            '- sucursal_id: string',
            '- items: ReservaItemDTO[] = []',
            '- fecha_programada: string'
        ],
        methods=[
            '+ openModal(): void',
            '+ submitReservation(): Promise<void>',
            '+ validateMaxItemsLimit(): bool'
        ]
    )
    d.add_class(
        'ui_voucher', x=0.21, y_top=0.55, w=0.165,
        name='ComprobanteReservaComponent', stereotype='boundary',
        attributes=[
            '- codigo_qr: string',
            '- expiraEn: timestamp',
            '- estado: string = "pendiente"'
        ],
        methods=[
            '+ displayQrCode(): void',
            '+ downloadVoucherPdf(): void',
            '+ startCountdownTimer(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU19ReservaService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- ttl_hours: int = 4'
        ],
        methods=[
            '+ checkAvailability(items, sucursal_id): bool',
            '+ createReservation(data: ReservaDTO): Reserva',
            '+ lockStockForReservation(item_id, qty): void',
            '+ generateReservationQR(reserva_id): str'
        ]
    )
    d.add_class(
        'reserva', x=0.70, y_top=0.91, w=0.22,
        name='Reserva', stereotype='entity', table='reserva',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# cliente_id: uuid [FK]',
            '# sucursal_id: uuid [FK]',
            '+ codigo_qr: text',
            '+ estado: varchar(20) = "pendiente"',
            '+ expira_en: timestamptz',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ insertReservation(data): Reserva',
            '+ getActiveByCustomer(cli_id): list',
            '+ isExpired(): bool'
        ]
    )
    d.add_class(
        'reserva_item', x=0.91, y_top=0.91, w=0.15,
        name='ReservaItem', stereotype='entity', table='reserva_item',
        attributes=[
            '+ id: uuid [PK]',
            '# reserva_id: uuid [FK]',
            '# prenda_variante_id: uuid [FK]',
            '+ cantidad: integer',
            '+ precio_unitario: numeric'
        ],
        methods=[
            '+ insertItems(items): void'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.50, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ stock_actual: integer',
            '+ stock_bloqueado: integer'
        ],
        methods=[
            '+ holdStock(qty): void',
            '+ hasEnoughStock(qty): bool'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.23, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '+ accion: varchar(20) = "crear_reserva"'
        ],
        methods=[
            '+ logReservationCreated(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_modal', side1='right', side2='left', label="«creates reservation»")
    d.add_connector('actor', 'ui_voucher', side1='bottom', side2='left', label="«receives QR»", rad=-0.08)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='left', label="«submits reservation»", is_dep=True)
    d.add_connector('ctrl', 'reserva', side1='right', side2='left', label="«persists reservation»", is_dep=True)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«blocks stock»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('reserva', 'reserva_item', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    d.add_connector('reserva', 'inventario', side1='bottom', side2='top', mult1="1", mult2="1..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu19_creacion_reservas.png")
    svg_path = os.path.join(output_dir, "clases_cu19_creacion_reservas.svg")
    d.save(png_path, svg_path)


def generate_clases_cu20(output_dir):
    """CU-20: Consultar y cancelar reservas activas"""
    d = UMLClassDiagram(
        title="CU-20: Consultar y Cancelar Reservas Activas",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Liberación de stock apartado y trazabilidad de estado"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente', stereotype='actor',
        attributes=[
            '+ clienteId: uuid',
            '+ sessionToken: str'
        ],
        methods=[
            '+ viewMyReservations()',
            '+ openCancelDialog()',
            '+ confirmCancelReservation()'
        ]
    )
    d.add_class(
        'ui_list', x=0.21, y_top=0.91, w=0.165,
        name='MisReservasComponent', stereotype='boundary',
        attributes=[
            '- reservas: ReservaCard[] = []',
            '- activeTab: string = "vigentes"',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadReservations(): Promise<void>',
            '+ openCancelDialog(id): void'
        ]
    )
    d.add_class(
        'ui_dialog', x=0.21, y_top=0.55, w=0.165,
        name='DialogoCancelacion', stereotype='boundary',
        attributes=[
            '- reservaId: string',
            '- motivo: string = ""',
            '- isCancelling: boolean = false'
        ],
        methods=[
            '+ confirmCancellation(): Promise<void>',
            '+ closeDialog(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU20ReservaController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getMyReservations(cliente_id): list',
            '+ cancelReservation(reserva_id, reason): bool',
            '+ releaseHoldStock(reserva_id): void'
        ]
    )
    d.add_class(
        'reserva', x=0.70, y_top=0.91, w=0.22,
        name='Reserva', stereotype='entity', table='reserva',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20) = "cancelada"',
            '+ cancelado_en: timestamptz',
            '+ motivo_cancelacion: text'
        ],
        methods=[
            '+ cancel(reason: str): void',
            '+ isCancellable(): bool'
        ]
    )
    d.add_class(
        'historial', x=0.91, y_top=0.91, w=0.15,
        name='ReservaEstadoHistorial', stereotype='entity', table='reserva_estado_historial',
        attributes=[
            '+ id: uuid [PK]',
            '# reserva_id: uuid [FK]',
            '+ estado_anterior: varchar(20)',
            '+ estado_nuevo: varchar(20)',
            '+ motivo: text'
        ],
        methods=[
            '+ logStatusChange(data): void'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.50, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ stock_bloqueado: integer'
        ],
        methods=[
            '+ releaseHold(qty: int): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.23, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "cancelar_reserva"'
        ],
        methods=[
            '+ logReservationCancelled(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_list', side1='right', side2='left', label="«inspects bookings»")
    d.add_connector('actor', 'ui_dialog', side1='bottom', side2='left', label="«confirms cancel»", rad=-0.08)
    d.add_connector('ui_list', 'ctrl', side1='right', side2='left', label="«loads bookings»", is_dep=True)
    d.add_connector('ui_dialog', 'ctrl', side1='right', side2='bottom', label="«calls cancel»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'reserva', side1='right', side2='left', label="«cancels booking»", is_dep=True)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«releases stock»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('reserva', 'historial', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu20_consulta_reservas.png")
    svg_path = os.path.join(output_dir, "clases_cu20_consulta_reservas.svg")
    d.save(png_path, svg_path)


def generate_clases_cu21(output_dir):
    """CU-21: Preparar reservas en sucursal (apartado físico en probadores)"""
    d = UMLClassDiagram(
        title="CU-21: Preparar Reservas en Sucursal (Probadores)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Workflow de atención y apartado en probador para staff"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Encargado', stereotype='actor',
        attributes=[
            '+ staffId: uuid',
            '+ assignedSucursalId: uuid'
        ],
        methods=[
            '+ viewPendingReservations()',
            '+ scanItemsToProbador()',
            '+ reportStockIncidence()'
        ]
    )
    d.add_class(
        'ui_tray', x=0.21, y_top=0.91, w=0.165,
        name='BandejaReservasSucursal', stereotype='boundary',
        attributes=[
            '- reservasPendientes: ReservaRow[] = []',
            '- sucursalId: string'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadPendingReservations(): Promise<void>',
            '+ openPrepareModal(id): void'
        ]
    )
    d.add_class(
        'ui_prep', x=0.21, y_top=0.55, w=0.165,
        name='ModalPreparacionProbador', stereotype='boundary',
        attributes=[
            '- probador_numero: string = ""',
            '- scannedSkus: string[] = []',
            '- isComplete: boolean = false'
        ],
        methods=[
            '+ scanItem(barcode): void',
            '+ assignProbador(): Promise<void>',
            '+ openIncidentModal(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU21PreparacionController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listPendingReservations(sucursal_id): list',
            '+ prepareReservation(res_id, probador): void',
            '+ reportIncident(res_id, data): void'
        ]
    )
    d.add_class(
        'reserva', x=0.70, y_top=0.91, w=0.22,
        name='Reserva', stereotype='entity', table='reserva',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20) = "lista_en_probador"',
            '+ probador_asignado: varchar(20)',
            '+ preparado_en: timestamptz'
        ],
        methods=[
            '+ setStatusReady(probador: str): void',
            '+ markWithIncident(motive: str): void'
        ]
    )
    d.add_class(
        'historial', x=0.91, y_top=0.91, w=0.15,
        name='ReservaEstadoHistorial', stereotype='entity', table='reserva_estado_historial',
        attributes=[
            '+ id: uuid [PK]',
            '# reserva_id: uuid [FK]',
            '+ estado_nuevo: varchar(20)',
            '+ comentario: text'
        ],
        methods=[
            '+ logStatus(data): void'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.52, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ stock_actual: integer',
            '+ stock_bloqueado: integer'
        ],
        methods=[
            '+ confirmHold(qty): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "preparar_reserva"'
        ],
        methods=[
            '+ logPrepared(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_tray', side1='right', side2='left', label="«monitors queue»")
    d.add_connector('actor', 'ui_prep', side1='bottom', side2='left', label="«places in fitting room»", rad=-0.08)
    d.add_connector('ui_tray', 'ctrl', side1='right', side2='left', label="«lists queue»", is_dep=True)
    d.add_connector('ui_prep', 'ctrl', side1='right', side2='bottom', label="«marks ready»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'reserva', side1='right', side2='left', label="«updates status»", is_dep=True)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('reserva', 'historial', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu21_preparacion_reservas.png")
    svg_path = os.path.join(output_dir, "clases_cu21_preparacion_reservas.svg")
    d.save(png_path, svg_path)


def generate_clases_cu22(output_dir):
    """CU-22: Realizar compra digital (checkout con carrito de compras)"""
    d = UMLClassDiagram(
        title="CU-22: Realizar Compra Digital (Checkout E-Commerce)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Validación de existencias, cálculo de totales y orden online"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente', stereotype='actor',
        attributes=[
            '+ clienteId: uuid',
            '+ email: string',
            '+ shippingAddress: str'
        ],
        methods=[
            '+ reviewCartItems()',
            '+ fillCheckoutDetails()',
            '+ confirmAndPay()'
        ]
    )
    d.add_class(
        'ui_cart', x=0.21, y_top=0.91, w=0.165,
        name='CarritoComponent', stereotype='boundary',
        attributes=[
            '- items: CartItemDTO[] = []',
            '- subtotal: number = 0',
            '- cuponCode: string | null'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ updateQuantity(sku, qty): void',
            '+ proceedToCheckout(): void'
        ]
    )
    d.add_class(
        'ui_check', x=0.21, y_top=0.55, w=0.165,
        name='CheckoutComponent', stereotype='boundary',
        attributes=[
            '- direccion_envio: string = ""',
            '- metodo_pago: string = "stripe"',
            '- orderSummary: OrderTotalsDTO'
        ],
        methods=[
            '+ submitOrder(): Promise<void>',
            '+ validateShippingAddress(): bool',
            '+ launchPaymentGateway(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU22CheckoutService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getCart(cliente_id): CartDTO',
            '+ validateCartStock(cart_id): bool',
            '+ calculateTotals(items, coupon): OrderTotalsDTO',
            '+ createOnlineOrder(data: OrderCreateDTO): Venta'
        ]
    )
    d.add_class(
        'venta', x=0.70, y_top=0.91, w=0.22,
        name='Venta', stereotype='entity', table='venta',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# cliente_id: uuid [FK]',
            '+ total: numeric(10,2)',
            '+ tipo_venta: varchar(20) = "online"',
            '+ estado: varchar(20) = "pendiente_pago"',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ createOrder(data): Venta',
            '+ markPaid(): void',
            '+ cancelOrder(): void'
        ]
    )
    d.add_class(
        'detalle', x=0.91, y_top=0.91, w=0.15,
        name='VentaDetalle', stereotype='entity', table='venta_detalle',
        attributes=[
            '+ id: uuid [PK]',
            '# venta_id: uuid [FK]',
            '# prenda_variante_id: uuid [FK]',
            '+ cantidad: integer',
            '+ precio_unitario: numeric'
        ],
        methods=[
            '+ insertDetails(items): void'
        ]
    )
    d.add_class(
        'carrito', x=0.43, y_top=0.52, w=0.20,
        name='Carrito', stereotype='entity', table='carrito',
        attributes=[
            '+ id: uuid [PK]',
            '# cliente_id: uuid [FK]',
            '+ activo: boolean = true'
        ],
        methods=[
            '+ clearCart(): void',
            '+ getActiveCart(cli_id): Carrito'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.50, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ stock_actual: integer'
        ],
        methods=[
            '+ decrementStock(qty: int): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.23, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "crear_orden_online"'
        ],
        methods=[
            '+ logOrderPlaced(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_cart', side1='right', side2='left', label="«reviews basket»")
    d.add_connector('actor', 'ui_check', side1='bottom', side2='left', label="«completes checkout»", rad=-0.08)
    d.add_connector('ui_cart', 'ctrl', side1='right', side2='left', label="«gets cart»", is_dep=True)
    d.add_connector('ui_check', 'ctrl', side1='right', side2='bottom', label="«creates order»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'venta', side1='right', side2='left', label="«creates order entity»", is_dep=True)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«deducts inventory»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('venta', 'detalle', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu22_checkout_carrito.png")
    svg_path = os.path.join(output_dir, "clases_cu22_checkout_carrito.svg")
    d.save(png_path, svg_path)


def generate_clases_cu23(output_dir):
    """CU-23: Realizar compra presencial en caja (punto de venta POS online)"""
    d = UMLClassDiagram(
        title="CU-23: Compra Presencial en Caja (POS Online)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Facturación en tiempo real, lector de códigos y ticket fiscal"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cajero POS', stereotype='actor',
        attributes=[
            '+ cajaId: uuid',
            '+ sucursalId: uuid',
            '+ cashierId: uuid'
        ],
        methods=[
            '+ scanBarcodeSku()',
            '+ selectPaymentMethod()',
            '+ finalizeSale()',
            '+ printThermalTicket()'
        ]
    )
    d.add_class(
        'ui_pos', x=0.21, y_top=0.91, w=0.165,
        name='PosTerminalComponent', stereotype='boundary',
        attributes=[
            '- scannedItems: PosLineItem[] = []',
            '- subtotal: number = 0',
            '- barcodeBuffer: string = ""'
        ],
        methods=[
            '+ onBarcodeScanned(code): void',
            '+ addLineItem(sku): void',
            '+ openPaymentModal(): void'
        ]
    )
    d.add_class(
        'ui_cobro', x=0.21, y_top=0.55, w=0.165,
        name='ModalCobroPos', stereotype='boundary',
        attributes=[
            '- totalAPagar: number',
            '- montoEfectivo: number',
            '- cambio: number = 0',
            '- metodo: string = "efectivo"'
        ],
        methods=[
            '+ calculateChange(): number',
            '+ confirmPayment(): Promise<void>',
            '+ printReceipt(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU23PosController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ scanBarcode(barcode: str): PrendaVariante',
            '+ processSale(data: SaleCreateDTO): Venta',
            '+ deductInventoryImmediate(items, suc_id): void',
            '+ generateReceiptNumber(emp_id): str'
        ]
    )
    d.add_class(
        'venta', x=0.70, y_top=0.91, w=0.22,
        name='Venta', stereotype='entity', table='venta',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# sucursal_id: uuid [FK]',
            '# usuario_cajero_id: uuid [FK]',
            '+ numero_factura: varchar(40)',
            '+ total: numeric(10,2)',
            '+ tipo_venta: varchar(20) = "pos"',
            '+ metodo_pago: varchar(30)'
        ],
        methods=[
            '+ recordPosSale(data): Venta',
            '+ getDailyTotals(suc_id): dict'
        ]
    )
    d.add_class(
        'detalle', x=0.91, y_top=0.91, w=0.15,
        name='VentaDetalle', stereotype='entity', table='venta_detalle',
        attributes=[
            '+ id: uuid [PK]',
            '# venta_id: uuid [FK]',
            '# prenda_variante_id: uuid [FK]',
            '+ cantidad: integer',
            '+ precio_unitario: numeric'
        ],
        methods=[
            '+ insertDetails(items): void'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.52, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ stock_actual: integer'
        ],
        methods=[
            '+ decrementStockImmediate(qty: int): void'
        ]
    )
    d.add_class(
        'movimiento', x=0.91, y_top=0.52, w=0.15,
        name='MovimientoInventario', stereotype='entity', table='movimiento_inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ tipo: varchar(30) = "venta_pos"',
            '+ cantidad: integer'
        ],
        methods=[
            '+ logPosMovement(data): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "venta_pos"'
        ],
        methods=[
            '+ logPosSale(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_pos', side1='right', side2='left', label="«scans products»")
    d.add_connector('actor', 'ui_cobro', side1='bottom', side2='left', label="«receives cash/card»", rad=-0.08)
    d.add_connector('ui_pos', 'ctrl', side1='right', side2='left', label="«scans barcode»", is_dep=True)
    d.add_connector('ui_cobro', 'ctrl', side1='right', side2='bottom', label="«submits sale»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'venta', side1='right', side2='left', label="«records POS sale»", is_dep=True)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«decrements stock»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('venta', 'detalle', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    d.add_connector('inventario', 'movimiento', side1='right', side2='left', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu23_punto_venta_pos.png")
    svg_path = os.path.join(output_dir, "clases_cu23_punto_venta_pos.svg")
    d.save(png_path, svg_path)

