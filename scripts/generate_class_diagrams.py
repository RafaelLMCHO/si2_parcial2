import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Color palette for UML Class Diagrams
PALETTE = {
    'bg': '#FFFFFF',
    'title': '#0F172A',
    'subtitle': '#475569',
    'border_dark': '#1E293B',
    'line': '#334155',
    'line_dep': '#64748B',
    
    # Stereotype color themes
    'boundary': {
        'header_fill': '#BAE6FD',
        'body_fill': '#F0F9FF',
        'border': '#0284C7',
        'tag_color': '#0369A1'
    },
    'control': {
        'header_fill': '#BBF7D0',
        'body_fill': '#F0FDF4',
        'border': '#16A34A',
        'tag_color': '#15803D'
    },
    'entity': {
        'header_fill': '#FED7AA',
        'body_fill': '#FFFBEB',
        'border': '#D97706',
        'tag_color': '#B45309'
    },
    'dto': {
        'header_fill': '#E9D5FF',
        'body_fill': '#FAF5FF',
        'border': '#9333EA',
        'tag_color': '#7E22CE'
    }
}


class UMLClassDiagram:
    def __init__(self, title, subtitle, width=20, height=14):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=300)
        self.fig.patch.set_facecolor(PALETTE['bg'])
        self.ax.set_facecolor(PALETTE['bg'])
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        
        # Header banner
        self.ax.text(0.5, 0.975, title, fontsize=15, fontweight='bold', ha='center', va='top', color=PALETTE['title'])
        self.ax.text(0.5, 0.950, subtitle, fontsize=9.2, ha='center', va='top', color=PALETTE['subtitle'])
        
        self.classes = {}

    def add_class(self, key, x, y_top, w, name, stereotype, attributes, methods, table=""):
        """
        Draws a standardized 3-compartment UML Class.
        (x, y_top) specifies the horizontal center and top edge of the class.
        """
        theme = PALETTE.get(stereotype, PALETTE['entity'])
        
        line_h = 0.016
        header_h = 0.048 if table else 0.038
        attr_h = max(0.025, len(attributes) * line_h + 0.014)
        method_h = max(0.025, len(methods) * line_h + 0.014)
        total_h = header_h + attr_h + method_h
        
        y_bottom = y_top - total_h
        x_left = x - w / 2
        x_right = x + w / 2
        
        self.classes[key] = {
            'x': x, 'y_top': y_top, 'y_bottom': y_bottom,
            'x_left': x_left, 'x_right': x_right,
            'w': w, 'h': total_h,
            'center_y': y_top - total_h / 2
        }
        
        # 1. Outer Box & Background
        outer_rect = patches.FancyBboxPatch(
            (x_left, y_bottom), w, total_h,
            boxstyle="round,pad=0.003,rounding_size=0.008",
            facecolor=theme['body_fill'], edgecolor=theme['border'],
            linewidth=1.5, zorder=2
        )
        self.ax.add_patch(outer_rect)
        
        # 2. Header Compartment Fill
        header_rect = patches.FancyBboxPatch(
            (x_left, y_top - header_h), w, header_h,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            facecolor=theme['header_fill'], edgecolor=theme['border'],
            linewidth=1.2, zorder=3
        )
        self.ax.add_patch(header_rect)
        
        # Header Text
        st_label = f"«{stereotype}»"
        self.ax.text(x, y_top - 0.010, st_label, fontsize=7.2, fontweight='bold', ha='center', va='center', color=theme['tag_color'], zorder=4)
        self.ax.text(x, y_top - 0.023, name, fontsize=8.8, fontweight='bold', ha='center', va='center', color=PALETTE['title'], zorder=4)
        if table:
            self.ax.text(x, y_top - 0.037, f"[Tabla: {table}]", fontsize=6.8, fontstyle='italic', ha='center', va='center', color=PALETTE['subtitle'], zorder=4)
            
        # Divider 1: Header - Attributes
        div1_y = y_top - header_h
        self.ax.plot([x_left, x_right], [div1_y, div1_y], color=theme['border'], linewidth=1.2, zorder=4)
        
        # Divider 2: Attributes - Methods
        div2_y = div1_y - attr_h
        self.ax.plot([x_left, x_right], [div2_y, div2_y], color=theme['border'], linewidth=1.2, zorder=4)
        
        # 3. Attributes Text (Mantenidos con esquema BD)
        curr_y = div1_y - 0.012
        for attr in attributes:
            self.ax.text(x_left + 0.008, curr_y, attr, fontsize=6.8, ha='left', va='center', fontfamily='monospace', color='#1E293B', zorder=4)
            curr_y -= line_h
            
        # 4. Methods Text (En Inglés)
        curr_y = div2_y - 0.012
        for meth in methods:
            self.ax.text(x_left + 0.008, curr_y, meth, fontsize=6.8, ha='left', va='center', fontfamily='monospace', color='#0F172A', zorder=4)
            curr_y -= line_h

    def add_connector(self, k1, k2, side1='right', side2='left', label="", mult1="", mult2="",
                      is_dep=False, is_comp=False, rad=0.0):
        c1 = self.classes[k1]
        c2 = self.classes[k2]
        
        if side1 == 'right': p1 = (c1['x_right'], c1['center_y'])
        elif side1 == 'left': p1 = (c1['x_left'], c1['center_y'])
        elif side1 == 'top': p1 = (c1['x'], c1['y_top'])
        else: p1 = (c1['x'], c1['y_bottom'])
        
        if side2 == 'right': p2 = (c2['x_right'], c2['center_y'])
        elif side2 == 'left': p2 = (c2['x_left'], c2['center_y'])
        elif side2 == 'top': p2 = (c2['x'], c2['y_top'])
        else: p2 = (c2['x'], c2['y_bottom'])
        
        ls = '--' if is_dep else '-'
        arrow = '->' if is_dep else '-'
        color = PALETTE['line_dep'] if is_dep else PALETTE['line']
        
        self.ax.annotate(
            "", xy=p2, xytext=p1,
            arrowprops=dict(
                arrowstyle=arrow,
                color=color,
                linestyle=ls,
                lw=1.3,
                connectionstyle=f"arc3,rad={rad}"
            ),
            zorder=1
        )
        
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2 + (rad * 0.1)
        if label:
            self.ax.text(
                mx, my + 0.008, label, fontsize=6.8, fontweight='bold', ha='center', va='center',
                color='#1E293B', zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", fc="#FFFFFF", ec="#CBD5E1", lw=0.8, alpha=0.92)
            )
            
        if mult1:
            dx = 0.012 if side1 == 'right' else (-0.012 if side1 == 'left' else 0)
            dy = 0.010 if side1 == 'top' else (-0.010 if side1 == 'bottom' else 0.008)
            self.ax.text(p1[0] + dx, p1[1] + dy, mult1, fontsize=7.2, fontweight='bold', color='#334155', zorder=5)
            
        if mult2:
            dx = -0.012 if side2 == 'right' else (0.012 if side2 == 'left' else 0)
            dy = 0.010 if side2 == 'top' else (-0.010 if side2 == 'bottom' else 0.008)
            self.ax.text(p2[0] + dx, p2[1] + dy, mult2, fontsize=7.2, fontweight='bold', color='#334155', zorder=5)
            
        if is_comp:
            diam = patches.RegularPolygon(
                p1, numVertices=4, radius=0.007, orientation=0.785,
                facecolor=PALETTE['border_dark'], edgecolor=PALETTE['border_dark'], zorder=6
            )
            self.ax.add_patch(diam)

    def add_legend(self, x=0.02, y=0.04):
        box = patches.FancyBboxPatch(
            (x, y), 0.96, 0.038,
            boxstyle="round,pad=0.004,rounding_size=0.006",
            facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.0, zorder=2
        )
        self.ax.add_patch(box)
        
        items = [
            ("«boundary» UI / Frontend", PALETTE['boundary']['header_fill'], PALETTE['boundary']['border']),
            ("«control» Lógica / Servicio API", PALETTE['control']['header_fill'], PALETTE['control']['border']),
            ("«entity» Modelo / Tabla PostgreSQL", PALETTE['entity']['header_fill'], PALETTE['entity']['border']),
            ("«dto» Schema Request / Response", PALETTE['dto']['header_fill'], PALETTE['dto']['border']),
            ("◆ Composición / Asociación BD", "#334155", "#334155"),
            ("---> Dependencia / Invocación", "#64748B", "#64748B")
        ]
        
        step = 0.96 / len(items)
        for i, (txt, fill, border) in enumerate(items):
            ix = x + i * step + 0.012
            iy = y + 0.019
            self.ax.add_patch(patches.Rectangle((ix, iy - 0.007), 0.012, 0.014, fc=fill, ec=border, lw=1))
            self.ax.text(ix + 0.016, iy, txt, fontsize=7.0, ha='left', va='center', color='#1E293B', fontweight='bold')

    def save(self, png_path, svg_path):
        self.fig.savefig(png_path, bbox_inches='tight')
        self.fig.savefig(svg_path, bbox_inches='tight')
        plt.close(self.fig)
        print(f"Generated: {png_path}")


# ========================================================================================
# CU-01: Iniciar Sesión (Login)
# ========================================================================================
def generate_clases_cu01(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-01: INICIAR SESIÓN (LOGIN)",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'login_ui', x=0.12, y_top=0.91, w=0.19,
        name='LoginComponent', stereotype='boundary',
        attributes=[
            '- empresa_slug: string = ""',
            '- correo: string = ""',
            '- password: string = ""',
            '- rememberMe: boolean = false',
            '- loading: boolean = false',
            '- errorMessage: string = ""'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ onSubmit(): Promise<void>',
            '+ redirectTo(route: string): void',
            '+ showError(message: string): void',
            '+ resetForm(): void'
        ]
    )
    d.add_class(
        'auth_ctrl', x=0.38, y_top=0.91, w=0.23,
        name='AuthService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- secret_key: str',
            '- access_token_expire: int = 30',
            '- refresh_token_expire: int = 7'
        ],
        methods=[
            '+ login(data: LoginRequest, ip): LoginResponse',
            '+ verifyPassword(plain, hashed): bool',
            '+ createAccessToken(data: dict): str',
            '+ createRefreshToken(data: dict): str',
            '+ hashToken(token: str): str'
        ]
    )
    d.add_class(
        'login_req', x=0.12, y_top=0.62, w=0.19,
        name='LoginRequest', stereotype='dto',
        attributes=[
            '+ empresa_slug: str | None',
            '+ correo: EmailStr',
            '+ password: str'
        ],
        methods=[]
    )
    d.add_class(
        'login_res', x=0.12, y_top=0.45, w=0.19,
        name='LoginResponse', stereotype='dto',
        attributes=[
            '+ access_token: str',
            '+ refresh_token: str',
            '+ token_type: str = "bearer"',
            '+ user: UserOut'
        ],
        methods=[]
    )
    d.add_class(
        'empresa', x=0.67, y_top=0.91, w=0.22,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ slug: citext [UNIQUE]',
            '+ nit: varchar(20) [UNIQUE]',
            '+ correo: citext',
            '+ estado: varchar(20)',
            '+ created_at: timestamptz'
        ],
        methods=[
            '+ findBySlug(slug: str): Empresa',
            '+ isActive(): bool'
        ]
    )
    d.add_class(
        'suscrip', x=0.90, y_top=0.91, w=0.17,
        name='Suscripcion', stereotype='entity', table='suscripcion',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# plan_id: smallint [FK]',
            '+ estado: varchar(20)',
            '+ fecha_inicio: date',
            '+ fecha_fin: date'
        ],
        methods=[
            '+ isValid(): bool',
            '+ getActiveByCompany(emp_id): Suscrip'
        ]
    )
    d.add_class(
        'rol', x=0.38, y_top=0.60, w=0.21,
        name='Rol', stereotype='entity', table='rol',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(50)',
            '+ descripcion: text',
            '+ es_global: boolean'
        ],
        methods=[
            '+ findById(rol_id): Rol',
            '+ getPermissions(): list[str]'
        ]
    )
    d.add_class(
        'usuario', x=0.67, y_top=0.60, w=0.22,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# rol_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ correo: citext',
            '- password_hash: text',
            '+ email_verificado: boolean',
            '+ estado: varchar(20)',
            '+ ultimo_acceso: timestamptz'
        ],
        methods=[
            '+ findByEmail(correo, slug): Usuario',
            '+ updateLastAccess(id): void',
            '+ isActive(): bool'
        ]
    )
    d.add_class(
        'sesion', x=0.67, y_top=0.24, w=0.22,
        name='Sesion', stereotype='entity', table='sesion',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '- refresh_token_hash: text [UNIQUE]',
            '+ ip_origen: inet',
            '+ expira_en: timestamptz',
            '+ revocado_en: timestamptz'
        ],
        methods=[
            '+ createSession(user_id, hash, exp): Sesion',
            '+ isValid(): bool',
            '+ revokeSession(id): void'
        ]
    )
    d.add_class(
        'audit', x=0.38, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ actor_tipo: varchar(20)',
            '+ accion: varchar(20) = "login"',
            '+ entidad: varchar(60)',
            '+ datos_despues: jsonb',
            '+ ip: inet',
            '+ ocurrido_en: timestamptz'
        ],
        methods=[
            '+ logLoginSuccess(user_id, ip): void',
            '+ logLoginFailure(correo, ip): void'
        ]
    )
    
    d.add_connector('login_ui', 'auth_ctrl', side1='right', side2='left', label="«invokes» POST /login", is_dep=True)
    d.add_connector('login_ui', 'login_req', side1='bottom', side2='top', label="«submits»", is_dep=True)
    d.add_connector('auth_ctrl', 'login_res', side1='bottom', side2='right', label="«returns»", is_dep=True)
    d.add_connector('auth_ctrl', 'empresa', side1='right', side2='left', label="«queries slug»", is_dep=True)
    d.add_connector('auth_ctrl', 'usuario', side1='right', side2='left', label="«validates / updates»", is_dep=True)
    d.add_connector('auth_ctrl', 'sesion', side1='bottom', side2='left', label="«creates session»", is_dep=True, rad=-0.1)
    d.add_connector('auth_ctrl', 'audit', side1='bottom', side2='top', label="«logs login»", is_dep=True)
    
    d.add_connector('empresa', 'suscrip', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'usuario', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('rol', 'usuario', side1='right', side2='left', mult1="1", mult2="0..*")
    d.add_connector('usuario', 'sesion', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('usuario', 'audit', side1='bottom', side2='right', mult1="1", mult2="0..*", rad=0.08)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu01_iniciar_sesion.png")
    svg_path = os.path.join(output_dir, "clases_cu01_iniciar_sesion.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-02: Registrarse y Verificar Correo
# ========================================================================================
def generate_clases_cu02(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-02: REGISTRARSE Y VERIFICAR CORREO",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'reg_ui', x=0.12, y_top=0.91, w=0.19,
        name='RegisterComponent', stereotype='boundary',
        attributes=[
            '- empresa_slug: string = ""',
            '- nombre: string = ""',
            '- correo: string = ""',
            '- telefono: string = ""',
            '- password: string = ""',
            '- confirmPassword: string = ""',
            '- loading: boolean = false',
            '- mensaje: string = ""'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ onSubmit(): Promise<void>',
            '+ validatePassword(): boolean',
            '+ navigateToVerification(): void'
        ]
    )
    d.add_class(
        'ver_ui', x=0.12, y_top=0.51, w=0.19,
        name='VerifyEmailComponent', stereotype='boundary',
        attributes=[
            '- token: string = ""',
            '- empresa_slug: string = ""',
            '- loading: boolean = false',
            '- verificado: boolean = false',
            '- error: string = ""'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ verifyToken(): Promise<void>',
            '+ redirectToLogin(): void'
        ]
    )
    d.add_class(
        'auth_ctrl', x=0.38, y_top=0.91, w=0.23,
        name='AuthService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- token_expire_hours: int = 24'
        ],
        methods=[
            '+ register(data: RegisterRequest): RegisterResponse',
            '+ verifyEmail(data: VerifyEmailRequest): VerifyEmailResponse',
            '+ generateToken(): str',
            '+ hashToken(token: str): str',
            '+ sendVerificationEmail(email, token): void'
        ]
    )
    d.add_class(
        'reg_req', x=0.12, y_top=0.25, w=0.19,
        name='RegisterRequest', stereotype='dto',
        attributes=[
            '+ empresa_slug: str',
            '+ nombre: str',
            '+ correo: EmailStr',
            '+ password: str',
            '+ telefono: str | None'
        ],
        methods=[]
    )
    d.add_class(
        'ver_req', x=0.38, y_top=0.25, w=0.21,
        name='VerifyEmailRequest', stereotype='dto',
        attributes=[
            '+ token: str',
            '+ empresa_slug: str'
        ],
        methods=[]
    )
    d.add_class(
        'empresa', x=0.67, y_top=0.91, w=0.22,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ slug: citext [UNIQUE]',
            '+ nit: varchar(20) [UNIQUE]',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ validateExistenceBySlug(slug): bool',
            '+ isActive(): bool'
        ]
    )
    d.add_class(
        'rol', x=0.91, y_top=0.91, w=0.16,
        name='Rol', stereotype='entity', table='rol',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(50) = "cliente"',
            '+ es_global: boolean'
        ],
        methods=[
            '+ getClientRole(emp_id): Rol'
        ]
    )
    d.add_class(
        'usuario', x=0.67, y_top=0.60, w=0.22,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# rol_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ correo: citext',
            '- password_hash: text',
            '+ email_verificado: boolean = false',
            '+ email_verificado_en: timestamptz',
            '+ estado: varchar(20) = "activo"'
        ],
        methods=[
            '+ emailExists(correo, emp_id): bool',
            '+ createInactiveUser(data): Usuario',
            '+ activateEmail(user_id): void'
        ]
    )
    d.add_class(
        'token_ent', x=0.91, y_top=0.60, w=0.17,
        name='VerificacionCorreo', stereotype='entity', table='verificacion_correo',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '- token_hash: text [UNIQUE]',
            '+ expira_en: timestamptz',
            '+ verificado_en: timestamptz',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ createToken(user_id, hash, exp): Verif',
            '+ validateActiveToken(hash): Verif',
            '+ markAsConsumed(id): void'
        ]
    )
    d.add_class(
        'audit', x=0.67, y_top=0.22, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20)',
            '+ entidad: varchar(60)',
            '+ datos_despues: jsonb',
            '+ ip: inet',
            '+ ocurrido_en: timestamptz'
        ],
        methods=[
            '+ logUserRegistration(user_id): void',
            '+ logEmailVerification(user_id): void'
        ]
    )
    
    d.add_connector('reg_ui', 'auth_ctrl', side1='right', side2='left', label="«invokes» POST /register", is_dep=True)
    d.add_connector('ver_ui', 'auth_ctrl', side1='right', side2='bottom', label="«invokes» POST /verify-email", is_dep=True, rad=0.08)
    d.add_connector('reg_ui', 'reg_req', side1='bottom', side2='top', label="«submits»", is_dep=True)
    d.add_connector('ver_ui', 'ver_req', side1='bottom', side2='left', label="«submits»", is_dep=True, rad=-0.05)
    
    d.add_connector('auth_ctrl', 'empresa', side1='right', side2='left', label="«validates tenant»", is_dep=True)
    d.add_connector('auth_ctrl', 'usuario', side1='right', side2='left', label="«creates / activates»", is_dep=True)
    d.add_connector('auth_ctrl', 'token_ent', side1='bottom', side2='left', label="«generates / consumes»", is_dep=True, rad=-0.08)
    d.add_connector('auth_ctrl', 'audit', side1='bottom', side2='left', label="«logs events»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'rol', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'usuario', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('rol', 'usuario', side1='bottom', side2='right', mult1="1", mult2="0..*", rad=0.06)
    d.add_connector('usuario', 'token_ent', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('usuario', 'audit', side1='bottom', side2='top', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu02_registrarse.png")
    svg_path = os.path.join(output_dir, "clases_cu02_registrarse.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-03: Gestionar Perfil y Cambio de Contraseña
# ========================================================================================
def generate_clases_cu03(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-03: GESTIONAR PERFIL Y CAMBIO DE CONTRASEÑA",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'profile_ui', x=0.12, y_top=0.91, w=0.19,
        name='ProfileComponent', stereotype='boundary',
        attributes=[
            '- nombre: string = ""',
            '- telefono: string = ""',
            '- passwordActual: string = ""',
            '- nuevaPassword: string = ""',
            '- loading: boolean = false',
            '- mensaje: string = ""'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadProfile(): Promise<void>',
            '+ updateProfile(): Promise<void>',
            '+ changePassword(): Promise<void>',
            '+ showSuccess(msg): void',
            '+ showError(msg): void'
        ]
    )
    d.add_class(
        'auth_ctrl', x=0.38, y_top=0.91, w=0.23,
        name='AuthService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getProfile(user_id): UserOut',
            '+ updateProfile(user_id, data): UserOut',
            '+ changePassword(user_id, data): void',
            '+ verifyPassword(plain, hashed): bool',
            '+ revokeOtherSessions(user_id, cur_sess): void'
        ]
    )
    d.add_class(
        'user_upd_req', x=0.12, y_top=0.55, w=0.19,
        name='UserUpdateRequest', stereotype='dto',
        attributes=[
            '+ nombre: str | None',
            '+ telefono: str | None'
        ],
        methods=[]
    )
    d.add_class(
        'pwd_req', x=0.12, y_top=0.38, w=0.19,
        name='ChangePasswordRequest', stereotype='dto',
        attributes=[
            '+ password_actual: str',
            '+ password_nueva: str'
        ],
        methods=[]
    )
    d.add_class(
        'user_out', x=0.12, y_top=0.21, w=0.19,
        name='UserOut', stereotype='dto',
        attributes=[
            '+ id: str',
            '+ nombre: str',
            '+ correo: str',
            '+ telefono: str | None'
        ],
        methods=[]
    )
    d.add_class(
        'usuario', x=0.68, y_top=0.91, w=0.23,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ correo: citext',
            '- password_hash: text',
            '+ telefono: varchar(20)',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ findById(user_id): Usuario',
            '+ updatePersonalData(nombre, tel): void',
            '+ updatePasswordHash(new_hash): void'
        ]
    )
    d.add_class(
        'sesion', x=0.68, y_top=0.53, w=0.23,
        name='Sesion', stereotype='entity', table='sesion',
        attributes=[
            '+ id: uuid [PK]',
            '# usuario_id: uuid [FK]',
            '+ revocado_en: timestamptz'
        ],
        methods=[
            '+ revokeOtherActiveSessions(user_id, cur_id): void',
            '+ getActiveSessions(user_id): list'
        ]
    )
    d.add_class(
        'audit', x=0.68, y_top=0.24, w=0.23,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20)',
            '+ entidad: varchar(60)',
            '+ datos_despues: jsonb',
            '+ ocurrido_en: timestamptz'
        ],
        methods=[
            '+ logProfileUpdate(user_id, diff): void',
            '+ logPasswordChange(user_id): void'
        ]
    )
    
    d.add_connector('profile_ui', 'auth_ctrl', side1='right', side2='left', label="«calls»", is_dep=True)
    d.add_connector('profile_ui', 'user_upd_req', side1='bottom', side2='top', is_dep=True)
    d.add_connector('auth_ctrl', 'usuario', side1='right', side2='left', label="«queries / updates»", is_dep=True)
    d.add_connector('auth_ctrl', 'sesion', side1='bottom', side2='left', label="«revokes concurrent»", is_dep=True, rad=-0.08)
    d.add_connector('auth_ctrl', 'audit', side1='bottom', side2='left', label="«logs changes»", is_dep=True, rad=-0.12)
    
    d.add_connector('usuario', 'sesion', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('usuario', 'audit', side1='bottom', side2='right', mult1="1", mult2="0..*", rad=0.08)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu03_gestionar_perfil.png")
    svg_path = os.path.join(output_dir, "clases_cu03_gestionar_perfil.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-04: Cerrar Sesión y Refresco de Tokens
# ========================================================================================
def generate_clases_cu04(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-04: CERRAR SESIÓN Y REFRESCO DE TOKENS",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'nav_ui', x=0.13, y_top=0.91, w=0.20,
        name='NavbarComponent', stereotype='boundary',
        attributes=[
            '- currentUser: UserOut | None'
        ],
        methods=[
            '+ onLogout(): Promise<void>',
            '+ clearLocalStorage(): void',
            '+ redirectToLogin(): void'
        ]
    )
    d.add_class(
        'int_ui', x=0.13, y_top=0.64, w=0.20,
        name='AuthInterceptor', stereotype='boundary',
        attributes=[
            '- isRefreshing: boolean = false'
        ],
        methods=[
            '+ intercept(req, next): Observable',
            '+ handle401Error(req, next): Observable',
            '+ refreshToken(): Promise<string>',
            '+ retryRequest(req): Observable'
        ]
    )
    d.add_class(
        'ref_req', x=0.13, y_top=0.33, w=0.20,
        name='TokenRefreshRequest', stereotype='dto',
        attributes=[
            '+ refresh_token: str'
        ],
        methods=[]
    )
    d.add_class(
        'auth_ctrl', x=0.40, y_top=0.91, w=0.24,
        name='AuthService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- jwt_secret: str'
        ],
        methods=[
            '+ logout(session_token: str): void',
            '+ refresh(token: str): TokenRefreshResponse',
            '+ validateSession(hash: str): Sesion',
            '+ rotateRefreshToken(session_id): str',
            '+ logAuditEvent(action, user_id): void'
        ]
    )
    d.add_class(
        'sesion', x=0.70, y_top=0.91, w=0.24,
        name='Sesion', stereotype='entity', table='sesion',
        attributes=[
            '+ id: uuid [PK]',
            '# usuario_id: uuid [FK]',
            '- refresh_token_hash: text [UNIQUE]',
            '+ expira_en: timestamptz',
            '+ revocado_en: timestamptz'
        ],
        methods=[
            '+ findActiveByHash(hash): Sesion',
            '+ revokeSession(id): void',
            '+ rotateToken(id, new_hash, new_exp): void'
        ]
    )
    d.add_class(
        'usuario', x=0.70, y_top=0.56, w=0.24,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20)',
            '+ ultimo_acceso: timestamptz'
        ],
        methods=[
            '+ isActive(): bool',
            '+ verifyTenantActive(empresa_id): bool'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.24,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20)',
            '+ ocurrido_en: timestamptz'
        ],
        methods=[
            '+ logLogout(user_id): void',
            '+ logTokenRefresh(user_id): void'
        ]
    )
    
    d.add_connector('nav_ui', 'auth_ctrl', side1='right', side2='left', label="«invokes» POST /logout", is_dep=True)
    d.add_connector('int_ui', 'auth_ctrl', side1='right', side2='bottom', label="«invokes» POST /refresh", is_dep=True, rad=0.08)
    d.add_connector('auth_ctrl', 'sesion', side1='right', side2='left', label="«queries / revokes»", is_dep=True)
    d.add_connector('auth_ctrl', 'usuario', side1='bottom', side2='left', label="«verifies status»", is_dep=True, rad=-0.08)
    d.add_connector('auth_ctrl', 'audit', side1='bottom', side2='left', label="«logs events»", is_dep=True, rad=-0.12)
    
    d.add_connector('usuario', 'sesion', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('usuario', 'audit', side1='bottom', side2='top', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu04_cerrar_sesion.png")
    svg_path = os.path.join(output_dir, "clases_cu04_cerrar_sesion.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-05: Registrar Auditoría del Sistema
# ========================================================================================
def generate_clases_cu05(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-05: REGISTRAR AUDITORÍA DEL SISTEMA",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'http_ui', x=0.13, y_top=0.91, w=0.20,
        name='HttpRequestBoundary', stereotype='boundary',
        attributes=[
            '- method: string',
            '- path: string',
            '- headers: Record<string, string>'
        ],
        methods=[
            '+ dispatchRequest(): Response',
            '+ handleResponse(): void'
        ]
    )
    d.add_class(
        'audit_ctx', x=0.13, y_top=0.60, w=0.20,
        name='AuditContext', stereotype='dto',
        attributes=[
            '+ user_id: str | None',
            '+ empresa_id: str | None',
            '+ role: str | None',
            '+ ip_address: str | None'
        ],
        methods=[]
    )
    d.add_class(
        'audit_mw', x=0.40, y_top=0.91, w=0.24,
        name='AuditMiddleware', stereotype='control',
        attributes=[
            '- excluded_paths: list[str]',
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ auditMiddleware(request, call_next): Response',
            '+ extractClaimsFromJwt(jwt_token): dict',
            '+ redactSensitiveData(payload): dict',
            '+ isExcludedRoute(path): bool'
        ]
    )
    d.add_class(
        'usuario', x=0.70, y_top=0.91, w=0.24,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# rol_id: uuid [FK]',
            '+ correo: citext'
        ],
        methods=[
            '+ findUserContext(user_id): dict',
            '+ getUserRole(user_id): str'
        ]
    )
    d.add_class(
        'empresa', x=0.70, y_top=0.58, w=0.24,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ slug: citext [UNIQUE]',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ findTenantById(id): Empresa'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.25, w=0.24,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ actor_tipo: varchar(20)',
            '+ accion: varchar(20)',
            '+ entidad: varchar(60)',
            '+ datos_despues: jsonb',
            '+ ip: inet',
            '+ ocurrido_en: timestamptz'
        ],
        methods=[
            '+ insertAuditRecord(data: dict): void',
            '+ sanitizePayload(payload: dict): dict'
        ]
    )
    
    d.add_connector('http_ui', 'audit_mw', side1='right', side2='left', label="«intercepts HTTP»", is_dep=True)
    d.add_connector('audit_mw', 'usuario', side1='right', side2='left', label="«resolves claims»", is_dep=True)
    d.add_connector('audit_mw', 'empresa', side1='right', side2='left', label="«identifies tenant»", is_dep=True)
    d.add_connector('audit_mw', 'audit', side1='bottom', side2='left', label="«persists sanitized log»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'usuario', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('usuario', 'audit', side1='bottom', side2='top', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu05_registrar_auditoria.png")
    svg_path = os.path.join(output_dir, "clases_cu05_registrar_auditoria.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-06: Gestión de Planes y Registro de Empresas SaaS
# ========================================================================================
def generate_clases_cu06(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-06: GESTIÓN DE PLANES Y REGISTRO DE EMPRESAS SAAS",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'planes_ui', x=0.13, y_top=0.91, w=0.20,
        name='PlanesSaaSComponent', stereotype='boundary',
        attributes=[
            '- planes: PlanOut[] = []',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadPlans(): Promise<void>',
            '+ openCreateCompanyModal(): void'
        ]
    )
    d.add_class(
        'emp_modal', x=0.13, y_top=0.62, w=0.20,
        name='ModalCrearEmpresa', stereotype='boundary',
        attributes=[
            '- nombre: string = ""',
            '- nit: string = ""',
            '- correo_admin: string = ""',
            '- nombre_admin: string = ""'
        ],
        methods=[
            '+ submitCompany(): Promise<void>',
            '+ validateNit(): boolean',
            '+ showTemporaryCredentials(): void'
        ]
    )
    d.add_class(
        'saas_service', x=0.40, y_top=0.91, w=0.24,
        name='SaaSService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listPlans(): list[PlanOut]',
            '+ createPlan(nombre, precio, lims): dict',
            '+ createEmpresa(data: EmpresaCreateRequest): Response',
            '+ generateUniqueSlug(nombre): str',
            '+ seedTenantRoles(empresa_id): void',
            '+ createTemporaryAdminUser(emp_id, email): dict'
        ]
    )
    d.add_class(
        'plan_ent', x=0.68, y_top=0.91, w=0.21,
        name='PlanSaaS', stereotype='entity', table='plan',
        attributes=[
            '+ id: smallint [PK]',
            '+ codigo: varchar(20) [UNIQUE]',
            '+ nombre: varchar(60)',
            '+ precio_mensual: numeric(12,2)',
            '+ activo: boolean = true'
        ],
        methods=[
            '+ getActivePlans(): list[PlanSaaS]',
            '+ findByCode(code): PlanSaaS'
        ]
    )
    d.add_class(
        'empresa', x=0.68, y_top=0.60, w=0.21,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ slug: citext [UNIQUE]',
            '+ nit: varchar(20) [UNIQUE]',
            '+ estado: varchar(20) = "pendiente_plan"'
        ],
        methods=[
            '+ nitExists(nit): bool',
            '+ insertCompany(data): Empresa'
        ]
    )
    d.add_class(
        'rol', x=0.91, y_top=0.60, w=0.16,
        name='Rol', stereotype='entity', table='rol',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(50)'
        ],
        methods=[
            '+ initializeTenantRoles(emp_id): void'
        ]
    )
    d.add_class(
        'usuario', x=0.68, y_top=0.24, w=0.21,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# rol_id: uuid [FK]',
            '+ correo: citext',
            '- password_hash: text',
            '+ email_verificado: boolean = true'
        ],
        methods=[
            '+ createAdminUser(data): Usuario'
        ]
    )
    d.add_class(
        'audit', x=0.91, y_top=0.24, w=0.16,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_afectada_id: uuid',
            '+ actor_tipo: varchar(20) = "superadmin"'
        ],
        methods=[
            '+ logSuperadminAction(data): void'
        ]
    )
    
    d.add_connector('planes_ui', 'saas_service', side1='right', side2='left', label="«calls» listPlans()", is_dep=True)
    d.add_connector('emp_modal', 'saas_service', side1='right', side2='bottom', label="«calls» createEmpresa()", is_dep=True, rad=0.08)
    d.add_connector('saas_service', 'plan_ent', side1='right', side2='left', label="«queries plans»", is_dep=True)
    d.add_connector('saas_service', 'empresa', side1='right', side2='left', label="«inserts tenant»", is_dep=True)
    d.add_connector('saas_service', 'rol', side1='right', side2='left', label="«seeds roles»", is_dep=True, rad=0.06)
    d.add_connector('saas_service', 'usuario', side1='bottom', side2='left', label="«creates temp admin»", is_dep=True, rad=-0.08)
    d.add_connector('saas_service', 'audit', side1='bottom', side2='left', label="«safe audit»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'rol', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'usuario', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu06_gestion_planes.png")
    svg_path = os.path.join(output_dir, "clases_cu06_gestion_planes.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-07: Suscripciones SaaS y Pagos / Asignación
# ========================================================================================
def generate_clases_cu07(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-07: SUSCRIPCIONES SAAS Y ASIGNACIÓN DE PLANES",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'suscrip_ui', x=0.13, y_top=0.91, w=0.20,
        name='SuscripcionesSaasComponent', stereotype='boundary',
        attributes=[
            '- suscripcionActual: any',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadCurrentSubscription(): Promise<void>',
            '+ openChangePlanModal(): void'
        ]
    )
    d.add_class(
        'modal_plan', x=0.13, y_top=0.62, w=0.20,
        name='ModalAsignarPlan', stereotype='boundary',
        attributes=[
            '- planSeleccionado: string = ""',
            '- renovacionAuto: boolean = true'
        ],
        methods=[
            '+ selectPlan(codigo): void',
            '+ submitSubscriptionChange(): Promise<void>',
            '+ validateBranchLimits(): boolean'
        ]
    )
    d.add_class(
        'saas_ctrl', x=0.40, y_top=0.91, w=0.24,
        name='CU07SuscripcionesController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getSubscription(empresa_id): dict',
            '+ assignSubscription(empresa_id, data): dict',
            '+ validateDowngradeLimits(empresa_id, plan_id): bool',
            '+ activateTenantAccount(empresa_id): void'
        ]
    )
    d.add_class(
        'suscrip', x=0.68, y_top=0.91, w=0.21,
        name='Suscripcion', stereotype='entity', table='suscripcion',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# plan_id: smallint [FK]',
            '+ estado: varchar(20)',
            '+ fecha_inicio: date',
            '+ fecha_fin: date',
            '+ renovacion_auto: boolean'
        ],
        methods=[
            '+ upsertSubscription(data): Suscripcion',
            '+ isSubscriptionActive(): bool'
        ]
    )
    d.add_class(
        'plan', x=0.91, y_top=0.91, w=0.16,
        name='Plan', stereotype='entity', table='plan',
        attributes=[
            '+ id: smallint [PK]',
            '+ codigo: varchar(20) [UNIQUE]',
            '+ precio_mensual: numeric'
        ],
        methods=[
            '+ getPlanLimits(plan_id): dict',
            '+ findByCode(code): Plan'
        ]
    )
    d.add_class(
        'empresa', x=0.68, y_top=0.55, w=0.21,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ updateStatus(empresa_id, new_status): void'
        ]
    )
    d.add_class(
        'sucursal', x=0.91, y_top=0.55, w=0.16,
        name='Sucursal', stereotype='entity', table='sucursal',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ activa: boolean = true'
        ],
        methods=[
            '+ countActiveBranches(empresa_id): int'
        ]
    )
    d.add_class(
        'audit', x=0.68, y_top=0.24, w=0.21,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '+ accion: varchar(20) = "update"'
        ],
        methods=[
            '+ logSubscriptionChange(emp_id, plan): void'
        ]
    )
    
    d.add_connector('suscrip_ui', 'saas_ctrl', side1='right', side2='left', label="«queries sub»", is_dep=True)
    d.add_connector('modal_plan', 'saas_ctrl', side1='right', side2='bottom', label="«assigns plan»", is_dep=True, rad=0.08)
    d.add_connector('saas_ctrl', 'suscrip', side1='right', side2='left', label="«upserts»", is_dep=True)
    d.add_connector('saas_ctrl', 'empresa', side1='right', side2='left', label="«activates»", is_dep=True)
    d.add_connector('saas_ctrl', 'sucursal', side1='bottom', side2='left', label="«checks branch quota»", is_dep=True, rad=-0.08)
    d.add_connector('saas_ctrl', 'audit', side1='bottom', side2='left', label="«audits change»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'suscrip', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('plan', 'suscrip', side1='left', side2='right', mult1="1", mult2="0..*")
    d.add_connector('empresa', 'sucursal', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu07_suscripciones_saas.png")
    svg_path = os.path.join(output_dir, "clases_cu07_suscripciones_saas.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-08: Facturación SaaS e Historial de Facturas
# ========================================================================================
def generate_clases_cu08(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-08: FACTURACIÓN SAAS E HISTORIAL DE FACTURAS",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'fact_ui', x=0.13, y_top=0.91, w=0.20,
        name='FacturacionSaasComponent', stereotype='boundary',
        attributes=[
            '- facturas: FacturaSaasOut[] = []',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ listInvoices(): Promise<void>',
            '+ filterByDate(start, end): void',
            '+ downloadPdf(invoice_id): void'
        ]
    )
    d.add_class(
        'fact_modal', x=0.13, y_top=0.56, w=0.20,
        name='FacturaDetalleModal', stereotype='boundary',
        attributes=[
            '- facturaSeleccionada: any'
        ],
        methods=[
            '+ viewInvoiceDetail(id): void',
            '+ retryPayment(): Promise<void>'
        ]
    )
    d.add_class(
        'fact_ctrl', x=0.40, y_top=0.91, w=0.24,
        name='CU08FacturacionController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listInvoices(empresa_id): list[dict]',
            '+ getInvoiceById(id): dict',
            '+ generateInvoiceReceipt(id): str',
            '+ processStripeWebhook(payload): void'
        ]
    )
    d.add_class(
        'factura', x=0.68, y_top=0.91, w=0.22,
        name='FacturaSaaS', stereotype='entity', table='factura_saas',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ monto: numeric(12,2)',
            '+ moneda: char(3) = "BOB"',
            '+ estado: varchar(20)',
            '+ stripe_invoice_id: varchar(100)',
            '+ pdf_url: text',
            '+ created_at: timestamptz'
        ],
        methods=[
            '+ getCompanyInvoices(emp_id): list',
            '+ updateInvoiceStatus(id, st): void',
            '+ findReceipt(id): FacturaSaaS'
        ]
    )
    d.add_class(
        'empresa', x=0.68, y_top=0.55, w=0.22,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ nit: varchar(20)',
            '+ correo: citext'
        ],
        methods=[
            '+ getBillingInfo(emp_id): dict'
        ]
    )
    d.add_class(
        'suscrip', x=0.91, y_top=0.55, w=0.16,
        name='Suscripcion', stereotype='entity', table='suscripcion',
        attributes=[
            '+ id: uuid [PK]',
            '# plan_id: smallint [FK]'
        ],
        methods=[
            '+ getCurrentPlanPrice(): float'
        ]
    )
    d.add_class(
        'audit', x=0.68, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '+ accion: varchar(20) = "export"'
        ],
        methods=[
            '+ logInvoiceDownload(inv_id): void'
        ]
    )
    
    d.add_connector('fact_ui', 'fact_ctrl', side1='right', side2='left', label="«lists invoices»", is_dep=True)
    d.add_connector('fact_modal', 'fact_ctrl', side1='right', side2='bottom', label="«downloads receipt»", is_dep=True, rad=0.08)
    d.add_connector('fact_ctrl', 'factura', side1='right', side2='left', label="«queries records»", is_dep=True)
    d.add_connector('fact_ctrl', 'empresa', side1='right', side2='left', label="«fetches billing info»", is_dep=True)
    d.add_connector('fact_ctrl', 'audit', side1='bottom', side2='left', label="«logs access»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'factura', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'suscrip', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu08_facturacion_saas.png")
    svg_path = os.path.join(output_dir, "clases_cu08_facturacion_saas.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-09: Métricas Globales SaaS (Superadmin Dashboard)
# ========================================================================================
def generate_clases_cu09(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-09: MÉTRICAS GLOBALES SAAS (DASHBOARD)",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'dash_ui', x=0.13, y_top=0.91, w=0.21,
        name='MetricasDashboardComponent', stereotype='boundary',
        attributes=[
            '- metricsData: MetricasSaaSOut | None',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ loadMetrics(): Promise<void>',
            '+ refreshDashboard(): void',
            '+ exportReport(): void'
        ]
    )
    d.add_class(
        'metrics_dto', x=0.13, y_top=0.55, w=0.21,
        name='MetricasSaaSOut', stereotype='dto',
        attributes=[
            '+ tenants_activos: int',
            '+ usuarios_totales: int',
            '+ sucursales: int',
            '+ mrr: float'
        ],
        methods=[]
    )
    d.add_class(
        'metrics_ctrl', x=0.40, y_top=0.91, w=0.24,
        name='CU09MetricasController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getMetrics(): dict',
            '+ calculateMRR(): float',
            '+ countActiveTenants(): int',
            '+ countTotalUsers(): int',
            '+ countBranches(): int'
        ]
    )
    d.add_class(
        'empresa', x=0.68, y_top=0.91, w=0.21,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20)',
            '+ created_at: timestamptz'
        ],
        methods=[
            '+ countActiveTenants(): int'
        ]
    )
    d.add_class(
        'usuario', x=0.91, y_top=0.91, w=0.16,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ countTotalUsers(): int'
        ]
    )
    d.add_class(
        'sucursal', x=0.68, y_top=0.55, w=0.21,
        name='Sucursal', stereotype='entity', table='sucursal',
        attributes=[
            '+ id: uuid [PK]',
            '+ activa: boolean'
        ],
        methods=[
            '+ countBranches(): int'
        ]
    )
    d.add_class(
        'suscrip', x=0.91, y_top=0.55, w=0.16,
        name='Suscripcion', stereotype='entity', table='suscripcion',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ calculateMRR(): float'
        ]
    )
    d.add_class(
        'plan', x=0.68, y_top=0.24, w=0.21,
        name='Plan', stereotype='entity', table='plan',
        attributes=[
            '+ id: smallint [PK]',
            '+ precio_mensual: numeric'
        ],
        methods=[]
    )
    
    d.add_connector('dash_ui', 'metrics_ctrl', side1='right', side2='left', label="«fetches metrics»", is_dep=True)
    d.add_connector('dash_ui', 'metrics_dto', side1='bottom', side2='top', is_dep=True)
    d.add_connector('metrics_ctrl', 'empresa', side1='right', side2='left', label="«counts tenants»", is_dep=True)
    d.add_connector('metrics_ctrl', 'usuario', side1='right', side2='left', label="«counts users»", is_dep=True, rad=0.06)
    d.add_connector('metrics_ctrl', 'sucursal', side1='bottom', side2='left', label="«counts branches»", is_dep=True, rad=-0.08)
    d.add_connector('metrics_ctrl', 'suscrip', side1='bottom', side2='left', label="«sums active MRR»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'usuario', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'sucursal', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'suscrip', side1='bottom', side2='left', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu09_metricas_saas.png")
    svg_path = os.path.join(output_dir, "clases_cu09_metricas_saas.svg")
    d.save(png_path, svg_path)


# ========================================================================================
# CU-10: Gestión de Empleados, Usuarios y Roles
# ========================================================================================
def generate_clases_cu10(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-10: GESTIÓN DE EMPLEADOS, USUARIOS Y ROLES",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    d.add_class(
        'emp_ui', x=0.13, y_top=0.91, w=0.20,
        name='GestionEmpleadosComponent', stereotype='boundary',
        attributes=[
            '- empleados: EmpleadoOut[] = []',
            '- loading: boolean = false'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ listEmployees(): Promise<void>',
            '+ openCreateModal(): void',
            '+ openEditModal(emp_id): void',
            '+ deactivateEmployee(id): void'
        ]
    )
    d.add_class(
        'modal_emp', x=0.13, y_top=0.56, w=0.20,
        name='ModalEmpleadoForm', stereotype='boundary',
        attributes=[
            '- nombre: string = ""',
            '- correo: string = ""',
            '- rol: string = "cajero"',
            '- sucursal_id: string | null'
        ],
        methods=[
            '+ submitEmployee(): Promise<void>',
            '+ validateRoleRestriction(): bool',
            '+ validateEmailUniqueness(): bool'
        ]
    )
    d.add_class(
        'emp_ctrl', x=0.40, y_top=0.91, w=0.24,
        name='CU10GestionEmpleadosController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listEmployees(empresa_id): list[dict]',
            '+ createEmployee(empresa_id, data): dict',
            '+ updateEmployee(empresa_id, id, data): dict',
            '+ validateTenantRoleBR12(role): bool',
            '+ checkEmailDuplicity(email, emp_id): bool'
        ]
    )
    d.add_class(
        'usuario', x=0.68, y_top=0.91, w=0.22,
        name='Usuario', stereotype='entity', table='usuario',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# rol_id: uuid [FK]',
            '# sucursal_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ correo: citext',
            '- password_hash: text',
            '+ telefono: varchar(20)',
            '+ email_verificado: boolean = true',
            '+ estado: varchar(20) = "activo"'
        ],
        methods=[
            '+ createEmployeeRecord(data): Usuario',
            '+ updateEmployeeData(id, data): void',
            '+ emailExistsInTenant(email, emp_id): bool',
            '+ deactivateUser(id): void'
        ]
    )
    d.add_class(
        'rol', x=0.91, y_top=0.91, w=0.16,
        name='Rol', stereotype='entity', table='rol',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(50)',
            '+ es_global: boolean'
        ],
        methods=[
            '+ getAssignableTenantRoles(): list',
            '+ verifyNotSuperadmin(name): bool'
        ]
    )
    d.add_class(
        'empresa', x=0.68, y_top=0.55, w=0.22,
        name='Empresa', stereotype='entity', table='empresa',
        attributes=[
            '+ id: uuid [PK]',
            '+ nombre: varchar(120)',
            '+ estado: varchar(20)'
        ],
        methods=[]
    )
    d.add_class(
        'sucursal', x=0.91, y_top=0.55, w=0.16,
        name='Sucursal', stereotype='entity', table='sucursal',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(100)'
        ],
        methods=[
            '+ getAvailableBranches(emp_id): list'
        ]
    )
    d.add_class(
        'audit', x=0.68, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ accion: varchar(20)',
            '+ entidad: varchar(60) = "usuario"'
        ],
        methods=[
            '+ logEmployeeCreated(user_id): void',
            '+ logEmployeeUpdated(user_id): void'
        ]
    )
    
    d.add_connector('emp_ui', 'emp_ctrl', side1='right', side2='left', label="«manages staff»", is_dep=True)
    d.add_connector('modal_emp', 'emp_ctrl', side1='right', side2='bottom', label="«creates employee»", is_dep=True, rad=0.08)
    d.add_connector('emp_ctrl', 'usuario', side1='right', side2='left', label="«inserts / updates»", is_dep=True)
    d.add_connector('emp_ctrl', 'rol', side1='right', side2='left', label="«checks BR-12»", is_dep=True, rad=0.06)
    d.add_connector('emp_ctrl', 'audit', side1='bottom', side2='left', label="«audits staff changes»", is_dep=True, rad=-0.12)
    
    d.add_connector('empresa', 'usuario', side1='top', side2='bottom', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('rol', 'usuario', side1='left', side2='right', mult1="1", mult2="0..*")
    d.add_connector('sucursal', 'usuario', side1='left', side2='bottom', mult1="0..1", mult2="0..*")
    d.add_connector('empresa', 'sucursal', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu10_gestion_empleados.png")
    svg_path = os.path.join(output_dir, "clases_cu10_gestion_empleados.svg")
    d.save(png_path, svg_path)


if __name__ == '__main__':
    out_dir = os.path.join(os.getcwd(), 'docs', 'diagramas', 'diagrama de clases')
    os.makedirs(out_dir, exist_ok=True)
    
    generate_clases_cu01(out_dir)
    generate_clases_cu02(out_dir)
    generate_clases_cu03(out_dir)
    generate_clases_cu04(out_dir)
    generate_clases_cu05(out_dir)
    generate_clases_cu06(out_dir)
    generate_clases_cu07(out_dir)
    generate_clases_cu08(out_dir)
    generate_clases_cu09(out_dir)
    generate_clases_cu10(out_dir)
    
    print("Class diagrams for CU-01 to CU-10 generated successfully!")
