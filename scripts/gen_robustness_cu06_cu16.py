import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Modern Soft UI Palette - compatible with CU01-CU05
COLORS = {
    'bg': '#F8FAFC',
    'actor_fill': '#EDE9FE',
    'actor_edge': '#7C3AED',
    'boundary_fill': '#E0F2FE',
    'boundary_edge': '#0284C7',
    'controller_fill': '#DCFCE7',
    'controller_edge': '#16A34A',
    'entity_fill': '#FEF3C7',
    'entity_edge': '#D97706',
    'text': '#0F172A',
    'subtext': '#475569',
    'line': '#64748B',
    'arrow_crud': '#B45309',
    'arrow_call': '#0369A1',
    'label_bg': '#FFFFFF',
}

def setup_canvas(title, subtitle, width=16.0, height=9.6):
    fig, ax = plt.subplots(figsize=(width, height), dpi=300)
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Header
    ax.text(0.5, 0.968, title, fontsize=14.5, fontweight='bold', ha='center', va='top', color=COLORS['text'])
    ax.text(0.5, 0.935, subtitle, fontsize=9.2, ha='center', va='top', color=COLORS['subtext'])
    
    # Legend
    legend_items = [
        ('Actor (Línea simple)', COLORS['actor_fill'], COLORS['actor_edge']),
        ('Boundary (Vistas / UI / Modales)', COLORS['boundary_fill'], COLORS['boundary_edge']),
        ('Controller (Controladores Backend)', COLORS['controller_fill'], COLORS['controller_edge']),
        ('Entity (Modelos de BD)', COLORS['entity_fill'], COLORS['entity_edge']),
    ]
    x_leg = 0.06
    for label, fill, edge in legend_items:
        patch = patches.FancyBboxPatch(
            (x_leg, 0.020), 0.19, 0.038,
            boxstyle="round,pad=0.01,rounding_size=0.015",
            facecolor=fill, edgecolor=edge, linewidth=1.5
        )
        ax.add_patch(patch)
        ax.text(x_leg + 0.095, 0.039, label, fontsize=8.0, ha='center', va='center', fontweight='bold', color=COLORS['text'])
        x_leg += 0.23
        
    return fig, ax

def draw_actor(ax, x, y, name, sub=""):
    w, h = 0.115, 0.08
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=COLORS['actor_fill'], edgecolor=COLORS['actor_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.018, "[ACTOR]", fontsize=8.2, fontweight='bold', ha='center', va='center', color=COLORS['actor_edge'], zorder=4)
    ax.text(x, y - 0.003, name, fontsize=9.2, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.022, sub, fontsize=7.4, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_boundary(ax, x, y, name, sub=""):
    w, h = 0.155, 0.08
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=COLORS['boundary_fill'], edgecolor=COLORS['boundary_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.020, "«boundary»", fontsize=8.2, fontweight='bold', ha='center', va='center', color=COLORS['boundary_edge'], zorder=4)
    ax.text(x, y + 0.002, name, fontsize=8.6, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.020, sub, fontsize=7.2, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_controller(ax, x, y, name, sub=""):
    w, h = 0.165, 0.082
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor=COLORS['controller_fill'], edgecolor=COLORS['controller_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.020, "«control»", fontsize=8.2, fontweight='bold', ha='center', va='center', color=COLORS['controller_edge'], zorder=4)
    ax.text(x, y + 0.002, name, fontsize=8.6, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.020, sub, fontsize=7.2, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_entity(ax, x, y, name, sub=""):
    w, h = 0.14, 0.075
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor=COLORS['entity_fill'], edgecolor=COLORS['entity_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.018, "«entity»", fontsize=8.0, fontweight='bold', ha='center', va='center', color=COLORS['entity_edge'], zorder=4)
    ax.text(x, y - 0.002, name, fontsize=8.6, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.020, sub, fontsize=7.0, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_actor_link(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color='#64748B', linewidth=2.0, linestyle='-', zorder=2)

def draw_call_arrow(ax, x1, y1, x2, y2, label, offset_y=0.022, rad=0.0):
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.30,head_length=0.40",
            color=COLORS['arrow_call'],
            lw=1.7,
            connectionstyle=connectionstyle
        ),
        zorder=2
    )
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + offset_y
    ax.text(
        mx, my, label, fontsize=7.5, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.20", fc=COLORS['label_bg'], ec=COLORS['boundary_edge'], lw=1, alpha=0.95),
        color=COLORS['arrow_call'], fontweight='bold', zorder=5
    )

def draw_crud_arrow(ax, x1, y1, x2, y2, crud_verb, detail="", rad=0.0, offset_y=0.02, offset_x=0.0):
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.30,head_length=0.40",
            color=COLORS['arrow_crud'],
            lw=1.7,
            connectionstyle=connectionstyle
        ),
        zorder=2
    )
    mx = (x1 + x2) / 2 + offset_x
    my = (y1 + y2) / 2 + offset_y
    label = f"{crud_verb}: {detail}" if detail else crud_verb
    ax.text(
        mx, my, label, fontsize=7.2, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.18", fc=COLORS['label_bg'], ec=COLORS['entity_edge'], lw=1, alpha=0.95),
        color=COLORS['arrow_crud'], fontweight='bold', zorder=5
    )

def save_and_close(fig, output_dir, name):
    png_path = os.path.join(output_dir, f"{name}.png")
    svg_path = os.path.join(output_dir, f"{name}.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {name}.png and {name}.svg")

# =========================================================================
# CU-06: REGISTRAR EMPRESA CONTRATANTE (TENANT CON ENTORNO LÓGICO AISLADO)
# Boundaries: EmpresasPanelComponent (Lista de tenants) y EmpresaFormComponent (Formulario alta)
# =========================================================================
def generate_cu06(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-06: REGISTRAR EMPRESA CONTRATANTE (TENANT AISLADO)",
        "Actor: Superadministrador SaaS | Boundaries: EmpresasPanelComponent, EmpresaFormComponent | Controllers: list_empresas(), create_empresa() | Entities: Empresa, Rol, Usuario, BitacoraAuditoria"
    )
    # Actor
    draw_actor(ax, 0.08, 0.50, "Superadmin", "Superadministrador")
    
    # Boundaries (2 vistas del frontend: panel listado y formulario de creación)
    draw_boundary(ax, 0.27, 0.68, "EmpresasPanelUI", "saas/panel.component.html")
    draw_boundary(ax, 0.27, 0.32, "EmpresaFormUI", "empresa-form.component.html")
    
    # Controllers
    draw_controller(ax, 0.52, 0.68, "list_empresas()", "saas.py (Router)")
    draw_controller(ax, 0.52, 0.32, "create_empresa()", "saas_service.py")
    
    # Entities
    draw_entity(ax, 0.86, 0.80, "Empresa", "db / empresa (tenant)")
    draw_entity(ax, 0.86, 0.58, "Rol", "db / rol (admin_empresa)")
    draw_entity(ax, 0.86, 0.36, "Usuario", "db / usuario (admin)")
    draw_entity(ax, 0.86, 0.16, "BitacoraAuditoria", "db / bitacora")
    
    # Actor -> Boundaries (línea simple sin llamada)
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # Boundaries -> Controllers
    draw_call_arrow(ax, 0.35, 0.68, 0.435, 0.68, "GET /api/v1/saas/empresas", offset_y=0.025)
    draw_call_arrow(ax, 0.35, 0.32, 0.435, 0.32, "POST /api/v1/saas/empresas\n(razon_social, nit, admin)", offset_y=-0.035)
    
    # list_empresas -> Empresa
    draw_crud_arrow(ax, 0.60, 0.70, 0.79, 0.80, "GET", "listar empresas y estados", rad=0.0, offset_y=0.02)
    
    # create_empresa -> Entities
    draw_crud_arrow(ax, 0.60, 0.38, 0.79, 0.76, "POST", "crear empresa ('pendiente_plan')", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.60, 0.35, 0.79, 0.58, "GET", "obtener rol admin_empresa", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.31, 0.79, 0.36, "POST", "crear usuario admin tenant", rad=0.03, offset_y=-0.02)
    draw_crud_arrow(ax, 0.60, 0.27, 0.79, 0.16, "POST", "auditar alta tenant", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu06_registrar_empresa")

# =========================================================================
# CU-07: ASIGNAR PLAN Y GESTIONAR SUSCRIPCIÓN
# Boundaries: EmpresaDetailComponent (Ficha tenant) y PlanAssignModal (Modal de selección de planes)
# =========================================================================
def generate_cu07(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-07: ASIGNAR PLAN Y GESTIONAR SUSCRIPCIÓN",
        "Actor: Superadministrador SaaS | Boundaries: EmpresaDetailComponent, PlanAssignModal | Controllers: list_planes(), assign_suscripcion() | Entities: Empresa, Plan, Suscripcion, BitacoraAuditoria"
    )
    draw_actor(ax, 0.08, 0.50, "Superadmin", "Superadministrador")
    
    draw_boundary(ax, 0.27, 0.68, "EmpresaDetailUI", "empresa-detail.component.html")
    draw_boundary(ax, 0.27, 0.32, "PlanAssignModal", "plan-assign-modal.html")
    
    draw_controller(ax, 0.52, 0.68, "list_planes()", "saas_service.py")
    draw_controller(ax, 0.52, 0.32, "assign_suscripcion()", "saas_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Plan", "db / plan (límites)")
    draw_entity(ax, 0.86, 0.60, "Empresa", "db / empresa (estado)")
    draw_entity(ax, 0.86, 0.38, "Suscripcion", "db / suscripcion (activa)")
    draw_entity(ax, 0.86, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    draw_call_arrow(ax, 0.35, 0.68, 0.435, 0.68, "GET /api/v1/saas/planes", offset_y=0.025)
    draw_call_arrow(ax, 0.35, 0.32, 0.435, 0.32, "PUT /api/v1/saas/empresas/{id}/suscripcion\n(plan_id, meses)", offset_y=-0.035)
    
    # list_planes -> Plan
    draw_crud_arrow(ax, 0.60, 0.70, 0.79, 0.80, "GET", "consultar planes disponibles", rad=0.0, offset_y=0.02)
    
    # assign_suscripcion -> Entities
    draw_crud_arrow(ax, 0.60, 0.38, 0.79, 0.60, "PATCH", "activar empresa ('activa')", rad=-0.06, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.32, 0.79, 0.38, "POST", "crear suscripción vigente", rad=0.03, offset_y=-0.02)
    draw_crud_arrow(ax, 0.60, 0.26, 0.79, 0.18, "POST", "auditar asignación de plan", rad=0.08, offset_y=-0.03)
    
    save_and_close(fig, out_dir, "cu07_asignar_plan")

# =========================================================================
# CU-08: CONSULTAR PLAN Y LÍMITES DE SUSCRIPCIÓN
# Boundaries: MiSuscripcionComponent (Estado plan y límites de sucursales e IA)
# =========================================================================
def generate_cu08(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-08: CONSULTAR PLAN Y LÍMITES DE SUSCRIPCIÓN",
        "Actor: Administrador de Empresa | Boundary: MiSuscripcionComponent | Controllers: get_mi_suscripcion(), list_sucursales() | Entities: Suscripcion, Plan, PlanLimite, Sucursal"
    )
    draw_actor(ax, 0.08, 0.50, "Admin Empresa", "Tenant Manager")
    draw_boundary(ax, 0.26, 0.50, "MiSuscripcionUI", "mi-suscripcion.component.html")
    
    draw_controller(ax, 0.50, 0.68, "get_mi_suscripcion()", "suscripciones.py")
    draw_controller(ax, 0.50, 0.35, "list_sucursales()", "sucursales.py")
    
    draw_entity(ax, 0.86, 0.80, "Suscripcion", "db / suscripcion (vigencia)")
    draw_entity(ax, 0.86, 0.60, "Plan", "db / plan")
    draw_entity(ax, 0.86, 0.38, "PlanLimite", "db / plan_limite (BR-02/03)")
    draw_entity(ax, 0.86, 0.18, "Sucursal", "db / sucursal (activas)")
    
    draw_actor_link(ax, 0.14, 0.50, 0.18, 0.50)
    
    draw_call_arrow(ax, 0.34, 0.54, 0.42, 0.68, "GET /api/v1/suscripcion\n(token tenant)", offset_y=0.03)
    draw_call_arrow(ax, 0.34, 0.46, 0.42, 0.35, "GET /api/v1/sucursales\n(conteo sucursales)", offset_y=-0.04)
    
    draw_crud_arrow(ax, 0.58, 0.72, 0.79, 0.80, "GET", "consultar suscripción actual", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.58, 0.66, 0.79, 0.60, "GET", "datos y características de plan", rad=-0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.58, 0.62, 0.79, 0.38, "GET", "límites de sucursales / IA", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.58, 0.35, 0.79, 0.18, "GET", "contar sucursales activas (BR-02)", rad=0.04, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu08_consultar_plan_limites")

# =========================================================================
# CU-09: PANEL DE ADMINISTRACIÓN SAAS (SUPERVISIÓN Y SUSPENSIÓN GLOBAL)
# Boundaries: SaasDashboardComponent (Métricas globales) y EmpresaDetailComponent (Ficha y acciones de suspensión/reactivación)
# =========================================================================
def generate_cu09(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-09: PANEL DE ADMINISTRACIÓN SAAS (SUPERVISIÓN Y SUSPENSIÓN)",
        "Actor: Superadministrador SaaS | Boundaries: SaasDashboardComponent, EmpresaDetailComponent | Controllers: get_metricas(), suspend_empresa(), reactivate_empresa() | Entities: Empresa, Suscripcion, Sesion, BitacoraAuditoria"
    )
    draw_actor(ax, 0.08, 0.50, "Superadmin", "Superadministrador")
    
    draw_boundary(ax, 0.27, 0.70, "SaasDashboardUI", "saas/panel.component.html")
    draw_boundary(ax, 0.27, 0.34, "EmpresaDetailUI", "empresa-detail.component.html")
    
    draw_controller(ax, 0.52, 0.75, "get_metricas()", "saas_service.py")
    draw_controller(ax, 0.52, 0.48, "suspend_empresa()", "saas_service.py")
    draw_controller(ax, 0.52, 0.24, "reactivate_empresa()", "saas_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Empresa", "db / empresa (estado)")
    draw_entity(ax, 0.86, 0.60, "Suscripcion", "db / suscripcion (métricas)")
    draw_entity(ax, 0.86, 0.40, "Sesion", "db / sesion (revocar tokens)")
    draw_entity(ax, 0.86, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.70)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.34)
    
    draw_call_arrow(ax, 0.35, 0.72, 0.435, 0.75, "GET /api/v1/saas/metricas", offset_y=0.025)
    draw_call_arrow(ax, 0.35, 0.40, 0.435, 0.48, "POST /api/v1/saas/empresas/{id}/suspender", offset_y=0.02)
    draw_call_arrow(ax, 0.35, 0.30, 0.435, 0.24, "POST /api/v1/saas/empresas/{id}/reactivar", offset_y=-0.03)
    
    # get_metricas
    draw_crud_arrow(ax, 0.60, 0.77, 0.79, 0.80, "GET", "conteo global tenants", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.73, 0.79, 0.60, "GET", "suscripciones por vencer", rad=-0.02, offset_y=0.02)
    
    # suspend_empresa
    draw_crud_arrow(ax, 0.60, 0.52, 0.79, 0.78, "PATCH", "marcar estado 'suspendida'", rad=-0.06, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.48, 0.79, 0.40, "DELETE", "revocar sesiones activas tenant", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.44, 0.79, 0.22, "POST", "auditar suspensión", rad=0.06, offset_y=-0.02)
    
    # reactivate_empresa
    draw_crud_arrow(ax, 0.60, 0.26, 0.79, 0.76, "PATCH", "restablecer estado 'activa'", rad=-0.10, offset_y=0.03)
    draw_crud_arrow(ax, 0.60, 0.22, 0.79, 0.16, "POST", "auditar reactivación", rad=0.03, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu09_panel_saas_supervision")

# =========================================================================
# CU-10: ADMINISTRAR USUARIOS Y ROLES POR EMPRESA
# Boundaries: EmpleadosListComponent (Listado y roles) y EmpleadoFormModal (Alta de empleado)
# =========================================================================
def generate_cu10(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-10: ADMINISTRAR USUARIOS Y ROLES POR EMPRESA",
        "Actor: Administrador de Empresa | Boundaries: EmpleadosListComponent, EmpleadoFormModal | Controllers: list_roles(), list_empleados(), create_empleado(), delete_empleado() | Entities: Usuario, Rol, Sucursal, BitacoraAuditoria"
    )
    draw_actor(ax, 0.08, 0.50, "Admin Empresa", "Tenant Manager")
    
    draw_boundary(ax, 0.27, 0.68, "EmpleadosListUI", "empleados-list.component.html")
    draw_boundary(ax, 0.27, 0.32, "EmpleadoFormModal", "empleado-form-modal.html")
    
    draw_controller(ax, 0.52, 0.78, "list_roles()", "empleados.py")
    draw_controller(ax, 0.52, 0.56, "list_empleados()", "empleado_service.py")
    draw_controller(ax, 0.52, 0.36, "create_empleado()", "empleado_service.py")
    draw_controller(ax, 0.52, 0.18, "delete_empleado()", "empleado_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Rol", "db / rol (cajero/encargado)")
    draw_entity(ax, 0.86, 0.60, "Usuario", "db / usuario (empleados)")
    draw_entity(ax, 0.86, 0.38, "Sucursal", "db / sucursal (asignación)")
    draw_entity(ax, 0.86, 0.16, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # From EmpleadosListUI
    draw_call_arrow(ax, 0.35, 0.74, 0.435, 0.78, "GET /api/v1/empleados/roles", offset_y=0.02)
    draw_call_arrow(ax, 0.35, 0.64, 0.435, 0.56, "GET /api/v1/empleados", offset_y=0.02)
    draw_call_arrow(ax, 0.35, 0.58, 0.435, 0.18, "DELETE /api/v1/empleados/{id}", offset_y=-0.04)
    
    # From EmpleadoFormModal
    draw_call_arrow(ax, 0.35, 0.32, 0.435, 0.36, "POST /api/v1/empleados\n(datos, rol_id, sucursal_id)", offset_y=-0.035)
    
    # list_roles -> Rol
    draw_crud_arrow(ax, 0.60, 0.78, 0.79, 0.80, "GET", "listar roles del tenant", rad=0.0, offset_y=0.02)
    
    # list_empleados -> Usuario
    draw_crud_arrow(ax, 0.60, 0.56, 0.79, 0.60, "GET", "filtrar empleados por empresa_id", rad=0.0, offset_y=0.02)
    
    # create_empleado -> Entities
    draw_crud_arrow(ax, 0.60, 0.40, 0.79, 0.62, "POST", "crear usuario con hash clave", rad=-0.06, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.36, 0.79, 0.38, "GET", "validar sucursal de tenant", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.32, 0.79, 0.18, "POST", "auditar alta empleado", rad=0.06, offset_y=-0.02)
    
    # delete_empleado -> Entities
    draw_crud_arrow(ax, 0.60, 0.20, 0.79, 0.56, "PATCH", "baja lógica (deleted_at)", rad=-0.08, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.16, 0.79, 0.14, "POST", "auditar baja empleado", rad=0.02, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu10_administrar_usuarios_roles")

# =========================================================================
# CU-11: ADMINISTRAR SUCURSALES (LÍMITES BR-02)
# Boundaries: SucursalesListComponent (Listado y estado de cupos) y SucursalFormModal (Alta de sucursal)
# =========================================================================
def generate_cu11(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-11: ADMINISTRAR SUCURSALES (LÍMITES BR-02)",
        "Actor: Administrador de Empresa | Boundaries: SucursalesListComponent, SucursalFormModal | Controllers: list_sucursales(), get_limite_sucursales(), create_sucursal() | Entities: Sucursal, Ciudad, Suscripcion, PlanLimite"
    )
    draw_actor(ax, 0.08, 0.50, "Admin Empresa", "Tenant Manager")
    
    draw_boundary(ax, 0.27, 0.68, "SucursalesListUI", "sucursales-list.component.html")
    draw_boundary(ax, 0.27, 0.32, "SucursalFormModal", "sucursal-form-modal.html")
    
    draw_controller(ax, 0.52, 0.72, "list_sucursales()", "sucursal_service.py")
    draw_controller(ax, 0.52, 0.50, "get_limite_sucursales()", "sucursal_service.py")
    draw_controller(ax, 0.52, 0.26, "create_sucursal()", "sucursal_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Sucursal", "db / sucursal (tenant)")
    draw_entity(ax, 0.86, 0.60, "Ciudad", "db / ciudad (catálogo)")
    draw_entity(ax, 0.86, 0.40, "Suscripcion", "db / suscripcion (activa)")
    draw_entity(ax, 0.86, 0.18, "PlanLimite", "db / plan_limite (BR-02: máx 2/10)")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # From SucursalesListUI
    draw_call_arrow(ax, 0.35, 0.72, 0.435, 0.72, "GET /api/v1/sucursales", offset_y=0.025)
    draw_call_arrow(ax, 0.35, 0.60, 0.435, 0.50, "verificarCupoDisponible()", offset_y=0.02)
    
    # From SucursalFormModal
    draw_call_arrow(ax, 0.35, 0.32, 0.435, 0.26, "POST /api/v1/sucursales\n(nombre, ciudad_id, dir)", offset_y=-0.035)
    
    # list_sucursales -> Sucursal
    draw_crud_arrow(ax, 0.60, 0.72, 0.79, 0.80, "GET", "listar sucursales de la empresa", rad=0.0, offset_y=0.02)
    
    # get_limite_sucursales -> Suscripcion & PlanLimite
    draw_crud_arrow(ax, 0.60, 0.52, 0.79, 0.42, "GET", "verificar suscripción activa", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.48, 0.79, 0.20, "GET", "consultar límite según plan (BR-02)", rad=0.04, offset_y=-0.02)
    
    # create_sucursal -> Sucursal & Ciudad
    draw_crud_arrow(ax, 0.60, 0.30, 0.79, 0.76, "POST", "insertar nueva tienda sucursal", rad=-0.10, offset_y=0.03)
    draw_crud_arrow(ax, 0.60, 0.24, 0.79, 0.60, "GET", "validar existencia de ciudad", rad=-0.06, offset_y=0.02)
    
    save_and_close(fig, out_dir, "cu11_administrar_sucursales")

# =========================================================================
# CU-12: ADMINISTRAR CATÁLOGO DE PRODUCTOS (CRUD PRENDAS, VARIANTES SKU)
# Boundaries: PrendaCatalogAdminUI (Grilla prendas) y PrendaVarianteModal (Formulario prenda y variantes)
# =========================================================================
def generate_cu12(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-12: ADMINISTRAR CATÁLOGO DE PRODUCTOS (PRENDAS Y VARIANTES SKU)",
        "Actor: Administrador de Empresa | Boundaries: PrendaCatalogAdminUI, PrendaVarianteModal | Controllers: get_auxiliares(), create_prenda(), add_variante_to_prenda() | Entities: Prenda, Categoria, Variante, PrecioHistorial, BitacoraAuditoria"
    )
    draw_actor(ax, 0.08, 0.50, "Admin Empresa", "Tenant Manager")
    
    draw_boundary(ax, 0.27, 0.68, "PrendaAdminListUI", "prendas-admin.component.html")
    draw_boundary(ax, 0.27, 0.32, "PrendaVarianteModal", "prenda-variante-modal.html")
    
    draw_controller(ax, 0.52, 0.74, "get_auxiliares()", "catalogo.py")
    draw_controller(ax, 0.52, 0.50, "create_prenda()", "catalogo_service.py")
    draw_controller(ax, 0.52, 0.26, "add_variante()", "catalogo_service.py")
    
    draw_entity(ax, 0.86, 0.82, "Prenda", "db / prenda")
    draw_entity(ax, 0.86, 0.66, "Categoria", "db / categoria")
    draw_entity(ax, 0.86, 0.50, "Variante", "db / variante (SKU)")
    draw_entity(ax, 0.86, 0.34, "PrecioHistorial", "db / precio_historial")
    draw_entity(ax, 0.86, 0.16, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # From PrendaAdminListUI
    draw_call_arrow(ax, 0.35, 0.72, 0.435, 0.74, "GET /api/v1/catalogo/auxiliares", offset_y=0.025)
    
    # From PrendaVarianteModal
    draw_call_arrow(ax, 0.35, 0.42, 0.435, 0.50, "POST /api/v1/catalogo/admin/prendas", offset_y=0.02)
    draw_call_arrow(ax, 0.35, 0.28, 0.435, 0.26, "POST /admin/prendas/{id}/variantes", offset_y=-0.035)
    
    # get_auxiliares
    draw_crud_arrow(ax, 0.60, 0.74, 0.79, 0.66, "GET", "categorías, tallas y colores", rad=-0.02, offset_y=0.02)
    
    # create_prenda
    draw_crud_arrow(ax, 0.60, 0.54, 0.79, 0.82, "POST", "crear prenda base tenant", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.60, 0.50, 0.79, 0.34, "POST", "registrar precio base inicial", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.60, 0.46, 0.79, 0.18, "POST", "auditar alta prenda", rad=0.08, offset_y=-0.03)
    
    # add_variante
    draw_crud_arrow(ax, 0.60, 0.28, 0.79, 0.50, "POST", "insertar variante con SKU único", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.24, 0.79, 0.14, "POST", "auditar alta variante", rad=0.04, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu12_administrar_catalogo_prendas")

# =========================================================================
# CU-13: CONSULTAR CATÁLOGO DE PRENDAS (ALERTA DESACTUALIZADO)
# Boundaries: CatalogoWebUI (Navegador) y CatalogoFlutterUI (App móvil con soporte offline)
# =========================================================================
def generate_cu13(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-13: CONSULTAR CATÁLOGO DE PRENDAS (ALERTA DESACTUALIZADO)",
        "Actor: Cliente | Boundaries: CatalogoWebUI, CatalogoFlutterUI | Controllers: get_catalog_version(), list_prendas() | Entities: Prenda, Variante, Categoria, CatalogoCacheLocal"
    )
    draw_actor(ax, 0.08, 0.50, "Cliente", "Visitante Web / App")
    
    draw_boundary(ax, 0.27, 0.68, "CatalogoWebUI", "catalogo-cliente.component.ts")
    draw_boundary(ax, 0.27, 0.32, "CatalogoFlutterUI", "mobile/catalogo_screen.dart")
    
    draw_controller(ax, 0.52, 0.68, "get_catalog_version()", "catalogo_service.py")
    draw_controller(ax, 0.52, 0.35, "list_prendas()", "catalogo_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Prenda", "db / prenda (activas)")
    draw_entity(ax, 0.86, 0.60, "Variante", "db / variante (talla, color)")
    draw_entity(ax, 0.86, 0.40, "Categoria", "db / categoria")
    draw_entity(ax, 0.86, 0.18, "CatalogoCacheLocal", "local / SQLite / IndexedDB")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # From CatalogoFlutterUI (Offline checking)
    draw_call_arrow(ax, 0.35, 0.42, 0.435, 0.68, "checkVersionOffline()\n(comparar versión cache)", offset_y=0.03)
    
    # From Both -> list_prendas
    draw_call_arrow(ax, 0.35, 0.64, 0.435, 0.38, "GET /api/v1/catalogo/prendas\n(consultar catálogo)", offset_y=0.02)
    draw_call_arrow(ax, 0.35, 0.28, 0.435, 0.32, "leerCacheLocalSiOffline()", offset_y=-0.035)
    
    # get_catalog_version
    draw_crud_arrow(ax, 0.60, 0.70, 0.79, 0.22, "GET", "comparar version_catalogo con cache", rad=0.09, offset_y=-0.03)
    
    # list_prendas
    draw_crud_arrow(ax, 0.60, 0.40, 0.79, 0.80, "GET", "consultar prendas activas tenant", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.60, 0.36, 0.79, 0.60, "GET", "obtener variantes y precios", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.32, 0.79, 0.40, "GET", "árbol de categorías", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.60, 0.28, 0.79, 0.16, "PUT", "actualizar cache local / stale banner", rad=0.06, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu13_consultar_catalogo_prendas")

# =========================================================================
# CU-14: FILTRAR PRODUCTOS MULTIDIMENSIONAL
# Boundaries: FilterSidebarComponent (Filtros laterales) y ProductGridComponent (Grilla de resultados)
# =========================================================================
def generate_cu14(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-14: FILTRAR PRODUCTOS MULTIDIMENSIONAL",
        "Actor: Cliente | Boundaries: FilterSidebarComponent, ProductGridComponent | Controllers: get_auxiliares(), list_prendas(filtros) | Entities: Prenda, Variante, Color/Talla, Categoria, PrecioHistorial"
    )
    draw_actor(ax, 0.08, 0.50, "Cliente", "Comprador")
    
    draw_boundary(ax, 0.27, 0.68, "FilterSidebarUI", "catalog-filters.html")
    draw_boundary(ax, 0.27, 0.32, "ProductGridUI", "product-grid.component.html")
    
    draw_controller(ax, 0.52, 0.68, "get_auxiliares()", "catalogo.py")
    draw_controller(ax, 0.52, 0.35, "list_prendas(filtros)", "catalogo_service.py")
    
    draw_entity(ax, 0.86, 0.82, "Prenda", "db / prenda")
    draw_entity(ax, 0.86, 0.66, "Variante", "db / variante (SKU)")
    draw_entity(ax, 0.86, 0.50, "Color / Talla", "db / color, talla (catálogos)")
    draw_entity(ax, 0.86, 0.34, "Categoria", "db / categoria")
    draw_entity(ax, 0.86, 0.16, "PrecioHistorial", "db / precio_historial")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # From FilterSidebarUI
    draw_call_arrow(ax, 0.35, 0.68, 0.435, 0.68, "GET /api/v1/catalogo/auxiliares\n(opciones de filtros)", offset_y=0.03)
    
    # From ProductGridUI / Sidebar
    draw_call_arrow(ax, 0.35, 0.35, 0.435, 0.35, "GET /api/v1/catalogo/prendas\n(color, talla, precio_min/max)", offset_y=-0.035)
    
    # get_auxiliares
    draw_crud_arrow(ax, 0.60, 0.70, 0.79, 0.50, "GET", "catálogos de colores y tallas", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.66, 0.79, 0.34, "GET", "categorías de la empresa", rad=-0.02, offset_y=0.02)
    
    # list_prendas(filtros)
    draw_crud_arrow(ax, 0.60, 0.40, 0.79, 0.82, "GET", "filtrar prendas disponibles", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.60, 0.36, 0.79, 0.66, "GET", "matchear variantes coincidentes", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.32, 0.79, 0.16, "GET", "validar rango de precios", rad=0.04, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu14_filtrar_productos")

# =========================================================================
# CU-15: ADMINISTRAR PROVEEDORES TEXTILES
# Boundaries: ProveedoresListComponent (Lista) y ProveedorFormModal (Alta/Edición)
# =========================================================================
def generate_cu15(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-15: ADMINISTRAR PROVEEDORES TEXTILES",
        "Actor: Administrador de Empresa | Boundaries: ProveedoresListComponent, ProveedorFormModal | Controllers: list_proveedores(), create_proveedor(), delete_proveedor() | Entities: Proveedor, Prenda, BitacoraAuditoria"
    )
    draw_actor(ax, 0.08, 0.50, "Admin Empresa", "Tenant Manager")
    
    draw_boundary(ax, 0.27, 0.68, "ProveedoresListUI", "proveedores-list.html")
    draw_boundary(ax, 0.27, 0.32, "ProveedorFormModal", "proveedor-form-modal.html")
    
    draw_controller(ax, 0.52, 0.74, "list_proveedores()", "proveedor_service.py")
    draw_controller(ax, 0.52, 0.50, "create_proveedor()", "proveedor_service.py")
    draw_controller(ax, 0.52, 0.26, "delete_proveedor()", "proveedor_service.py")
    
    draw_entity(ax, 0.86, 0.75, "Proveedor", "db / proveedor (tenant)")
    draw_entity(ax, 0.86, 0.48, "Prenda", "db / prenda (asociaciones)")
    draw_entity(ax, 0.86, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # From ProveedoresListUI
    draw_call_arrow(ax, 0.35, 0.72, 0.435, 0.74, "GET /api/v1/proveedores", offset_y=0.025)
    draw_call_arrow(ax, 0.35, 0.58, 0.435, 0.26, "DELETE /api/v1/proveedores/{id}", offset_y=-0.04)
    
    # From ProveedorFormModal
    draw_call_arrow(ax, 0.35, 0.36, 0.435, 0.50, "POST /api/v1/proveedores\n(nit, nombre, contacto)", offset_y=0.02)
    
    # list_proveedores
    draw_crud_arrow(ax, 0.60, 0.74, 0.79, 0.75, "GET", "listar proveedores de empresa", rad=0.0, offset_y=0.02)
    
    # create_proveedor
    draw_crud_arrow(ax, 0.60, 0.52, 0.79, 0.73, "POST", "validar NIT e insertar proveedor", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.48, 0.79, 0.22, "POST", "auditar alta proveedor", rad=0.06, offset_y=-0.02)
    
    # delete_proveedor
    draw_crud_arrow(ax, 0.60, 0.28, 0.79, 0.48, "GET", "verificar prendas asociadas", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.24, 0.79, 0.71, "PATCH", "baja lógica (deleted_at)", rad=-0.09, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.20, 0.79, 0.18, "POST", "auditar baja de proveedor", rad=0.02, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu15_administrar_proveedores")

# =========================================================================
# CU-16: ADMINISTRAR TEMPORADAS Y COLECCIONES COMERCIALES
# Boundaries: TemporadaViewComponent (Gestión temporadas) y ColeccionModal (Gestión colecciones)
# =========================================================================
def generate_cu16(out_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-16: ADMINISTRAR TEMPORADAS Y COLECCIONES COMERCIALES",
        "Actor: Administrador de Empresa | Boundaries: TemporadaViewComponent, ColeccionModal | Controllers: list_temporadas(), create_temporada(), create_coleccion() | Entities: Temporada, Coleccion, Prenda, BitacoraAuditoria"
    )
    draw_actor(ax, 0.08, 0.50, "Admin Empresa", "Tenant Manager")
    
    draw_boundary(ax, 0.27, 0.68, "TemporadaViewUI", "temporadas.component.html")
    draw_boundary(ax, 0.27, 0.32, "ColeccionModal", "coleccion-modal.html")
    
    draw_controller(ax, 0.52, 0.74, "list_temporadas()", "coleccion_service.py")
    draw_controller(ax, 0.52, 0.50, "create_temporada()", "coleccion_service.py")
    draw_controller(ax, 0.52, 0.26, "create_coleccion()", "coleccion_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Temporada", "db / temporada (fechas)")
    draw_entity(ax, 0.86, 0.60, "Coleccion", "db / coleccion")
    draw_entity(ax, 0.86, 0.40, "Prenda", "db / prenda")
    draw_entity(ax, 0.86, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.138, 0.53, 0.192, 0.68)
    draw_actor_link(ax, 0.138, 0.47, 0.192, 0.32)
    
    # From TemporadaViewUI
    draw_call_arrow(ax, 0.35, 0.72, 0.435, 0.74, "GET /api/v1/colecciones/temporadas", offset_y=0.025)
    draw_call_arrow(ax, 0.35, 0.56, 0.435, 0.50, "POST /api/v1/colecciones/temporadas", offset_y=0.02)
    
    # From ColeccionModal
    draw_call_arrow(ax, 0.35, 0.32, 0.435, 0.26, "POST /api/v1/colecciones/colecciones", offset_y=-0.035)
    
    # list_temporadas
    draw_crud_arrow(ax, 0.60, 0.74, 0.79, 0.80, "GET", "listar temporadas de empresa", rad=0.0, offset_y=0.02)
    
    # create_temporada
    draw_crud_arrow(ax, 0.60, 0.52, 0.79, 0.78, "POST", "validar fechas e insertar temporada", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.48, 0.79, 0.20, "POST", "auditar alta temporada", rad=0.06, offset_y=-0.02)
    
    # create_coleccion
    draw_crud_arrow(ax, 0.60, 0.28, 0.79, 0.60, "POST", "crear colección vinculada a temporada", rad=-0.06, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.24, 0.79, 0.40, "PATCH", "vincular prendas a colección", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.60, 0.20, 0.79, 0.16, "POST", "auditar alta colección", rad=0.03, offset_y=-0.02)
    
    save_and_close(fig, out_dir, "cu16_administrar_temporadas_colecciones")


if __name__ == '__main__':
    out_dir = os.path.join(os.getcwd(), 'Segundo-parcial', 'docs', 'diagramas')
    os.makedirs(out_dir, exist_ok=True)
    generate_cu06(out_dir)
    generate_cu07(out_dir)
    generate_cu08(out_dir)
    generate_cu09(out_dir)
    generate_cu10(out_dir)
    generate_cu11(out_dir)
    generate_cu12(out_dir)
    generate_cu13(out_dir)
    generate_cu14(out_dir)
    generate_cu15(out_dir)
    generate_cu16(out_dir)
    print("Multi-boundary and multi-controller robustness diagrams CU-06 to CU-16 updated successfully!")
