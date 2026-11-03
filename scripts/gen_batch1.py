import os
import sys

# Add current script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robustness_base import (
    setup_canvas, draw_actor, draw_boundary, draw_controller, draw_entity,
    draw_actor_link, draw_call_arrow, draw_crud_arrow, save_and_close
)

# -------------------------------------------------------------------------
# CU-06: Registrar empresa contratante (Tenant aislado)
# -------------------------------------------------------------------------
def generate_cu06(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-06: REGISTRAR EMPRESA CONTRATANTE (TENANT AISLADO)",
        "Actor: Superadministrador SaaS | Boundary: TenantRegisterComponent | Controller: create_tenant() | Entidades: Empresa, Rol, Usuario, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Superadmin", "Superadministrador")
    draw_boundary(ax, 0.30, 0.50, "TenantRegisterUI", "saas-empresas.component")
    draw_controller(ax, 0.55, 0.50, "create_tenant()", "saas_service.py")
    
    draw_entity(ax, 0.88, 0.78, "Empresa", "db / empresa (tenant)")
    draw_entity(ax, 0.88, 0.58, "Rol", "db / rol (admin_empresa)")
    draw_entity(ax, 0.88, 0.38, "Usuario", "db / usuario (admin)")
    draw_entity(ax, 0.88, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/saas/empresas\n(razon_social, nit, admin)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.78, "POST", "crear empresa (pendiente_plan)", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.58, "GET", "obtener rol administrador", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.38, "POST", "crear usuario admin tenant", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.18, "POST", "auditar alta tenant", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu06_registrar_empresa")

# -------------------------------------------------------------------------
# CU-07: Asignar plan y gestionar suscripcion
# -------------------------------------------------------------------------
def generate_cu07(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-07: ASIGNAR PLAN Y GESTIONAR SUSCRIPCIÓN",
        "Actor: Superadministrador SaaS | Boundary: AssignPlanComponent | Controller: assign_plan() | Entidades: Empresa, Plan, Suscripcion, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Superadmin", "Superadministrador")
    draw_boundary(ax, 0.30, 0.50, "AssignPlanUI", "plan-assign.component")
    draw_controller(ax, 0.55, 0.50, "assign_plan()", "saas_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Empresa", "db / empresa")
    draw_entity(ax, 0.88, 0.60, "Plan", "db / plan")
    draw_entity(ax, 0.88, 0.40, "Suscripcion", "db / suscripcion")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/saas/suscripciones\n(empresa_id, plan_id, meses)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "PATCH", "activar estado empresa", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "verificar plan y límites", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "POST", "crear suscripcion activa", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar asignacion plan", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu07_asignar_plan")

# -------------------------------------------------------------------------
# CU-08: Consultar plan y limites de suscripcion
# -------------------------------------------------------------------------
def generate_cu08(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-08: CONSULTAR PLAN Y LÍMITES DE SUSCRIPCIÓN",
        "Actor: Administrador Empresa | Boundary: SubscriptionStatusUI | Controller: get_my_subscription() | Entidades: Suscripcion, Plan, PlanLimite, Sucursal"
    )
    draw_actor(ax, 0.10, 0.50, "Admin Empresa", "Tenant Manager")
    draw_boundary(ax, 0.30, 0.50, "SubscriptionStatusUI", "my-subscription.component")
    draw_controller(ax, 0.55, 0.50, "get_my_plan()", "suscripcion_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Suscripcion", "db / suscripcion")
    draw_entity(ax, 0.88, 0.60, "Plan", "db / plan")
    draw_entity(ax, 0.88, 0.40, "PlanLimite", "db / plan_limite")
    draw_entity(ax, 0.88, 0.20, "Sucursal", "db / sucursal (activas)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET /api/v1/suscripcion/actual\n(token tenant)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "consultar vigencia suscripcion", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "datos de plan contratado", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "límites de sucursales / IA", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET", "contar sucursales activas", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu08_consultar_plan_limites")

# -------------------------------------------------------------------------
# CU-09: Panel de administracion SaaS (supervision y suspension)
# -------------------------------------------------------------------------
def generate_cu09(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-09: PANEL DE ADMINISTRACIÓN SAAS (SUPERVISIÓN Y SUSPENSIÓN)",
        "Actor: Superadministrador SaaS | Boundary: SaasDashboardUI | Controller: saas_admin_actions() | Entidades: Empresa, Suscripcion, BitacoraAuditoria, Venta"
    )
    draw_actor(ax, 0.10, 0.50, "Superadmin", "Superadministrador")
    draw_boundary(ax, 0.30, 0.50, "SaasDashboardUI", "saas-dashboard.component")
    draw_controller(ax, 0.55, 0.50, "saas_admin()", "saas_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Empresa", "db / empresa (status)")
    draw_entity(ax, 0.88, 0.60, "Suscripcion", "db / suscripcion")
    draw_entity(ax, 0.88, 0.40, "Venta", "db / venta (métricas)")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET / PATCH /api/v1/saas/...\n(listar tenants / suspender)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET/PATCH", "listar / suspender empresa", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "suscripciones por vencer", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "volumen transaccional global", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar accion superadmin", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu09_panel_saas_supervision")

# -------------------------------------------------------------------------
# CU-10: Administrar usuarios y roles por empresa (aislados)
# -------------------------------------------------------------------------
def generate_cu10(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-10: ADMINISTRAR USUARIOS Y ROLES POR EMPRESA",
        "Actor: Administrador Empresa | Boundary: UserManagementUI | Controller: empleado_service() | Entidades: Usuario, Rol, Sucursal, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Admin Empresa", "Tenant Manager")
    draw_boundary(ax, 0.30, 0.50, "UserManagementUI", "usuarios.component")
    draw_controller(ax, 0.55, 0.50, "manage_users()", "empleado_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Usuario", "db / usuario (empleados)")
    draw_entity(ax, 0.88, 0.60, "Rol", "db / rol (cajero/encargado)")
    draw_entity(ax, 0.88, 0.40, "Sucursal", "db / sucursal")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/empleados\n(datos, rol, sucursal_id)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST/PATCH", "crear / baja lógica usuario", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "verificar rol de tenant", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "validar sucursal de tenant", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar alta empleado", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu10_administrar_usuarios_roles")

# -------------------------------------------------------------------------
# CU-11: Administrar sucursales (BR-02 limites)
# -------------------------------------------------------------------------
def generate_cu11(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-11: ADMINISTRAR SUCURSALES (LÍMITES BR-02)",
        "Actor: Administrador Empresa | Boundary: SucursalManagementUI | Controller: sucursal_service() | Entidades: Sucursal, Ciudad, Suscripcion, PlanLimite"
    )
    draw_actor(ax, 0.10, 0.50, "Admin Empresa", "Tenant Manager")
    draw_boundary(ax, 0.30, 0.50, "SucursalUI", "sucursales.component")
    draw_controller(ax, 0.55, 0.50, "create_sucursal()", "sucursal_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Sucursal", "db / sucursal")
    draw_entity(ax, 0.88, 0.60, "Ciudad", "db / ciudad")
    draw_entity(ax, 0.88, 0.40, "Suscripcion", "db / suscripcion")
    draw_entity(ax, 0.88, 0.20, "PlanLimite", "db / plan_limite")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/sucursales\n(nombre, ciudad_id, dir)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "crear sucursal tenant", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "verificar ciudad catálogo", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "verificar suscripción activa", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET", "validar límite sucursales (BR-02)", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu11_administrar_sucursales")

# -------------------------------------------------------------------------
# CU-12: Administrar catalogo de productos (CRUD prendas, variantes SKU)
# -------------------------------------------------------------------------
def generate_cu12(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-12: ADMINISTRAR CATÁLOGO DE PRODUCTOS (PRENDAS Y VARIANTES SKU)",
        "Actor: Administrador Empresa | Boundary: CatalogoAdminUI | Controller: catalogo_service() | Entidades: Prenda, Categoria, Variante, PrecioHistorial, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Admin Empresa", "Tenant Manager")
    draw_boundary(ax, 0.30, 0.50, "CatalogoAdminUI", "prendas-admin.component")
    draw_controller(ax, 0.55, 0.50, "crud_prenda()", "catalogo_service.py")
    
    draw_entity(ax, 0.88, 0.82, "Prenda", "db / prenda")
    draw_entity(ax, 0.88, 0.66, "Categoria", "db / categoria")
    draw_entity(ax, 0.88, 0.50, "Variante", "db / variante (SKU)")
    draw_entity(ax, 0.88, 0.34, "PrecioHistorial", "db / precio_historial")
    draw_entity(ax, 0.88, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/prendas\n(datos, categoria_id, variantes)")
    
    draw_crud_arrow(ax, 0.63, 0.54, 0.81, 0.82, "POST/PATCH", "crear prenda / baja lógica", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.52, 0.81, 0.66, "GET", "verificar categoría de tenant", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.50, 0.81, 0.50, "POST", "insertar variantes con SKU único", rad=0.00, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.34, "POST", "registrar precio inicial", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.46, 0.81, 0.18, "POST", "auditar modificación catálogo", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu12_administrar_catalogo_prendas")

# -------------------------------------------------------------------------
# CU-13: Consultar catalogo de prendas (Online / Offline Warning)
# -------------------------------------------------------------------------
def generate_cu13(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-13: CONSULTAR CATÁLOGO DE PRENDAS (ALERTA DESACTUALIZACIÓN)",
        "Actor: Cliente | Boundary: CatalogoPublicoUI | Controller: get_catalogo() | Entidades: Prenda, Variante, Categoria, CatalogoLocalCache"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente", "Visitante Web / App")
    draw_boundary(ax, 0.30, 0.50, "CatalogoPublicoUI", "catalogo.component / Flutter")
    draw_controller(ax, 0.55, 0.50, "getCatalogo()", "catalogo_service.py / PWA")
    
    draw_entity(ax, 0.88, 0.80, "Prenda", "db / prenda (activas)")
    draw_entity(ax, 0.88, 0.60, "Variante", "db / variante (talla, color)")
    draw_entity(ax, 0.88, 0.40, "Categoria", "db / categoria")
    draw_entity(ax, 0.88, 0.20, "CatalogoCache", "local / SQLite / IndexedDB")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET /api/v1/catalogo\n(tenant_slug, online_status)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "consultar prendas activas", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "obtener variantes y precios", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "árbol de categorías", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET/PUT", "leer cache / marcar stale banner", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu13_consultar_catalogo_prendas")

# -------------------------------------------------------------------------
# CU-14: Filtrar productos (talla, color, categoria, precio)
# -------------------------------------------------------------------------
def generate_cu14(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-14: FILTRAR PRODUCTOS MULTIDIMENSIONAL",
        "Actor: Cliente | Boundary: FilterSidebarUI | Controller: filter_products() | Entidades: Prenda, Variante, Color, Talla, Categoria"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente", "Comprador")
    draw_boundary(ax, 0.30, 0.50, "FilterSidebarUI", "catalog-filters.component")
    draw_controller(ax, 0.55, 0.50, "applyFilters()", "catalogo_service.py")
    
    draw_entity(ax, 0.88, 0.82, "Prenda", "db / prenda")
    draw_entity(ax, 0.88, 0.66, "Variante", "db / variante (SKU)")
    draw_entity(ax, 0.88, 0.50, "Color / Talla", "db / color, talla (global)")
    draw_entity(ax, 0.88, 0.34, "Categoria", "db / categoria")
    draw_entity(ax, 0.88, 0.18, "PrecioHistorial", "db / precio_historial (rango)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET /api/v1/catalogo/filtros\n(color, talla, precio_min, max)")
    
    draw_crud_arrow(ax, 0.63, 0.54, 0.81, 0.82, "GET", "filtrar prendas disponibles", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.52, 0.81, 0.66, "GET", "buscar variantes coincidentes", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.50, 0.81, 0.50, "GET", "matchear color y talla", rad=0.00, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.34, "GET", "filtrar por categoría", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.46, 0.81, 0.18, "GET", "validar rango de precios", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu14_filtrar_productos")

# -------------------------------------------------------------------------
# CU-15: Administrar proveedores textiles
# -------------------------------------------------------------------------
def generate_cu15(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-15: ADMINISTRAR PROVEEDORES TEXTILES",
        "Actor: Administrador Empresa | Boundary: ProveedorAdminUI | Controller: proveedor_service() | Entidades: Proveedor, Prenda, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Admin Empresa", "Tenant Manager")
    draw_boundary(ax, 0.30, 0.50, "ProveedorAdminUI", "proveedores.component")
    draw_controller(ax, 0.55, 0.50, "manage_proveedor()", "proveedor_service.py")
    
    draw_entity(ax, 0.88, 0.75, "Proveedor", "db / proveedor (tenant)")
    draw_entity(ax, 0.88, 0.50, "Prenda", "db / prenda (insumos)")
    draw_entity(ax, 0.88, 0.25, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST / PUT / DELETE /api/v1/proveedores\n(nit, razon_social, contacto)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.75, "POST/PATCH", "CRUD proveedor / validar NIT único", rad=-0.06, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.50, 0.81, 0.50, "GET", "verificar prendas asociadas", rad=0.00, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.47, 0.81, 0.25, "POST", "auditar cambios de proveedor", rad=0.06, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu15_administrar_proveedores")

# -------------------------------------------------------------------------
# CU-16: Administrar temporadas y colecciones comerciales
# -------------------------------------------------------------------------
def generate_cu16(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-16: ADMINISTRAR TEMPORADAS Y COLECCIONES COMERCIALES",
        "Actor: Administrador Empresa | Boundary: ColeccionAdminUI | Controller: coleccion_service() | Entidades: Temporada, Coleccion, Prenda, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Admin Empresa", "Tenant Manager")
    draw_boundary(ax, 0.30, 0.50, "ColeccionAdminUI", "temporadas.component")
    draw_controller(ax, 0.55, 0.50, "manage_season()", "coleccion_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Temporada", "db / temporada (fechas)")
    draw_entity(ax, 0.88, 0.60, "Coleccion", "db / coleccion")
    draw_entity(ax, 0.88, 0.40, "Prenda", "db / prenda")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/temporadas\n(nombre, fecha_inicio, fecha_fin)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "validar e insertar temporada", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "POST", "asociar coleccion a temporada", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "PATCH", "vincular prendas a coleccion", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar catalogo comercial", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu16_administrar_temporadas_colecciones")

# -------------------------------------------------------------------------
# CU-17: Gestionar inventario global y local (ajustes y transferencias)
# -------------------------------------------------------------------------
def generate_cu17(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-17: GESTIONAR INVENTARIO (AJUSTES Y TRANSFERENCIAS)",
        "Actor: Encargado Sucursal / Admin | Boundary: InventarioUI | Controller: inventario_service() | Entidades: Inventario, MovimientoInventario, TransferenciaInventario, Variante"
    )
    draw_actor(ax, 0.10, 0.50, "Encargado / Admin", "Sucursal / Tenant")
    draw_boundary(ax, 0.30, 0.50, "InventarioUI", "inventario-kardex.component")
    draw_controller(ax, 0.55, 0.50, "ajustar_stock()", "inventario_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Inventario", "db / inventario (stock actual)")
    draw_entity(ax, 0.88, 0.60, "MovimientoInv", "db / movimiento_inventario")
    draw_entity(ax, 0.88, 0.40, "TransferenciaInv", "db / transferencia_inventario")
    draw_entity(ax, 0.88, 0.20, "Variante", "db / variante (SKU)")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/inventario/transferir\n(origen, destino, items)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "PATCH", "descontar origen / sumar destino", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "POST", "kardex transaccional append-only", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "POST", "registrar guía de transferencia", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET", "verificar existencia de variante", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu17_gestionar_inventario")

# -------------------------------------------------------------------------
# CU-18: Consultar disponibilidad por sucursal (stock fisico)
# -------------------------------------------------------------------------
def generate_cu18(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-18: CONSULTAR DISPONIBILIDAD POR SUCURSAL",
        "Actor: Cliente / Cajero | Boundary: StockConsultUI | Controller: get_stock_by_branch() | Entidades: Sucursal, Inventario, Variante, Prenda"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente / Cajero", "Consultante")
    draw_boundary(ax, 0.30, 0.50, "StockConsultUI", "stock-lookup.component")
    draw_controller(ax, 0.55, 0.50, "check_stock()", "inventario_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Sucursal", "db / sucursal")
    draw_entity(ax, 0.88, 0.60, "Inventario", "db / inventario (cantidad_disponible)")
    draw_entity(ax, 0.88, 0.40, "Variante", "db / variante (talla, color)")
    draw_entity(ax, 0.88, 0.20, "Prenda", "db / prenda")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "GET /api/v1/inventario/sucursal\n(variante_id, sucursal_id)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "GET", "listar tiendas habilitadas", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "consultar stock en tiempo real", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "GET", "obtener SKU y atributos", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "GET", "ficha técnica de la prenda", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu18_consultar_disponibilidad_sucursal")

# -------------------------------------------------------------------------
# CU-19: Realizar reserva de multiples prendas (modo en linea)
# -------------------------------------------------------------------------
def generate_cu19(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-19: REALIZAR RESERVA DE PRENDAS (EN LÍNEA)",
        "Actor: Cliente | Boundary: ReservaOnlineUI | Controller: create_reservation() | Entidades: Reserva, ReservaDetalle, Inventario, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente", "Comprador Registrado")
    draw_boundary(ax, 0.30, 0.50, "ReservaOnlineUI", "reserva-modal.component")
    draw_controller(ax, 0.55, 0.50, "create_reserva()", "reserva_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Reserva", "db / reserva (pendiente)")
    draw_entity(ax, 0.88, 0.60, "ReservaDetalle", "db / reserva_detalle")
    draw_entity(ax, 0.88, 0.40, "Inventario", "db / inventario (cantidad_reservada)")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "POST /api/v1/reservas\n(sucursal_id, items, fecha_visita)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "POST", "crear reserva con UUID", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "POST", "insertar variantes a probar", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "PATCH", "bloquear stock en inventario", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar solicitud de reserva", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu19_realizar_reserva_online")

# -------------------------------------------------------------------------
# CU-20: Consultar y cancelar reservas activas
# -------------------------------------------------------------------------
def generate_cu20(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-20: CONSULTAR Y CANCELAR RESERVAS ACTIVAS",
        "Actor: Cliente / Encargado | Boundary: MisReservasUI | Controller: cancel_reservation() | Entidades: Reserva, ReservaDetalle, Inventario, BitacoraAuditoria"
    )
    draw_actor(ax, 0.10, 0.50, "Cliente / Encargado", "Usuario / Personal")
    draw_boundary(ax, 0.30, 0.50, "MisReservasUI", "mis-reservas.component")
    draw_controller(ax, 0.55, 0.50, "cancel_reserva()", "reserva_service.py")
    
    draw_entity(ax, 0.88, 0.80, "Reserva", "db / reserva (cancelada)")
    draw_entity(ax, 0.88, 0.60, "ReservaDetalle", "db / reserva_detalle")
    draw_entity(ax, 0.88, 0.40, "Inventario", "db / inventario (liberar stock)")
    draw_entity(ax, 0.88, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.165, 0.50, 0.22, 0.50)
    draw_call_arrow(ax, 0.38, 0.50, 0.47, 0.50, "PATCH /api/v1/reservas/{id}/cancelar\n(motivo_cancelacion)")
    
    draw_crud_arrow(ax, 0.63, 0.53, 0.81, 0.80, "PATCH", "cambiar estado a cancelada", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.63, 0.51, 0.81, 0.60, "GET", "leer líneas de prendas reservadas", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.63, 0.48, 0.81, 0.40, "PATCH", "restituir stock disponible", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.63, 0.45, 0.81, 0.20, "POST", "auditar liberación de reserva", rad=0.10, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu20_consultar_cancelar_reservas")

if __name__ == '__main__':
    out = os.path.join(os.getcwd(), 'Segundo-parcial', 'docs', 'diagramas')
    os.makedirs(out, exist_ok=True)
    generate_cu06(out)
    generate_cu07(out)
    generate_cu08(out)
    generate_cu09(out)
    generate_cu10(out)
    generate_cu11(out)
    generate_cu12(out)
    generate_cu13(out)
    generate_cu14(out)
    generate_cu15(out)
    generate_cu16(out)
    generate_cu17(out)
    generate_cu18(out)
    generate_cu19(out)
    generate_cu20(out)
    print("Batch 1 (CU06-CU20) completed!")

