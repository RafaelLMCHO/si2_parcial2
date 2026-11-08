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
        
        # Store bounds for connectors
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
        
        # 3. Attributes Text
        curr_y = div1_y - 0.012
        for attr in attributes:
            # Color code PK, FK, UNIQUE badges
            self.ax.text(x_left + 0.008, curr_y, attr, fontsize=6.8, ha='left', va='center', fontfamily='monospace', color='#1E293B', zorder=4)
            curr_y -= line_h
            
        # 4. Methods Text
        curr_y = div2_y - 0.012
        for meth in methods:
            self.ax.text(x_left + 0.008, curr_y, meth, fontsize=6.8, ha='left', va='center', fontfamily='monospace', color='#0F172A', zorder=4)
            curr_y -= line_h

    def add_connector(self, k1, k2, side1='right', side2='left', label="", mult1="", mult2="",
                      is_dep=False, is_comp=False, rad=0.0):
        """
        Connects class k1 to k2 from side1 to side2.
        side can be 'left', 'right', 'top', 'bottom'.
        """
        c1 = self.classes[k1]
        c2 = self.classes[k2]
        
        # Compute start point
        if side1 == 'right': p1 = (c1['x_right'], c1['center_y'])
        elif side1 == 'left': p1 = (c1['x_left'], c1['center_y'])
        elif side1 == 'top': p1 = (c1['x'], c1['y_top'])
        else: p1 = (c1['x'], c1['y_bottom'])
        
        # Compute end point
        if side2 == 'right': p2 = (c2['x_right'], c2['center_y'])
        elif side2 == 'left': p2 = (c2['x_left'], c2['center_y'])
        elif side2 == 'top': p2 = (c2['x'], c2['y_top'])
        else: p2 = (c2['x'], c2['y_bottom'])
        
        ls = '--' if is_dep else '-'
        arrow = '->' if is_dep else '-'
        color = PALETTE['line_dep'] if is_dep else PALETTE['line']
        
        # Draw connection line
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
        
        # Midpoint label
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2 + (rad * 0.1)
        if label:
            self.ax.text(
                mx, my + 0.008, label, fontsize=6.8, fontweight='bold', ha='center', va='center',
                color='#1E293B', zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", fc="#FFFFFF", ec="#CBD5E1", lw=0.8, alpha=0.92)
            )
            
        # Multiplicities
        if mult1:
            dx = 0.012 if side1 == 'right' else (-0.012 if side1 == 'left' else 0)
            dy = 0.010 if side1 == 'top' else (-0.010 if side1 == 'bottom' else 0.008)
            self.ax.text(p1[0] + dx, p1[1] + dy, mult1, fontsize=7.2, fontweight='bold', color='#334155', zorder=5)
            
        if mult2:
            dx = -0.012 if side2 == 'right' else (0.012 if side2 == 'left' else 0)
            dy = 0.010 if side2 == 'top' else (-0.010 if side2 == 'bottom' else 0.008)
            self.ax.text(p2[0] + dx, p2[1] + dy, mult2, fontsize=7.2, fontweight='bold', color='#334155', zorder=5)
            
        # Composition Diamond at p1
        if is_comp:
            diam = patches.RegularPolygon(
                p1, numVertices=4, radius=0.007, orientation=0.785,
                facecolor=PALETTE['border_dark'], edgecolor=PALETTE['border_dark'], zorder=6
            )
            self.ax.add_patch(diam)

    def add_legend(self, x=0.02, y=0.04):
        """Draws a standardized legend explaining UML Stereotypes and DB mappings."""
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
            ("«schema» DTO Request / Response", PALETTE['dto']['header_fill'], PALETTE['dto']['border']),
            ("◆ Composición / Asociación BD", "#334155", "#334155"),
            ("---> Dependencia / Invocación", "#64748B", "#64748B")
        ]
        
        step = 0.96 / len(items)
        for i, (txt, fill, border) in enumerate(items):
            ix = x + i * step + 0.012
            iy = y + 0.019
            # mini badge
            self.ax.add_patch(patches.Rectangle((ix, iy - 0.007), 0.012, 0.014, fc=fill, ec=border, lw=1))
            self.ax.text(ix + 0.016, iy, txt, fontsize=7.0, ha='left', va='center', color='#1E293B', fontweight='bold')

    def save(self, png_path, svg_path):
        self.fig.savefig(png_path, bbox_inches='tight')
        self.fig.savefig(svg_path, bbox_inches='tight')
        plt.close(self.fig)
        print(f"Generated: {png_path}")


# ----------------------------------------------------------------------------------------
# Generador CU-01
# ----------------------------------------------------------------------------------------
def generate_clases_cu01(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-01: INICIAR SESIÓN (LOGIN)",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    
    # 1. Boundary: LoginComponent
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
            '+ redirigir(ruta: string): void',
            '+ mostrarError(msg: string): void',
            '+ limpiarFormulario(): void'
        ]
    )
    
    # 2. Control: AuthService
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
            '+ verify_password(plain, hashed): bool',
            '+ create_access_token(data: dict): str',
            '+ create_refresh_token(data: dict): str',
            '+ hash_token(token: str): str'
        ]
    )
    
    # 3. Schemas: LoginRequest & LoginResponse
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
    
    # 4. Entity: Empresa
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
            '+ buscar_por_slug(slug: str): Empresa',
            '+ esta_activa(): bool'
        ]
    )
    
    # 5. Entity: Suscripcion
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
            '+ es_vigente(): bool',
            '+ obtener_activa(emp_id): Suscrip'
        ]
    )
    
    # 6. Entity: Rol
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
            '+ obtener_por_id(rol_id): Rol',
            '+ consultar_permisos(): list'
        ]
    )
    
    # 7. Entity: Usuario
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
            '+ buscar_por_correo(correo, slug): Usuario',
            '+ actualizar_ultimo_acceso(id): void',
            '+ es_activo(): bool'
        ]
    )
    
    # 8. Entity: Sesion
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
            '+ crear_sesion(user_id, hash, exp): Sesion',
            '+ es_activa_y_vigente(): bool',
            '+ revocar_sesion(id): void'
        ]
    )
    
    # 9. Entity: BitacoraAuditoria
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
            '+ registrar_evento_login(user_id, ip): void',
            '+ registrar_intento_fallido(correo, ip): void'
        ]
    )
    
    # Relationships
    d.add_connector('login_ui', 'auth_ctrl', side1='right', side2='left', label="«invoca» POST /login", is_dep=True)
    d.add_connector('login_ui', 'login_req', side1='bottom', side2='top', label="«submits»", is_dep=True)
    d.add_connector('auth_ctrl', 'login_res', side1='bottom', side2='right', label="«returns»", is_dep=True)
    
    # Control to Entities
    d.add_connector('auth_ctrl', 'empresa', side1='right', side2='left', label="«consulta slug»", is_dep=True)
    d.add_connector('auth_ctrl', 'usuario', side1='right', side2='left', label="«valida y actualiza»", is_dep=True)
    d.add_connector('auth_ctrl', 'sesion', side1='bottom', side2='left', label="«crea sesión»", is_dep=True, rad=-0.1)
    d.add_connector('auth_ctrl', 'audit', side1='bottom', side2='top', label="«audita login»", is_dep=True)
    
    # Domain / DB Associations
    d.add_connector('empresa', 'suscrip', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'usuario', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('rol', 'usuario', side1='right', side2='left', mult1="1", mult2="0..*")
    d.add_connector('usuario', 'sesion', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('usuario', 'audit', side1='bottom', side2='right', mult1="1", mult2="0..*", rad=0.08)
    
    d.add_legend()
    
    png_path = os.path.join(output_dir, "clases_cu01_iniciar_sesion.png")
    svg_path = os.path.join(output_dir, "clases_cu01_iniciar_sesion.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# Generador CU-02
# ----------------------------------------------------------------------------------------
def generate_clases_cu02(output_dir):
    d = UMLClassDiagram(
        "DIAGRAMA DE CLASES UML - CU-02: REGISTRARSE Y VERIFICAR CORREO",
        "Realización del Caso de Uso (ICONIX) | Mapeo Boundary-Control-Entity con Esquema PostgreSQL"
    )
    
    # 1. Boundary: RegisterComponent
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
            '+ validarPassword(): boolean',
            '+ navegarAVerificacion(): void'
        ]
    )
    
    # 2. Boundary: VerifyEmailComponent
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
            '+ verificarToken(): Promise<void>',
            '+ redirigirALogin(): void'
        ]
    )
    
    # 3. Control: AuthService
    d.add_class(
        'auth_ctrl', x=0.38, y_top=0.91, w=0.23,
        name='AuthService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- token_expire_hours: int = 24'
        ],
        methods=[
            '+ register(data: RegisterRequest): RegisterResponse',
            '+ verify_email(data: VerifyEmailRequest): VerifyEmailResponse',
            '+ generate_token(): str',
            '+ hash_token(token: str): str',
            '+ send_verification_email(email, token): void'
        ]
    )
    
    # 4. Schemas / DTOs
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
    
    # 5. Entity: Empresa
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
            '+ validar_existencia_por_slug(slug): bool',
            '+ esta_activa(): bool'
        ]
    )
    
    # 6. Entity: Rol
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
            '+ obtener_rol_cliente(emp_id): Rol'
        ]
    )
    
    # 7. Entity: Usuario
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
            '+ existe_correo(correo, emp_id): bool',
            '+ crear_usuario_inactivo(data): Usuario',
            '+ activar_correo(user_id): void'
        ]
    )
    
    # 8. Entity: VerificacionCorreo
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
            '+ crear_token(user_id, hash, exp): Verif',
            '+ validar_token_vigente(hash): Verif',
            '+ marcar_consumido(id): void'
        ]
    )
    
    # 9. Entity: BitacoraAuditoria
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
            '+ registrar_registro_usuario(user_id): void',
            '+ registrar_verificacion_email(user_id): void'
        ]
    )
    
    # Relationships
    d.add_connector('reg_ui', 'auth_ctrl', side1='right', side2='left', label="«invoca» POST /register", is_dep=True)
    d.add_connector('ver_ui', 'auth_ctrl', side1='right', side2='bottom', label="«invoca» POST /verify-email", is_dep=True, rad=0.08)
    d.add_connector('reg_ui', 'reg_req', side1='bottom', side2='top', label="«submits»", is_dep=True)
    d.add_connector('ver_ui', 'ver_req', side1='bottom', side2='left', label="«submits»", is_dep=True, rad=-0.05)
    
    # Control to Entities
    d.add_connector('auth_ctrl', 'empresa', side1='right', side2='left', label="«valida tenant»", is_dep=True)
    d.add_connector('auth_ctrl', 'usuario', side1='right', side2='left', label="«crea / activa»", is_dep=True)
    d.add_connector('auth_ctrl', 'token_ent', side1='bottom', side2='left', label="«genera / consume»", is_dep=True, rad=-0.08)
    d.add_connector('auth_ctrl', 'audit', side1='bottom', side2='left', label="«audita eventos»", is_dep=True, rad=-0.12)
    
    # Domain / DB Associations
    d.add_connector('empresa', 'rol', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('empresa', 'usuario', side1='bottom', side2='top', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('rol', 'usuario', side1='bottom', side2='right', mult1="1", mult2="0..*", rad=0.06)
    d.add_connector('usuario', 'token_ent', side1='right', side2='left', mult1="1", mult2="0..*", is_comp=True)
    d.add_connector('usuario', 'audit', side1='bottom', side2='top', mult1="1", mult2="0..*")
    
    d.add_legend()
    
    png_path = os.path.join(output_dir, "clases_cu02_registrarse.png")
    svg_path = os.path.join(output_dir, "clases_cu02_registrarse.svg")
    d.save(png_path, svg_path)


if __name__ == '__main__':
    out_dir = os.path.join(os.getcwd(), 'docs', 'diagramas', 'diagrama de clases')
    os.makedirs(out_dir, exist_ok=True)
    generate_clases_cu01(out_dir)
    generate_clases_cu02(out_dir)
    print("Class diagrams for CU-01 and CU-02 generated successfully!")
