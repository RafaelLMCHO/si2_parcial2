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
    generate_consolidado(out_dir)
    print("All diagrams generated successfully!")
