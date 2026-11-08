import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Color palette (Modern Professional UI)
COLORS = {
    'bg': '#FFFFFF',
    'header_bg': '#F8FAFC',
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
    'lifeline': '#94A3B8',
    'msg_call': '#0F172A',
    'msg_return': '#475569',
    'crud_badge': '#B45309',
    'frame_bg': '#F8FAFC',
    'frame_edge': '#64748B',
    'tag_bg': '#E2E8F0',
    'tag_text': '#1E293B',
}

class SequenceDiagram:
    def __init__(self, title, subtitle, width=17, height=13):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=300)
        self.fig.patch.set_facecolor(COLORS['bg'])
        self.ax.set_facecolor(COLORS['bg'])
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        
        # Header
        self.ax.text(0.5, 0.975, title, fontsize=15, fontweight='bold', ha='center', va='top', color=COLORS['text'])
        self.ax.text(0.5, 0.950, subtitle, fontsize=9.5, ha='center', va='top', color=COLORS['subtext'])
        
        self.participants = {}
        self.y_lifeline_top = 0.885
        self.y_lifeline_bottom = 0.05

    def add_participant(self, key, label, ptype, x, sub="", w=None, h=None, font_size=None, sub_size=None):
        """ptype: 'actor', 'boundary', 'control', 'entity'"""
        self.participants[key] = x
        w = w if w is not None else 0.088
        h = h if h is not None else 0.048
        f_size = font_size if font_size is not None else 8.5
        s_size = sub_size if sub_size is not None else 7.0
        t_size = max(6.2, f_size - 1.0)
        y = 0.910
        
        if ptype == 'actor':
            fill, edge, tag = COLORS['actor_fill'], COLORS['actor_edge'], "[ACTOR]"
        elif ptype == 'boundary':
            fill, edge, tag = COLORS['boundary_fill'], COLORS['boundary_edge'], "«boundary»"
        elif ptype == 'control':
            fill, edge, tag = COLORS['controller_fill'], COLORS['controller_edge'], "«control»"
        else: # entity
            fill, edge, tag = COLORS['entity_fill'], COLORS['entity_edge'], "«entity»"
            
        rect = patches.FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            facecolor=fill, edgecolor=edge, linewidth=1.6, zorder=4
        )
        self.ax.add_patch(rect)
        self.ax.text(x, y + 0.012, tag, fontsize=t_size, fontweight='bold', ha='center', va='center', color=edge, zorder=5)
        self.ax.text(x, y - 0.002, label, fontsize=f_size, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=5)
        if sub:
            self.ax.text(x, y - 0.015, sub, fontsize=s_size, ha='center', va='center', color=COLORS['subtext'], zorder=5)
            
        # Draw vertical lifeline
        self.ax.plot(
            [x, x], [self.y_lifeline_top, self.y_lifeline_bottom],
            linestyle='--', color=COLORS['lifeline'], linewidth=1.2, zorder=2
        )

    def add_message(self, src_key, dst_key, y, label, is_return=False, self_call=False, font_size=None):
        x1 = self.participants[src_key]
        x2 = self.participants[dst_key]
        f_size = font_size if font_size is not None else 7.8
        
        if self_call:
            # Curved self call
            self.ax.annotate(
                "", xy=(x1, y - 0.018), xytext=(x1, y),
                arrowprops=dict(
                    arrowstyle="->,head_width=0.3,head_length=0.4",
                    color=COLORS['msg_call'],
                    lw=1.4,
                    connectionstyle="arc3,rad=-0.8"
                ),
                zorder=3
            )
            self.ax.text(
                x1 + 0.012, y - 0.009, label, fontsize=f_size, ha='left', va='center',
                color=COLORS['msg_call'], fontweight='bold', zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", fc="#FFFFFF", ec="#CBD5E1", lw=0.8, alpha=0.92)
            )
            return

        if is_return:
            # Dashed return message
            self.ax.annotate(
                "", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(
                    arrowstyle="->,head_width=0.28,head_length=0.38",
                    color=COLORS['msg_return'],
                    linestyle='--',
                    lw=1.2
                ),
                zorder=3
            )
            mx = (x1 + x2) / 2
            self.ax.text(
                mx, y + 0.009, label, fontsize=max(6.8, f_size - 0.3), ha='center', va='bottom',
                color=COLORS['msg_return'], style='italic', zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc="#FFFFFF", ec="none", alpha=0.85)
            )
        else:
            # Solid synchronous call
            self.ax.annotate(
                "", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(
                    arrowstyle="->,head_width=0.32,head_length=0.45",
                    color=COLORS['msg_call'],
                    lw=1.4
                ),
                zorder=3
            )
            mx = (x1 + x2) / 2
            # Highlight CRUD verbs if present
            is_crud = any(label.startswith(v) or f" {v}:" in label for v in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
            color = COLORS['crud_badge'] if is_crud else COLORS['msg_call']
            
            self.ax.text(
                mx, y + 0.009, label, fontsize=f_size, ha='center', va='bottom',
                color=color, fontweight='bold', zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", fc="#FFFFFF", ec="#E2E8F0", lw=0.8, alpha=0.92)
            )

    def add_frame(self, operator, guard, x_left, x_right, y_top, y_bottom, divider_y=None, else_guard=""):
        """Draws alt, opt, or loop frame with optional divider."""
        w = x_right - x_left
        h = y_top - y_bottom
        rect = patches.FancyBboxPatch(
            (x_left, y_bottom), w, h,
            boxstyle="round,pad=0.004,rounding_size=0.01",
            facecolor='#F8FAFC', edgecolor=COLORS['frame_edge'],
            linestyle='--', linewidth=1.1, alpha=0.55, zorder=1
        )
        self.ax.add_patch(rect)
        
        # Tag box (e.g. "alt", "opt", "loop")
        tag_w, tag_h = 0.038, 0.018
        tag_rect = patches.FancyBboxPatch(
            (x_left, y_top - tag_h), tag_w, tag_h,
            boxstyle="round,pad=0.002,rounding_size=0.004",
            facecolor=COLORS['tag_bg'], edgecolor=COLORS['frame_edge'],
            linewidth=1.0, zorder=3
        )
        self.ax.add_patch(tag_rect)
        self.ax.text(x_left + tag_w/2, y_top - tag_h/2, operator, fontsize=7.5, fontweight='bold', ha='center', va='center', color=COLORS['tag_text'], zorder=4)
        
        # Guard condition
        self.ax.text(x_left + tag_w + 0.008, y_top - tag_h/2, guard, fontsize=7.6, fontweight='bold', ha='left', va='center', color='#334155', zorder=4)
        
        # Divider for alt / else
        if divider_y is not None:
            self.ax.plot(
                [x_left, x_right], [divider_y, divider_y],
                linestyle=':', color=COLORS['frame_edge'], linewidth=1.2, zorder=2
            )
            if else_guard:
                self.ax.text(x_left + 0.01, divider_y - 0.010, else_guard, fontsize=7.4, fontweight='bold', ha='left', va='center', color='#475569', zorder=4)

    def save(self, png_path, svg_path):
        self.fig.savefig(png_path, bbox_inches='tight')
        self.fig.savefig(svg_path, bbox_inches='tight')
        plt.close(self.fig)
        print(f"Generated: {png_path}")


# ----------------------------------------------------------------------------------------
# CU-01: Iniciar Sesión (Login)
# ----------------------------------------------------------------------------------------
def generate_seq_cu01(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-01: INICIAR SESIÓN (LOGIN)",
        "Interacciones, Métodos CRUD y Fragmentos de Control (alt / opt) | Metodología ICONIX"
    )
    
    # Participants (9 lifelines)
    d.add_participant('actor', 'Usuario', 'actor', 0.06, 'Admin/Cliente')
    d.add_participant('login_ui', 'LoginComponent', 'boundary', 0.17, 'login.html')
    d.add_participant('auth_ctrl', 'login()', 'control', 0.28, 'auth_service.py')
    d.add_participant('empresa', 'Empresa', 'entity', 0.39, 'db / empresa')
    d.add_participant('suscrip', 'Suscripcion', 'entity', 0.50, 'db / suscripcion')
    d.add_participant('rol', 'Rol', 'entity', 0.61, 'db / rol')
    d.add_participant('usuario', 'Usuario', 'entity', 0.72, 'db / usuario')
    d.add_participant('sesion', 'Sesion', 'entity', 0.83, 'db / sesion')
    d.add_participant('audit', 'BitacoraAuditoria', 'entity', 0.94, 'db / bitacora')
    
    # Message Flow
    d.add_message('actor', 'login_ui', 0.84, "1. Ingresar empresa_slug, correo, password")
    d.add_message('login_ui', 'auth_ctrl', 0.80, "2. POST /api/v1/auth/login")
    
    # opt: Superadmin
    d.add_frame("opt", "[Usuario es Superadmin Global (sin empresa)]", 0.25, 0.44, 0.78, 0.73)
    d.add_message('auth_ctrl', 'auth_ctrl', 0.75, "empresa_slug = null", self_call=True)
    
    # Queries (GET)
    d.add_message('auth_ctrl', 'empresa', 0.70, "3. GET: buscar empresa activa por slug")
    d.add_message('empresa', 'auth_ctrl', 0.67, "4. empresa_id, estado='activa'", is_return=True)
    
    d.add_message('auth_ctrl', 'suscrip', 0.63, "5. GET: verificar vigencia suscripción")
    d.add_message('suscrip', 'auth_ctrl', 0.60, "6. suscripción activa y vigente", is_return=True)
    
    d.add_message('auth_ctrl', 'rol', 0.56, "7. GET: consultar rol y permisos")
    d.add_message('rol', 'auth_ctrl', 0.53, "8. rol='administrador'", is_return=True)
    
    d.add_message('auth_ctrl', 'usuario', 0.49, "9. GET: validar credenciales y correo verificado")
    d.add_message('usuario', 'auth_ctrl', 0.46, "10. password_hash, email_verificado", is_return=True)
    
    d.add_message('auth_ctrl', 'auth_ctrl', 0.42, "11. verify_password(clave, hash)", self_call=True)
    
    # alt: Credenciales válidas vs inválidas
    d.add_frame(
        "alt", "[Credenciales válidas y correo verificado]",
        0.03, 0.97, 0.39, 0.08,
        divider_y=0.20,
        else_guard="[else: Credenciales incorrectas o correo no verificado]"
    )
    
    d.add_message('auth_ctrl', 'usuario', 0.36, "12. PATCH: actualizar ultimo_acceso = now()")
    d.add_message('auth_ctrl', 'sesion', 0.32, "13. POST: crear nueva sesión (refresh_token_hash)")
    d.add_message('sesion', 'auth_ctrl', 0.29, "14. session_id generado", is_return=True)
    d.add_message('auth_ctrl', 'audit', 0.26, "15. POST: registrar auditoría login exitoso")
    d.add_message('auth_ctrl', 'login_ui', 0.23, "16. 200 OK: LoginResponse(access_token, refresh_token)", is_return=True)
    d.add_message('login_ui', 'actor', 0.21, "17. Almacenar sesión y redirigir a /profile")
    
    # else branch
    d.add_message('auth_ctrl', 'audit', 0.16, "18. POST: registrar auditoría intento fallido / rechazado")
    d.add_message('auth_ctrl', 'login_ui', 0.12, "19. 401 / 403 Error (CREDENCIALES_INVALIDAS)", is_return=True)
    d.add_message('login_ui', 'actor', 0.09, "20. Mostrar mensaje de error en pantalla")
    
    png_path = os.path.join(output_dir, "secuencia_cu01_iniciar_sesion.png")
    svg_path = os.path.join(output_dir, "secuencia_cu01_iniciar_sesion.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-02: Registrarse y Verificar Correo
# ----------------------------------------------------------------------------------------
def generate_seq_cu02(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-02: REGISTRARSE Y VERIFICAR CORREO",
        "Registro de Cliente, Emisión y Confirmación de Token | Metodología ICONIX"
    )
    
    d.add_participant('actor', 'Cliente', 'actor', 0.05, 'Visitante')
    d.add_participant('reg_ui', 'RegisterComponent', 'boundary', 0.15, 'register.html')
    d.add_participant('ver_ui', 'VerifyEmailComponent', 'boundary', 0.25, 'verify-email.html')
    d.add_participant('reg_ctrl', 'register()', 'control', 0.36, 'auth_service.py')
    d.add_participant('ver_ctrl', 'verify_email()', 'control', 0.47, 'auth_service.py')
    d.add_participant('empresa', 'Empresa', 'entity', 0.58, 'db / empresa')
    d.add_participant('rol', 'Rol', 'entity', 0.68, 'db / rol')
    d.add_participant('usuario', 'Usuario', 'entity', 0.78, 'db / usuario')
    d.add_participant('token', 'VerificacionCorreo', 'entity', 0.88, 'db / verificacion')
    d.add_participant('audit', 'BitacoraAuditoria', 'entity', 0.96, 'db / bitacora')
    
    # FASE 1: REGISTRO
    d.add_message('actor', 'reg_ui', 0.84, "1. Completar formulario (nombre, correo, teléfono, clave)")
    d.add_message('reg_ui', 'reg_ctrl', 0.80, "2. POST /api/v1/auth/register (datos cliente)")
    d.add_message('reg_ctrl', 'empresa', 0.77, "3. GET: validar empresa existente por slug")
    d.add_message('reg_ctrl', 'rol', 0.74, "4. GET: obtener id de rol 'cliente'")
    d.add_message('reg_ctrl', 'usuario', 0.71, "5. GET: verificar si correo ya existe en tenant")
    
    # alt: Correo disponible vs duplicado
    d.add_frame(
        "alt", "[Correo disponible]",
        0.03, 0.98, 0.68, 0.43,
        divider_y=0.48,
        else_guard="[else: Correo duplicado]"
    )
    
    d.add_message('reg_ctrl', 'usuario', 0.65, "6. POST: crear usuario (inactivo, email_verificado=false)")
    d.add_message('reg_ctrl', 'token', 0.61, "7. POST: crear registro de token con expiración")
    d.add_message('reg_ctrl', 'audit', 0.57, "8. POST: registrar auditoría de registro")
    
    # opt: Modo demo
    d.add_frame("opt", "[Modo Demo: exponer token]", 0.33, 0.51, 0.55, 0.52)
    
    d.add_message('reg_ctrl', 'reg_ui', 0.52, "9. 201 Created: RegisterResponse (mensaje confirmación)", is_return=True)
    d.add_message('reg_ui', 'actor', 0.49, "10. Mostrar aviso: Revise su correo para verificar")
    
    d.add_message('reg_ctrl', 'reg_ui', 0.45, "11. 409 Conflict: CORREO_DUPLICADO", is_return=True)
    
    # FASE 2: VERIFICACIÓN
    d.add_message('actor', 'ver_ui', 0.39, "12. Ingresar token recibido")
    d.add_message('ver_ui', 'ver_ctrl', 0.35, "13. POST /api/v1/auth/verify-email (token, slug)")
    d.add_message('ver_ctrl', 'token', 0.31, "14. GET: validar token por hash y expiración")
    
    # alt: Token válido vs inválido
    d.add_frame(
        "alt", "[Token válido y vigente]",
        0.03, 0.98, 0.28, 0.07,
        divider_y=0.14,
        else_guard="[else: Token inválido o expirado]"
    )
    d.add_message('ver_ctrl', 'usuario', 0.25, "15. PATCH: activar usuario (estado='activo', verificado=true)")
    d.add_message('ver_ctrl', 'token', 0.22, "16. DELETE: invalidar / consumir token utilizado")
    d.add_message('ver_ctrl', 'audit', 0.19, "17. POST: registrar auditoría de verificación")
    d.add_message('ver_ctrl', 'ver_ui', 0.16, "18. 200 OK: VerifyEmailResponse ('Correo verificado')", is_return=True)
    
    d.add_message('ver_ctrl', 'ver_ui', 0.11, "19. 400 Bad Request: TOKEN_INVALIDO", is_return=True)
    d.add_message('ver_ui', 'actor', 0.08, "20. Notificar resultado en pantalla")
    
    png_path = os.path.join(output_dir, "secuencia_cu02_registrarse.png")
    svg_path = os.path.join(output_dir, "secuencia_cu02_registrarse.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-03: Gestionar Perfil y Cambiar Contraseña
# ----------------------------------------------------------------------------------------
def generate_seq_cu03(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-03: GESTIONAR PERFIL Y CAMBIO DE CONTRASEÑA",
        "Consulta de Perfil, Actualización Personal y Revocación de Sesiones | Metodología ICONIX"
    )
    
    d.add_participant('actor', 'Usuario', 'actor', 0.06, 'Autenticado')
    d.add_participant('profile_ui', 'ProfileComponent', 'boundary', 0.19, 'profile.html')
    d.add_participant('get_ctrl', 'get_me()', 'control', 0.32, 'auth_service.py')
    d.add_participant('upd_ctrl', 'update_me()', 'control', 0.45, 'auth_service.py')
    d.add_participant('pass_ctrl', 'change_password()', 'control', 0.58, 'auth_service.py')
    d.add_participant('usuario', 'Usuario', 'entity', 0.72, 'db / usuario')
    d.add_participant('sesion', 'Sesion', 'entity', 0.85, 'db / sesion')
    d.add_participant('audit', 'BitacoraAuditoria', 'entity', 0.95, 'db / bitacora')
    
    # 1. Carga de perfil
    d.add_message('actor', 'profile_ui', 0.84, "1. Abrir vista de perfil")
    d.add_message('profile_ui', 'get_ctrl', 0.80, "2. GET /api/v1/users/me (Bearer Token)")
    d.add_message('get_ctrl', 'usuario', 0.76, "3. GET: leer datos perfil por usuario_id")
    d.add_message('usuario', 'get_ctrl', 0.73, "4. datos usuario (sin password_hash)", is_return=True)
    d.add_message('get_ctrl', 'profile_ui', 0.70, "5. 200 OK: UserOut", is_return=True)
    d.add_message('profile_ui', 'actor', 0.67, "6. Renderizar formulario con datos actuales")
    
    # 2. Actualización opcional de datos
    d.add_frame("opt", "[Modificación de datos personales (nombre o teléfono)]", 0.03, 0.97, 0.64, 0.47)
    d.add_message('actor', 'profile_ui', 0.61, "7. Modificar valores y hacer clic en Guardar")
    d.add_message('profile_ui', 'upd_ctrl', 0.58, "8. PATCH /api/v1/users/me (nombre, teléfono)")
    d.add_message('upd_ctrl', 'usuario', 0.54, "9. PUT / PATCH: actualizar nombre y teléfono")
    d.add_message('upd_ctrl', 'audit', 0.51, "10. POST: registrar auditoría de actualización")
    d.add_message('upd_ctrl', 'profile_ui', 0.48, "11. 200 OK: Perfil actualizado", is_return=True)
    
    # 3. Cambio de contraseña
    d.add_message('actor', 'profile_ui', 0.44, "12. Ingresar password actual y nueva")
    d.add_message('profile_ui', 'pass_ctrl', 0.40, "13. POST /api/v1/users/me/password (claves)")
    d.add_message('pass_ctrl', 'usuario', 0.36, "14. GET: consultar password_hash actual")
    
    # alt: Contraseña actual correcta vs incorrecta
    d.add_frame(
        "alt", "[Contraseña actual correcta]",
        0.03, 0.97, 0.33, 0.07,
        divider_y=0.14,
        else_guard="[else: Contraseña actual incorrecta]"
    )
    
    d.add_message('pass_ctrl', 'usuario', 0.30, "15. PATCH: guardar nuevo password_hash")
    
    # loop: Revocar demás sesiones
    d.add_frame("loop", "[Para cada sesión remota activa (id <> sesion_actual)]", 0.54, 0.88, 0.28, 0.23)
    d.add_message('pass_ctrl', 'sesion', 0.25, "16. DELETE: revocar sesión concurrente (revocado_en=now)")
    
    d.add_message('pass_ctrl', 'audit', 0.20, "17. POST: registrar auditoría de cambio de clave")
    d.add_message('pass_ctrl', 'profile_ui', 0.17, "18. 200 OK: 'Contraseña actualizada y demás sesiones revocadas'", is_return=True)
    d.add_message('profile_ui', 'actor', 0.15, "19. Notificar éxito al usuario")
    
    d.add_message('pass_ctrl', 'profile_ui', 0.11, "20. 400 Bad Request: PASSWORD_INCORRECTA", is_return=True)
    d.add_message('profile_ui', 'actor', 0.08, "21. Mostrar error: 'La contraseña actual es incorrecta'")
    
    png_path = os.path.join(output_dir, "secuencia_cu03_gestionar_perfil.png")
    svg_path = os.path.join(output_dir, "secuencia_cu03_gestionar_perfil.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-04: Cerrar Sesión y Refresco de Tokens
# ----------------------------------------------------------------------------------------
def generate_seq_cu04(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-04: CERRAR SESIÓN Y REFRESCO DE TOKENS",
        "Logout Seguro, Preservación Offline y Rotación de Refresh Token | Metodología ICONIX"
    )
    
    d.add_participant('actor', 'Usuario', 'actor', 0.06, 'Autenticado')
    d.add_participant('nav_ui', 'Navbar / Profile', 'boundary', 0.19, 'Acción Logout')
    d.add_participant('int_ui', 'AuthInterceptor', 'boundary', 0.33, 'auth.interceptor.ts')
    d.add_participant('out_ctrl', 'logout()', 'control', 0.47, 'auth_service.py')
    d.add_participant('ref_ctrl', 'refresh()', 'control', 0.60, 'auth_service.py')
    d.add_participant('sesion', 'Sesion', 'entity', 0.74, 'db / sesion')
    d.add_participant('usuario', 'Usuario', 'entity', 0.86, 'db / usuario')
    d.add_participant('audit', 'BitacoraAuditoria', 'entity', 0.95, 'db / bitacora')
    
    # FLUJO A: LOGOUT
    d.add_message('actor', 'nav_ui', 0.84, "1. Clic en 'Cerrar Sesión'")
    d.add_message('nav_ui', 'out_ctrl', 0.80, "2. POST /api/v1/auth/logout (Bearer Token)")
    d.add_message('out_ctrl', 'sesion', 0.76, "3. DELETE: revocar sesión (UPDATE revocado_en = now())")
    d.add_message('out_ctrl', 'audit', 0.72, "4. POST: registrar auditoría de logout")
    d.add_message('out_ctrl', 'nav_ui', 0.68, "5. 200 OK: {'mensaje': 'Sesión cerrada'}", is_return=True)
    
    # opt: Preservar offline
    d.add_frame("opt", "[Preservar cola de sincronización offline (IndexedDB)]", 0.03, 0.28, 0.65, 0.58)
    d.add_message('nav_ui', 'nav_ui', 0.61, "Conservar cola offline fs_queue", self_call=True)
    
    d.add_message('nav_ui', 'actor', 0.55, "6. Limpiar tokens de sesión (fs_*) y redirigir a /login")
    
    # FLUJO B: REFRESH AUTOMÁTICO
    d.add_message('actor', 'int_ui', 0.49, "7. Petición protegida recibe 401 (Access Token expirado)")
    d.add_message('int_ui', 'ref_ctrl', 0.45, "8. POST /api/v1/auth/refresh (refresh_token)")
    d.add_message('ref_ctrl', 'sesion', 0.41, "9. GET: consultar sesión activa y vigente por hash")
    
    # alt: Refresh válido vs revocado/expirado
    d.add_frame(
        "alt", "[Refresh token válido y no revocado]",
        0.03, 0.97, 0.38, 0.07,
        divider_y=0.16,
        else_guard="[else: Refresh token revocado o expirado]"
    )
    
    d.add_message('ref_ctrl', 'usuario', 0.34, "10. GET: verificar estado activo del usuario y empresa")
    d.add_message('ref_ctrl', 'sesion', 0.30, "11. PUT / PATCH: rotar nuevo hash y expira_en")
    d.add_message('ref_ctrl', 'audit', 0.26, "12. POST: registrar auditoría de refresh")
    d.add_message('ref_ctrl', 'int_ui', 0.22, "13. 200 OK: RefreshResponse(nuevo access_token, nuevo refresh_token)", is_return=True)
    d.add_message('int_ui', 'int_ui', 0.18, "14. Reintento automático de petición original", self_call=True)
    
    d.add_message('ref_ctrl', 'int_ui', 0.13, "15. 401 Unauthorized: REFRESH_INVALIDO", is_return=True)
    d.add_message('int_ui', 'actor', 0.09, "16. Limpiar credenciales y redirigir a /login")
    
    png_path = os.path.join(output_dir, "secuencia_cu04_cerrar_sesion.png")
    svg_path = os.path.join(output_dir, "secuencia_cu04_cerrar_sesion.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-05: Registrar Auditoría del Sistema
# ----------------------------------------------------------------------------------------
def generate_seq_cu05(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-05: REGISTRAR AUDITORÍA TRANSVERSAL",
        "Intercepción HTTP, Extracción de Claims, Redacción de Secretos y Persistencia | Metodología ICONIX"
    )
    
    d.add_participant('actor', 'Actor / Sistema', 'actor', 0.06, 'Usuario / Superadmin')
    d.add_participant('http_ui', 'HttpRequestBoundary', 'boundary', 0.20, 'Vistas / HTTP')
    d.add_participant('mw', 'audit_middleware()', 'control', 0.36, 'audit.py')
    d.add_participant('router', 'FastAPI Router', 'control', 0.52, 'Router Endpoints')
    d.add_participant('usuario', 'Usuario', 'entity', 0.68, 'db / usuario')
    d.add_participant('empresa', 'Empresa', 'entity', 0.82, 'db / empresa')
    d.add_participant('audit', 'BitacoraAuditoria', 'entity', 0.94, 'db / bitacora')
    
    d.add_message('actor', 'http_ui', 0.84, "1. Enviar solicitud HTTP (GET, POST, PUT, DELETE)")
    d.add_message('http_ui', 'mw', 0.80, "2. Interceptar Request (método, ruta, body, headers)")
    
    # alt: Ruta excluida vs ruta auditable
    d.add_frame(
        "alt", "[Ruta excluida (/docs, /health, /openapi.json)]",
        0.03, 0.97, 0.77, 0.08,
        divider_y=0.67,
        else_guard="[else: Ruta auditable de la API]"
    )
    
    d.add_message('mw', 'router', 0.73, "3. call_next(request)")
    d.add_message('router', 'mw', 0.70, "4. Response HTTP", is_return=True)
    d.add_message('mw', 'http_ui', 0.68, "5. Response directa sin registrar auditoría", is_return=True)
    
    d.add_message('mw', 'router', 0.63, "6. call_next(request): procesar operación")
    d.add_message('router', 'mw', 0.59, "7. Response HTTP (status_code, payload)", is_return=True)
    
    # opt: Token presente
    d.add_frame("opt", "[Header Authorization presente: decodificar JWT]", 0.30, 0.88, 0.56, 0.40)
    d.add_message('mw', 'mw', 0.52, "decode_access_token(JWT)", self_call=True)
    d.add_message('mw', 'usuario', 0.47, "8. GET: extraer usuario_id y rol del token")
    d.add_message('mw', 'empresa', 0.43, "9. GET: extraer empresa_id del tenant")
    
    # loop: Enmascarar secretos
    d.add_frame("loop", "[Para cada clave en payload: password, token, hash, secret]", 0.30, 0.55, 0.37, 0.27)
    d.add_message('mw', 'mw', 0.32, "_redact(): enmascarar con '***'", self_call=True)
    
    d.add_message('mw', 'audit', 0.23, "10. POST: guardar log HTTP con datos redactados (***)")
    d.add_message('mw', 'http_ui', 0.17, "11. Devolver Response original intacta", is_return=True)
    d.add_message('http_ui', 'actor', 0.12, "12. Renderizar resultado en la interfaz")
    
    png_path = os.path.join(output_dir, "secuencia_cu05_registrar_auditoria.png")
    svg_path = os.path.join(output_dir, "secuencia_cu05_registrar_auditoria.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-06: Gestión de Planes y Registro de Empresas SaaS
# ----------------------------------------------------------------------------------------
def generate_seq_cu06(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-06: GESTIÓN DE PLANES Y REGISTRO DE EMPRESAS SAAS",
        "Catálogo de Tarifas SaaS, Onboarding de Tenant y Creación de Admin Inicial | Metodología ICONIX",
        width=18, height=13.5
    )
    d.y_lifeline_bottom = 0.03
    
    d.add_participant('actor', 'Superadmin', 'actor', 0.05, 'Admin SaaS')
    d.add_participant('planes_ui', 'PlanesSaaSComponent', 'boundary', 0.14, 'planes-saas.html')
    d.add_participant('modal_ui', 'ModalCrearEmpresa', 'boundary', 0.24, 'empresa-modal.html')
    d.add_participant('planes_ctrl', 'listar_planes()', 'control', 0.35, 'cu06_planes_ctrl.py')
    d.add_participant('empresa_ctrl', 'create_empresa()', 'control', 0.46, 'saas_service.py')
    d.add_participant('plan', 'PlanSaaS', 'entity', 0.57, 'db / plan_saas')
    d.add_participant('empresa', 'Empresa', 'entity', 0.68, 'db / empresa')
    d.add_participant('rol', 'Rol', 'entity', 0.78, 'db / rol y permiso')
    d.add_participant('usuario', 'Usuario', 'entity', 0.88, 'db / usuario')
    d.add_participant('audit', 'BitacoraAuditoria', 'entity', 0.97, 'db / bitacora')
    
    # FASE 1: CONSULTA DE PLANES Y CREACIÓN OPCIONAL
    d.add_message('actor', 'planes_ui', 0.85, "1. Abrir vista de planes y tenants SaaS")
    d.add_message('planes_ui', 'planes_ctrl', 0.81, "2. GET /api/v1/saas/planes (Bearer Superadmin)")
    d.add_message('planes_ctrl', 'plan', 0.77, "3. GET: consultar planes activos y cuotas")
    d.add_message('plan', 'planes_ctrl', 0.74, "4. planes_saas (precios, límites sucursales/usuarios)", is_return=True)
    d.add_message('planes_ctrl', 'planes_ui', 0.71, "5. 200 OK: list[PlanOut]", is_return=True)
    d.add_message('planes_ui', 'actor', 0.68, "6. Renderizar tabla de planes disponibles y botón 'Nueva Empresa'")
    
    # opt: Superadmin define nuevo plan
    d.add_frame("opt", "[Superadmin define nuevo plan tarifario]", 0.03, 0.62, 0.655, 0.540)
    d.add_message('actor', 'planes_ui', 0.62, "7. Ingresar nuevo plan (nombre, precio, límites)")
    d.add_message('planes_ui', 'planes_ctrl', 0.58, "8. POST /api/v1/saas/planes (nombre, precio, límites)")
    d.add_message('planes_ctrl', 'plan', 0.55, "9. POST: insertar nuevo plan_saas con límites")
    
    # FASE 2: ONBOARDING DE EMPRESA TENANT
    d.add_message('actor', 'modal_ui', 0.51, "10. Clic 'Nueva Empresa' y completar datos (nombre, nit, correo_admin)")
    d.add_message('modal_ui', 'empresa_ctrl', 0.47, "11. POST /api/v1/saas/empresas (EmpresaCreateRequest)")
    d.add_message('empresa_ctrl', 'empresa_ctrl', 0.435, "pg_advisory_xact_lock(nit, correo_admin)", self_call=True)
    d.add_message('empresa_ctrl', 'empresa', 0.40, "12. GET: verificar si NIT ya está registrado")
    d.add_message('empresa_ctrl', 'usuario', 0.365, "13. GET: verificar si correo_admin ya existe")
    
    # alt: Conflicto duplicados vs Registro exitoso
    d.add_frame(
        "alt", "[NIT y correo disponibles (Unicidad confirmada)]",
        0.03, 0.98, 0.345, 0.045,
        divider_y=0.095,
        else_guard="[else: Conflicto NIT o Correo ya registrados]"
    )
    
    d.add_message('empresa_ctrl', 'empresa_ctrl', 0.315, "_unique_slug(nombre) -> slug generado", self_call=True)
    d.add_message('empresa_ctrl', 'empresa', 0.28, "14. POST: insertar empresa (estado='pendiente_plan', slug)")
    
    # loop: Roles y permisos
    d.add_frame("loop", "[Para cada rol base: admin, cajero, encargado, cliente]", 0.44, 0.82, 0.260, 0.210)
    d.add_message('empresa_ctrl', 'rol', 0.225, "15. POST: crear rol base y vincular rol_permiso")
    
    d.add_message('empresa_ctrl', 'usuario', 0.190, "16. POST: crear usuario admin activo con password temporal")
    d.add_message('empresa_ctrl', 'audit', 0.165, "17. POST: registrar auditoría superadmin (_safe_audit)")
    d.add_message('empresa_ctrl', 'modal_ui', 0.135, "18. 201 Created: EmpresaCreateResponse (empresa_id, slug, password_temporal)", is_return=True)
    d.add_message('modal_ui', 'actor', 0.115, "19. Mostrar credenciales temporales generadas (Listo para CU-07)")
    
    # else branch
    d.add_message('empresa_ctrl', 'modal_ui', 0.075, "20. 409 Conflict: NIT_DUPLICADO / CORREO_ADMIN_DUPLICADO", is_return=True)
    d.add_message('modal_ui', 'actor', 0.050, "21. Notificar conflicto de unicidad en pantalla")
    
    png_path = os.path.join(output_dir, "secuencia_cu06_gestion_planes.png")
    svg_path = os.path.join(output_dir, "secuencia_cu06_gestion_planes.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-17: Gestión de Inventario, Kárdex y Ajustes
# ----------------------------------------------------------------------------------------
def generate_seq_cu17(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-17: GESTIÓN DE INVENTARIO, KÁRDEX Y AJUSTES",
        "Consulta de Stock, Ajustes Manuales (+/-), Kárdex Inmutable y Auditoría | Metodología ICONIX"
    )
    d.add_participant('actor', 'Encargado', 'actor', 0.06, 'Staff / Admin')
    d.add_participant('ui', 'MatrizInventario', 'boundary', 0.18, 'inventario.html')
    d.add_participant('modal', 'ModalAjuste', 'boundary', 0.31, 'ajuste-modal.html')
    d.add_participant('ctrl', 'inventario_ctrl', 'control', 0.46, 'inventario_service.py')
    d.add_participant('inv', 'Inventario', 'entity', 0.60, 'db / inventario')
    d.add_participant('var', 'PrendaVariante', 'entity', 0.73, 'db / variante')
    d.add_participant('mov', 'Kardex', 'entity', 0.85, 'db / mov_inventario')
    d.add_participant('aud', 'Auditoria', 'entity', 0.95, 'db / bitacora')

    d.add_message('actor', 'ui', 0.84, "1. Solicitar existencias de inventario")
    d.add_message('ui', 'ctrl', 0.80, "2. GET /api/v1/inventario (sucursal_id, solo_bajo_minimo)")
    d.add_message('ctrl', 'inv', 0.76, "3. GET: consultar stock_fisico y stock_minimo")
    d.add_message('ctrl', 'var', 0.72, "4. GET: recuperar SKU, talla, color y datos de prenda")
    d.add_message('ctrl', 'ui', 0.68, "5. Response 200 (existencias, alertas stock crítico)", is_return=True)
    d.add_message('ui', 'actor', 0.64, "6. Renderizar matriz con semáforo de existencias")
    d.add_message('actor', 'modal', 0.60, "7. Abrir modal e ingresar ajuste manual (+/- cant, motivo)")
    d.add_message('modal', 'ctrl', 0.56, "8. POST /api/v1/inventario/movimientos/ajuste")
    d.add_message('ctrl', 'inv', 0.52, "9. GET: verificar variante y stock FOR UPDATE")

    d.add_frame(
        "alt", "[stock_fisico + cantidad >= 0 (Ajuste Válido)]",
        0.03, 0.97, 0.50, 0.15,
        divider_y=0.27,
        else_guard="[else: stock resultante < 0 (Error Stock Insuficiente)]"
    )
    d.add_message('ctrl', 'inv', 0.46, "10. PATCH / UPDATE: actualizar stock_fisico (+/-)")
    d.add_message('ctrl', 'mov', 0.41, "11. POST: asentar movimiento en kárdex (tipo='ajuste')")
    d.add_message('ctrl', 'aud', 0.36, "12. POST: auditar evento stock.ajustar")
    d.add_message('ctrl', 'modal', 0.32, "13. Response 200 OK (ajuste registrado)", is_return=True)
    d.add_message('modal', 'actor', 0.29, "14. Confirmación visual y actualización en tiempo real")

    d.add_message('ctrl', 'modal', 0.23, "15. Error 409 Conflict: 'Stock resultante no puede ser menor a cero'", is_return=True)
    d.add_message('modal', 'actor', 0.18, "16. Mostrar alerta Toast de restricción")

    png_path = os.path.join(output_dir, "secuencia_cu17_gestion_inventario.png")
    svg_path = os.path.join(output_dir, "secuencia_cu17_gestion_inventario.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-18: Disponibilidad en Tiendas / Búsqueda Omnicanal
# ----------------------------------------------------------------------------------------
def generate_seq_cu18(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-18: DISPONIBILIDAD EN TIENDAS / BÚSQUEDA OMNICANAL",
        "Consulta de Stock Multi-Sucursal en Tiempo Real y Cálculo de Disponibilidad | Metodología ICONIX"
    )
    d.add_participant('actor', 'Cliente', 'actor', 0.06, 'Visitante / Comprador')
    d.add_participant('cat_ui', 'CatalogoComponent', 'boundary', 0.19, 'catalogo.html')
    d.add_participant('map_ui', 'MapaDisponibilidad', 'boundary', 0.33, 'tiendas-modal.html')
    d.add_participant('ctrl', 'inventario_ctrl', 'control', 0.48, 'inventario_service.py')
    d.add_participant('empresa', 'Empresa', 'entity', 0.62, 'db / empresa')
    d.add_participant('sucursal', 'Sucursal', 'entity', 0.74, 'db / sucursal')
    d.add_participant('inv', 'Inventario', 'entity', 0.86, 'db / inventario')
    d.add_participant('var', 'PrendaVariante', 'entity', 0.95, 'db / variante')

    d.add_message('actor', 'cat_ui', 0.84, "1. Seleccionar prenda y talla en catálogo web/móvil")
    d.add_message('actor', 'map_ui', 0.80, "2. Clic en 'Ver disponibilidad en tiendas físicas'")
    d.add_message('map_ui', 'ctrl', 0.76, "3. GET /api/v1/prendas/{id}/disponibilidad (variante_id, ciudad)")
    d.add_message('ctrl', 'empresa', 0.71, "4. GET: verificar tenant activo y políticas de stock")
    d.add_message('ctrl', 'var', 0.67, "5. GET: validar variante_id y SKU activo")
    d.add_message('ctrl', 'sucursal', 0.63, "6. GET: listar sucursales físicas operativas")

    d.add_frame("loop", "[Para cada sucursal física de la empresa]", 0.44, 0.98, 0.60, 0.38)
    d.add_message('ctrl', 'inv', 0.55, "7. GET: consultar stock_fisico y stock_reservado")
    d.add_message('ctrl', 'ctrl', 0.50, "calcular_disponible = stock_fisico - stock_reservado", self_call=True)
    d.add_message('ctrl', 'map_ui', 0.44, "8. Agregar sucursal con unidades disponibles y distancia", is_return=True)

    d.add_frame(
        "alt", "[disponible > 0 en sucursales]",
        0.03, 0.97, 0.35, 0.12,
        divider_y=0.23,
        else_guard="[else: stock agotado en todas las tiendas]"
    )
    d.add_message('map_ui', 'actor', 0.29, "9. Mostrar mapa interactivo con stock verde y botón 'Reservar'")
    d.add_message('map_ui', 'actor', 0.17, "10. Notificar 'Sin stock cercano', sugerir envío a domicilio")

    png_path = os.path.join(output_dir, "secuencia_cu18_disponibilidad_tiendas.png")
    svg_path = os.path.join(output_dir, "secuencia_cu18_disponibilidad_tiendas.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-19: Creación de Reservas y Probador
# ----------------------------------------------------------------------------------------
def generate_seq_cu19(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-19: CREACIÓN DE RESERVAS Y PROBADOR",
        "Validación de Stock Omnicanal, Apartado Temporal (TTL 48h) y Emisión de Voucher | Metodología ICONIX"
    )
    d.add_participant('actor', 'Cliente', 'actor', 0.06, 'Usuario autenticado')
    d.add_participant('ui', 'ReservaProbadorUI', 'boundary', 0.19, 'reserva-probador.html')
    d.add_participant('ctrl', 'reserva_ctrl', 'control', 0.34, 'reserva_service.py')
    d.add_participant('inv', 'Inventario', 'entity', 0.49, 'db / inventario')
    d.add_participant('res', 'Reserva', 'entity', 0.63, 'db / reserva')
    d.add_participant('item', 'ReservaItem', 'entity', 0.76, 'db / reserva_item')
    d.add_participant('hist', 'ReservaHistorial', 'entity', 0.87, 'db / historial')
    d.add_participant('aud', 'Auditoria', 'entity', 0.96, 'db / bitacora')

    d.add_message('actor', 'ui', 0.84, "1. Seleccionar sucursal, fecha/hora y prendas a reservar")
    d.add_message('ui', 'ctrl', 0.80, "2. POST /api/v1/reservas/validar (sucursal_id, fecha, items)")
    d.add_message('ctrl', 'inv', 0.76, "3. GET: verificar disponible (stock_fisico - stock_reservado >= cant)")
    d.add_message('ctrl', 'ui', 0.72, "4. Validación exitosa: prendas disponibles", is_return=True)
    d.add_message('actor', 'ui', 0.68, "5. Confirmar reserva (Idempotency-Key en Header)")
    d.add_message('ui', 'ctrl', 0.64, "6. POST /api/v1/reservas (datos_reserva, items)")

    d.add_frame(
        "alt", "[Stock suficiente para todas las prendas]",
        0.03, 0.98, 0.61, 0.14,
        divider_y=0.25,
        else_guard="[else: Conflicto de stock por concurrencia]"
    )
    d.add_message('ctrl', 'inv', 0.57, "7. PATCH / UPDATE: stock_reservado = stock_reservado + cant")
    d.add_message('ctrl', 'res', 0.52, "8. POST: insertar reserva ('pendiente', expira_en = now + 48h, voucher)")
    d.add_message('ctrl', 'item', 0.47, "9. POST: insertar reserva_item (variante_id, cantidad)")
    d.add_message('ctrl', 'hist', 0.42, "10. POST: historial estado inicial 'pendiente'")
    d.add_message('ctrl', 'aud', 0.37, "11. POST: auditar creación de reserva")
    d.add_message('ctrl', 'ui', 0.32, "12. Response 201 Created (codigo_reserva, voucher_url)", is_return=True)
    d.add_message('ui', 'actor', 0.28, "13. Exhibir voucher con código QR para probador")

    d.add_message('ctrl', 'ui', 0.21, "14. Response 409 Conflict: 'Prenda no disponible'", is_return=True)
    d.add_message('ui', 'actor', 0.17, "15. Notificar stock insuficiente y solicitar cambio de talla")

    png_path = os.path.join(output_dir, "secuencia_cu19_creacion_reservas.png")
    svg_path = os.path.join(output_dir, "secuencia_cu19_creacion_reservas.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-20: Consulta y Seguimiento de Reservas del Cliente
# ----------------------------------------------------------------------------------------
def generate_seq_cu20(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-20: CONSULTA Y GESTIÓN DE RESERVAS DEL CLIENTE",
        "Historial de Reservas, Transiciones de Estado y Cancelación con Devolución de Stock | Metodología ICONIX"
    )
    d.add_participant('actor', 'Cliente', 'actor', 0.06, 'Usuario autenticado')
    d.add_participant('ui', 'MisReservasUI', 'boundary', 0.20, 'mis-reservas.html')
    d.add_participant('modal', 'ModalCancelar', 'boundary', 0.35, 'cancelar-modal.html')
    d.add_participant('ctrl', 'reserva_ctrl', 'control', 0.50, 'reserva_service.py')
    d.add_participant('res', 'Reserva', 'entity', 0.64, 'db / reserva')
    d.add_participant('hist', 'ReservaHistorial', 'entity', 0.76, 'db / historial')
    d.add_participant('inv', 'Inventario', 'entity', 0.88, 'db / inventario')
    d.add_participant('aud', 'Auditoria', 'entity', 0.96, 'db / bitacora')

    d.add_message('actor', 'ui', 0.84, "1. Acceder a sección 'Mis Reservas'")
    d.add_message('ui', 'ctrl', 0.80, "2. GET /api/v1/reservas (filtrar usuario_id autenticado)")
    d.add_message('ctrl', 'res', 0.76, "3. GET: consultar reservas activas e históricas del cliente")
    d.add_message('ctrl', 'hist', 0.71, "4. GET: recuperar traza de estados, fechas y probador asignado")
    d.add_message('ctrl', 'ui', 0.66, "5. Response 200 (listado con estado: Pendiente, Preparada, Expirada)", is_return=True)
    d.add_message('ui', 'actor', 0.61, "6. Renderizar tarjetas de reservas y código QR")
    d.add_message('actor', 'modal', 0.57, "7. Clic en 'Cancelar Reserva' e ingresar motivo")
    d.add_message('modal', 'ctrl', 0.52, "8. POST /api/v1/reservas/{id}/cancelar (motivo)")

    d.add_frame(
        "alt", "[Reserva en estado 'pendiente' o 'preparada']",
        0.03, 0.98, 0.49, 0.14,
        divider_y=0.25,
        else_guard="[else: Reserva ya completada o expirada]"
    )
    d.add_message('ctrl', 'res', 0.45, "9. PATCH / UPDATE: estado = 'cancelada', cancelada_en = now()")
    d.add_message('ctrl', 'hist', 0.40, "10. POST: registrar transición a 'cancelada'")
    d.add_message('ctrl', 'inv', 0.35, "11. PATCH / UPDATE: stock_reservado = stock_reservado - cant")
    d.add_message('ctrl', 'aud', 0.30, "12. POST: auditar evento reserva.cancelada")
    d.add_message('ctrl', 'modal', 0.27, "13. Response 200 OK (reserva cancelada y stock liberado)", is_return=True)

    d.add_message('ctrl', 'modal', 0.21, "14. Error 400 Bad Request: 'La reserva ya no puede ser cancelada'", is_return=True)
    d.add_message('modal', 'actor', 0.17, "15. Mostrar mensaje de restricción en pantalla")

    png_path = os.path.join(output_dir, "secuencia_cu20_consulta_reservas.png")
    svg_path = os.path.join(output_dir, "secuencia_cu20_consulta_reservas.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-21: Preparación y Validación de Reservas (Staff de Tienda)
# ----------------------------------------------------------------------------------------
def generate_seq_cu21(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-21: PREPARACIÓN Y VALIDACIÓN DE RESERVAS (STAFF)",
        "Pick & Pack en Sucursal, Asignación de Probador y Reporte de Incidencias | Metodología ICONIX",
        width=19, height=14
    )
    d.y_lifeline_bottom = 0.04
    
    # 11 Participantes idénticos al Diagrama de Robustez de CU-21
    d.add_participant('actor', 'Encargado', 'actor', 0.048, 'Staff de Sucursal', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('bandeja_ui', 'BandejaReservas', 'boundary', 0.138, 'reservas-por-preparar', w=0.074, font_size=7.0, sub_size=5.8)
    d.add_participant('modal_prep', 'ModalPreparacion', 'boundary', 0.228, 'preparar-reserva.html', w=0.074, font_size=7.0, sub_size=5.8)
    d.add_participant('modal_inc', 'ModalIncidencia', 'boundary', 0.318, 'incidencia-stock.html', w=0.074, font_size=7.0, sub_size=5.8)
    
    d.add_participant('listar_ctrl', 'listar_reservas', 'control', 0.410, 'reserva_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('prep_ctrl', 'preparar_reserva', 'control', 0.502, 'reserva_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('inc_ctrl', 'registrar_incid', 'control', 0.595, 'reserva_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    
    d.add_participant('reserva', 'Reserva', 'entity', 0.690, 'db / reserva', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('historial', 'ReservaHistorial', 'entity', 0.785, 'db / historial_reserva', w=0.074, font_size=7.0, sub_size=5.8)
    d.add_participant('inventario', 'Inventario', 'entity', 0.880, 'db / inventario', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.965, 'db / bitacora', w=0.060, font_size=6.8, sub_size=5.6)
    
    # 1. Consulta de reservas por preparar en sucursal
    d.add_message('actor', 'bandeja_ui', 0.85, "1. Acceder a bandeja de reservas por preparar en tienda")
    d.add_message('bandeja_ui', 'listar_ctrl', 0.81, "2. GET /api/v1/reservas/por-preparar")
    d.add_message('listar_ctrl', 'reserva', 0.77, "3. GET: filtrar por sucursal y 'pendiente'")
    d.add_message('listar_ctrl', 'bandeja_ui', 0.73, "4. Response 200 OK (reservas pendientes para Pick & Pack)", is_return=True)
    d.add_message('bandeja_ui', 'actor', 0.68, "5. Visualizar listado de prendas y probadores asignables", is_return=True)
    
    # 2. alt frame: Preparación exitosa vs Incidencia física
    d.add_frame(
        "alt", "[Prendas en perchero y probador físico disponible]",
        0.02, 0.99, 0.64, 0.06,
        divider_y=0.34,
        else_guard="[else: Prenda dañada / extraviada en tienda (Reporte de Incidencia)]"
    )
    
    # Camino Exitoso: Preparar reserva y asignar probador
    d.add_message('actor', 'modal_prep', 0.60, "6. Seleccionar reserva, abrir modal y asignar probador 'P1'")
    d.add_message('modal_prep', 'prep_ctrl', 0.55, "7. POST /api/v1/reservas/{id}/preparar (probador asignado)")
    d.add_message('prep_ctrl', 'reserva', 0.50, "8. PATCH: estado='preparada', probador='P1'")
    d.add_message('prep_ctrl', 'historial', 0.46, "9. POST: historial: pendiente -> preparada")
    d.add_message('prep_ctrl', 'auditoria', 0.42, "10. POST: auditar preparacion física")
    d.add_message('prep_ctrl', 'modal_prep', 0.38, "11. Response 200 OK (probador asignado y prendas listas)", is_return=True)
    
    # Camino Alternativo: Reportar Incidencia de Stock
    d.add_message('actor', 'modal_inc', 0.29, "12. Detectar anomalía física y abrir modal de incidencia")
    d.add_message('modal_inc', 'inc_ctrl', 0.25, "13. POST /api/v1/reservas/{id}/incidencia (prenda dañada/extraviada)")
    d.add_message('inc_ctrl', 'reserva', 0.21, "14. PATCH: estado='incidencia_stock'")
    d.add_message('inc_ctrl', 'historial', 0.17, "15. POST: historial: incidencia")
    d.add_message('inc_ctrl', 'inventario', 0.13, "16. PATCH / UPDATE: liberar reserva del ítem dañado")
    d.add_message('inc_ctrl', 'auditoria', 0.09, "17. POST: auditar incidencia de prenda")
    
    png_path = os.path.join(output_dir, "secuencia_cu21_preparacion_reservas.png")
    svg_path = os.path.join(output_dir, "secuencia_cu21_preparacion_reservas.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-22: Carrito de Compras y Checkout Omnicanal
# ----------------------------------------------------------------------------------------
def generate_seq_cu22(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-22: CARRITO DE COMPRAS Y CHECKOUT OMNICANAL",
        "Validación de Stock, Cupones de Descuento, Opciones de Entrega y Creación de Orden | Metodología ICONIX"
    )
    d.add_participant('actor', 'Cliente', 'actor', 0.06, 'Comprador online')
    d.add_participant('cart_ui', 'CarritoComponent', 'boundary', 0.18, 'carrito.html')
    d.add_participant('check_ui', 'CheckoutComponent', 'boundary', 0.31, 'checkout.html')
    d.add_participant('ctrl', 'checkout_ctrl', 'control', 0.46, 'checkout_service.py')
    d.add_participant('cupon', 'Cupon', 'entity', 0.59, 'db / cupon')
    d.add_participant('inv', 'Inventario', 'entity', 0.72, 'db / inventario')
    d.add_participant('venta', 'Venta', 'entity', 0.84, 'db / venta')
    d.add_participant('envio', 'Envio', 'entity', 0.92, 'db / envio')
    d.add_participant('aud', 'Auditoria', 'entity', 0.97, 'db / bitacora')

    d.add_message('actor', 'cart_ui', 0.84, "1. Modificar carrito e ingresar código de cupón")
    d.add_message('cart_ui', 'ctrl', 0.80, "2. POST /api/v1/checkout/validar (cupon_codigo, tipo_entrega)")
    d.add_message('ctrl', 'cupon', 0.76, "3. GET: validar vigencia, usos y porcentaje descuento")
    d.add_message('ctrl', 'inv', 0.71, "4. GET: verificar disponibilidad de stock por variante")
    d.add_message('ctrl', 'cart_ui', 0.67, "5. Response 200 (descuento aplicado y totales)", is_return=True)
    d.add_message('actor', 'check_ui', 0.63, "6. Seleccionar entrega (domicilio / recojo en tienda) y confirmar orden")
    d.add_message('check_ui', 'ctrl', 0.58, "7. POST /api/v1/checkout/orden (Idempotency-Key en Header)")

    d.add_frame(
        "alt", "[Stock verificado e Idempotencia garantizada]",
        0.03, 0.98, 0.55, 0.14,
        divider_y=0.25,
        else_guard="[else: Stock insuficiente por compra concurrente]"
    )
    d.add_message('ctrl', 'venta', 0.51, "8. POST: crear venta y detalle (estado='pendiente_pago')")
    d.add_message('ctrl', 'envio', 0.46, "9. POST: registrar orden de envío o recojo en tienda")
    d.add_message('ctrl', 'cupon', 0.41, "10. PATCH: registrar uso del cupón de descuento")
    d.add_message('ctrl', 'aud', 0.36, "11. POST: auditar creación de orden omnicanal")
    d.add_message('ctrl', 'check_ui', 0.31, "12. Response 201 Created (orden_id, paso: 'pagar')", is_return=True)
    d.add_message('check_ui', 'actor', 0.27, "13. Redirigir a pasarela de pagos (CU-24)")

    d.add_message('ctrl', 'check_ui', 0.21, "14. Error 409 Conflict: 'Variante sin stock'", is_return=True)
    d.add_message('check_ui', 'actor', 0.17, "15. Notificar al cliente para ajustar carrito")

    png_path = os.path.join(output_dir, "secuencia_cu22_checkout_carrito.png")
    svg_path = os.path.join(output_dir, "secuencia_cu22_checkout_carrito.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-23: Punto de Venta (POS) - Caja y Facturación
# ----------------------------------------------------------------------------------------
def generate_seq_cu23(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-23: PUNTO DE VENTA (POS) - CAJA Y FACTURACIÓN",
        "Escaneo Barcode, Descuento Atómico de Stock, Kárdex, Venta Pagada y Emisión de Ticket | Metodología ICONIX",
        width=20, height=14
    )
    # 13 Participantes idénticos al Diagrama de Robustez de CU-23
    d.add_participant('cajero', 'Cajero', 'actor', 0.045, 'Mostrador POS', w=0.065, font_size=7.6, sub_size=6.2)
    d.add_participant('pos_ui', 'PantallaPOS', 'boundary', 0.120, 'pos-mostrador.html', w=0.068, font_size=7.2, sub_size=6.0)
    d.add_participant('cobro_ui', 'ModalCobroPOS', 'boundary', 0.198, 'pos-cobro.html', w=0.068, font_size=7.2, sub_size=6.0)
    d.add_participant('ticket_ui', 'TicketImpresion', 'boundary', 0.276, 'pos-ticket.html', w=0.068, font_size=7.2, sub_size=6.0)
    
    d.add_participant('buscar_ctrl', 'buscar_por_barcode', 'control', 0.355, 'pos_service.py', w=0.070, font_size=7.2, sub_size=6.0)
    d.add_participant('venta_ctrl', 'procesar_venta_pos', 'control', 0.435, 'pos_service.py', w=0.070, font_size=7.2, sub_size=6.0)
    d.add_participant('ticket_ctrl', 'generar_ticket', 'control', 0.515, 'pos_service.py', w=0.068, font_size=7.2, sub_size=6.0)
    
    d.add_participant('var', 'PrendaVariante', 'entity', 0.595, 'db / variante', w=0.068, font_size=7.2, sub_size=6.0)
    d.add_participant('inv', 'Inventario', 'entity', 0.675, 'db / inventario', w=0.068, font_size=7.2, sub_size=6.0)
    d.add_participant('mov', 'Kardex', 'entity', 0.755, 'db / kardex', w=0.068, font_size=7.2, sub_size=6.0)
    d.add_participant('venta', 'Venta / Detalle', 'entity', 0.835, 'db / venta', w=0.068, font_size=7.2, sub_size=6.0)
    d.add_participant('pago', 'Pago', 'entity', 0.910, 'db / pago', w=0.065, font_size=7.2, sub_size=6.0)
    d.add_participant('aud', 'BitacoraAuditoria', 'entity', 0.975, 'db / bitacora', w=0.055, font_size=6.8, sub_size=5.8)
    
    # 1. Escaneo Barcode
    d.add_message('cajero', 'pos_ui', 0.84, "1. Escanear código de barras o SKU")
    d.add_message('pos_ui', 'buscar_ctrl', 0.80, "2. GET /api/v1/pos/scanner (código de barras o SKU)")
    d.add_message('buscar_ctrl', 'var', 0.76, "3. GET: identificar variante por código")
    d.add_message('buscar_ctrl', 'inv', 0.72, "4. GET: verificar stock local sucursal")
    d.add_message('buscar_ctrl', 'pos_ui', 0.68, "5. Response 200 (variante encontrada, precio, existencias)", is_return=True)
    d.add_message('pos_ui', 'cajero', 0.65, "6. Añadir ítem a la línea de venta activa", is_return=True)
    
    # 2. Cobro presencial
    d.add_message('cajero', 'cobro_ui', 0.61, "7. Abrir modal y confirmar cobro (efectivo/tarjeta)")
    d.add_message('cobro_ui', 'venta_ctrl', 0.57, "8. POST /api/v1/pos/ventas (items, pago, cliente)")
    
    # alt: Stock disponible vs insuficiente
    d.add_frame(
        "alt", "[Stock físico disponible en mostrador]",
        0.02, 0.99, 0.54, 0.22,
        divider_y=0.29,
        else_guard="[else: Stock insuficiente en sucursal]"
    )
    d.add_message('venta_ctrl', 'inv', 0.50, "9. PATCH / UPDATE: descontar stock_fisico (-)")
    d.add_message('venta_ctrl', 'mov', 0.46, "10. POST: kárdex inmutable tipo 'salida_pos'")
    d.add_message('venta_ctrl', 'venta', 0.42, "11. POST: crear venta estado 'pagada'")
    d.add_message('venta_ctrl', 'pago', 0.38, "12. POST: registrar pago contado / cambio")
    d.add_message('venta_ctrl', 'aud', 0.34, "13. POST: auditar venta presencial")
    d.add_message('venta_ctrl', 'cobro_ui', 0.30, "14. Response 200 OK (venta_id, pago_id)", is_return=True)
    
    d.add_message('venta_ctrl', 'cobro_ui', 0.26, "15. Error 409 Conflict: 'Stock insuficiente'", is_return=True)
    d.add_message('cobro_ui', 'cajero', 0.23, "16. Notificar alerta de falta de existencias", is_return=True)
    
    # 3. Emisión de Ticket
    d.add_message('cajero', 'ticket_ui', 0.19, "17. Solicitar emisión de ticket de venta")
    d.add_message('ticket_ui', 'ticket_ctrl', 0.15, "18. GET /api/v1/pos/ventas/{id}/ticket")
    d.add_message('ticket_ctrl', 'venta', 0.12, "19. GET: recuperar cabecera, líneas y pago")
    d.add_message('ticket_ctrl', 'ticket_ui', 0.09, "20. Response 200 (datos de comprobante fiscal y QR)", is_return=True)
    d.add_message('ticket_ui', 'cajero', 0.06, "21. Imprimir ticket térmico y entregar al cliente", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu23_punto_venta_pos.png")
    svg_path = os.path.join(output_dir, "secuencia_cu23_punto_venta_pos.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-24: Procesamiento de Pagos, Pasarelas y Reembolsos
# ----------------------------------------------------------------------------------------
def generate_seq_cu24(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-24: PROCESAMIENTO DE PAGOS, PASARELAS Y REEMBOLSOS",
        "PaymentIntent Stripe, Webhook con Firma Criptográfica, Polling e Idempotencia | Metodología ICONIX",
        width=19, height=14
    )
    # 11 Participantes idénticos al Diagrama de Robustez de CU-24
    d.add_participant('actor', 'Cliente / Stripe', 'actor', 0.050, 'Usuario / Pasarela', w=0.075, font_size=7.5, sub_size=6.2)
    d.add_participant('elements_ui', 'StripeElements', 'boundary', 0.140, 'stripe-elements.html', w=0.075, font_size=7.5, sub_size=6.2)
    d.add_participant('webhook_ui', 'WebhookEndpoint', 'boundary', 0.230, 'API Webhook Pública', w=0.075, font_size=7.5, sub_size=6.2)
    d.add_participant('confirm_ui', 'ConfirmacionPago', 'boundary', 0.320, 'pago-confirmado.html', w=0.075, font_size=7.5, sub_size=6.2)
    
    d.add_participant('intencion_ctrl', 'crear_intencion', 'control', 0.415, 'pago_service.py', w=0.075, font_size=7.5, sub_size=6.2)
    d.add_participant('webhook_ctrl', 'procesar_webhook', 'control', 0.510, 'pago_service.py', w=0.075, font_size=7.5, sub_size=6.2)
    d.add_participant('polling_ctrl', 'consultar_polling', 'control', 0.605, 'pago_service.py', w=0.075, font_size=7.5, sub_size=6.2)
    
    d.add_participant('pago', 'Pago', 'entity', 0.700, 'db / pago', w=0.075, font_size=7.5, sub_size=6.2)
    d.add_participant('stripe_ev', 'StripeEvento', 'entity', 0.795, 'db / stripe_evento', w=0.075, font_size=7.5, sub_size=6.2)
    d.add_participant('venta', 'Venta', 'entity', 0.885, 'db / venta', w=0.072, font_size=7.5, sub_size=6.2)
    d.add_participant('aud', 'BitacoraAuditoria', 'entity', 0.965, 'db / bitacora', w=0.062, font_size=7.0, sub_size=5.8)
    
    # 1. Creación de Intención de Pago
    d.add_message('actor', 'elements_ui', 0.84, "1. Seleccionar 'Pagar con Tarjeta' en checkout")
    d.add_message('elements_ui', 'intencion_ctrl', 0.80, "2. POST /api/v1/pagos/intencion (orden_id, metodo)")
    d.add_message('intencion_ctrl', 'venta', 0.76, "3. GET: verificar orden pendiente")
    d.add_message('intencion_ctrl', 'pago', 0.72, "4. POST: crear pago 'pendiente' (client_secret)")
    d.add_message('intencion_ctrl', 'elements_ui', 0.68, "5. Response 200 (client_secret para montar tarjeta)", is_return=True)
    d.add_message('elements_ui', 'actor', 0.64, "6. Montar formulario seguro de Stripe Elements", is_return=True)
    
    # 2. Webhook Asíncrono de Confirmación (Pasarela Stripe)
    d.add_message('actor', 'webhook_ui', 0.59, "7. POST /api/v1/pagos/webhook/stripe (Stripe-Signature, evento)")
    d.add_message('webhook_ui', 'webhook_ctrl', 0.55, "8. procesar_webhook(payload, signature)")
    
    # alt: Firma válida vs inválida
    d.add_frame(
        "alt", "[Firma criptográfica válida y evento no duplicado]",
        0.02, 0.99, 0.52, 0.25,
        divider_y=0.31,
        else_guard="[else: Firma inválida o evento duplicado (Replay)]"
    )
    d.add_message('webhook_ctrl', 'stripe_ev', 0.48, "9. POST: registrar evento (prevenir replay)")
    d.add_message('webhook_ctrl', 'pago', 0.44, "10. PATCH: marcar pago 'completado'")
    d.add_message('webhook_ctrl', 'venta', 0.40, "11. PATCH: actualizar venta a 'pagada'")
    d.add_message('webhook_ctrl', 'aud', 0.36, "12. POST: auditar cobro pasarela")
    d.add_message('webhook_ctrl', 'webhook_ui', 0.32, "13. Response 200 {'received': True}", is_return=True)
    
    d.add_message('webhook_ctrl', 'webhook_ui', 0.27, "14. Response 400 Bad Request o ignore duplicado", is_return=True)
    
    # 3. Polling de Confirmación en Frontend
    d.add_message('actor', 'confirm_ui', 0.21, "15. Cliente espera confirmación en pantalla")
    d.add_message('confirm_ui', 'polling_ctrl', 0.17, "16. GET /api/v1/pagos/{id}/polling")
    d.add_message('polling_ctrl', 'pago', 0.13, "17. GET: consultar estado actual del pago")
    d.add_message('polling_ctrl', 'confirm_ui', 0.09, "18. Response 200 (estado='completado', venta_id)", is_return=True)
    d.add_message('confirm_ui', 'actor', 0.06, "19. Redirigir a comprobante de compra exitosa", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu24_procesamiento_pagos.png")
    svg_path = os.path.join(output_dir, "secuencia_cu24_procesamiento_pagos.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-25: Descargar Catálogo Offline
# ----------------------------------------------------------------------------------------
def generate_seq_cu25(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-25: DESCARGAR CATÁLOGO OFFLINE",
        "Descarga de Lote Multitenant, Almacenamiento en IndexedDB/SQLite y Caché Local | Metodología ICONIX",
        width=18, height=13
    )
    # 9 Participantes idénticos al Diagrama de Robustez de CU-25
    d.add_participant('actor', 'Cliente / Cajero', 'actor', 0.055, 'Dispositivo Offline (PWA)', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('cat_ui', 'CatalogoOffline', 'boundary', 0.160, 'catalogo-offline.html', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('sw_cache', 'ServiceWorkerCache', 'boundary', 0.270, 'IndexedDB/SQLite View', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('desc_ctrl', 'descargar_catalogo', 'control', 0.385, 'sync_service.py', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('persist_ctrl', 'persistir_local', 'control', 0.500, 'IDB/SQLite Controller', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('empresa', 'Empresa', 'entity', 0.615, 'db / empresa', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('prenda', 'Prenda', 'entity', 0.725, 'db / prenda', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('variante', 'Variante', 'entity', 0.835, 'db / variante', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('inventario', 'Inventario', 'entity', 0.945, 'db / inventario', w=0.075, font_size=7.2, sub_size=6.0)
    
    # Mensajes
    d.add_message('actor', 'cat_ui', 0.84, "1. Solicitar sincronización de catálogo offline")
    d.add_message('cat_ui', 'desc_ctrl', 0.80, "2. GET /api/v1/sync/catalogo-offline (sucursal_id)")
    d.add_message('desc_ctrl', 'empresa', 0.75, "3. GET: verificar tenant activo")
    d.add_message('desc_ctrl', 'prenda', 0.70, "4. GET: consultar prendas activas")
    d.add_message('desc_ctrl', 'variante', 0.65, "5. GET: obtener variantes, precios y tallas")
    d.add_message('desc_ctrl', 'inventario', 0.60, "6. GET: descargar existencias sucursal")
    d.add_message('desc_ctrl', 'cat_ui', 0.55, "7. Response 200 OK (lote de catálogo estructurado)", is_return=True)
    
    d.add_message('cat_ui', 'sw_cache', 0.49, "8. Notificar lote descargado a Service Worker")
    d.add_message('sw_cache', 'persist_ctrl', 0.44, "9. almacenarLoteLocal(prendas, variantes, stock)")
    
    d.add_frame(
        "loop", "[Por cada registro de prendas, variantes e inventario]",
        0.44, 0.98, 0.40, 0.22
    )
    d.add_message('persist_ctrl', 'persist_ctrl', 0.35, "10. PUT / POST: sincronizar tabla local SQLite/IDB", self_call=True)
    d.add_message('persist_ctrl', 'sw_cache', 0.27, "11. Confirmar lote local indexado y persistido", is_return=True)
    
    d.add_message('sw_cache', 'cat_ui', 0.17, "12. Actualizar estado de caché offline (100% disponible)", is_return=True)
    d.add_message('cat_ui', 'actor', 0.11, "13. Notificar 'Catálogo listo para operar sin conexión'", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu25_descargar_catalogo_offline.png")
    svg_path = os.path.join(output_dir, "secuencia_cu25_descargar_catalogo_offline.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-26: Registrar Reserva Offline
# ----------------------------------------------------------------------------------------
def generate_seq_cu26(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-26: REGISTRAR RESERVA OFFLINE",
        "Generación de UUID v4 en Cliente, Registro en Cola Offline y Descuento de Stock Local | Metodología ICONIX",
        width=18, height=13
    )
    # 8 Participantes idénticos al Diagrama de Robustez de CU-26
    d.add_participant('actor', 'Cliente', 'actor', 0.065, 'Usuario sin conexión', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('form_ui', 'FormularioReserva', 'boundary', 0.190, 'reserva-offline.html', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('voucher_ui', 'VoucherLocalView', 'boundary', 0.320, 'voucher-local.html (UUID)', w=0.080, font_size=7.5, sub_size=6.2)
    
    d.add_participant('uuid_ctrl', 'generar_uuid_local', 'control', 0.455, 'UUID v4 Generador Cliente', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('sync_ctrl', 'registrar_reserva', 'control', 0.590, 'sync_service.py', w=0.080, font_size=7.5, sub_size=6.2)
    
    d.add_participant('op_pend', 'OperacionPendiente', 'entity', 0.725, 'db / operacion_pendiente', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('inv_local', 'InventarioLocal', 'entity', 0.850, 'IDB/SQLite Inventario', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.955, 'db / bitacora', w=0.065, font_size=7.0, sub_size=5.8)
    
    d.add_message('actor', 'form_ui', 0.84, "1. Solicitar reserva de prenda en modo offline")
    d.add_message('form_ui', 'uuid_ctrl', 0.79, "2. solicitarReservaOffline(prendas, fecha_visita)")
    d.add_message('uuid_ctrl', 'uuid_ctrl', 0.74, "3. emitirUUID() (asignar identificador cliente)", self_call=True)
    d.add_message('uuid_ctrl', 'sync_ctrl', 0.68, "4. POST /api/v1/sync/reservas-offline (payload encolado)")
    
    d.add_frame(
        "alt", "[Stock local disponible en almacenamiento del cliente]",
        0.03, 0.98, 0.63, 0.22,
        divider_y=0.33,
        else_guard="[else: Existencias locales agotadas]"
    )
    d.add_message('sync_ctrl', 'op_pend', 0.58, "5. POST / INSERT: encolar op 'reserva_offline' (pendiente)")
    d.add_message('sync_ctrl', 'inv_local', 0.52, "6. PATCH: descontar stock_disponible local")
    d.add_message('sync_ctrl', 'auditoria', 0.46, "7. POST: auditar registro offline")
    d.add_message('sync_ctrl', 'voucher_ui', 0.40, "8. Renderizar voucher local con UUID y código QR", is_return=True)
    d.add_message('voucher_ui', 'actor', 0.35, "9. Entregar comprobante provisional (pendiente_sync)", is_return=True)
    
    d.add_message('sync_ctrl', 'form_ui', 0.29, "10. Error: Prenda agotada en caché local", is_return=True)
    d.add_message('form_ui', 'actor', 0.25, "11. Mostrar notificación de stock no disponible", is_return=True)
    
    d.add_message('voucher_ui', 'actor', 0.15, "12. Notificar sincronización en segundo plano al reconectar", is_return=True)
    d.add_message('voucher_ui', 'actor', 0.08, "13. Operación encolada en IndexedDB con estado 'pendiente'", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu26_registrar_reserva_offline.png")
    svg_path = os.path.join(output_dir, "secuencia_cu26_registrar_reserva_offline.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-27: Bloquear Stock Soft-Lock con TTL
# ----------------------------------------------------------------------------------------
def generate_seq_cu27(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-27: BLOQUEAR STOCK SOFT-LOCK CON TTL",
        "Bloqueo Temporal de Existencias con TTL de 45 Minutos y Liberación Automática | Metodología ICONIX",
        width=18, height=13
    )
    # 9 Participantes idénticos al Diagrama de Robustez de CU-27
    d.add_participant('actor', 'Cliente / Terminal', 'actor', 0.055, 'Terminal Desconectado', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('detalle_ui', 'DetallePrenda', 'boundary', 0.160, 'prenda-detalle.html', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('badge_ui', 'BadgeTTL', 'boundary', 0.270, 'Badge Reservado 45 min', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('crear_ctrl', 'crear_soft_lock', 'control', 0.385, 'sync_service.py', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('expira_ctrl', 'verificar_expira', 'control', 0.500, 'TTL Check Controller', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('liberar_ctrl', 'liberar_soft_lock', 'control', 0.615, 'sync_service.py', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('softlock', 'SoftLock', 'entity', 0.730, 'db / soft_lock (45m)', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('inventario', 'Inventario', 'entity', 0.840, 'db / inventario', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.948, 'db / bitacora', w=0.068, font_size=7.0, sub_size=5.8)
    
    d.add_message('actor', 'detalle_ui', 0.85, "1. Iniciar reserva de prenda")
    d.add_message('detalle_ui', 'crear_ctrl', 0.81, "2. POST /api/v1/sync/soft-locks (variante_id, cantidad, dispositivo)")
    d.add_message('crear_ctrl', 'inventario', 0.77, "3. GET: verificar stock no bloqueado")
    d.add_message('crear_ctrl', 'softlock', 0.72, "4. POST / INSERT: crear soft_lock (expira_en=now+45m)")
    d.add_message('crear_ctrl', 'badge_ui', 0.67, "5. Inicializar temporizador de 45 minutos")
    d.add_message('badge_ui', 'actor', 0.63, "6. Mostrar insignia 'Reservado por 45 min'", is_return=True)
    
    d.add_message('badge_ui', 'expira_ctrl', 0.57, "7. comprobarTTL() (tiempo transcurrido)")
    d.add_message('expira_ctrl', 'softlock', 0.52, "8. GET: consultar expira_en vs now()")
    
    d.add_frame(
        "alt", "[TTL expirado > 45 min y sin confirmación]",
        0.03, 0.98, 0.48, 0.17,
        divider_y=0.28,
        else_guard="[else: Venta confirmada dentro del tiempo límite]"
    )
    d.add_message('expira_ctrl', 'liberar_ctrl', 0.43, "9. [TTL expirado > 45 min] liberar bloqueo")
    d.add_message('liberar_ctrl', 'softlock', 0.38, "10. DELETE: eliminar soft_lock expirado")
    d.add_message('liberar_ctrl', 'auditoria', 0.33, "11. POST: auditar liberación por TTL")
    d.add_message('liberar_ctrl', 'badge_ui', 0.29, "12. Notificar liberación de prenda", is_return=True)
    
    d.add_message('expira_ctrl', 'softlock', 0.24, "13. Mantener soft-lock activo y proceder al cobro")
    d.add_message('badge_ui', 'actor', 0.13, "14. Mostrar alerta: 'Tiempo agotado, prenda devuelta al stock general'", is_return=True)
    d.add_message('detalle_ui', 'actor', 0.07, "15. Actualizar vista de prenda con inventario liberado", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu27_bloquear_stock_soft_lock.png")
    svg_path = os.path.join(output_dir, "secuencia_cu27_bloquear_stock_soft_lock.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-28: Venta de Contado Offline
# ----------------------------------------------------------------------------------------
def generate_seq_cu28(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-28: VENTA DE CONTADO OFFLINE",
        "Cobro en Efectivo sin Conexión, Cola OperacionPendiente y Ticket Preliminar | Metodología ICONIX",
        width=19, height=14
    )
    # 10 Participantes idénticos al Diagrama de Robustez de CU-28
    d.add_participant('actor', 'Cajero', 'actor', 0.050, 'Mostrador Desconectado', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('pos_ui', 'POSOffline', 'boundary', 0.145, 'pos-offline.component', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('modal_cobro', 'ModalCobroEfectivo', 'boundary', 0.245, 'cobro-efectivo-offline', w=0.074, font_size=7.0, sub_size=5.8)
    d.add_participant('ticket_view', 'TicketPreliminar', 'boundary', 0.350, 'Ticket PENDIENTE', w=0.072, font_size=7.2, sub_size=6.0)
    
    d.add_participant('venta_ctrl', 'asentar_venta', 'control', 0.460, 'sync_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('ticket_ctrl', 'generar_ticket', 'control', 0.570, 'pos_offline_service', w=0.072, font_size=7.2, sub_size=6.0)
    
    d.add_participant('op_pend', 'OperacionPendiente', 'entity', 0.680, 'db / operacion_pendiente', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('inv_local', 'InventarioLocal', 'entity', 0.790, 'SQLite / IDB Inventario', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('venta', 'Venta', 'entity', 0.890, 'db / venta (pendiente_sync)', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.965, 'db / bitacora', w=0.060, font_size=6.8, sub_size=5.6)
    
    d.add_message('actor', 'pos_ui', 0.85, "1. Registrar prendas seleccionadas en terminal offline")
    d.add_message('pos_ui', 'modal_cobro', 0.81, "2. Desplegar modal para pago en efectivo")
    d.add_message('actor', 'modal_cobro', 0.77, "3. Ingresar efectivo recibido y confirmar cobro")
    d.add_message('modal_cobro', 'venta_ctrl', 0.73, "4. confirmarCobroLocal()")
    d.add_message('pos_ui', 'venta_ctrl', 0.69, "5. POST /api/v1/sync/ventas-offline (datos venta, efectivo recibido)")
    
    d.add_message('venta_ctrl', 'op_pend', 0.64, "6. POST / INSERT: guardar en operacion_pendiente (uuid)")
    d.add_message('venta_ctrl', 'inv_local', 0.59, "7. PATCH / UPDATE: reducir stock físico local")
    d.add_message('venta_ctrl', 'ticket_ctrl', 0.54, "8. imprimirComprobante() (leyenda sync)")
    
    d.add_message('ticket_ctrl', 'venta', 0.49, "9. POST / INSERT: venta local 'pendiente_sync'")
    d.add_message('ticket_ctrl', 'auditoria', 0.44, "10. POST: auditar cobro en efectivo offline")
    d.add_message('ticket_ctrl', 'ticket_view', 0.39, "11. Enviar datos de comprobante para impresión física")
    d.add_message('ticket_view', 'actor', 0.34, "12. Imprimir ticket preliminar con marca 'PENDIENTE DE SINCRONIZACIÓN'", is_return=True)
    
    d.add_message('venta_ctrl', 'modal_cobro', 0.28, "13. Transacción local exitosa (en cola)", is_return=True)
    d.add_message('modal_cobro', 'pos_ui', 0.22, "14. Cerrar modal de cobro y reiniciar mostrador", is_return=True)
    d.add_message('pos_ui', 'actor', 0.15, "15. Notificar: Venta registrada en dispositivo, lista para sincronizar", is_return=True)
    d.add_message('ticket_view', 'actor', 0.08, "16. Entregar ticket impreso al cliente", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu28_venta_contado_offline.png")
    svg_path = os.path.join(output_dir, "secuencia_cu28_venta_contado_offline.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-29: Validar Comprobante y Cambio QR Offline
# ----------------------------------------------------------------------------------------
def generate_seq_cu29(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-29: VALIDAR COMPROBANTE Y CAMBIO QR OFFLINE",
        "Validación Criptográfica HMAC-SHA256, Reingreso y Salida de Inventario sin Internet | Metodología ICONIX",
        width=18, height=13
    )
    # 9 Participantes idénticos al Diagrama de Robustez de CU-29
    d.add_participant('actor', 'Cajero', 'actor', 0.055, 'Mostrador / Devoluciones', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('qr_ui', 'LectorQRCambios', 'boundary', 0.160, 'lector-qr-cambio.html', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('nota_ui', 'FormNotaCambio', 'boundary', 0.270, 'nota-cambio-form.html', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('qr_ctrl', 'validar_qr', 'control', 0.385, 'HMAC-SHA256 Controller', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('cambio_ctrl', 'procesar_cambio', 'control', 0.500, 'sync_service.py', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('venta', 'Venta', 'entity', 0.615, 'db / venta (ticket)', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('nota_cambio', 'NotaCambio', 'entity', 0.725, 'db / nota_cambio', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('inventario', 'Inventario', 'entity', 0.835, 'db / inventario (+ / -)', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.948, 'db / bitacora', w=0.068, font_size=7.0, sub_size=5.8)
    
    d.add_message('actor', 'qr_ui', 0.85, "1. Escanear código QR de ticket impreso")
    d.add_message('qr_ui', 'qr_ctrl', 0.81, "2. POST /api/v1/sync/validar-qr (qr_data)")
    d.add_message('qr_ctrl', 'venta', 0.76, "3. GET: verificar firma HMAC y venta original")
    
    d.add_frame(
        "alt", "[Firma criptográfica válida y dentro del período de cambio]",
        0.03, 0.98, 0.72, 0.20,
        divider_y=0.33,
        else_guard="[else: Firma inválida o ticket alterado]"
    )
    d.add_message('qr_ctrl', 'qr_ui', 0.67, "4. Retornar ticket original válido y prendas elegibles", is_return=True)
    d.add_message('qr_ui', 'nota_ui', 0.62, "5. Cargar formulario para cambio de prenda")
    d.add_message('actor', 'nota_ui', 0.57, "6. Seleccionar prenda devuelta y nueva prenda")
    d.add_message('nota_ui', 'cambio_ctrl', 0.52, "7. POST /api/v1/sync/nota-cambio (variante_devuelta, nueva, firma)")
    
    d.add_message('cambio_ctrl', 'nota_cambio', 0.47, "8. POST / INSERT: emitir nota_cambio con firma QR")
    d.add_message('cambio_ctrl', 'inventario', 0.42, "9. PATCH / UPDATE: reingresar devuelta (+) y descontar nueva (-)")
    d.add_message('cambio_ctrl', 'auditoria', 0.37, "10. POST: auditar cambio de prenda")
    
    d.add_message('qr_ctrl', 'qr_ui', 0.28, "11. Error: Firma QR apócrifa o ticket fuera de plazo", is_return=True)
    d.add_message('qr_ui', 'actor', 0.24, "12. Notificar rechazo de cambio al cajero", is_return=True)
    
    d.add_message('cambio_ctrl', 'nota_ui', 0.15, "13. Comprobante de cambio generado exitosamente", is_return=True)
    d.add_message('nota_ui', 'actor', 0.08, "14. Imprimir nota de cambio física con nuevo hash QR", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu29_validar_qr_cambio_offline.png")
    svg_path = os.path.join(output_dir, "secuencia_cu29_validar_qr_cambio_offline.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-30: Consultar Cola de Operaciones Offline
# ----------------------------------------------------------------------------------------
def generate_seq_cu30(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-30: CONSULTAR COLA DE OPERACIONES OFFLINE",
        "Inspección FIFO, Filtro por Estados y Auditoría de Sincronización Pendiente | Metodología ICONIX",
        width=18, height=13
    )
    # 8 Participantes idénticos al Diagrama de Robustez de CU-30
    d.add_participant('actor', 'Cajero / Admin', 'actor', 0.065, 'Monitor de Sync', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('cola_ui', 'ColaOperaciones', 'boundary', 0.190, 'cola-sync.component', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('modal_ui', 'DetalleModal', 'boundary', 0.320, 'operacion-detalle.html', w=0.080, font_size=7.5, sub_size=6.2)
    
    d.add_participant('cola_ctrl', 'consultar_cola', 'control', 0.455, 'sync_service.py', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('filtro_ctrl', 'filtrar_estado', 'control', 0.590, 'sync_service.py', w=0.080, font_size=7.5, sub_size=6.2)
    
    d.add_participant('op_pend', 'OperacionPendiente', 'entity', 0.725, 'db / operacion_pendiente', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('sucursal', 'Sucursal', 'entity', 0.850, 'db / sucursal', w=0.080, font_size=7.5, sub_size=6.2)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.955, 'db / bitacora', w=0.065, font_size=7.0, sub_size=5.8)
    
    d.add_message('actor', 'cola_ui', 0.85, "1. Abrir monitor de sincronización")
    d.add_message('cola_ui', 'cola_ctrl', 0.80, "2. GET /api/v1/sync/cola (sucursal_id)")
    d.add_message('cola_ctrl', 'sucursal', 0.75, "3. GET: verificar sucursal asociada")
    d.add_message('cola_ctrl', 'op_pend', 0.70, "4. GET: listar operaciones pendientes (FIFO)")
    d.add_message('cola_ctrl', 'cola_ui', 0.65, "5. Renderizar lista de operaciones encoladas", is_return=True)
    
    d.add_message('actor', 'cola_ui', 0.59, "6. Seleccionar filtro por estado ('pendiente', 'conflicto')")
    d.add_message('cola_ui', 'filtro_ctrl', 0.54, "7. filtrarOperaciones(estado: pendiente, conflicto, resuelta)")
    d.add_message('filtro_ctrl', 'cola_ui', 0.49, "8. Actualizar vista de tabla con operaciones filtradas", is_return=True)
    
    d.add_message('actor', 'cola_ui', 0.43, "9. Clic en 'Ver Detalle' de una operación")
    d.add_message('cola_ui', 'modal_ui', 0.38, "10. Desplegar modal de inspección técnica")
    d.add_message('modal_ui', 'cola_ctrl', 0.33, "11. Solicitar payload completo y registro de errores")
    d.add_message('cola_ctrl', 'op_pend', 0.28, "12. GET: inspeccionar payload y errores")
    d.add_message('cola_ctrl', 'auditoria', 0.23, "13. POST: auditar inspección de cola")
    d.add_message('cola_ctrl', 'modal_ui', 0.17, "14. Devolver detalle JSON y trazabilidad de sincronización", is_return=True)
    d.add_message('modal_ui', 'actor', 0.11, "15. Mostrar visor JSON de payload y traza técnica", is_return=True)
    d.add_message('modal_ui', 'actor', 0.05, "16. Habilitar opciones de reintento o resolución manual", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu30_cola_operaciones_offline.png")
    svg_path = os.path.join(output_dir, "secuencia_cu30_cola_operaciones_offline.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-31: Sincronizar Operaciones Pendientes
# ----------------------------------------------------------------------------------------
def generate_seq_cu31(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-31: SINCRONIZAR OPERACIONES PENDIENTES",
        "Garantía de Idempotencia (RNF05), Procesamiento FIFO de Lotes y Commit Central | Metodología ICONIX",
        width=19, height=14
    )
    # 10 Participantes idénticos al Diagrama de Robustez de CU-31
    d.add_participant('actor', 'Sistema / Cajero', 'actor', 0.050, 'Disparador Sync', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('btn_ui', 'BotonSync', 'boundary', 0.145, 'sync-toolbar.component', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('modal_ui', 'SyncProgress', 'boundary', 0.245, 'sync-progress.modal', w=0.072, font_size=7.2, sub_size=6.0)
    
    d.add_participant('lote_ctrl', 'procesar_lote', 'control', 0.355, 'sync_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('idemp_ctrl', 'validar_idemp', 'control', 0.470, 'RNF05 Controller', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('asentar_ctrl', 'asentar_op', 'control', 0.580, 'FIFO Commit Controller', w=0.072, font_size=7.2, sub_size=6.0)
    
    d.add_participant('idemp_ent', 'SyncIdempotencia', 'entity', 0.690, 'db / sync_idempotencia', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('op_pend', 'OperacionPendiente', 'entity', 0.795, 'db / operacion_pendiente', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('venta_inv', 'Venta / Inventario', 'entity', 0.895, 'db / venta & inventario', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.965, 'db / bitacora', w=0.060, font_size=6.8, sub_size=5.6)
    
    d.add_message('actor', 'btn_ui', 0.85, "1. Disparar sincronización (manual o por reconexión)")
    d.add_message('btn_ui', 'modal_ui', 0.81, "2. Abrir modal y mostrar barra de progreso")
    d.add_message('btn_ui', 'lote_ctrl', 0.77, "3. POST /api/v1/sync (lote de operaciones)")
    
    d.add_frame(
        "loop", "[Por cada operación del lote en orden cronológico FIFO]",
        0.31, 0.98, 0.74, 0.23
    )
    d.add_message('lote_ctrl', 'idemp_ctrl', 0.70, "4. verificarClave() (idempotency_key)")
    d.add_message('idemp_ctrl', 'idemp_ent', 0.65, "5. GET / POST: comprobar/guardar idempotency_key")
    
    d.add_frame(
        "alt", "[Clave nueva - aplicar transacción]",
        0.42, 0.97, 0.61, 0.26,
        divider_y=0.34,
        else_guard="[else: Clave existente - replay sin duplicar]"
    )
    d.add_message('idemp_ctrl', 'asentar_ctrl', 0.56, "6. [clave nueva] aplicar transacción")
    d.add_message('asentar_ctrl', 'venta_inv', 0.50, "7. POST / PATCH: insertar venta y descontar stock central")
    d.add_message('asentar_ctrl', 'op_pend', 0.44, "8. PATCH: estado -> 'aplicada' o 'conflicto'")
    d.add_message('asentar_ctrl', 'auditoria', 0.38, "9. POST: auditar sincronización de lote")
    
    d.add_message('idemp_ctrl', 'lote_ctrl', 0.30, "10. Retornar respuesta previa (idempotente)", is_return=True)
    
    d.add_message('lote_ctrl', 'modal_ui', 0.18, "11. Actualizar progreso del lote: 100% procesado", is_return=True)
    d.add_message('modal_ui', 'btn_ui', 0.12, "12. Notificar lote sincronizado y cerrar modal", is_return=True)
    d.add_message('btn_ui', 'actor', 0.06, "13. Mostrar badge verde: 'Todas las operaciones sincronizadas'", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu31_sincronizar_operaciones.png")
    svg_path = os.path.join(output_dir, "secuencia_cu31_sincronizar_operaciones.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-32: Resolver Conflictos de Sincronización
# ----------------------------------------------------------------------------------------
def generate_seq_cu32(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-32: RESOLVER CONFLICTOS DE SINCRONIZACIÓN",
        "Arbitraje de Inconsistencias, Conciliación de Kárdex y Ajustes FIFO / Manual | Metodología ICONIX",
        width=18, height=13
    )
    # 9 Participantes idénticos al Diagrama de Robustez de CU-32
    d.add_participant('actor', 'Encargado / Admin', 'actor', 0.055, 'Resolutor Discrepancias', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('bandeja_ui', 'BandejaConflictos', 'boundary', 0.160, 'conflictos-sync.html', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('modal_ui', 'ModalResolucion', 'boundary', 0.270, 'resolver-conflicto.html', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('list_ctrl', 'listar_conflictos', 'control', 0.385, 'sync_service.py', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('res_ctrl', 'resolver_conflicto', 'control', 0.500, 'FIFO/Manual Controller', w=0.075, font_size=7.2, sub_size=6.0)
    
    d.add_participant('op_pend', 'OperacionPendiente', 'entity', 0.615, 'db / op_pendiente (conflicto)', w=0.075, font_size=7.0, sub_size=5.8)
    d.add_participant('inventario', 'Inventario', 'entity', 0.725, 'db / inventario (ajuste)', w=0.075, font_size=7.0, sub_size=5.8)
    d.add_participant('mov_inv', 'MovimientoInventario', 'entity', 0.835, 'db / mov_inventario', w=0.075, font_size=7.0, sub_size=5.8)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.948, 'db / bitacora', w=0.068, font_size=7.0, sub_size=5.8)
    
    d.add_message('actor', 'bandeja_ui', 0.85, "1. Abrir bandeja de conflictos de sincronización")
    d.add_message('bandeja_ui', 'list_ctrl', 0.81, "2. GET /api/v1/sync/conflictos (sucursal_id)")
    d.add_message('list_ctrl', 'op_pend', 0.76, "3. GET: recuperar operaciones en conflicto y error")
    d.add_message('list_ctrl', 'bandeja_ui', 0.71, "4. Renderizar lista de transacciones en conflicto", is_return=True)
    
    d.add_message('actor', 'bandeja_ui', 0.65, "5. Seleccionar conflicto específico a resolver")
    d.add_message('bandeja_ui', 'modal_ui', 0.60, "6. Abrir modal con opciones arbitrales")
    d.add_message('actor', 'modal_ui', 0.55, "7. Elegir decisión: 'ajustar' (forzar inventario) o 'anular'")
    d.add_message('modal_ui', 'res_ctrl', 0.50, "8. POST /api/v1/sync/conflictos/resolver (decision)")
    
    d.add_frame(
        "alt", "[Decisión = 'ajustar' (aplicar venta y ajustar existencias)]",
        0.03, 0.98, 0.46, 0.19,
        divider_y=0.29,
        else_guard="[else: Decisión = 'anular' (cancelar operación y registrar motivo)]"
    )
    d.add_message('res_ctrl', 'op_pend', 0.42, "9. PATCH: cambiar estado a 'resuelta' o 'rechazada'")
    d.add_message('res_ctrl', 'inventario', 0.38, "10. PATCH / UPDATE: aplicar ajuste de stock correctivo")
    d.add_message('res_ctrl', 'mov_inv', 0.34, "11. POST: asentar en kárdex la resolución")
    d.add_message('res_ctrl', 'auditoria', 0.30, "12. POST: auditar decisión administrativa")
    
    d.add_message('res_ctrl', 'op_pend', 0.25, "13. PATCH: marcar op como 'rechazada' sin alterar inventario")
    d.add_message('res_ctrl', 'modal_ui', 0.15, "14. Response 200 OK: Conflicto procesado", is_return=True)
    d.add_message('modal_ui', 'bandeja_ui', 0.10, "15. Remover operación de la bandeja activa", is_return=True)
    d.add_message('bandeja_ui', 'actor', 0.05, "16. Notificar al encargado: Conflicto resuelto exitosamente", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu32_resolver_conflictos.png")
    svg_path = os.path.join(output_dir, "secuencia_cu32_resolver_conflictos.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-33: Reportes y Dashboards Convencionales
# ----------------------------------------------------------------------------------------
def generate_seq_cu33(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-33: REPORTES Y DASHBOARDS CONVENCIONALES",
        "KPIs Ejecutivos, Ventas por Período, Agregación y Rotación de Stock | Metodología ICONIX",
        width=19, height=14
    )
    d.y_lifeline_bottom = 0.04
    # 10 Participantes idénticos al Diagrama de Robustez de CU-33
    d.add_participant('actor', 'Administrador', 'actor', 0.050, 'Analista de Métricas', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('rep_ui', 'ReportesComponent', 'boundary', 0.145, 'reportes-convencionales', w=0.074, font_size=7.0, sub_size=5.8)
    d.add_participant('filtro_ui', 'FiltrosReporte', 'boundary', 0.245, 'Fechas/Sucursal/Cat', w=0.072, font_size=7.0, sub_size=5.8)
    
    d.add_participant('dash_ctrl', 'obtener_dashboard', 'control', 0.355, 'reporte_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('ventas_ctrl', 'ventas_periodo', 'control', 0.465, 'reporte_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('rot_ctrl', 'rotacion_stock', 'control', 0.575, 'reporte_service.py', w=0.072, font_size=7.2, sub_size=6.0)
    
    d.add_participant('venta', 'Venta', 'entity', 0.685, 'db / venta (kpis)', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('detalle', 'VentaDetalle', 'entity', 0.790, 'db / venta_detalle', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('inventario', 'Inventario', 'entity', 0.890, 'db / inventario (stock)', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('mov_inv', 'MovInventario', 'entity', 0.965, 'db / mov_inventario', w=0.060, font_size=6.8, sub_size=5.6)
    
    # 1. Carga inicial del dashboard de métricas
    d.add_message('actor', 'rep_ui', 0.85, "1. Acceder al panel de reportes convencionales")
    d.add_message('rep_ui', 'dash_ctrl', 0.81, "2. GET /api/v1/reportes/convencionales/dashboard (kpis)")
    d.add_message('dash_ctrl', 'venta', 0.77, "3. GET: calcular facturación de hoy, mes y ticket promedio")
    d.add_message('dash_ctrl', 'detalle', 0.73, "4. GET: ranking top 10 prendas más demandadas")
    d.add_message('dash_ctrl', 'rep_ui', 0.69, "5. Response 200 OK (KPIs consolidados y métricas globales)", is_return=True)
    d.add_message('rep_ui', 'actor', 0.65, "6. Renderizar tarjetas de métricas y gráficos de ventas", is_return=True)
    
    # 2. Consulta de ventas por rango y sucursal
    d.add_message('actor', 'filtro_ui', 0.59, "7. Seleccionar rango de fechas y sucursal específica")
    d.add_message('filtro_ui', 'ventas_ctrl', 0.55, "8. GET /api/v1/reportes/convencionales/ventas (fecha_ini, fin, suc)")
    d.add_message('ventas_ctrl', 'venta', 0.51, "9. GET: agregación temporal de ventas y transacciones")
    d.add_message('ventas_ctrl', 'filtro_ui', 0.47, "10. Response 200 OK (serie de tiempo de ingresos)", is_return=True)
    d.add_message('filtro_ui', 'rep_ui', 0.43, "11. Actualizar gráfico comparativo de tendencias", is_return=True)
    
    # 3. Análisis de rotación de stock y kárdex
    d.add_message('actor', 'filtro_ui', 0.37, "12. Solicitar análisis de rotación de inventario por categoría")
    d.add_message('filtro_ui', 'rot_ctrl', 0.33, "13. GET /api/v1/reportes/convencionales/rotacion (cat_id, suc_id)")
    d.add_message('rot_ctrl', 'inventario', 0.28, "14. GET: balance existencias y alertas stock crítico")
    d.add_message('rot_ctrl', 'mov_inv', 0.23, "15. GET: calcular ratio de rotación (entradas vs salidas)")
    d.add_message('rot_ctrl', 'rep_ui', 0.17, "16. Response 200 OK (índices de rotación y productos en riesgo)", is_return=True)
    d.add_message('rep_ui', 'actor', 0.11, "17. Desplegar matriz de rotación y sugerencias de reabastecimiento", is_return=True)
    d.add_message('rep_ui', 'actor', 0.05, "18. Exportar reporte consolidado en CSV/Impresión", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu33_reportes_convencionales.png")
    svg_path = os.path.join(output_dir, "secuencia_cu33_reportes_convencionales.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-34: Reportes Generativos con IA (Whitelist & Exportación)
# ----------------------------------------------------------------------------------------
def generate_seq_cu34(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-34: REPORTES GENERATIVOS CON IA (WHITELIST & EXPORTACIÓN)",
        "Consultas en Lenguaje Natural, Whitelist BR-08, Logs y Exportación Multi-formato | Metodología ICONIX",
        width=18, height=13
    )
    d.y_lifeline_bottom = 0.04
    # 9 Participantes idénticos al Diagrama de Robustez de CU-34
    d.add_participant('actor', 'Gerente / Admin', 'actor', 0.055, 'Usuario Plan Pro (BR-03)', w=0.075, font_size=7.2, sub_size=6.0)
    d.add_participant('ia_ui', 'ReporteIaComponent', 'boundary', 0.165, 'reporte-ia.html (Texto/Voz)', w=0.075, font_size=7.0, sub_size=5.8)
    d.add_participant('modal_exp', 'ModalExportar', 'boundary', 0.280, 'Selector XLSX / PDF', w=0.075, font_size=7.0, sub_size=5.8)
    
    d.add_participant('ia_ctrl', 'procesar_ia', 'control', 0.400, 'Whitelist BR-08 Controller', w=0.075, font_size=7.0, sub_size=5.8)
    d.add_participant('exp_ctrl', 'exportar_reporte', 'control', 0.520, 'openpyxl / ReportLab', w=0.075, font_size=7.0, sub_size=5.8)
    
    d.add_participant('ia_log', 'ConsultaIaLog', 'entity', 0.640, 'db / consulta_ia_log', w=0.075, font_size=7.0, sub_size=5.8)
    d.add_participant('rep_exp', 'ReporteExportado', 'entity', 0.750, 'db / reporte_exportado', w=0.075, font_size=7.0, sub_size=5.8)
    d.add_participant('vistas', 'Venta / Inventario', 'entity', 0.855, 'db / vistas agregadas', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.955, 'db / bitacora', w=0.065, font_size=6.8, sub_size=5.6)
    
    # 1. Consulta IA
    d.add_message('actor', 'ia_ui', 0.85, "1. Ingresar consulta en lenguaje natural (texto o voz)")
    d.add_message('ia_ui', 'ia_ctrl', 0.81, "2. POST /api/v1/reportes/ia/consultar (prompt, canal)")
    d.add_message('ia_ctrl', 'ia_log', 0.76, "3. POST / INSERT: registrar consulta, prompt, latencia y tokens")
    
    # alt: Whitelist válida vs inválida
    d.add_frame(
        "alt", "[Consulta acotada bajo Whitelist estricta BR-08]",
        0.03, 0.98, 0.72, 0.26,
        divider_y=0.36,
        else_guard="[else: Consulta no permitida o fuera de Whitelist]"
    )
    d.add_message('ia_ctrl', 'vistas', 0.67, "4. GET: consulta SQL acotada bajo Whitelist BR-08")
    d.add_message('ia_ctrl', 'ia_ui', 0.62, "5. Response 200 OK (datos tabulares + análisis LLM)", is_return=True)
    d.add_message('ia_ui', 'actor', 0.57, "6. Mostrar tabla de resultados y síntesis ejecutiva", is_return=True)
    
    d.add_message('actor', 'modal_exp', 0.51, "7. Solicitar exportación del reporte generado")
    d.add_message('modal_exp', 'exp_ctrl', 0.46, "8. POST /api/v1/reportes/ia/exportar (formato: 'xlsx' | 'pdf')")
    d.add_message('exp_ctrl', 'rep_exp', 0.42, "9. POST / INSERT: guardar archivo exportado con TTL")
    d.add_message('exp_ctrl', 'auditoria', 0.38, "10. POST: auditar exportación masiva de datos")
    
    d.add_message('ia_ctrl', 'ia_ui', 0.31, "11. Error 400: 'Consulta denegada por directiva de seguridad BR-08'", is_return=True)
    d.add_message('ia_ui', 'actor', 0.27, "12. Notificar restricción de consulta al usuario", is_return=True)
    
    # Descarga final
    d.add_message('exp_ctrl', 'modal_exp', 0.18, "13. Response 200 OK (URL de descarga firmada temporal)", is_return=True)
    d.add_message('modal_exp', 'actor', 0.11, "14. Descarga automática de archivo .xlsx o .pdf corporativo", is_return=True)
    d.add_message('modal_exp', 'actor', 0.05, "15. Confirmar retención y cifrado en almacenamiento temporal", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu34_reporte_generativo_ia.png")
    svg_path = os.path.join(output_dir, "secuencia_cu34_reporte_generativo_ia.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-35: Dashboard Analítico ML con Síntesis Audio TTS
# ----------------------------------------------------------------------------------------
def generate_seq_cu35(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-35: DASHBOARD ANALÍTICO ML CON SÍNTESIS AUDIO TTS",
        "Proyección de Demanda, Clustering RFM K-Means y Audio Prescriptivo | Metodología ICONIX",
        width=19, height=14
    )
    d.y_lifeline_bottom = 0.04
    # 10 Participantes idénticos al Diagrama de Robustez de CU-35
    d.add_participant('actor', 'Director Comercial', 'actor', 0.050, 'Decisor Estratégico', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('ml_ui', 'DashboardMlComponent', 'boundary', 0.145, 'dashboard-ml.html', w=0.074, font_size=7.0, sub_size=5.8)
    d.add_participant('audio_ui', 'ReproductorAudioTts', 'boundary', 0.245, 'Barra Audio TTS', w=0.072, font_size=7.0, sub_size=5.8)
    
    d.add_participant('dem_ctrl', 'predecir_demanda', 'control', 0.355, 'ml_analytics_service.py', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('rfm_ctrl', 'segmentar_rfm', 'control', 0.465, 'K-Means Clustering', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('tts_ctrl', 'sintesis_audio', 'control', 0.575, 'ml_analytics_service.py', w=0.072, font_size=7.0, sub_size=5.8)
    
    d.add_participant('modelo', 'ModeloMl', 'entity', 0.685, 'db / modelo_ml', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('venta', 'Venta', 'entity', 0.790, 'db / venta (series)', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('cliente', 'Cliente', 'entity', 0.890, 'db / cliente (RFM)', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('auditoria', 'BitacoraAuditoria', 'entity', 0.965, 'db / bitacora', w=0.060, font_size=6.8, sub_size=5.6)
    
    # 1. Proyección de Demanda Supervisada
    d.add_message('actor', 'ml_ui', 0.85, "1. Abrir panel analítico y solicitar proyección de demanda")
    d.add_message('ml_ui', 'dem_ctrl', 0.81, "2. GET /api/v1/inteligencia/ml/demanda (entrenar y proyectar)")
    d.add_message('dem_ctrl', 'venta', 0.77, "3. GET: extraer dataset histórico de ventas por categoría")
    d.add_message('dem_ctrl', 'modelo', 0.73, "4. GET / PUT: leer y actualizar métricas r2_score y MAE")
    d.add_message('dem_ctrl', 'ml_ui', 0.69, "5. Response 200 OK (curva de proyección y horizonte 30 días)", is_return=True)
    d.add_message('ml_ui', 'actor', 0.65, "6. Renderizar gráfico predictivo de demanda con intervalos de confianza", is_return=True)
    
    # 2. Segmentación RFM No Supervisada
    d.add_message('actor', 'ml_ui', 0.59, "7. Solicitar segmentación no supervisada de clientes")
    d.add_message('ml_ui', 'rfm_ctrl', 0.55, "8. GET /api/v1/inteligencia/ml/segmentacion (clusters RFM k=3..5)")
    d.add_message('rfm_ctrl', 'cliente', 0.51, "9. GET: recuperar variables recencia, frecuencia y monto")
    d.add_message('rfm_ctrl', 'modelo', 0.47, "10. Actualizar métrica Silhouette Score del clustering")
    d.add_message('rfm_ctrl', 'ml_ui', 0.43, "11. Response 200 OK (centroides y perfiles de cluster)", is_return=True)
    d.add_message('ml_ui', 'actor', 0.39, "12. Desplegar visualizador 3D/Scatter de clusters de clientes", is_return=True)
    
    # 3. Síntesis de Audio Prescriptivo TTS
    d.add_message('actor', 'audio_ui', 0.33, "13. Presionar 'Reproducir Resumen Ejecutivo en Audio'")
    d.add_message('audio_ui', 'tts_ctrl', 0.28, "14. POST /api/v1/inteligencia/ml/sintesis-audio (texto diagnóstico)")
    d.add_message('tts_ctrl', 'auditoria', 0.23, "15. POST: auditar generación y consumo de audio TTS")
    d.add_message('tts_ctrl', 'audio_ui', 0.17, "16. Response 200 OK (stream de audio sintetizado WAV/MP3)", is_return=True)
    d.add_message('audio_ui', 'actor', 0.11, "17. Reproducir audio con recomendaciones tácticas de inventario", is_return=True)
    d.add_message('audio_ui', 'actor', 0.05, "18. Ofrecer descarga del archivo de audio para gerencia", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu35_dashboard_analitico_ml.png")
    svg_path = os.path.join(output_dir, "secuencia_cu35_dashboard_analitico_ml.svg")
    d.save(png_path, svg_path)


# ----------------------------------------------------------------------------------------
# CU-36: Vestidor Virtual con Realidad Aumentada (RA)
# ----------------------------------------------------------------------------------------
def generate_seq_cu36(output_dir):
    d = SequenceDiagram(
        "DIAGRAMA DE SECUENCIA - CU-36: VESTIDOR VIRTUAL CON REALIDAD AUMENTADA (RA)",
        "Modelos 3D GLB, Canvas AR WebRTC, Biometría y Sesión de Prueba Virtual | Metodología ICONIX",
        width=19, height=14
    )
    d.y_lifeline_bottom = 0.04
    # 10 Participantes idénticos al Diagrama de Robustez de CU-36
    d.add_participant('actor', 'Cliente Digital', 'actor', 0.050, 'Comprador Web/Móvil', w=0.072, font_size=7.2, sub_size=6.0)
    d.add_participant('vest_ui', 'VestidorComponent', 'boundary', 0.145, 'vestidor-virtual.html', w=0.074, font_size=7.0, sub_size=5.8)
    d.add_participant('ar_ui', 'CamaraArCanvas', 'boundary', 0.245, 'videoElement + arCanvas', w=0.074, font_size=7.0, sub_size=5.8)
    
    d.add_participant('ar_ctrl', 'listar_prendas_ar', 'control', 0.355, 'vestidor_ar_service.py', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('av_ctrl', 'obtener_avatar', 'control', 0.465, 'vestidor_ar_service.py', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('ses_ctrl', 'sesion_prueba', 'control', 0.575, 'vestidor_ar_service.py', w=0.072, font_size=7.0, sub_size=5.8)
    
    d.add_participant('prenda_ar', 'PrendaAr', 'entity', 0.685, 'db / prenda_ar (3D)', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('avatar', 'AvatarCliente', 'entity', 0.790, 'db / avatar_cliente', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('medida', 'MedidaCorporal', 'entity', 0.890, 'db / medida_corporal', w=0.072, font_size=7.0, sub_size=5.8)
    d.add_participant('sesion', 'SesionPrueba', 'entity', 0.965, 'db / sesion_prueba_ar', w=0.060, font_size=6.8, sub_size=5.6)
    
    # 1. Explorar catálogo de prendas compatibles con RA
    d.add_message('actor', 'vest_ui', 0.85, "1. Abrir probador virtual y explorar catálogo")
    d.add_message('vest_ui', 'ar_ctrl', 0.81, "2. GET /api/v1/vestidor/prendas (catálogo con modelos 3D / RA)")
    d.add_message('ar_ctrl', 'prenda_ar', 0.77, "3. GET: recuperar modelo 3D GLB y puntos de ajuste")
    d.add_message('ar_ctrl', 'vest_ui', 0.73, "4. Response 200 OK (prendas con activos 3D disponibles)", is_return=True)
    d.add_message('vest_ui', 'actor', 0.69, "5. Mostrar selector de prendas, tallas y variantes de color", is_return=True)
    
    # 2. Carga del avatar biométrico del cliente
    d.add_message('actor', 'vest_ui', 0.63, "6. Seleccionar avatar guardado o ingresar medidas anatómicas")
    d.add_message('vest_ui', 'av_ctrl', 0.59, "7. GET /api/v1/vestidor/avatar (perfil anatómico del usuario)")
    d.add_message('av_ctrl', 'avatar', 0.55, "8. GET / POST: obtener o registrar avatar 3D del usuario")
    d.add_message('av_ctrl', 'medida', 0.51, "9. GET: leer medidas anatómicas (busto, cintura, hombro)")
    d.add_message('av_ctrl', 'vest_ui', 0.47, "10. Response 200 OK (avatar 3D parametrizado con medidas)", is_return=True)
    
    # 3. Activación de cámara y sesión de prueba en tiempo real
    d.add_message('actor', 'ar_ui', 0.41, "11. Activar cámara web/móvil para superposición en vivo")
    d.add_message('ar_ui', 'ses_ctrl', 0.36, "12. POST /api/v1/vestidor/sesiones (prenda_id, variante, avatar)")
    d.add_message('ses_ctrl', 'sesion', 0.31, "13. POST / PUT: iniciar y finalizar sesión guardando captura")
    d.add_message('ses_ctrl', 'ar_ui', 0.26, "14. Response 200 OK (sesión activa y anclajes anatómicos)", is_return=True)
    
    # Renderizado y ajuste
    d.add_message('ar_ui', 'actor', 0.19, "15. Renderizar prenda 3D superpuesta en tiempo real sobre el cuerpo", is_return=True)
    d.add_message('actor', 'vest_ui', 0.13, "16. Confirmar ajuste de talla visualizado satisfactoriamente")
    d.add_message('vest_ui', 'actor', 0.07, "17. Opción directa: Añadir talla seleccionada al Carrito (CU-22)", is_return=True)
    
    png_path = os.path.join(output_dir, "secuencia_cu36_vestidor_virtual_ra.png")
    svg_path = os.path.join(output_dir, "secuencia_cu36_vestidor_virtual_ra.svg")
    d.save(png_path, svg_path)


if __name__ == '__main__':
    out_dir = os.path.join(os.getcwd(), 'docs', 'diagramas')
    os.makedirs(out_dir, exist_ok=True)
    generate_seq_cu01(out_dir)
    generate_seq_cu02(out_dir)
    generate_seq_cu03(out_dir)
    generate_seq_cu04(out_dir)
    generate_seq_cu05(out_dir)
    generate_seq_cu06(out_dir)
    generate_seq_cu17(out_dir)
    generate_seq_cu18(out_dir)
    generate_seq_cu19(out_dir)
    generate_seq_cu20(out_dir)
    generate_seq_cu21(out_dir)
    generate_seq_cu22(out_dir)
    generate_seq_cu23(out_dir)
    generate_seq_cu24(out_dir)
    generate_seq_cu25(out_dir)
    generate_seq_cu26(out_dir)
    generate_seq_cu27(out_dir)
    generate_seq_cu28(out_dir)
    generate_seq_cu29(out_dir)
    generate_seq_cu30(out_dir)
    generate_seq_cu31(out_dir)
    generate_seq_cu32(out_dir)
    generate_seq_cu33(out_dir)
    generate_seq_cu34(out_dir)
    generate_seq_cu35(out_dir)
    generate_seq_cu36(out_dir)
    print("All sequence diagrams generated successfully!")

