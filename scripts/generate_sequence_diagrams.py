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

    def add_participant(self, key, label, ptype, x, sub=""):
        """ptype: 'actor', 'boundary', 'control', 'entity'"""
        self.participants[key] = x
        w, h = 0.088, 0.048
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
        self.ax.text(x, y + 0.012, tag, fontsize=7.5, fontweight='bold', ha='center', va='center', color=edge, zorder=5)
        self.ax.text(x, y - 0.002, label, fontsize=8.5, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=5)
        if sub:
            self.ax.text(x, y - 0.015, sub, fontsize=7.0, ha='center', va='center', color=COLORS['subtext'], zorder=5)
            
        # Draw vertical lifeline
        self.ax.plot(
            [x, x], [self.y_lifeline_top, self.y_lifeline_bottom],
            linestyle='--', color=COLORS['lifeline'], linewidth=1.2, zorder=2
        )

    def add_message(self, src_key, dst_key, y, label, is_return=False, self_call=False):
        x1 = self.participants[src_key]
        x2 = self.participants[dst_key]
        
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
                x1 + 0.012, y - 0.009, label, fontsize=7.8, ha='left', va='center',
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
                mx, y + 0.009, label, fontsize=7.5, ha='center', va='bottom',
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
                mx, y + 0.009, label, fontsize=7.8, ha='center', va='bottom',
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
    d.add_participant('reg_ui', 'RegisterUI', 'boundary', 0.15, 'register.html')
    d.add_participant('ver_ui', 'VerifyEmailUI', 'boundary', 0.25, 'verify-email.html')
    d.add_participant('reg_ctrl', 'register()', 'control', 0.36, 'auth_service.py')
    d.add_participant('ver_ctrl', 'verify_email()', 'control', 0.47, 'auth_service.py')
    d.add_participant('empresa', 'Empresa', 'entity', 0.58, 'db / empresa')
    d.add_participant('rol', 'Rol', 'entity', 0.68, 'db / rol')
    d.add_participant('usuario', 'Usuario', 'entity', 0.78, 'db / usuario')
    d.add_participant('token', 'Verificacion', 'entity', 0.88, 'db / verificacion')
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
    
    d.add_participant('actor', 'Usuario Auth', 'actor', 0.06, 'Sesión Activa')
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
    
    d.add_participant('actor', 'Usuario Auth', 'actor', 0.06, 'Sesión Activa')
    d.add_participant('nav_ui', 'Navbar/Profile', 'boundary', 0.19, 'app.html')
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
    d.add_participant('http_ui', 'HttpBoundary', 'boundary', 0.20, 'Vistas / Clientes HTTP')
    d.add_participant('mw', 'AuditMiddleware', 'control', 0.36, 'audit.py')
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


if __name__ == '__main__':
    out_dir = os.path.join(os.getcwd(), 'docs', 'diagramas')
    os.makedirs(out_dir, exist_ok=True)
    generate_seq_cu01(out_dir)
    generate_seq_cu02(out_dir)
    generate_seq_cu03(out_dir)
    generate_seq_cu04(out_dir)
    generate_seq_cu05(out_dir)
    print("All sequence diagrams generated successfully!")

