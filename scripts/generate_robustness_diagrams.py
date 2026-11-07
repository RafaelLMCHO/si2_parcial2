import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Color palette (Modern Soft UI)
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
    'label_edge': '#CBD5E1',
}

def setup_canvas(title, subtitle, width=15, height=9):
    fig, ax = plt.subplots(figsize=(width, height), dpi=300)
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Header
    ax.text(0.5, 0.96, title, fontsize=16, fontweight='bold', ha='center', va='top', color=COLORS['text'])
    ax.text(0.5, 0.925, subtitle, fontsize=10.5, ha='center', va='top', color=COLORS['subtext'])
    
    # Legend
    legend_items = [
        ('Actor (Línea simple)', COLORS['actor_fill'], COLORS['actor_edge']),
        ('Boundary (Vista)', COLORS['boundary_fill'], COLORS['boundary_edge']),
        ('Controller (Función)', COLORS['controller_fill'], COLORS['controller_edge']),
        ('Entity (Modelo BD)', COLORS['entity_fill'], COLORS['entity_edge']),
    ]
    x_leg = 0.12
    for label, fill, edge in legend_items:
        patch = patches.FancyBboxPatch(
            (x_leg, 0.03), 0.16, 0.035,
            boxstyle="round,pad=0.01,rounding_size=0.015",
            facecolor=fill, edgecolor=edge, linewidth=1.5
        )
        ax.add_patch(patch)
        ax.text(x_leg + 0.08, 0.0475, label, fontsize=8.5, ha='center', va='center', fontweight='bold', color=COLORS['text'])
        x_leg += 0.20
        
    return fig, ax

def draw_actor(ax, x, y, name, sub=""):
    w, h = 0.12, 0.08
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=COLORS['actor_fill'], edgecolor=COLORS['actor_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.018, "[ACTOR]", fontsize=9, fontweight='bold', ha='center', va='center', color=COLORS['actor_edge'], zorder=4)
    ax.text(x, y - 0.005, name, fontsize=10, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.025, sub, fontsize=8, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_boundary(ax, x, y, name, sub=""):
    w, h = 0.15, 0.085
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=COLORS['boundary_fill'], edgecolor=COLORS['boundary_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.022, "«boundary»", fontsize=9, fontweight='bold', ha='center', va='center', color=COLORS['boundary_edge'], zorder=4)
    ax.text(x, y + 0.002, name, fontsize=9.5, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.022, sub, fontsize=8, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_controller(ax, x, y, name, sub=""):
    w, h = 0.15, 0.085
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor=COLORS['controller_fill'], edgecolor=COLORS['controller_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.022, "«control»", fontsize=9, fontweight='bold', ha='center', va='center', color=COLORS['controller_edge'], zorder=4)
    ax.text(x, y + 0.002, name, fontsize=9.5, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.022, sub, fontsize=8, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_entity(ax, x, y, name, sub=""):
    w, h = 0.13, 0.075
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor=COLORS['entity_fill'], edgecolor=COLORS['entity_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.018, "«entity»", fontsize=8.5, fontweight='bold', ha='center', va='center', color=COLORS['entity_edge'], zorder=4)
    ax.text(x, y - 0.002, name, fontsize=9.5, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.022, sub, fontsize=7.5, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_actor_link(ax, x1, y1, x2, y2):
    """Solid connection with NO label between Actor and Boundary."""
    ax.plot([x1, x2], [y1, y2], color='#64748B', linewidth=2.0, linestyle='-', zorder=2)

def draw_call_arrow(ax, x1, y1, x2, y2, label, offset_y=0.025, rad=0.0):
    """Arrow from Boundary to Controller with label."""
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.35,head_length=0.45",
            color=COLORS['arrow_call'],
            lw=1.8,
            connectionstyle=connectionstyle
        ),
        zorder=2
    )
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + offset_y
    ax.text(
        mx, my, label, fontsize=8.2, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.25", fc=COLORS['label_bg'], ec=COLORS['boundary_edge'], lw=1, alpha=0.95),
        color=COLORS['arrow_call'], fontweight='bold', zorder=5
    )

def draw_crud_arrow(ax, x1, y1, x2, y2, crud_verb, detail="", rad=0.0, offset_y=0.02, offset_x=0.0):
    """Arrow from Controller to Entity with CRUD label (GET, POST, PUT, DELETE)."""
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.35,head_length=0.45",
            color=COLORS['arrow_crud'],
            lw=1.8,
            connectionstyle=connectionstyle
        ),
        zorder=2
    )
    mx = (x1 + x2) / 2 + offset_x
    my = (y1 + y2) / 2 + offset_y
    label = f"{crud_verb}: {detail}" if detail else crud_verb
    ax.text(
        mx, my, label, fontsize=7.8, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.22", fc=COLORS['label_bg'], ec=COLORS['entity_edge'], lw=1, alpha=0.95),
        color=COLORS['arrow_crud'], fontweight='bold', zorder=5
    )


# -------------------------------------------------------------
# CU-01
# -------------------------------------------------------------
def generate_cu01(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-01: INICIAR SESIÓN (LOGIN)",
        "Boundary: LoginComponent | Controller: login() | Entities: Empresa, Suscripcion, Rol, Usuario, Sesion, BitacoraAuditoria"
    )
    
    # Positions
    draw_actor(ax, 0.10, 0.50, "Usuario", "Admin / Cliente")
    draw_boundary(ax, 0.30, 0.50, "LoginComponent", "login.component.html")
    draw_controller(ax, 0.55, 0.50, "login()", "auth_service.py")
    
    # Entities
    draw_entity(ax, 0.88, 0.84, "Empresa", "db / empresa")
    draw_entity(ax, 0.88, 0.70, "Suscripcion", "db / suscripcion")
    draw_entity(ax, 0.88, 0.56, "Rol", "db / rol")
    draw_entity(ax, 0.88, 0.42, "Usuario", "db / usuario")
    draw_entity(ax, 0.88, 0.28, "Sesion", "db / sesion")
    draw_entity(ax, 0.88, 0.14, "BitacoraAuditoria", "db / bitacora")
    
    # Actor -> Boundary (No label)
    draw_actor_link(ax, 0.16, 0.50, 0.225, 0.50)
    
    # Boundary -> Controller
    draw_call_arrow(ax, 0.375, 0.50, 0.475, 0.50, "POST /api/v1/auth/login\n(credenciales)")
    
    # Controller -> Entities (CRUD)
    draw_crud_arrow(ax, 0.625, 0.53, 0.815, 0.84, "GET", "buscar empresa activa", rad=-0.08, offset_y=0.03)
    draw_crud_arrow(ax, 0.625, 0.52, 0.815, 0.70, "GET", "verificar vigencia suscripción", rad=-0.04, offset_y=0.025)
    draw_crud_arrow(ax, 0.625, 0.51, 0.815, 0.56, "GET", "consultar rol y permisos", rad=-0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.625, 0.49, 0.815, 0.44, "GET", "validar clave y verificación", rad=0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.625, 0.47, 0.815, 0.40, "PATCH", "actualizar ultimo_acceso", rad=0.06, offset_y=-0.025)
    draw_crud_arrow(ax, 0.625, 0.46, 0.815, 0.28, "POST", "crear sesión (refresh_token)", rad=0.08, offset_y=-0.025)
    draw_crud_arrow(ax, 0.625, 0.44, 0.815, 0.14, "POST", "registrar evento auditoría", rad=0.12, offset_y=-0.03)
    
    png_path = os.path.join(output_dir, "cu01_iniciar_sesion.png")
    svg_path = os.path.join(output_dir, "cu01_iniciar_sesion.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-02
# -------------------------------------------------------------
def generate_cu02(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-02: REGISTRARSE Y VERIFICAR CORREO",
        "Boundaries: RegisterComponent, VerifyEmailComponent | Controllers: register(), verify_email() | Entities: Empresa, Rol, Usuario, VerificacionCorreo, BitacoraAuditoria"
    )
    
    # Actor
    draw_actor(ax, 0.09, 0.50, "Cliente", "Visitante")
    
    # Boundaries
    draw_boundary(ax, 0.28, 0.68, "RegisterComponent", "register.component.html")
    draw_boundary(ax, 0.28, 0.32, "VerifyEmailComponent", "verify-email.component.html")
    
    # Controllers
    draw_controller(ax, 0.52, 0.68, "register()", "auth_service.py")
    draw_controller(ax, 0.52, 0.32, "verify_email()", "auth_service.py")
    
    # Entities
    draw_entity(ax, 0.86, 0.82, "Empresa", "db / empresa")
    draw_entity(ax, 0.86, 0.66, "Rol", "db / rol ('cliente')")
    draw_entity(ax, 0.86, 0.50, "Usuario", "db / usuario")
    draw_entity(ax, 0.86, 0.34, "VerificacionCorreo", "db / verificacion_correo")
    draw_entity(ax, 0.86, 0.18, "BitacoraAuditoria", "db / bitacora")
    
    # Actor -> Boundaries (No label)
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    # Boundaries -> Controllers
    draw_call_arrow(ax, 0.355, 0.68, 0.445, 0.68, "POST /api/v1/auth/register\n(datos cliente)")
    draw_call_arrow(ax, 0.355, 0.32, 0.445, 0.32, "POST /api/v1/auth/verify-email\n(token, slug)")
    
    # register() -> Entities
    draw_crud_arrow(ax, 0.595, 0.72, 0.795, 0.82, "GET", "verificar empresa slug", rad=-0.04, offset_y=0.025)
    draw_crud_arrow(ax, 0.595, 0.70, 0.795, 0.68, "GET", "obtener rol 'cliente'", rad=-0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.595, 0.67, 0.795, 0.54, "GET", "verificar no duplicidad correo", rad=-0.02, offset_y=0.025)
    draw_crud_arrow(ax, 0.595, 0.65, 0.795, 0.49, "POST", "crear usuario inactivo", rad=0.05, offset_y=-0.02)
    draw_crud_arrow(ax, 0.595, 0.63, 0.795, 0.37, "POST", "crear token verificación", rad=0.09, offset_y=-0.025)
    draw_crud_arrow(ax, 0.595, 0.61, 0.795, 0.22, "POST", "auditar registro", rad=0.14, offset_y=-0.03)
    
    # verify_email() -> Entities
    draw_crud_arrow(ax, 0.595, 0.34, 0.795, 0.34, "GET", "validar token y expiración", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.595, 0.36, 0.795, 0.46, "PATCH", "activar (email_verificado=true)", rad=-0.06, offset_y=0.025)
    draw_crud_arrow(ax, 0.595, 0.31, 0.795, 0.31, "DELETE", "invalidar token consumido", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.595, 0.29, 0.795, 0.17, "POST", "auditar verificación", rad=0.06, offset_y=-0.025)
    
    png_path = os.path.join(output_dir, "cu02_registrarse.png")
    svg_path = os.path.join(output_dir, "cu02_registrarse.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-03
# -------------------------------------------------------------
def generate_cu03(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-03: GESTIONAR PERFIL Y CAMBIO DE CONTRASEÑA",
        "Boundary: ProfileComponent | Controllers: get_me(), update_me(), change_password() | Entities: Usuario, Sesion, BitacoraAuditoria"
    )
    
    # Actor
    draw_actor(ax, 0.09, 0.50, "Usuario", "Autenticado")
    
    # Boundary
    draw_boundary(ax, 0.27, 0.50, "ProfileComponent", "profile.component.html")
    
    # Controllers
    draw_controller(ax, 0.53, 0.72, "get_me()", "auth_service.py")
    draw_controller(ax, 0.53, 0.50, "update_me()", "auth_service.py")
    draw_controller(ax, 0.53, 0.28, "change_password()", "auth_service.py")
    
    # Entities
    draw_entity(ax, 0.86, 0.70, "Usuario", "db / usuario")
    draw_entity(ax, 0.86, 0.50, "Sesion", "db / sesion")
    draw_entity(ax, 0.86, 0.30, "BitacoraAuditoria", "db / bitacora")
    
    # Actor -> Boundary (No label)
    draw_actor_link(ax, 0.15, 0.50, 0.195, 0.50)
    
    # Boundary -> Controllers
    draw_call_arrow(ax, 0.345, 0.53, 0.455, 0.72, "GET /api/v1/users/me")
    draw_call_arrow(ax, 0.345, 0.50, 0.455, 0.50, "PATCH /api/v1/users/me\n(datos)")
    draw_call_arrow(ax, 0.345, 0.47, 0.455, 0.28, "POST /api/v1/users/me/password\n(claves)")
    
    # get_me() -> Entities
    draw_crud_arrow(ax, 0.605, 0.74, 0.795, 0.74, "GET", "leer datos perfil", rad=0.0, offset_y=0.02)
    
    # update_me() -> Entities
    draw_crud_arrow(ax, 0.605, 0.53, 0.795, 0.68, "PUT / PATCH", "actualizar nombre/teléfono", rad=-0.04, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.48, 0.795, 0.33, "POST", "auditar actualización perfil", rad=0.04, offset_y=-0.025)
    
    # change_password() -> Entities
    draw_crud_arrow(ax, 0.605, 0.32, 0.795, 0.64, "GET", "verificar password_hash actual", rad=-0.08, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.30, 0.795, 0.66, "PATCH", "guardar nuevo password_hash", rad=-0.05, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.28, 0.795, 0.48, "DELETE", "revocar demás sesiones activas", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.25, 0.795, 0.28, "POST", "auditar cambio contraseña", rad=0.0, offset_y=-0.025)
    
    png_path = os.path.join(output_dir, "cu03_gestionar_perfil.png")
    svg_path = os.path.join(output_dir, "cu03_gestionar_perfil.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-04
# -------------------------------------------------------------
def generate_cu04(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-04: CERRAR SESIÓN Y REFRESCO DE TOKENS",
        "Boundaries: Navbar / ProfileComponent, AuthInterceptor | Controllers: logout(), refresh() | Entities: Sesion, Usuario, BitacoraAuditoria"
    )
    
    # Actor
    draw_actor(ax, 0.09, 0.50, "Usuario", "Autenticado")
    
    # Boundaries
    draw_boundary(ax, 0.28, 0.68, "Navbar / Profile", "Acción Logout")
    draw_boundary(ax, 0.28, 0.32, "AuthInterceptor", "auth.interceptor.ts")
    
    # Controllers
    draw_controller(ax, 0.53, 0.68, "logout()", "auth_service.py")
    draw_controller(ax, 0.53, 0.32, "refresh()", "auth_service.py")
    
    # Entities
    draw_entity(ax, 0.86, 0.68, "Sesion", "db / sesion")
    draw_entity(ax, 0.86, 0.48, "Usuario", "db / usuario")
    draw_entity(ax, 0.86, 0.28, "BitacoraAuditoria", "db / bitacora")
    
    # Actor -> Boundaries (No label)
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    # Boundaries -> Controllers
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.68, "POST /api/v1/auth/logout")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.32, "POST /api/v1/auth/refresh\n(refresh_token)")
    
    # logout() -> Entities
    draw_crud_arrow(ax, 0.605, 0.70, 0.795, 0.70, "DELETE", "revocar sesión (revocado_en=now)", rad=0.0, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.66, 0.795, 0.33, "POST", "auditar cierre de sesión", rad=0.06, offset_y=-0.025)
    
    # refresh() -> Entities
    draw_crud_arrow(ax, 0.605, 0.36, 0.795, 0.64, "GET", "validar token activo y vigente", rad=-0.05, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.34, 0.795, 0.66, "PUT / PATCH", "rotar token y expira_en", rad=-0.08, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.32, 0.795, 0.48, "GET", "comprobar usuario vigente", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.30, 0.795, 0.26, "POST", "auditar refresco de sesión", rad=0.0, offset_y=-0.025)
    
    png_path = os.path.join(output_dir, "cu04_cerrar_sesion.png")
    svg_path = os.path.join(output_dir, "cu04_cerrar_sesion.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-05
# -------------------------------------------------------------
def generate_cu05(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-05: REGISTRAR AUDITORÍA DEL SISTEMA",
        "Boundary: HttpRequestBoundary | Controller: audit_middleware() | Entities: Usuario, Empresa, BitacoraAuditoria"
    )
    
    # Actor
    draw_actor(ax, 0.09, 0.50, "Actor / Sistema", "Usuario / Superadmin")
    
    # Boundary
    draw_boundary(ax, 0.28, 0.50, "HttpRequestBoundary", "Vistas App / Peticiones HTTP")
    
    # Controller
    draw_controller(ax, 0.53, 0.50, "audit_middleware()", "audit.py")
    
    # Entities
    draw_entity(ax, 0.86, 0.72, "Usuario", "db / usuario")
    draw_entity(ax, 0.86, 0.50, "Empresa", "db / empresa")
    draw_entity(ax, 0.86, 0.28, "BitacoraAuditoria", "db / bitacora")
    
    # Actor -> Boundary (No label)
    draw_actor_link(ax, 0.15, 0.50, 0.205, 0.50)
    
    # Boundary -> Controller
    draw_call_arrow(ax, 0.355, 0.50, 0.455, 0.50, "despacharRequest()\n(GET, POST, PUT, DELETE)")
    
    # audit_middleware() -> Entities
    draw_crud_arrow(ax, 0.605, 0.53, 0.795, 0.72, "GET", "extraer contexto usuario (JWT)", rad=-0.04, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.50, 0.795, 0.50, "GET", "identificar tenant asociado", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.47, 0.795, 0.30, "POST", "crear registro con datos redactados", rad=0.04, offset_y=-0.025)
    
    # Extra note on CRUD coverage
    ax.text(
        0.70, 0.12,
        "Nota: El middleware intercepta y audita operaciones CRUD globales: GET (access), POST (insert), PUT/PATCH (update), DELETE (delete).",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    
    png_path = os.path.join(output_dir, "cu05_registrar_auditoria.png")
    svg_path = os.path.join(output_dir, "cu05_registrar_auditoria.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-17
# -------------------------------------------------------------
def generate_cu17(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-17: GESTIÓN DE INVENTARIO, KARDEX Y AJUSTES",
        "Boundaries: MatrizInventarioComponent, FormularioAjusteModal, AlertaNotification | Controllers: listar_existencias(), registrar_ajuste(), notificar_error() | Entities: Inventario, PrendaVariante, MovimientoInventario, BitacoraAuditoria",
        width=16, height=10
    )
    
    # Actor
    draw_actor(ax, 0.09, 0.52, "Encargado / Admin", "Usuario autenticado")
    
    # Boundaries
    draw_boundary(ax, 0.28, 0.72, "MatrizInventarioComponent", "inventario.component.html")
    draw_boundary(ax, 0.28, 0.40, "FormularioAjusteModal", "formulario-ajuste.component.html")
    draw_boundary(ax, 0.28, 0.18, "AlertaNotification", "Modal / Toast Notificación")
    
    # Controllers
    draw_controller(ax, 0.53, 0.75, "listar_existencias()", "inventario_service.py")
    draw_controller(ax, 0.53, 0.44, "registrar_ajuste()", "inventario_service.py")
    draw_controller(ax, 0.53, 0.20, "notificar_error()", "api_error(409) / HTTP")
    
    # Entities
    draw_entity(ax, 0.86, 0.82, "Inventario", "db / inventario")
    draw_entity(ax, 0.86, 0.62, "PrendaVariante", "db / prenda_variante")
    draw_entity(ax, 0.86, 0.42, "MovimientoInventario", "db / movimiento_inventario")
    draw_entity(ax, 0.86, 0.22, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    # Actor -> Boundaries (No label)
    draw_actor_link(ax, 0.15, 0.55, 0.205, 0.72)
    draw_actor_link(ax, 0.15, 0.48, 0.205, 0.40)
    
    # Boundaries -> Controllers
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.75, "GET /api/v1/inventario\n(sucursal, solo_bajo_minimo, q)")
    draw_call_arrow(ax, 0.355, 0.40, 0.455, 0.44, "POST /api/v1/inventario/movimientos/ajuste\n(sucursal_id, variante_id, cantidad, motivo)")
    
    # Controller -> Controller (Flujo alternativo / excepción)
    draw_call_arrow(ax, 0.53, 0.39, 0.53, 0.26, "[stock insuficiente]\nraise api_error(409)", offset_y=0.0, rad=-0.25)
    draw_call_arrow(ax, 0.455, 0.20, 0.355, 0.18, "Mensaje Error 409\n(stock no puede ser < 0)", offset_y=0.02, rad=0.0)
    
    # listar_existencias() -> Entities
    draw_crud_arrow(ax, 0.605, 0.78, 0.795, 0.83, "GET", "consultar stock_fisico y minimo", rad=-0.04, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.73, 0.795, 0.64, "GET", "obtener SKU, talla, color y prenda", rad=0.02, offset_y=0.02)
    
    # registrar_ajuste() -> Entities
    draw_crud_arrow(ax, 0.605, 0.48, 0.795, 0.80, "GET", "verificar variante en sucursal", rad=-0.08, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.45, 0.795, 0.77, "PATCH / UPDATE", "actualizar stock_fisico (+/-)", rad=-0.04, offset_y=-0.025)
    draw_crud_arrow(ax, 0.605, 0.42, 0.795, 0.44, "POST / INSERT", "kárdex inmutable (tipo='ajuste')", rad=0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.38, 0.795, 0.24, "POST / INSERT", "auditar evento stock.ajustar", rad=0.06, offset_y=-0.025)
    
    # Nota al pie de página
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: En CU-17, el actor únicamente interactúa con las vistas (boundaries). Las acciones y validaciones de negocio\n(control) regulan el acceso a las tablas de dominio (entities), garantizando la inmutabilidad del kárdex y la auditoría transversal.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    
    png_path = os.path.join(output_dir, "cu17_gestion_inventario.png")
    svg_path = os.path.join(output_dir, "cu17_gestion_inventario.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-18
# -------------------------------------------------------------
def generate_cu18(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-18: DISPONIBILIDAD EN TIENDAS / BÚSQUEDA OMNICANAL",
        "Boundaries: CatalogoPrendaComponent, MapaDisponibilidadModal | Controllers: consultar_disponibilidad_variante(), filtrar_sucursales() | Entities: PrendaVariante, Inventario, Sucursal, Empresa",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente", "Visitante / Comprador")
    
    draw_boundary(ax, 0.28, 0.68, "CatalogoPrendaComponent", "catalogo.component.html")
    draw_boundary(ax, 0.28, 0.32, "MapaDisponibilidadModal", "disponibilidad-tiendas.html")
    
    draw_controller(ax, 0.53, 0.68, "consultar_disponibilidad()", "inventario_service.py")
    draw_controller(ax, 0.53, 0.32, "filtrar_sucursales()", "inventario_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Empresa", "db / empresa")
    draw_entity(ax, 0.86, 0.60, "Sucursal", "db / sucursal")
    draw_entity(ax, 0.86, 0.40, "PrendaVariante", "db / prenda_variante")
    draw_entity(ax, 0.86, 0.20, "Inventario", "db / inventario")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.68, "GET /api/v1/prendas/{id}/disponibilidad\n(variante_id)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.32, "GET /api/v1/inventario/disponibilidad\n(sucursal_id, ciudad)")
    
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.80, "GET", "verificar tenant", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.69, 0.795, 0.62, "GET", "listar sucursales activas", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.66, 0.795, 0.44, "GET", "validar SKU y variantes activas", rad=0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.63, 0.795, 0.26, "GET", "calcular disponible (stock - reservado)", rad=0.05, offset_y=-0.02)
    
    draw_crud_arrow(ax, 0.605, 0.35, 0.795, 0.58, "GET", "filtrar por ciudad / distancia", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.30, 0.795, 0.22, "GET", "obtener existencias de sucursal", rad=0.02, offset_y=-0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Búsqueda omnicanal en tiempo real. Permite al cliente conocer existencias en tiendas físicas antes de acudir o reservar.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu18_disponibilidad_tiendas.png")
    svg_path = os.path.join(output_dir, "cu18_disponibilidad_tiendas.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-19
# -------------------------------------------------------------
def generate_cu19(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-19: CREACIÓN DE RESERVAS Y PROBADOR",
        "Boundaries: DetallePrendaComponent, ModalReservaProbador, ComprobanteReservaComponent | Controllers: validar_disponibilidad(), crear_reserva(), apartar_stock() | Entities: Reserva, ReservaItem, Inventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente", "Usuario autenticado")
    
    draw_boundary(ax, 0.28, 0.72, "ModalReservaProbador", "reserva-probador.html")
    draw_boundary(ax, 0.28, 0.35, "ComprobanteReservaComponent", "reserva-voucher.html")
    draw_boundary(ax, 0.28, 0.15, "AlertaNotification", "Error / Validación")
    
    draw_controller(ax, 0.53, 0.75, "validar_disponibilidad()", "reserva_service.py")
    draw_controller(ax, 0.53, 0.45, "crear_reserva()", "reserva_service.py")
    draw_controller(ax, 0.53, 0.18, "notificar_error()", "api_error(422/409)")
    
    draw_entity(ax, 0.86, 0.82, "Inventario", "db / inventario")
    draw_entity(ax, 0.86, 0.62, "Reserva", "db / reserva")
    draw_entity(ax, 0.86, 0.42, "ReservaItem", "db / reserva_item")
    draw_entity(ax, 0.86, 0.22, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.72)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.35)
    
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.75, "POST /api/v1/reservas/validar\n(sucursal, fecha, prendas)")
    draw_call_arrow(ax, 0.355, 0.38, 0.455, 0.45, "POST /api/v1/reservas\n(Idempotency-Key, datos)")
    
    draw_call_arrow(ax, 0.53, 0.40, 0.53, 0.25, "[sin stock / fecha pasada]\nerror validación", offset_y=0.0, rad=-0.25)
    draw_call_arrow(ax, 0.455, 0.18, 0.355, 0.15, "Respuesta Error\n(mostrar mensaje)", offset_y=0.02, rad=0.0)
    
    draw_crud_arrow(ax, 0.605, 0.77, 0.795, 0.82, "GET", "verificar disponible (sin side-effects)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.49, 0.795, 0.78, "PATCH / UPDATE", "apartar stock_reservado (+)", rad=-0.08, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.46, 0.795, 0.64, "POST", "crear cabecera con código digital", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.43, 0.795, 0.44, "POST", "insertar ítems de prendas", rad=0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.40, 0.795, 0.24, "POST", "auditar creación reserva", rad=0.06, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: El cliente reserva prendas para probador. La operación aparta temporalmente el stock y genera el voucher con código único.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu19_creacion_reservas.png")
    svg_path = os.path.join(output_dir, "cu19_creacion_reservas.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-20
# -------------------------------------------------------------
def generate_cu20(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-20: CONSULTA Y GESTIÓN DE RESERVAS DEL CLIENTE",
        "Boundaries: MisReservasComponent, DetalleReservaModal, DialogoCancelacion | Controllers: mis_reservas(), cancelar_reserva(), liberar_stock() | Entities: Reserva, ReservaEstadoHistorial, Inventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente", "Usuario autenticado")
    
    draw_boundary(ax, 0.28, 0.70, "MisReservasComponent", "mis-reservas.html")
    draw_boundary(ax, 0.28, 0.35, "DialogoCancelacion", "confirm-cancel.html")
    
    draw_controller(ax, 0.53, 0.70, "mis_reservas()", "reserva_service.py")
    draw_controller(ax, 0.53, 0.35, "cancelar_reserva()", "reserva_service.py")
    
    draw_entity(ax, 0.86, 0.82, "Reserva", "db / reserva")
    draw_entity(ax, 0.86, 0.62, "ReservaEstadoHistorial", "db / historial_reserva")
    draw_entity(ax, 0.86, 0.42, "Inventario", "db / inventario")
    draw_entity(ax, 0.86, 0.22, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.70)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.35)
    
    draw_call_arrow(ax, 0.355, 0.70, 0.455, 0.70, "GET /api/v1/reservas\n(filtrar solo propias)")
    draw_call_arrow(ax, 0.355, 0.35, 0.455, 0.35, "POST /api/v1/reservas/{id}/cancelar\n(motivo cancelación)")
    
    draw_crud_arrow(ax, 0.605, 0.73, 0.795, 0.82, "GET", "listar reservas del cliente", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.68, 0.795, 0.64, "GET", "obtener historial de estados", rad=0.01, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.39, 0.795, 0.80, "PATCH", "cambiar estado a 'cancelada'", rad=-0.08, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.36, 0.795, 0.60, "POST", "registrar transicion en historial", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.33, 0.795, 0.42, "PATCH / UPDATE", "liberar stock_reservado (-)", rad=0.02, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.30, 0.795, 0.24, "POST", "auditar cancelación", rad=0.06, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Al cancelar la reserva, el disparador o controlador restituye el stock reservado para mantener la consistencia omnicanal.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu20_consulta_reservas.png")
    svg_path = os.path.join(output_dir, "cu20_consulta_reservas.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-21
# -------------------------------------------------------------
def generate_cu21(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-21: PREPARACIÓN Y VALIDACIÓN DE RESERVAS (STAFF)",
        "Boundaries: BandejaReservasSucursal, ModalPreparacionProbador, ModalReporteIncidencia | Controllers: listar_reservas_sucursal(), preparar_reserva(), registrar_incidencia() | Entities: Reserva, ReservaEstadoHistorial, Inventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Encargado", "Staff de Sucursal")
    
    draw_boundary(ax, 0.28, 0.72, "BandejaReservasSucursal", "reservas-por-preparar.html")
    draw_boundary(ax, 0.28, 0.44, "ModalPreparacionProbador", "preparar-reserva.html")
    draw_boundary(ax, 0.28, 0.18, "ModalReporteIncidencia", "incidencia-stock.html")
    
    draw_controller(ax, 0.53, 0.72, "listar_reservas()", "reserva_service.py")
    draw_controller(ax, 0.53, 0.44, "preparar_reserva()", "reserva_service.py")
    draw_controller(ax, 0.53, 0.18, "registrar_incidencia()", "reserva_service.py")
    
    draw_entity(ax, 0.86, 0.82, "Reserva", "db / reserva")
    draw_entity(ax, 0.86, 0.60, "ReservaEstadoHistorial", "db / historial_reserva")
    draw_entity(ax, 0.86, 0.40, "Inventario", "db / inventario")
    draw_entity(ax, 0.86, 0.20, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.15, 0.54, 0.205, 0.72)
    draw_actor_link(ax, 0.15, 0.50, 0.205, 0.44)
    draw_actor_link(ax, 0.15, 0.46, 0.205, 0.18)
    
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.72, "GET /api/v1/reservas/por-preparar")
    draw_call_arrow(ax, 0.355, 0.44, 0.455, 0.44, "POST /api/v1/reservas/{id}/preparar\n(probador asignado)")
    draw_call_arrow(ax, 0.355, 0.18, 0.455, 0.18, "POST /api/v1/reservas/{id}/incidencia\n(prenda dañada/extraviada)")
    
    draw_crud_arrow(ax, 0.605, 0.74, 0.795, 0.82, "GET", "filtrar por sucursal y 'pendiente'", rad=-0.04, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.47, 0.795, 0.80, "PATCH", "estado='preparada', probador='P1'", rad=-0.06, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.44, 0.795, 0.60, "POST", "historial: pendiente -> preparada", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.41, 0.795, 0.22, "POST", "auditar preparacion física", rad=0.05, offset_y=-0.02)
    
    draw_crud_arrow(ax, 0.605, 0.22, 0.795, 0.76, "PATCH", "estado='incidencia_stock'", rad=-0.09, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.19, 0.795, 0.56, "POST", "historial: incidencia", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.16, 0.795, 0.38, "PATCH / UPDATE", "liberar reserva del ítem dañado", rad=0.01, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.14, 0.795, 0.18, "POST", "auditar incidencia de prenda", rad=0.06, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: El encargado prepara las prendas en el probador asignado o reporta incidencias liberando el stock correspondiente.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu21_preparacion_reservas.png")
    svg_path = os.path.join(output_dir, "cu21_preparacion_reservas.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-22
# -------------------------------------------------------------
def generate_cu22(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-22: CARRITO DE COMPRAS Y CHECKOUT OMNICANAL",
        "Boundaries: CarritoComponent, CheckoutComponent, ResumenOrdenModal | Controllers: obtener_carrito(), agregar_item(), validar_checkout(), crear_orden() | Entities: Carrito, CarritoDetalle, Cupon, Venta, Envio, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente", "Comprador online")
    
    draw_boundary(ax, 0.28, 0.72, "CarritoComponent", "carrito.component.html")
    draw_boundary(ax, 0.28, 0.38, "CheckoutComponent", "checkout.component.html")
    draw_boundary(ax, 0.28, 0.16, "ResumenOrdenModal", "orden-resumen.html")
    
    draw_controller(ax, 0.53, 0.80, "obtener_carrito()", "carrito_service.py")
    draw_controller(ax, 0.53, 0.58, "agregar_item()", "carrito_service.py")
    draw_controller(ax, 0.53, 0.36, "validar_checkout()", "checkout_service.py")
    draw_controller(ax, 0.53, 0.16, "crear_orden()", "checkout_service.py")
    
    draw_entity(ax, 0.86, 0.84, "Carrito / Detalle", "db / carrito")
    draw_entity(ax, 0.86, 0.65, "Cupon / Uso", "db / cupon")
    draw_entity(ax, 0.86, 0.46, "Venta / Detalle", "db / venta")
    draw_entity(ax, 0.86, 0.27, "Envio", "db / envio")
    draw_entity(ax, 0.86, 0.10, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.72)
    draw_actor_link(ax, 0.15, 0.48, 0.205, 0.38)
    
    draw_call_arrow(ax, 0.355, 0.74, 0.455, 0.80, "GET /api/v1/carrito")
    draw_call_arrow(ax, 0.355, 0.70, 0.455, 0.58, "POST /api/v1/carrito/items")
    draw_call_arrow(ax, 0.355, 0.40, 0.455, 0.36, "POST /api/v1/checkout/validar\n(recojo/envio, cupon)")
    draw_call_arrow(ax, 0.355, 0.36, 0.455, 0.16, "POST /api/v1/checkout/orden\n(Idempotency-Key)")
    
    draw_crud_arrow(ax, 0.605, 0.82, 0.795, 0.86, "GET / POST", "recuperar o crear carrito activo", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.60, 0.795, 0.82, "POST / PUT", "insertar/modificar item y cantidad", rad=-0.04, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.38, 0.795, 0.67, "GET", "validar cupon y calcular descuento", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.34, 0.795, 0.48, "GET", "comprobar inventario y precios", rad=0.01, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.18, 0.795, 0.46, "POST", "crear orden 'pendiente_pago'", rad=-0.05, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.15, 0.795, 0.27, "POST", "crear envio / recojo en tienda", rad=0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.12, 0.795, 0.12, "POST", "auditar orden checkout", rad=0.06, offset_y=-0.02)
    
    ax.text(
        0.50, 0.04,
        "Nota ICONIX: El checkout omnicanal valida stock, aplica cupones, calcula costos de envío y crea la orden garantizando idempotencia.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu22_checkout_carrito.png")
    svg_path = os.path.join(output_dir, "cu22_checkout_carrito.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-23
# -------------------------------------------------------------
def generate_cu23(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-23: PUNTO DE VENTA (POS) - CAJA Y FACTURACIÓN",
        "Boundaries: PantallaPOSComponent, ModalCobroPOS, TicketImpresionView | Controllers: buscar_por_barcode(), procesar_venta_pos(), generar_ticket() | Entities: PrendaVariante, Inventario, MovimientoInventario, Venta, Pago, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cajero", "Usuario de Mostrador")
    
    draw_boundary(ax, 0.28, 0.72, "PantallaPOSComponent", "pos-mostrador.html")
    draw_boundary(ax, 0.28, 0.44, "ModalCobroPOS", "pos-cobro.html")
    draw_boundary(ax, 0.28, 0.18, "TicketImpresionView", "pos-ticket.html")
    
    draw_controller(ax, 0.53, 0.74, "buscar_por_barcode()", "pos_service.py")
    draw_controller(ax, 0.53, 0.44, "procesar_venta_pos()", "pos_service.py")
    draw_controller(ax, 0.53, 0.18, "generar_ticket()", "pos_service.py")
    
    draw_entity(ax, 0.86, 0.84, "PrendaVariante", "db / prenda_variante")
    draw_entity(ax, 0.86, 0.68, "Inventario", "db / inventario")
    draw_entity(ax, 0.86, 0.52, "MovimientoInventario", "db / kardex")
    draw_entity(ax, 0.86, 0.36, "Venta / Detalle", "db / venta")
    draw_entity(ax, 0.86, 0.20, "Pago", "db / pago (efectivo/tarjeta)")
    draw_entity(ax, 0.86, 0.06, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.72)
    draw_actor_link(ax, 0.15, 0.50, 0.205, 0.44)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.18)
    
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.74, "GET /api/v1/pos/scanner\n(código de barras o SKU)")
    draw_call_arrow(ax, 0.355, 0.44, 0.455, 0.44, "POST /api/v1/pos/ventas\n(items, pago, cliente)")
    draw_call_arrow(ax, 0.355, 0.18, 0.455, 0.18, "GET /api/v1/pos/ventas/{id}/ticket")
    
    draw_crud_arrow(ax, 0.605, 0.76, 0.795, 0.84, "GET", "identificar variante por código", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.73, 0.795, 0.70, "GET", "verificar stock local sucursal", rad=0.01, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.48, 0.795, 0.68, "PATCH / UPDATE", "descontar stock_fisico (-)", rad=-0.05, offset_y=0.025)
    draw_crud_arrow(ax, 0.605, 0.45, 0.795, 0.53, "POST", "kárdex inmutable tipo 'salida_pos'", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.42, 0.795, 0.38, "POST", "crear venta estado 'pagada'", rad=0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.39, 0.795, 0.22, "POST", "registrar pago contado / cambio", rad=0.04, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.36, 0.795, 0.08, "POST", "auditar venta presencial", rad=0.07, offset_y=-0.025)
    
    draw_crud_arrow(ax, 0.605, 0.18, 0.795, 0.34, "GET", "recuperar cabecera, líneas y pago", rad=-0.03, offset_y=0.02)
    
    ax.text(
        0.50, 0.03,
        "Nota ICONIX: El POS realiza venta de mostrador atómica: descuenta inventario, asienta en kárdex, guarda venta pagada y emite ticket.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu23_punto_venta_pos.png")
    svg_path = os.path.join(output_dir, "cu23_punto_venta_pos.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-24
# -------------------------------------------------------------
def generate_cu24(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-24: PROCESAMIENTO DE PAGOS, PASARELAS Y REEMBOLSOS",
        "Boundaries: PasarelaStripeElements, WebhookStripeEndpoint, PollingConfirmacionView | Controllers: crear_intencion_pago(), procesar_webhook(), consultar_pago_polling() | Entities: Pago, StripeEvento, Venta, Inventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente / Stripe", "Usuario o Pasarela Externa")
    
    draw_boundary(ax, 0.28, 0.72, "PasarelaStripeElements", "stripe-elements.html")
    draw_boundary(ax, 0.28, 0.44, "WebhookStripeEndpoint", "API Webhook Pública")
    draw_boundary(ax, 0.28, 0.18, "ConfirmacionPagoView", "pago-confirmado.html")
    
    draw_controller(ax, 0.53, 0.74, "crear_intencion_pago()", "pago_service.py")
    draw_controller(ax, 0.53, 0.44, "procesar_webhook()", "pago_service.py")
    draw_controller(ax, 0.53, 0.18, "consultar_pago_polling()", "pago_service.py")
    
    draw_entity(ax, 0.86, 0.82, "Pago", "db / pago")
    draw_entity(ax, 0.86, 0.62, "StripeEvento", "db / stripe_evento (idempotencia)")
    draw_entity(ax, 0.86, 0.42, "Venta", "db / venta")
    draw_entity(ax, 0.86, 0.22, "BitacoraAuditoria", "db / bitacora")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.72)
    draw_actor_link(ax, 0.15, 0.50, 0.205, 0.44)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.18)
    
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.74, "POST /api/v1/pagos/intencion\n(orden_id, metodo)")
    draw_call_arrow(ax, 0.355, 0.44, 0.455, 0.44, "POST /api/v1/pagos/webhook/stripe\n(Stripe-Signature, evento)")
    draw_call_arrow(ax, 0.355, 0.18, 0.455, 0.18, "GET /api/v1/pagos/{id}/polling")
    
    draw_crud_arrow(ax, 0.605, 0.76, 0.795, 0.84, "POST", "crear pago 'pendiente' (client_secret)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.46, "GET", "verificar orden pendiente", rad=-0.01, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.47, 0.795, 0.64, "POST", "registrar evento (prevenir replay)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.44, 0.795, 0.80, "PATCH", "marcar pago 'completado'", rad=0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.41, 0.795, 0.44, "PATCH", "actualizar venta a 'pagada'", rad=0.01, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.38, 0.795, 0.24, "POST", "auditar cobro pasarela", rad=0.05, offset_y=-0.025)
    
    draw_crud_arrow(ax, 0.605, 0.18, 0.795, 0.78, "GET", "consultar estado actual del pago", rad=-0.07, offset_y=0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Procesamiento con Stripe. El webhook público valida firma, garantiza idempotencia y asienta la venta como pagada.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu24_procesamiento_pagos.png")
    svg_path = os.path.join(output_dir, "cu24_procesamiento_pagos.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-25
# -------------------------------------------------------------
def generate_cu25(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-25: DESCARGAR CATÁLOGO OFFLINE",
        "Boundaries: CatalogoOfflineComponent, ServiceWorkerCacheView | Controllers: descargar_catalogo_offline(), persistir_local() | Entities: Prenda, Variante, Inventario, Empresa",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente / Cajero", "Dispositivo Offline (PWA/Móvil)")
    
    draw_boundary(ax, 0.28, 0.68, "CatalogoOfflineComponent", "catalogo-offline.component.html")
    draw_boundary(ax, 0.28, 0.32, "ServiceWorkerCacheView", "IndexedDB / SQLite Storage")
    
    draw_controller(ax, 0.53, 0.68, "descargar_catalogo()", "sync_service.py")
    draw_controller(ax, 0.53, 0.32, "persistir_local()", "IndexedDB / SQLite Controller")
    
    draw_entity(ax, 0.86, 0.80, "Empresa", "db / empresa")
    draw_entity(ax, 0.86, 0.60, "Prenda", "db / prenda")
    draw_entity(ax, 0.86, 0.40, "Variante", "db / variante")
    draw_entity(ax, 0.86, 0.20, "Inventario", "db / inventario (existencias sucursal)")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.68, "GET /api/v1/sync/catalogo-offline\n(sucursal_id)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.32, "almacenarLoteLocal()\n(prendas, variantes, stock)")
    
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.80, "GET", "verificar tenant activo", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.69, 0.795, 0.62, "GET", "consultar prendas activas", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.66, 0.795, 0.42, "GET", "obtener variantes, precios y tallas", rad=0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.63, 0.795, 0.24, "GET", "descargar existencias sucursal", rad=0.05, offset_y=-0.02)
    
    draw_crud_arrow(ax, 0.605, 0.32, 0.795, 0.38, "PUT / POST", "sincronizar tabla local SQLite/IDB", rad=0.0, offset_y=0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Descarga el catálogo filtrado por empresa y sucursal para operar de forma autónoma sin conexión a Internet.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu25_descargar_catalogo_offline.png")
    svg_path = os.path.join(output_dir, "cu25_descargar_catalogo_offline.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-26
# -------------------------------------------------------------
def generate_cu26(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-26: REGISTRAR RESERVA OFFLINE",
        "Boundaries: FormularioReservaOffline, VoucherLocalView, BannerOffline | Controllers: generar_uuid_local(), registrar_reserva_offline() | Entities: OperacionPendiente, InventarioLocal, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente", "Usuario sin conexión")
    
    draw_boundary(ax, 0.28, 0.68, "FormularioReservaOffline", "reserva-offline.html")
    draw_boundary(ax, 0.28, 0.32, "VoucherLocalView", "voucher-local.html (UUID Local)")
    
    draw_controller(ax, 0.53, 0.70, "generar_uuid_local()", "UUID v4 Generador Cliente")
    draw_controller(ax, 0.53, 0.35, "registrar_reserva_offline()", "sync_service.py")
    
    draw_entity(ax, 0.86, 0.78, "OperacionPendiente", "db / operacion_pendiente")
    draw_entity(ax, 0.86, 0.50, "InventarioLocal", "IndexedDB / SQLite Inventario")
    draw_entity(ax, 0.86, 0.22, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.70, "solicitarReservaOffline()\n(prendas, fecha_visita)")
    draw_call_arrow(ax, 0.53, 0.65, 0.53, 0.40, "emitirUUID()\n(asignar identificador)", offset_y=0.0, rad=-0.2)
    draw_call_arrow(ax, 0.355, 0.35, 0.455, 0.35, "POST /api/v1/sync/reservas-offline\n(payload encolado)")
    
    draw_crud_arrow(ax, 0.605, 0.39, 0.795, 0.78, "POST / INSERT", "encolar op 'reserva_offline' (pendiente)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.35, 0.795, 0.50, "PATCH", "descontar stock_disponible local", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.31, 0.795, 0.24, "POST", "auditar registro offline", rad=0.05, offset_y=-0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Generación de UUID local en el cliente. Registra la reserva en almacenamiento local y la encola para sincronizar al restablecer conexión.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu26_registrar_reserva_offline.png")
    svg_path = os.path.join(output_dir, "cu26_registrar_reserva_offline.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-27
# -------------------------------------------------------------
def generate_cu27(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-27: BLOQUEAR STOCK SOFT-LOCK CON TTL",
        "Boundaries: DetallePrendaOffline, BadgeTemporizadorTTL | Controllers: crear_soft_lock(), verificar_expiracion(), liberar_soft_lock() | Entities: SoftLock, Inventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente / Dispositivo", "Terminal Desconectado")
    
    draw_boundary(ax, 0.28, 0.68, "DetallePrendaOffline", "prenda-detalle.html")
    draw_boundary(ax, 0.28, 0.32, "BadgeTemporizadorTTL", "Badge 'Reservado 45 min'")
    
    draw_controller(ax, 0.53, 0.72, "crear_soft_lock()", "sync_service.py")
    draw_controller(ax, 0.53, 0.42, "verificar_expiracion()", "sync_service.py (TTL Check)")
    draw_controller(ax, 0.53, 0.18, "liberar_soft_lock()", "sync_service.py")
    
    draw_entity(ax, 0.86, 0.78, "SoftLock", "db / soft_lock (TTL 45 min)")
    draw_entity(ax, 0.86, 0.48, "Inventario", "db / inventario")
    draw_entity(ax, 0.86, 0.18, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.72, "POST /api/v1/sync/soft-locks\n(variante_id, cantidad, dispositivo)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.42, "comprobarTTL()\n(tiempo transcurrido)")
    draw_call_arrow(ax, 0.53, 0.37, 0.53, 0.23, "[TTL expirado > 45 min]\nliberar bloqueo", offset_y=0.0, rad=-0.2)
    
    draw_crud_arrow(ax, 0.605, 0.74, 0.795, 0.80, "POST / INSERT", "crear soft_lock (expira_en=now+45m)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.70, 0.795, 0.52, "GET", "verificar stock no bloqueado", rad=0.0, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.44, 0.795, 0.74, "GET", "consultar expira_en vs now()", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.20, 0.795, 0.70, "DELETE", "eliminar soft_lock expirado", rad=-0.05, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.16, 0.795, 0.22, "POST", "auditar liberación por TTL", rad=0.04, offset_y=-0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Mecanismo de Soft-Lock con TTL (45 minutos) para evitar conflictos de concurrencia y sobreventa de prendas en entornos offline.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu27_bloquear_stock_soft_lock.png")
    svg_path = os.path.join(output_dir, "cu27_bloquear_stock_soft_lock.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-28
# -------------------------------------------------------------
def generate_cu28(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-28: VENTA DE CONTADO OFFLINE",
        "Boundaries: POSOfflineComponent, ModalCobroEfectivoOffline, TicketPreliminarView | Controllers: asentar_venta_offline(), generar_ticket_preliminar() | Entities: OperacionPendiente, InventarioLocal, Venta, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cajero", "Mostrador Desconectado")
    
    draw_boundary(ax, 0.28, 0.72, "POSOfflineComponent", "pos-offline.component.html")
    draw_boundary(ax, 0.28, 0.42, "ModalCobroEfectivoOffline", "cobro-efectivo-offline.html")
    draw_boundary(ax, 0.28, 0.18, "TicketPreliminarView", "Ticket con marca PENDIENTE")
    
    draw_controller(ax, 0.53, 0.68, "asentar_venta_offline()", "sync_service.py")
    draw_controller(ax, 0.53, 0.28, "generar_ticket_preliminar()", "pos_offline_service.ts")
    
    draw_entity(ax, 0.86, 0.80, "OperacionPendiente", "db / operacion_pendiente")
    draw_entity(ax, 0.86, 0.55, "InventarioLocal", "SQLite / IDB Inventario")
    draw_entity(ax, 0.86, 0.32, "Venta", "db / venta (estado='pendiente_sync')")
    draw_entity(ax, 0.86, 0.10, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    draw_actor_link(ax, 0.15, 0.54, 0.205, 0.72)
    draw_actor_link(ax, 0.15, 0.50, 0.205, 0.42)
    draw_actor_link(ax, 0.15, 0.46, 0.205, 0.18)
    
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.68, "POST /api/v1/sync/ventas-offline\n(datos venta, efectivo recibido)")
    draw_call_arrow(ax, 0.355, 0.42, 0.455, 0.66, "confirmarCobroLocal()")
    draw_call_arrow(ax, 0.53, 0.63, 0.53, 0.34, "imprimirComprobante()\n(leyenda sync)", offset_y=0.0, rad=-0.2)
    
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.80, "POST / INSERT", "guardar en operacion_pendiente (uuid)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.67, 0.795, 0.58, "PATCH / UPDATE", "reducir stock físico local", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.62, 0.795, 0.36, "POST / INSERT", "venta local 'pendiente_sync'", rad=0.03, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.28, 0.795, 0.12, "POST", "auditar cobro en efectivo offline", rad=0.04, offset_y=-0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: El sistema de mostrador emite ticket preliminar y descuenta stock local sin depender de la conectividad con el servidor central.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu28_venta_contado_offline.png")
    svg_path = os.path.join(output_dir, "cu28_venta_contado_offline.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-29
# -------------------------------------------------------------
def generate_cu29(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-29: VALIDAR COMPROBANTE Y CAMBIO QR OFFLINE",
        "Boundaries: LectorQRCambiosView, FormularioNotaCambio, ComprobanteCambioView | Controllers: validar_qr_comprobante(), procesar_nota_cambio() | Entities: NotaCambio, Venta, Inventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cajero", "Mostrador / Devoluciones")
    
    draw_boundary(ax, 0.28, 0.68, "LectorQRCambiosView", "lector-qr-cambio.html")
    draw_boundary(ax, 0.28, 0.32, "FormularioNotaCambio", "nota-cambio-form.html")
    
    draw_controller(ax, 0.53, 0.68, "validar_qr_comprobante()", "sync_service.py (HMAC-SHA256)")
    draw_controller(ax, 0.53, 0.32, "procesar_nota_cambio()", "sync_service.py")
    
    draw_entity(ax, 0.86, 0.80, "Venta", "db / venta (ticket original)")
    draw_entity(ax, 0.86, 0.60, "NotaCambio", "db / nota_cambio")
    draw_entity(ax, 0.86, 0.40, "Inventario", "db / inventario (reingreso/salida)")
    draw_entity(ax, 0.86, 0.18, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.68, "POST /api/v1/sync/validar-qr\n(qr_data)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.32, "POST /api/v1/sync/nota-cambio\n(variante_devuelta, nueva, firma)")
    
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.80, "GET", "verificar firma HMAC y venta original", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.36, 0.795, 0.62, "POST / INSERT", "emitir nota_cambio con firma QR", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.32, 0.795, 0.42, "PATCH / UPDATE", "reingresar devuelta (+) y descontar nueva (-)", rad=0.01, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.28, 0.795, 0.20, "POST", "auditar cambio de prenda", rad=0.05, offset_y=-0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Validación de tickets físicos mediante QR con firma criptográfica HMAC-SHA256, permitiendo gestionar cambios de prendas sin conexión.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu29_validar_qr_cambio_offline.png")
    svg_path = os.path.join(output_dir, "cu29_validar_qr_cambio_offline.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-30
# -------------------------------------------------------------
def generate_cu30(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-30: CONSULTAR COLA DE OPERACIONES OFFLINE",
        "Boundaries: ColaOperacionesComponent, BadgeConectividad, DetalleOperacionModal | Controllers: consultar_cola(), filtrar_por_estado() | Entities: OperacionPendiente, Sucursal, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cajero / Admin", "Monitor de Sincronización")
    
    draw_boundary(ax, 0.28, 0.68, "ColaOperacionesComponent", "cola-sync.component.html")
    draw_boundary(ax, 0.28, 0.32, "DetalleOperacionModal", "operacion-detalle.html")
    
    draw_controller(ax, 0.53, 0.68, "consultar_cola()", "sync_service.py")
    draw_controller(ax, 0.53, 0.32, "filtrar_por_estado()", "sync_service.py")
    
    draw_entity(ax, 0.86, 0.75, "OperacionPendiente", "db / operacion_pendiente")
    draw_entity(ax, 0.86, 0.45, "Sucursal", "db / sucursal")
    draw_entity(ax, 0.86, 0.18, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.68, "GET /api/v1/sync/cola\n(sucursal_id)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.32, "filtrarOperaciones()\n(estado: pendiente, conflicto, resuelta)")
    
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.76, "GET", "listar operaciones pendientes (FIFO)", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.68, 0.795, 0.48, "GET", "verificar sucursal asociada", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.32, 0.795, 0.74, "GET", "inspeccionar payload y errores", rad=-0.05, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.28, 0.795, 0.20, "POST", "auditar inspección de cola", rad=0.04, offset_y=-0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Permite monitorear el estado de cada transacción offline (pendiente, aplicada o en conflicto) asegurando la observabilidad (RNF10).",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu30_cola_operaciones_offline.png")
    svg_path = os.path.join(output_dir, "cu30_cola_operaciones_offline.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-31
# -------------------------------------------------------------
def generate_cu31(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-31: SINCRONIZAR OPERACIONES PENDIENTES",
        "Boundaries: BotonSyncComponent, SyncProgressModal, AlertaSyncExitosa | Controllers: procesar_lote_sync(), validar_idempotencia(), asentar_operacion() | Entities: SyncRegistroIdempotencia, OperacionPendiente, Venta, Inventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Sistema / Cajero", "Disparador de Sincronización")
    
    draw_boundary(ax, 0.28, 0.68, "BotonSyncComponent", "sync-toolbar.component.html")
    draw_boundary(ax, 0.28, 0.32, "SyncProgressModal", "sync-progress.modal.html")
    
    draw_controller(ax, 0.53, 0.74, "procesar_lote_sync()", "sync_service.py")
    draw_controller(ax, 0.53, 0.44, "validar_idempotencia()", "sync_service.py (RNF05)")
    draw_controller(ax, 0.53, 0.18, "asentar_operacion()", "sync_service.py (FIFO Commit)")
    
    draw_entity(ax, 0.86, 0.82, "SyncRegistroIdempotencia", "db / sync_registro_idempotencia")
    draw_entity(ax, 0.86, 0.62, "OperacionPendiente", "db / operacion_pendiente")
    draw_entity(ax, 0.86, 0.42, "Venta / Inventario", "db / venta & inventario")
    draw_entity(ax, 0.86, 0.20, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.74, "POST /api/v1/sync\n(lote de operaciones)")
    draw_call_arrow(ax, 0.53, 0.69, 0.53, 0.49, "verificarClave()\n(idempotency_key)", offset_y=0.0, rad=-0.2)
    draw_call_arrow(ax, 0.53, 0.39, 0.53, 0.23, "[clave nueva]\naplicar transacción", offset_y=0.0, rad=-0.2)
    
    draw_crud_arrow(ax, 0.605, 0.48, 0.795, 0.82, "GET / POST", "comprobar/guardar idempotency_key", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.44, 0.795, 0.62, "PATCH", "estado -> 'aplicada' o 'conflicto'", rad=0.0, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.20, 0.795, 0.44, "POST / PATCH", "insertar venta y descontar stock central", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.16, 0.795, 0.22, "POST", "auditar sincronización de lote", rad=0.04, offset_y=-0.02)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Garantía de idempotencia (RNF05). Si se reenvía un lote confirmado, el sistema devuelve el resultado previo sin duplicar ventas ni inventario.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu31_sincronizar_operaciones.png")
    svg_path = os.path.join(output_dir, "cu31_sincronizar_operaciones.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-32
# -------------------------------------------------------------
def generate_cu32(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-32: RESOLVER CONFLICTOS DE SINCRONIZACIÓN",
        "Boundaries: BandejaConflictosComponent, ModalResolucionConflicto, AlertaResolucion | Controllers: listar_conflictos(), resolver_conflicto(), aplicar_ajuste_fifo() | Entities: OperacionPendiente, Inventario, MovimientoInventario, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Encargado / Admin", "Resolutor de Discrepancias")
    
    draw_boundary(ax, 0.28, 0.68, "BandejaConflictosComponent", "conflictos-sync.html")
    draw_boundary(ax, 0.28, 0.32, "ModalResolucionConflicto", "resolver-conflicto.html")
    
    draw_controller(ax, 0.53, 0.70, "listar_conflictos()", "sync_service.py")
    draw_controller(ax, 0.53, 0.35, "resolver_conflicto()", "sync_service.py (FIFO / Manual)")
    
    draw_entity(ax, 0.86, 0.82, "OperacionPendiente", "db / operacion_pendiente (estado='conflicto')")
    draw_entity(ax, 0.86, 0.60, "Inventario", "db / inventario (ajuste forzado)")
    draw_entity(ax, 0.86, 0.38, "MovimientoInventario", "db / movimiento_inventario")
    draw_entity(ax, 0.86, 0.16, "BitacoraAuditoria", "db / bitacora_auditoria")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.70, "GET /api/v1/sync/conflictos\n(sucursal_id)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.35, "POST /api/v1/sync/conflictos/resolver\n(decision: 'ajustar', 'anular', 'reintentar')")
    
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.82, "GET", "recuperar operaciones en conflicto y error", rad=-0.04, offset_y=0.02)
    
    draw_crud_arrow(ax, 0.605, 0.39, 0.795, 0.80, "PATCH", "cambiar estado a 'resuelta' o 'rechazada'", rad=-0.06, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.35, 0.795, 0.60, "PATCH / UPDATE", "aplicar ajuste de stock correctivo", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.32, 0.795, 0.40, "POST", "asentar en kárdex la resolución", rad=0.02, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.28, 0.795, 0.18, "POST", "auditar decisión administrativa", rad=0.06, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Resolución de conflictos de concurrencia e inventario negativo por ventas simultáneas bajo orden FIFO o decisión manual.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu32_resolver_conflictos.png")
    svg_path = os.path.join(output_dir, "cu32_resolver_conflictos.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-33
# -------------------------------------------------------------
def generate_cu33(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-33: REPORTES Y DASHBOARDS CONVENCIONALES",
        "Boundaries: ReportesConvencionalesComponent, FiltrosReporteView | Controllers: obtener_dashboard_convencional(), obtener_ventas_periodo(), obtener_rotacion_stock() | Entities: Venta, VentaDetalle, Inventario, MovimientoInventario",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Administrador / Encargado", "Analista de Métricas")
    
    draw_boundary(ax, 0.28, 0.68, "ReportesConvencionalesComponent", "reportes-convencionales.html")
    draw_boundary(ax, 0.28, 0.32, "FiltrosReporteView", "Fechas / Sucursal / Categoría")
    
    draw_controller(ax, 0.53, 0.72, "obtener_dashboard_convencional()", "reporte_service.py")
    draw_controller(ax, 0.53, 0.50, "obtener_ventas_periodo()", "reporte_service.py")
    draw_controller(ax, 0.53, 0.28, "obtener_rotacion_stock()", "reporte_service.py")
    
    draw_entity(ax, 0.86, 0.82, "Venta", "db / venta (kpis hoy/mes)")
    draw_entity(ax, 0.86, 0.60, "VentaDetalle", "db / venta_detalle (top prendas)")
    draw_entity(ax, 0.86, 0.38, "Inventario", "db / inventario (stock crítico)")
    draw_entity(ax, 0.86, 0.16, "MovimientoInventario", "db / movimiento_inventario")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.72, "GET /api/v1/reportes/convencionales/dashboard\n(kpis generales, ventas por sucursal)")
    draw_call_arrow(ax, 0.355, 0.35, 0.455, 0.50, "GET /api/v1/reportes/convencionales/ventas\n(fecha_inicio, fecha_fin, sucursal)")
    draw_call_arrow(ax, 0.355, 0.30, 0.455, 0.28, "GET /api/v1/reportes/convencionales/rotacion\n(categoria_id, sucursal_id)")
    
    draw_crud_arrow(ax, 0.605, 0.74, 0.795, 0.82, "GET", "calcular facturación de hoy, mes y ticket promedio", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.70, 0.795, 0.62, "GET", "ranking top 10 prendas más demandadas", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.50, 0.795, 0.80, "GET", "agregación temporal de ventas y transacciones", rad=0.03, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.30, 0.795, 0.40, "GET", "balance existencias y alertas stock crítico", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.26, 0.795, 0.18, "GET", "calcular ratio de rotación (entradas vs salidas)", rad=0.04, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Generación de dashboards estándar y reportes de kárdex con aislamiento multi-tenant por empresa_id.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu33_reportes_convencionales.png")
    svg_path = os.path.join(output_dir, "cu33_reportes_convencionales.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-34
# -------------------------------------------------------------
def generate_cu34(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-34: REPORTES GENERATIVOS CON IA (WHITELIST & EXPORTACIÓN)",
        "Boundaries: ReporteIaComponent, ModalExportarDocumento | Controllers: procesar_reporte_ia(), exportar_reporte() | Entities: ConsultaIaLog, ReporteExportado, VistasAgregadas, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Gerente / Admin (Plan Pro)", "Usuario Avanzado BR-03")
    
    draw_boundary(ax, 0.28, 0.68, "ReporteIaComponent", "reporte-ia.html (Texto / Dictado Voz)")
    draw_boundary(ax, 0.28, 0.32, "ModalExportarDocumento", "Selector Formato XLSX / PDF")
    
    draw_controller(ax, 0.53, 0.70, "procesar_reporte_ia()", "ia_reporte_service.py (Whitelist BR-08)")
    draw_controller(ax, 0.53, 0.32, "exportar_reporte()", "ia_reporte_service.py (openpyxl / ReportLab)")
    
    draw_entity(ax, 0.86, 0.82, "ConsultaIaLog", "db / consulta_ia_log (prompt, tokens)")
    draw_entity(ax, 0.86, 0.60, "ReporteExportado", "db / reporte_exportado (url, formato, bytes)")
    draw_entity(ax, 0.86, 0.38, "Venta / Inventario", "db / vistas agregadas tenant")
    draw_entity(ax, 0.86, 0.16, "BitacoraAuditoria", "db / bitacora_auditoria (accion='export')")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.68, 0.455, 0.70, "POST /api/v1/reportes/ia/consultar\n(prompt texto/voz, canal)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.32, "POST /api/v1/reportes/ia/exportar\n(formato: 'xlsx' | 'pdf', columnas, filas)")
    
    draw_crud_arrow(ax, 0.605, 0.74, 0.795, 0.82, "POST / INSERT", "registrar consulta, prompt, latencia y tokens", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.68, 0.795, 0.42, "GET", "consulta SQL acotada bajo Whitelist BR-08", rad=-0.06, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.34, 0.795, 0.60, "POST / INSERT", "guardar archivo exportado con TTL de retención", rad=0.03, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.28, 0.795, 0.18, "POST", "auditar exportación masiva de datos corporativos", rad=0.06, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Consultas en lenguaje natural validadas contra Whitelist estricta (BR-08) y exportación protegida a usuarios Plan Pro (BR-03).",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu34_reporte_generativo_ia.png")
    svg_path = os.path.join(output_dir, "cu34_reporte_generativo_ia.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-35
# -------------------------------------------------------------
def generate_cu35(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-35: DASHBOARD ANALÍTICO ML CON SÍNTESIS AUDIO TTS",
        "Boundaries: DashboardMlComponent, ReproductorAudioTtsView | Controllers: entrenar_y_predecir_demanda(), segmentar_clientes_kmeans(), generar_audio_tts_sintesis() | Entities: ModeloMl, Venta, Cliente, BitacoraAuditoria",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Director Comercial / Gerente", "Decisor Estratégico")
    
    draw_boundary(ax, 0.28, 0.68, "DashboardMlComponent", "dashboard-ml.html (Visualizador RFM & ML)")
    draw_boundary(ax, 0.28, 0.32, "ReproductorAudioTtsView", "Barra Audio Diagnóstico Prescriptivo")
    
    draw_controller(ax, 0.53, 0.74, "entrenar_y_predecir_demanda()", "ml_analytics_service.py (Regresión)")
    draw_controller(ax, 0.53, 0.50, "segmentar_clientes_kmeans()", "ml_analytics_service.py (Clustering RFM)")
    draw_controller(ax, 0.53, 0.26, "generar_audio_tts_sintesis()", "ml_analytics_service.py (WAV sintetizado)")
    
    draw_entity(ax, 0.86, 0.82, "ModeloMl", "db / modelo_ml (métricas R2 / Silhouette)")
    draw_entity(ax, 0.86, 0.60, "Venta", "db / venta (dataset series de demanda)")
    draw_entity(ax, 0.86, 0.38, "Cliente", "db / cliente (matriz RFM)")
    draw_entity(ax, 0.86, 0.16, "BitacoraAuditoria", "db / bitacora_auditoria (ejecución modelos)")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.74, "GET /api/v1/inteligencia/ml/demanda\n(entrenar y proyectar ventas)")
    draw_call_arrow(ax, 0.355, 0.64, 0.455, 0.50, "GET /api/v1/inteligencia/ml/segmentacion\n(clusters RFM k=3..5)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.26, "POST /api/v1/inteligencia/ml/sintesis-audio\n(texto diagnóstico prescriptivo)")
    
    draw_crud_arrow(ax, 0.605, 0.76, 0.795, 0.82, "GET / PUT", "leer y actualizar métricas r2_score y MAE", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.72, 0.795, 0.62, "GET", "extraer dataset histórico de ventas por categoría", rad=-0.04, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.50, 0.795, 0.40, "GET", "recuperar variables recencia, frecuencia y monto", rad=-0.02, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.24, 0.795, 0.18, "POST", "auditar generación y consumo de audio TTS", rad=0.04, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Tablero prescriptivo con modelos scikit-learn (supervisado y no supervisado) y síntesis de voz ejecutiva.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu35_dashboard_analitico_ml.png")
    svg_path = os.path.join(output_dir, "cu35_dashboard_analitico_ml.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# CU-36
# -------------------------------------------------------------
def generate_cu36(output_dir):
    fig, ax = setup_canvas(
        "DIAGRAMA DE ROBUSTEZ - CU-36: VESTIDOR VIRTUAL CON REALIDAD AUMENTADA (RA)",
        "Boundaries: VestidorVirtualComponent, CamaraArCanvasView | Controllers: listar_prendas_ar(), obtener_o_crear_avatar(), iniciar_sesion_prueba(), finalizar_sesion_prueba() | Entities: PrendaAr, AvatarCliente, MedidaCorporal, SesionPruebaVirtual",
        width=16, height=10
    )
    draw_actor(ax, 0.09, 0.50, "Cliente Web / Móvil", "Comprador Digital")
    
    draw_boundary(ax, 0.28, 0.68, "VestidorVirtualComponent", "vestidor-virtual.html (Selector Prenda/Talla/Color)")
    draw_boundary(ax, 0.28, 0.32, "CamaraArCanvasView", "videoElement + arCanvas (Superposición RA)")
    
    draw_controller(ax, 0.53, 0.74, "listar_prendas_ar()", "vestidor_ar_service.py")
    draw_controller(ax, 0.53, 0.50, "obtener_o_crear_avatar()", "vestidor_ar_service.py")
    draw_controller(ax, 0.53, 0.26, "iniciar_sesion_prueba()", "vestidor_ar_service.py (Gestión Sesión RA)")
    
    draw_entity(ax, 0.86, 0.82, "PrendaAr", "db / prenda_ar (modelo 3D .glb, anclajes)")
    draw_entity(ax, 0.86, 0.60, "AvatarCliente", "db / avatar_cliente (altura, peso, piel)")
    draw_entity(ax, 0.86, 0.38, "MedidaCorporal", "db / medida_corporal (busto, cintura)")
    draw_entity(ax, 0.86, 0.16, "SesionPruebaVirtual", "db / sesion_prueba_virtual (resultado_url)")
    
    draw_actor_link(ax, 0.15, 0.53, 0.205, 0.68)
    draw_actor_link(ax, 0.15, 0.47, 0.205, 0.32)
    
    draw_call_arrow(ax, 0.355, 0.72, 0.455, 0.74, "GET /api/v1/vestidor/prendas\n(catálogo con modelos 3D / RA)")
    draw_call_arrow(ax, 0.355, 0.64, 0.455, 0.50, "GET /api/v1/vestidor/avatar\n(perfil anatómico del usuario)")
    draw_call_arrow(ax, 0.355, 0.32, 0.455, 0.26, "POST /api/v1/vestidor/sesiones\n(prenda_id, variante_id, avatar_id)")
    
    draw_crud_arrow(ax, 0.605, 0.76, 0.795, 0.82, "GET", "recuperar modelo 3D GLB y puntos de ajuste", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.52, 0.795, 0.62, "GET / POST", "obtener o registrar avatar 3D del usuario", rad=-0.03, offset_y=0.02)
    draw_crud_arrow(ax, 0.605, 0.48, 0.795, 0.40, "GET", "leer medidas anatómicas (busto, cintura, hombro)", rad=0.02, offset_y=-0.02)
    draw_crud_arrow(ax, 0.605, 0.26, 0.795, 0.18, "POST / PUT", "iniciar y finalizar sesión guardando captura", rad=0.04, offset_y=-0.025)
    
    ax.text(
        0.50, 0.05,
        "Nota ICONIX: Probador virtual con WebRTC / AR Canvas, superposición geométrica en tiempo real y persistencia biométrica.",
        fontsize=8.5, ha='center', va='center', style='italic', color=COLORS['subtext'],
        bbox=dict(boxstyle="round,pad=0.3", fc="#F1F5F9", ec="#CBD5E1", lw=1)
    )
    png_path = os.path.join(output_dir, "cu36_vestidor_virtual_ra.png")
    svg_path = os.path.join(output_dir, "cu36_vestidor_virtual_ra.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

# -------------------------------------------------------------
# Master Consolidated Diagram (CU-01 a CU-05)
# -------------------------------------------------------------
def generate_consolidado(output_dir):
    fig, ax = plt.subplots(figsize=(20, 16), dpi=300)
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Header
    ax.text(0.5, 0.98, "DIAGRAMA DE ROBUSTEZ INTEGRADO: CASOS DE USO CU-01 A CU-05", fontsize=18, fontweight='bold', ha='center', va='top', color=COLORS['text'])
    ax.text(0.5, 0.955, "FashionStore SaaS: Arquitectura ICONIX completa con Boundaries, Controllers, Entities y Métodos CRUD", fontsize=11, ha='center', va='top', color=COLORS['subtext'])
    
    # Legend
    legend_items = [
        ('Actor (Línea simple)', COLORS['actor_fill'], COLORS['actor_edge']),
        ('Boundary (Vista)', COLORS['boundary_fill'], COLORS['boundary_edge']),
        ('Controller (Función)', COLORS['controller_fill'], COLORS['controller_edge']),
        ('Entity (Modelo BD)', COLORS['entity_fill'], COLORS['entity_edge']),
    ]
    x_leg = 0.15
    for label, fill, edge in legend_items:
        patch = patches.FancyBboxPatch(
            (x_leg, 0.015), 0.15, 0.025,
            boxstyle="round,pad=0.008,rounding_size=0.01",
            facecolor=fill, edgecolor=edge, linewidth=1.5
        )
        ax.add_patch(patch)
        ax.text(x_leg + 0.075, 0.0275, label, fontsize=8.5, ha='center', va='center', fontweight='bold', color=COLORS['text'])
        x_leg += 0.18

    # ACTORS (Left column, x=0.07)
    draw_actor(ax, 0.07, 0.85, "Usuario", "CU-01 (Login)")
    draw_actor(ax, 0.07, 0.67, "Cliente", "CU-02 (Registro)")
    draw_actor(ax, 0.07, 0.49, "Usuario Auth", "CU-03 (Perfil)")
    draw_actor(ax, 0.07, 0.31, "Usuario Auth", "CU-04 (Logout)")
    draw_actor(ax, 0.07, 0.13, "Sistema / Actor", "CU-05 (Auditoría)")
    
    # BOUNDARIES (Col 2, x=0.25)
    draw_boundary(ax, 0.25, 0.85, "LoginComponent", "login.component.html")
    draw_boundary(ax, 0.25, 0.72, "RegisterComponent", "register.component.html")
    draw_boundary(ax, 0.25, 0.62, "VerifyEmailComponent", "verify-email.html")
    draw_boundary(ax, 0.25, 0.49, "ProfileComponent", "profile.component.html")
    draw_boundary(ax, 0.25, 0.36, "Navbar / Profile", "Acción Logout")
    draw_boundary(ax, 0.25, 0.26, "AuthInterceptor", "Interceptor Refresco")
    draw_boundary(ax, 0.25, 0.13, "HttpRequestBoundary", "Vistas Cliente / HTTP")
    
    # CONTROLLERS (Col 3, x=0.50)
    draw_controller(ax, 0.50, 0.85, "login()", "auth_service.py")
    draw_controller(ax, 0.50, 0.72, "register()", "auth_service.py")
    draw_controller(ax, 0.50, 0.62, "verify_email()", "auth_service.py")
    draw_controller(ax, 0.50, 0.53, "get_me()", "auth_service.py")
    draw_controller(ax, 0.50, 0.47, "update_me()", "auth_service.py")
    draw_controller(ax, 0.50, 0.41, "change_password()", "auth_service.py")
    draw_controller(ax, 0.50, 0.33, "logout()", "auth_service.py")
    draw_controller(ax, 0.50, 0.25, "refresh()", "auth_service.py")
    draw_controller(ax, 0.50, 0.13, "audit_middleware()", "audit.py")
    
    # ENTITIES (Col 4, x=0.88)
    draw_entity(ax, 0.88, 0.90, "Empresa", "db / empresa")
    draw_entity(ax, 0.88, 0.78, "Suscripcion", "db / suscripcion")
    draw_entity(ax, 0.88, 0.66, "Rol", "db / rol")
    draw_entity(ax, 0.88, 0.54, "Usuario", "db / usuario")
    draw_entity(ax, 0.88, 0.42, "VerificacionCorreo", "db / verificacion")
    draw_entity(ax, 0.88, 0.30, "Sesion", "db / sesion")
    draw_entity(ax, 0.88, 0.15, "BitacoraAuditoria", "db / bitacora")
    
    # ACTOR -> BOUNDARY LINKS (No labels)
    draw_actor_link(ax, 0.13, 0.85, 0.175, 0.85)
    draw_actor_link(ax, 0.13, 0.68, 0.175, 0.72)
    draw_actor_link(ax, 0.13, 0.66, 0.175, 0.62)
    draw_actor_link(ax, 0.13, 0.49, 0.175, 0.49)
    draw_actor_link(ax, 0.13, 0.32, 0.175, 0.36)
    draw_actor_link(ax, 0.13, 0.30, 0.175, 0.26)
    draw_actor_link(ax, 0.13, 0.13, 0.175, 0.13)
    
    # BOUNDARY -> CONTROLLER ARROWS
    draw_call_arrow(ax, 0.325, 0.85, 0.425, 0.85, "POST /api/v1/auth/login")
    draw_call_arrow(ax, 0.325, 0.72, 0.425, 0.72, "POST /api/v1/auth/register")
    draw_call_arrow(ax, 0.325, 0.62, 0.425, 0.62, "POST /api/v1/auth/verify-email")
    draw_call_arrow(ax, 0.325, 0.51, 0.425, 0.53, "GET /api/v1/users/me")
    draw_call_arrow(ax, 0.325, 0.49, 0.425, 0.47, "PATCH /api/v1/users/me")
    draw_call_arrow(ax, 0.325, 0.47, 0.425, 0.41, "POST /api/v1/users/me/password")
    draw_call_arrow(ax, 0.325, 0.36, 0.425, 0.33, "POST /api/v1/auth/logout")
    draw_call_arrow(ax, 0.325, 0.26, 0.425, 0.25, "POST /api/v1/auth/refresh")
    draw_call_arrow(ax, 0.325, 0.13, 0.425, 0.13, "despacharRequest() (HTTP)")
    
    # CONTROLLER -> ENTITY ARROWS (CRUD)
    # login
    draw_crud_arrow(ax, 0.575, 0.86, 0.815, 0.90, "GET", "empresa", rad=-0.05, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.85, 0.815, 0.79, "GET", "suscripcion", rad=-0.03, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.84, 0.815, 0.57, "GET", "usuario / clave", rad=-0.02, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.83, 0.815, 0.32, "POST", "crear sesión", rad=0.05, offset_y=-0.015)
    draw_crud_arrow(ax, 0.575, 0.82, 0.815, 0.18, "POST", "auditar", rad=0.09, offset_y=-0.015)
    
    # register & verify
    draw_crud_arrow(ax, 0.575, 0.72, 0.815, 0.67, "GET", "rol cliente", rad=-0.02, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.71, 0.815, 0.55, "POST", "crear usuario", rad=0.02, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.70, 0.815, 0.44, "POST", "token verificacion", rad=0.04, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.62, 0.815, 0.53, "PATCH", "activar usuario", rad=-0.04, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.61, 0.815, 0.41, "DELETE", "invalidar token", rad=0.02, offset_y=-0.015)
    
    # profile
    draw_crud_arrow(ax, 0.575, 0.53, 0.815, 0.54, "GET", "leer usuario", rad=0.0, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.47, 0.815, 0.52, "PUT / PATCH", "actualizar datos", rad=-0.02, offset_y=-0.015)
    draw_crud_arrow(ax, 0.575, 0.41, 0.815, 0.50, "PATCH", "nueva clave", rad=-0.04, offset_y=-0.015)
    draw_crud_arrow(ax, 0.575, 0.40, 0.815, 0.31, "DELETE", "revocar otras sesiones", rad=0.02, offset_y=0.015)
    
    # logout & refresh
    draw_crud_arrow(ax, 0.575, 0.33, 0.815, 0.30, "DELETE", "revocar sesion", rad=0.0, offset_y=0.015)
    draw_crud_arrow(ax, 0.575, 0.26, 0.815, 0.29, "PUT / PATCH", "rotar token sesion", rad=0.02, offset_y=-0.015)
    draw_crud_arrow(ax, 0.575, 0.24, 0.815, 0.16, "POST", "auditar refresh", rad=0.03, offset_y=-0.015)
    
    # audit
    draw_crud_arrow(ax, 0.575, 0.14, 0.815, 0.52, "GET", "contexto jwt", rad=-0.08, offset_y=0.02)
    draw_crud_arrow(ax, 0.575, 0.12, 0.815, 0.14, "POST", "insertar auditoría HTTP (GET, POST, PUT, DELETE)", rad=0.0, offset_y=-0.015)
    
    png_path = os.path.join(output_dir, "cu01_cu05_consolidado.png")
    svg_path = os.path.join(output_dir, "cu01_cu05_consolidado.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {png_path}")

if __name__ == '__main__':
    out_dir = os.path.join(os.getcwd(), 'docs', 'diagramas')
    os.makedirs(out_dir, exist_ok=True)
    generate_cu01(out_dir)
    generate_cu02(out_dir)
    generate_cu03(out_dir)
    generate_cu04(out_dir)
    generate_cu05(out_dir)
    generate_cu17(out_dir)
    generate_cu18(out_dir)
    generate_cu19(out_dir)
    generate_cu20(out_dir)
    generate_cu21(out_dir)
    generate_cu22(out_dir)
    generate_cu23(out_dir)
    generate_cu24(out_dir)
    generate_cu25(out_dir)
    generate_cu26(out_dir)
    generate_cu27(out_dir)
    generate_cu28(out_dir)
    generate_cu29(out_dir)
    generate_cu30(out_dir)
    generate_cu31(out_dir)
    generate_cu32(out_dir)
    generate_cu33(out_dir)
    generate_cu34(out_dir)
    generate_cu35(out_dir)
    generate_cu36(out_dir)
    generate_consolidado(out_dir)
    print("All diagrams generated successfully!")
