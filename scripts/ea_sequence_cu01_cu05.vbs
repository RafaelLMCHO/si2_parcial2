'==========================================================================================
' Enterprise Architect 15 - VBScript de Automatizacion
' Proyecto  : FashionStore SaaS - Segundo Parcial
' Proposito : Generar los 5 Diagramas de Secuencia (CU-01 al CU-05)
'             IDENTICOS a las imagenes PNG generadas con matplotlib.
' Elementos : Actor, Boundary, Control, Entity (ICONIX)
' Fragmentos: alt, opt, loop con guardas exactas de las imagenes
' Mensajes  : numerados, con etiqueta CRUD donde aplica, retornos punteados
' Uso       : Abrir EA 15 -> seleccionar paquete destino -> Specialize > Scripting > Run
'==========================================================================================
Option Explicit

'------------------------------------------
' PUNTO DE ENTRADA
'------------------------------------------
Sub Main()
    Dim rootPkg As EA.Package
    Set rootPkg = Repository.GetTreeSelectedPackage()
    If rootPkg Is Nothing Then
        MsgBox "Seleccione un paquete en el Project Browser antes de ejecutar el script.", vbExclamation
        Exit Sub
    End If

    Dim pkg As EA.Package
    Set pkg = rootPkg.Packages.AddNew("Diagramas_Secuencia_CU01_CU05", "")
    pkg.Notes = "Diagramas de Secuencia ICONIX generados automaticamente - FashionStore SaaS"
    pkg.Update()
    rootPkg.Packages.Refresh()

    Session.Output "Paquete creado: " & pkg.Name

    CU01_IniciarSesion    pkg
    CU02_RegistrarseVerificar pkg
    CU03_GestionarPerfil  pkg
    CU04_CerrarSesionRefresh pkg
    CU05_RegistrarAuditoria  pkg

    pkg.Diagrams.Refresh()
    pkg.Elements.Refresh()
    Repository.RefreshModelView pkg.PackageID

    Session.Output "==== FIN: 5 Diagramas generados correctamente ===="
    MsgBox "Los 5 Diagramas de Secuencia (CU-01 al CU-05) fueron creados en el paquete:" & vbCrLf & pkg.Name, vbInformation
End Sub

'==========================================================================================
' UTILITARIOS
'==========================================================================================

' Crea un elemento en el paquete con su estereotipo ICONIX
Function NuevoElemento(pkg As EA.Package, nombre As String, tipo As String, stereo As String) As EA.Element
    Dim el As EA.Element
    Set el = pkg.Elements.AddNew(nombre, tipo)
    el.Stereotype = stereo
    el.Update()
    pkg.Elements.Refresh()
    Set NuevoElemento = el
End Function

' Coloca un elemento en el diagrama con coordenadas
Function ColocarEnDiagrama(diag As EA.Diagram, el As EA.Element, _
                            xL As Long, xR As Long, yT As Long, yB As Long) As EA.DiagramObject
    Dim dobj As EA.DiagramObject
    Set dobj = diag.DiagramObjects.AddNew("", "")
    dobj.ElementID = el.ElementID
    dobj.left   = xL
    dobj.right  = xR
    dobj.top    = yT
    dobj.bottom = yB
    dobj.Update()
    diag.DiagramObjects.Refresh()
    Set ColocarEnDiagrama = dobj
End Function

' Crea un mensaje de secuencia (llamada o retorno)
Sub Mensaje(src As EA.Element, dst As EA.Element, _
            etiqueta As String, seq As Integer, esRetorno As Boolean)
    Dim con As EA.Connector
    Set con = src.Connectors.AddNew(etiqueta, "Sequence")
    con.SupplierID  = dst.ElementID
    con.SequenceNo  = seq
    If esRetorno Then
        con.Stereotype = "return"
        ' Linea punteada para retorno
        con.ClientEnd.Navigable  = "Non-Navigable"
        con.SupplierEnd.Navigable = "Navigable"
    End If
    con.Update()
    src.Connectors.Refresh()
End Sub

' Llamada reflexiva (self-call sobre el mismo lifeline)
Sub MensajeReflexivo(el As EA.Element, etiqueta As String, seq As Integer)
    Dim con As EA.Connector
    Set con = el.Connectors.AddNew(etiqueta, "Sequence")
    con.SupplierID = el.ElementID
    con.SequenceNo = seq
    con.Stereotype = "self"
    con.Update()
    el.Connectors.Refresh()
End Sub

' Crea un fragmento combinado (alt / opt / loop) en el diagrama
Function NuevoFragmento(pkg As EA.Package, diag As EA.Diagram, _
                         operador As String, guarda As String, _
                         xL As Long, xR As Long, yT As Long, yB As Long) As EA.Element
    Dim frag As EA.Element
    Set frag = pkg.Elements.AddNew(operador & " " & guarda, "InteractionFragment")
    frag.Stereotype = operador        ' alt | opt | loop
    frag.PDATA1     = operador
    frag.Notes      = guarda
    frag.Update()
    pkg.Elements.Refresh()

    Dim dobj As EA.DiagramObject
    Set dobj = diag.DiagramObjects.AddNew("", "")
    dobj.ElementID = frag.ElementID
    dobj.left   = xL
    dobj.right  = xR
    dobj.top    = yT
    dobj.bottom = yB
    dobj.Update()
    diag.DiagramObjects.Refresh()
    Set NuevoFragmento = frag
End Function

'==========================================================================================
' CU-01: INICIAR SESION (LOGIN)
' Participantes: Usuario | LoginComponent | login() |
'                Empresa | Suscripcion | Rol | Usuario(entity) | Sesion | BitacoraAuditoria
' Fragmentos   : opt [Superadmin Global]
'                alt [Credenciales validas / Credenciales invalidas]
' Mensajes     : 20 (1..20) con retornos y self-calls
'==========================================================================================
Sub CU01_IniciarSesion(pkg As EA.Package)
    Session.Output "Generando CU-01: Iniciar Sesion (Login)..."

    '--- Diagrama ---
    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-01 Iniciar Sesion (Login)", "Sequence")
    diag.Notes = "Fragmentos: opt [Superadmin Global], alt [Credenciales validas / invalidas] | CRUD: GET, PATCH, POST"
    diag.Update()

    '--- Lifelines (Actor y Boundaries/Controllers/Entities) ---
    Dim eActor   As EA.Element   ' [ACTOR]    Usuario
    Dim eLoginUI As EA.Element   ' boundary   LoginComponent
    Dim eCtrl    As EA.Element   ' control    login()
    Dim eEmpresa As EA.Element   ' entity     Empresa
    Dim eSuscr   As EA.Element   ' entity     Suscripcion
    Dim eRol     As EA.Element   ' entity     Rol
    Dim eUsr     As EA.Element   ' entity     Usuario (entity)
    Dim eSes     As EA.Element   ' entity     Sesion
    Dim eAud     As EA.Element   ' entity     BitacoraAuditoria

    Set eActor   = NuevoElemento(pkg, "Usuario",           "Actor",    "")
    Set eLoginUI = NuevoElemento(pkg, "LoginComponent",    "Sequence", "boundary")
    Set eCtrl    = NuevoElemento(pkg, "login()",           "Sequence", "control")
    Set eEmpresa = NuevoElemento(pkg, "Empresa",           "Sequence", "entity")
    Set eSuscr   = NuevoElemento(pkg, "Suscripcion",       "Sequence", "entity")
    Set eRol     = NuevoElemento(pkg, "Rol",               "Sequence", "entity")
    Set eUsr     = NuevoElemento(pkg, "Usuario",           "Sequence", "entity")
    Set eSes     = NuevoElemento(pkg, "Sesion",            "Sequence", "entity")
    Set eAud     = NuevoElemento(pkg, "BitacoraAuditoria", "Sequence", "entity")

    '--- Posiciones X en el diagrama (separacion ~130px) ---
    ' xLeft, xRight, yTop, yBottom
    ColocarEnDiagrama diag, eActor,   10,  110, -10, -800
    ColocarEnDiagrama diag, eLoginUI, 140, 260, -10, -800
    ColocarEnDiagrama diag, eCtrl,    290, 410, -10, -800
    ColocarEnDiagrama diag, eEmpresa, 440, 545, -10, -800
    ColocarEnDiagrama diag, eSuscr,   575, 680, -10, -800
    ColocarEnDiagrama diag, eRol,     710, 800, -10, -800
    ColocarEnDiagrama diag, eUsr,     830, 945, -10, -800
    ColocarEnDiagrama diag, eSes,     975,1080, -10, -800
    ColocarEnDiagrama diag, eAud,    1110,1250, -10, -800

    '--- Fragmento OPT: Superadmin Global (antes de la consulta a Empresa) ---
    NuevoFragmento pkg, diag, "opt", "[Usuario es Superadmin Global (sin empresa)]", _
                   285, 550, -95, -145

    '--- Fragmento ALT: Credenciales validas vs invalidas ---
    NuevoFragmento pkg, diag, "alt", "[Credenciales validas y correo verificado] / [else: Credenciales incorrectas o correo no verificado]", _
                   0, 1260, -380, -790

    '--- MENSAJES (numerados exactamente como en la imagen) ---
    ' 1. Actor -> LoginComponent
    Mensaje eActor,   eLoginUI, "1. Ingresar empresa_slug, correo, password",          1,  False
    ' 2. LoginComponent -> login()
    Mensaje eLoginUI, eCtrl,    "2. POST /api/v1/auth/login",                           2,  False
    ' Self-call dentro opt: empresa_slug = null
    MensajeReflexivo eCtrl, "empresa_slug = null", 3
    ' 3. login() -> Empresa
    Mensaje eCtrl,    eEmpresa, "3. GET: buscar empresa activa por slug",               4,  False
    ' 4. retorno Empresa -> login()
    Mensaje eEmpresa, eCtrl,    "4. empresa_id, estado='activa'",                       5,  True
    ' 5. login() -> Suscripcion
    Mensaje eCtrl,    eSuscr,   "5. GET: verificar vigencia suscripcion",               6,  False
    ' 6. retorno Suscripcion -> login()
    Mensaje eSuscr,   eCtrl,    "6. suscripcion activa y vigente",                      7,  True
    ' 7. login() -> Rol
    Mensaje eCtrl,    eRol,     "7. GET: consultar rol y permisos",                     8,  False
    ' 8. retorno Rol -> login()
    Mensaje eRol,     eCtrl,    "8. rol='administrador'",                               9,  True
    ' 9. login() -> Usuario (entity)
    Mensaje eCtrl,    eUsr,     "9. GET: validar credenciales y correo verificado",     10, False
    ' 10. retorno Usuario -> login()
    Mensaje eUsr,     eCtrl,    "10. password_hash, email_verificado",                  11, True
    ' 11. self-call: verify_password
    MensajeReflexivo eCtrl, "11. verify_password(clave, hash)", 12
    ' ---- ALT: rama positiva ----
    ' 12. PATCH usuario
    Mensaje eCtrl,    eUsr,     "12. PATCH: actualizar ultimo_acceso = now()",          13, False
    ' 13. POST sesion
    Mensaje eCtrl,    eSes,     "13. POST: crear nueva sesion (refresh_token_hash)",    14, False
    ' 14. retorno sesion
    Mensaje eSes,     eCtrl,    "14. session_id generado",                              15, True
    ' 15. POST auditoria
    Mensaje eCtrl,    eAud,     "15. POST: registrar auditoria login exitoso",          16, False
    ' 16. retorno login() -> LoginComponent
    Mensaje eCtrl,    eLoginUI, "16. 200 OK: LoginResponse(access_token, refresh_token)", 17, True
    ' 17. LoginComponent -> Actor
    Mensaje eLoginUI, eActor,   "17. Almacenar sesion y redirigir a /profile",         18, False
    ' ---- ALT: rama else ----
    ' 18. POST auditoria fallida
    Mensaje eCtrl,    eAud,     "18. POST: registrar auditoria intento fallido / rechazado", 19, False
    ' 19. retorno error
    Mensaje eCtrl,    eLoginUI, "19. 401 / 403 Error (CREDENCIALES_INVALIDAS)",         20, True
    ' 20. LoginComponent -> Actor: error
    Mensaje eLoginUI, eActor,   "20. Mostrar mensaje de error en pantalla",             21, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
    Session.Output "CU-01 completado."
End Sub

'==========================================================================================
' CU-02: REGISTRARSE Y VERIFICAR CORREO
' Participantes: Cliente | RegisterUI | VerifyEmailUI |
'                register() | verify_email() |
'                Empresa | Rol | Usuario | VerificacionCorreo | BitacoraAuditoria
' Fragmentos   : alt [Correo disponible / Correo duplicado]
'                opt [Modo Demo: exponer token]
'                alt [Token valido / Token invalido]
' Mensajes     : 20 (1..20)
'==========================================================================================
Sub CU02_RegistrarseVerificar(pkg As EA.Package)
    Session.Output "Generando CU-02: Registrarse y Verificar Correo..."

    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-02 Registrarse y Verificar Correo", "Sequence")
    diag.Notes = "Fragmentos: alt [Correo disponible/duplicado], opt [Modo Demo], alt [Token valido/invalido] | CRUD: GET, POST, PATCH, DELETE"
    diag.Update()

    Dim eActor    As EA.Element  ' Actor       Cliente
    Dim eRegUI    As EA.Element  ' boundary    RegisterUI
    Dim eVerUI    As EA.Element  ' boundary    VerifyEmailUI
    Dim eRegCtrl  As EA.Element  ' control     register()
    Dim eVerCtrl  As EA.Element  ' control     verify_email()
    Dim eEmpresa  As EA.Element  ' entity      Empresa
    Dim eRol      As EA.Element  ' entity      Rol
    Dim eUsr      As EA.Element  ' entity      Usuario
    Dim eToken    As EA.Element  ' entity      VerificacionCorreo
    Dim eAud      As EA.Element  ' entity      BitacoraAuditoria

    Set eActor   = NuevoElemento(pkg, "Cliente",            "Actor",    "")
    Set eRegUI   = NuevoElemento(pkg, "RegisterUI",         "Sequence", "boundary")
    Set eVerUI   = NuevoElemento(pkg, "VerifyEmailUI",      "Sequence", "boundary")
    Set eRegCtrl = NuevoElemento(pkg, "register()",         "Sequence", "control")
    Set eVerCtrl = NuevoElemento(pkg, "verify_email()",     "Sequence", "control")
    Set eEmpresa = NuevoElemento(pkg, "Empresa",            "Sequence", "entity")
    Set eRol     = NuevoElemento(pkg, "Rol",                "Sequence", "entity")
    Set eUsr     = NuevoElemento(pkg, "Usuario",            "Sequence", "entity")
    Set eToken   = NuevoElemento(pkg, "VerificacionCorreo", "Sequence", "entity")
    Set eAud     = NuevoElemento(pkg, "BitacoraAuditoria",  "Sequence", "entity")

    ColocarEnDiagrama diag, eActor,    10,  110, -10, -950
    ColocarEnDiagrama diag, eRegUI,   140,  240, -10, -950
    ColocarEnDiagrama diag, eVerUI,   270,  375, -10, -950
    ColocarEnDiagrama diag, eRegCtrl, 405,  520, -10, -950
    ColocarEnDiagrama diag, eVerCtrl, 550,  665, -10, -950
    ColocarEnDiagrama diag, eEmpresa, 695,  800, -10, -950
    ColocarEnDiagrama diag, eRol,     830,  925, -10, -950
    ColocarEnDiagrama diag, eUsr,     955, 1060, -10, -950
    ColocarEnDiagrama diag, eToken,  1090, 1210, -10, -950
    ColocarEnDiagrama diag, eAud,    1240, 1370, -10, -950

    '--- Fragmento ALT: Correo disponible vs duplicado ---
    NuevoFragmento pkg, diag, "alt", "[Correo disponible] / [else: Correo duplicado]", _
                   0, 1380, -265, -510

    '--- Fragmento OPT: Modo Demo ---
    NuevoFragmento pkg, diag, "opt", "[Modo Demo: exponer token en respuesta]", _
                   400, 680, -390, -430

    '--- Fragmento ALT: Token valido vs invalido ---
    NuevoFragmento pkg, diag, "alt", "[Token valido y vigente] / [else: Token invalido o expirado]", _
                   0, 1380, -580, -910

    '--- MENSAJES ---
    ' FASE 1: REGISTRO
    Mensaje eActor,   eRegUI,   "1. Completar formulario (nombre, correo, telefono, clave)",      1,  False
    Mensaje eRegUI,   eRegCtrl, "2. POST /api/v1/auth/register (datos cliente)",                  2,  False
    Mensaje eRegCtrl, eEmpresa, "3. GET: validar empresa existente por slug",                     3,  False
    Mensaje eRegCtrl, eRol,     "4. GET: obtener id de rol 'cliente'",                            4,  False
    Mensaje eRegCtrl, eUsr,     "5. GET: verificar si correo ya existe en tenant",                5,  False
    ' Rama ALT positiva
    Mensaje eRegCtrl, eUsr,     "6. POST: crear usuario (inactivo, email_verificado=false)",       6,  False
    Mensaje eRegCtrl, eToken,   "7. POST: crear registro de token con expiracion",                7,  False
    Mensaje eRegCtrl, eAud,     "8. POST: registrar auditoria de registro",                       8,  False
    ' Respuesta exitosa
    Mensaje eRegCtrl, eRegUI,   "9. 201 Created: RegisterResponse (mensaje confirmacion)",        9,  True
    Mensaje eRegUI,   eActor,   "10. Mostrar aviso: Revise su correo para verificar",             10, False
    ' Rama ALT negativa (correo duplicado)
    Mensaje eRegCtrl, eRegUI,   "11. 409 Conflict: CORREO_DUPLICADO",                             11, True

    ' FASE 2: VERIFICACION
    Mensaje eActor,   eVerUI,   "12. Ingresar token recibido",                                    12, False
    Mensaje eVerUI,   eVerCtrl, "13. POST /api/v1/auth/verify-email (token, slug)",               13, False
    Mensaje eVerCtrl, eToken,   "14. GET: validar token por hash y expiracion",                   14, False
    ' Rama ALT: Token valido
    Mensaje eVerCtrl, eUsr,     "15. PATCH: activar usuario (estado='activo', verificado=true)",  15, False
    Mensaje eVerCtrl, eToken,   "16. DELETE: invalidar / consumir token utilizado",               16, False
    Mensaje eVerCtrl, eAud,     "17. POST: registrar auditoria de verificacion",                  17, False
    Mensaje eVerCtrl, eVerUI,   "18. 200 OK: VerifyEmailResponse ('Correo verificado')",          18, True
    ' Rama ALT: Token invalido
    Mensaje eVerCtrl, eVerUI,   "19. 400 Bad Request: TOKEN_INVALIDO",                            19, True
    Mensaje eVerUI,   eActor,   "20. Notificar resultado en pantalla",                            20, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
    Session.Output "CU-02 completado."
End Sub

'==========================================================================================
' CU-03: GESTIONAR PERFIL Y CAMBIO DE CONTRASENA
' Participantes: UsuarioAuth | ProfileComponent | get_me() | update_me() |
'                change_password() | Usuario | Sesion | BitacoraAuditoria
' Fragmentos   : opt  [Modificacion de datos personales]
'                alt  [Contrasena actual correcta / incorrecta]
'                loop [Para cada sesion remota activa]
' Mensajes     : 21 (1..21)
'==========================================================================================
Sub CU03_GestionarPerfil(pkg As EA.Package)
    Session.Output "Generando CU-03: Gestionar Perfil y Cambio de Contrasena..."

    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-03 Gestionar Perfil y Contrasena", "Sequence")
    diag.Notes = "Fragmentos: opt [Modificacion datos], alt [Clave valida/incorrecta], loop [Revocar sesiones] | CRUD: GET, PUT/PATCH, DELETE, POST"
    diag.Update()

    Dim eActor     As EA.Element ' Actor     UsuarioAuth
    Dim eProfileUI As EA.Element ' boundary  ProfileComponent
    Dim eGetCtrl   As EA.Element ' control   get_me()
    Dim eUpdCtrl   As EA.Element ' control   update_me()
    Dim ePassCtrl  As EA.Element ' control   change_password()
    Dim eUsr       As EA.Element ' entity    Usuario
    Dim eSes       As EA.Element ' entity    Sesion
    Dim eAud       As EA.Element ' entity    BitacoraAuditoria

    Set eActor     = NuevoElemento(pkg, "Usuario Auth",        "Actor",    "")
    Set eProfileUI = NuevoElemento(pkg, "ProfileComponent",    "Sequence", "boundary")
    Set eGetCtrl   = NuevoElemento(pkg, "get_me()",            "Sequence", "control")
    Set eUpdCtrl   = NuevoElemento(pkg, "update_me()",         "Sequence", "control")
    Set ePassCtrl  = NuevoElemento(pkg, "change_password()",   "Sequence", "control")
    Set eUsr       = NuevoElemento(pkg, "Usuario",             "Sequence", "entity")
    Set eSes       = NuevoElemento(pkg, "Sesion",              "Sequence", "entity")
    Set eAud       = NuevoElemento(pkg, "BitacoraAuditoria",   "Sequence", "entity")

    ColocarEnDiagrama diag, eActor,      10,  110, -10, -920
    ColocarEnDiagrama diag, eProfileUI, 145,  270, -10, -920
    ColocarEnDiagrama diag, eGetCtrl,   300,  410, -10, -920
    ColocarEnDiagrama diag, eUpdCtrl,   440,  560, -10, -920
    ColocarEnDiagrama diag, ePassCtrl,  590,  730, -10, -920
    ColocarEnDiagrama diag, eUsr,       760,  870, -10, -920
    ColocarEnDiagrama diag, eSes,       900, 1005, -10, -920
    ColocarEnDiagrama diag, eAud,      1035, 1180, -10, -920

    '--- Fragmento OPT: Modificacion de datos personales ---
    NuevoFragmento pkg, diag, "opt", "[Modificacion de datos personales (nombre o telefono)]", _
                   0, 1190, -255, -430

    '--- Fragmento ALT: Contrasena correcta vs incorrecta ---
    NuevoFragmento pkg, diag, "alt", "[Contrasena actual correcta] / [else: Contrasena actual incorrecta]", _
                   0, 1190, -460, -900

    '--- Fragmento LOOP: Revocar sesiones remotas ---
    NuevoFragmento pkg, diag, "loop", "[Para cada sesion remota activa (id <> sesion_actual)]", _
                   585, 1010, -570, -630

    '--- MENSAJES ---
    ' 1. Carga de perfil
    Mensaje eActor,     eProfileUI, "1. Abrir vista de perfil",                                       1,  False
    Mensaje eProfileUI, eGetCtrl,   "2. GET /api/v1/users/me (Bearer Token)",                         2,  False
    Mensaje eGetCtrl,   eUsr,       "3. GET: leer datos perfil por usuario_id",                       3,  False
    Mensaje eUsr,       eGetCtrl,   "4. datos usuario (sin password_hash)",                            4,  True
    Mensaje eGetCtrl,   eProfileUI, "5. 200 OK: UserOut",                                             5,  True
    Mensaje eProfileUI, eActor,     "6. Renderizar formulario con datos actuales",                    6,  False

    ' OPT: Actualizacion
    Mensaje eActor,     eProfileUI, "7. Modificar valores y hacer clic en Guardar",                  7,  False
    Mensaje eProfileUI, eUpdCtrl,   "8. PATCH /api/v1/users/me (nombre, telefono)",                  8,  False
    Mensaje eUpdCtrl,   eUsr,       "9. PUT / PATCH: actualizar nombre y telefono",                   9,  False
    Mensaje eUpdCtrl,   eAud,       "10. POST: registrar auditoria de actualizacion",                 10, False
    Mensaje eUpdCtrl,   eProfileUI, "11. 200 OK: Perfil actualizado",                                11, True

    ' Cambio de contrasena (entrada)
    Mensaje eActor,     eProfileUI, "12. Ingresar password actual y nueva",                          12, False
    Mensaje eProfileUI, ePassCtrl,  "13. POST /api/v1/users/me/password (claves)",                   13, False
    Mensaje ePassCtrl,  eUsr,       "14. GET: consultar password_hash actual",                        14, False

    ' ALT: rama positiva
    Mensaje ePassCtrl,  eUsr,       "15. PATCH: guardar nuevo password_hash",                         15, False
    ' LOOP
    Mensaje ePassCtrl,  eSes,       "16. DELETE: revocar sesion concurrente (revocado_en=now)",       16, False
    Mensaje ePassCtrl,  eAud,       "17. POST: registrar auditoria de cambio de clave",               17, False
    Mensaje ePassCtrl,  eProfileUI, "18. 200 OK: Contrasena actualizada y demas sesiones revocadas", 18, True
    Mensaje eProfileUI, eActor,     "19. Notificar exito al usuario",                                19, False

    ' ALT: rama negativa
    Mensaje ePassCtrl,  eProfileUI, "20. 400 Bad Request: PASSWORD_INCORRECTA",                      20, True
    Mensaje eProfileUI, eActor,     "21. Mostrar error: La contrasena actual es incorrecta",          21, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
    Session.Output "CU-03 completado."
End Sub

'==========================================================================================
' CU-04: CERRAR SESION Y REFRESCO DE TOKENS
' Participantes: UsuarioAuth | Navbar/Profile | AuthInterceptor |
'                logout() | refresh() | Sesion | Usuario | BitacoraAuditoria
' Fragmentos   : opt  [Preservar cola offline]
'                alt  [Refresh token valido / Refresh token revocado]
' Mensajes     : 16 (1..16) con self-calls y retornos
'==========================================================================================
Sub CU04_CerrarSesionRefresh(pkg As EA.Package)
    Session.Output "Generando CU-04: Cerrar Sesion y Refresco de Tokens..."

    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-04 Cerrar Sesion y Refresco de Tokens", "Sequence")
    diag.Notes = "Fragmentos: opt [Preservar offline], alt [Refresh valido / revocado] | CRUD: DELETE, GET, PUT/PATCH, POST"
    diag.Update()

    Dim eActor    As EA.Element  ' Actor     UsuarioAuth
    Dim eNavUI    As EA.Element  ' boundary  Navbar/Profile
    Dim eIntUI    As EA.Element  ' boundary  AuthInterceptor
    Dim eOutCtrl  As EA.Element  ' control   logout()
    Dim eRefCtrl  As EA.Element  ' control   refresh()
    Dim eSes      As EA.Element  ' entity    Sesion
    Dim eUsr      As EA.Element  ' entity    Usuario
    Dim eAud      As EA.Element  ' entity    BitacoraAuditoria

    Set eActor   = NuevoElemento(pkg, "Usuario Auth",      "Actor",    "")
    Set eNavUI   = NuevoElemento(pkg, "Navbar/Profile",    "Sequence", "boundary")
    Set eIntUI   = NuevoElemento(pkg, "AuthInterceptor",   "Sequence", "boundary")
    Set eOutCtrl = NuevoElemento(pkg, "logout()",          "Sequence", "control")
    Set eRefCtrl = NuevoElemento(pkg, "refresh()",         "Sequence", "control")
    Set eSes     = NuevoElemento(pkg, "Sesion",            "Sequence", "entity")
    Set eUsr     = NuevoElemento(pkg, "Usuario",           "Sequence", "entity")
    Set eAud     = NuevoElemento(pkg, "BitacoraAuditoria", "Sequence", "entity")

    ColocarEnDiagrama diag, eActor,    10,  110, -10, -850
    ColocarEnDiagrama diag, eNavUI,   145,  270, -10, -850
    ColocarEnDiagrama diag, eIntUI,   300,  430, -10, -850
    ColocarEnDiagrama diag, eOutCtrl, 460,  580, -10, -850
    ColocarEnDiagrama diag, eRefCtrl, 610,  730, -10, -850
    ColocarEnDiagrama diag, eSes,     760,  870, -10, -850
    ColocarEnDiagrama diag, eUsr,     900, 1005, -10, -850
    ColocarEnDiagrama diag, eAud,    1035, 1180, -10, -850

    '--- Fragmento OPT: Preservar cola offline ---
    NuevoFragmento pkg, diag, "opt", "[Preservar cola de sincronizacion offline (IndexedDB)]", _
                   0, 290, -170, -245

    '--- Fragmento ALT: Refresh token valido vs revocado ---
    NuevoFragmento pkg, diag, "alt", "[Refresh token valido y no revocado] / [else: Refresh token revocado o expirado]", _
                   0, 1190, -380, -820

    '--- MENSAJES ---
    ' FLUJO A: LOGOUT
    Mensaje eActor,   eNavUI,   "1. Clic en Cerrar Sesion",                                          1,  False
    Mensaje eNavUI,   eOutCtrl, "2. POST /api/v1/auth/logout (Bearer Token)",                        2,  False
    Mensaje eOutCtrl, eSes,     "3. DELETE: revocar sesion (UPDATE revocado_en = now())",            3,  False
    Mensaje eOutCtrl, eAud,     "4. POST: registrar auditoria de logout",                            4,  False
    Mensaje eOutCtrl, eNavUI,   "5. 200 OK: {'mensaje': 'Sesion cerrada'}",                          5,  True
    ' OPT self-call
    MensajeReflexivo eNavUI, "Conservar cola offline fs_queue", 6
    Mensaje eNavUI,   eActor,   "6. Limpiar tokens de sesion (fs_*) y redirigir a /login",           7,  False

    ' FLUJO B: REFRESH AUTOMATICO
    Mensaje eActor,   eIntUI,   "7. Peticion protegida recibe 401 (Access Token expirado)",          8,  False
    Mensaje eIntUI,   eRefCtrl, "8. POST /api/v1/auth/refresh (refresh_token)",                      9,  False
    Mensaje eRefCtrl, eSes,     "9. GET: consultar sesion activa y vigente por hash",                10, False

    ' ALT: rama positiva (refresh valido)
    Mensaje eRefCtrl, eUsr,     "10. GET: verificar estado activo del usuario y empresa",            11, False
    Mensaje eRefCtrl, eSes,     "11. PUT / PATCH: rotar nuevo hash y expira_en",                    12, False
    Mensaje eRefCtrl, eAud,     "12. POST: registrar auditoria de refresh",                          13, False
    Mensaje eRefCtrl, eIntUI,   "13. 200 OK: RefreshResponse(nuevo access_token, nuevo refresh_token)", 14, True
    MensajeReflexivo eIntUI, "14. Reintento automatico de peticion original", 15

    ' ALT: rama negativa (refresh revocado)
    Mensaje eRefCtrl, eIntUI,   "15. 401 Unauthorized: REFRESH_INVALIDO",                           16, True
    Mensaje eIntUI,   eActor,   "16. Limpiar credenciales y redirigir a /login",                    17, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
    Session.Output "CU-04 completado."
End Sub

'==========================================================================================
' CU-05: REGISTRAR AUDITORIA TRANSVERSAL
' Participantes: Actor/Sistema | HttpBoundary | AuditMiddleware | FastAPI Router |
'                Usuario | Empresa | BitacoraAuditoria
' Fragmentos   : alt  [Ruta excluida / Ruta auditable]
'                opt  [Header Authorization presente]
'                loop [Para cada clave sensible en payload]
' Mensajes     : 12 (1..12) con self-calls y retornos
'==========================================================================================
Sub CU05_RegistrarAuditoria(pkg As EA.Package)
    Session.Output "Generando CU-05: Registrar Auditoria Transversal..."

    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-05 Registrar Auditoria Transversal", "Sequence")
    diag.Notes = "Fragmentos: alt [Ruta excluida/auditable], opt [JWT presente], loop [Enmascarar claves ***] | CRUD: GET, POST"
    diag.Update()

    Dim eActor   As EA.Element  ' Actor    Actor/Sistema
    Dim eHttpUI  As EA.Element  ' boundary HttpBoundary
    Dim eMW      As EA.Element  ' control  AuditMiddleware
    Dim eRouter  As EA.Element  ' control  FastAPI Router
    Dim eUsr     As EA.Element  ' entity   Usuario
    Dim eEmpresa As EA.Element  ' entity   Empresa
    Dim eAud     As EA.Element  ' entity   BitacoraAuditoria

    Set eActor   = NuevoElemento(pkg, "Actor / Sistema",     "Actor",    "")
    Set eHttpUI  = NuevoElemento(pkg, "HttpBoundary",        "Sequence", "boundary")
    Set eMW      = NuevoElemento(pkg, "AuditMiddleware",     "Sequence", "control")
    Set eRouter  = NuevoElemento(pkg, "FastAPI Router",      "Sequence", "control")
    Set eUsr     = NuevoElemento(pkg, "Usuario",             "Sequence", "entity")
    Set eEmpresa = NuevoElemento(pkg, "Empresa",             "Sequence", "entity")
    Set eAud     = NuevoElemento(pkg, "BitacoraAuditoria",   "Sequence", "entity")

    ColocarEnDiagrama diag, eActor,    10,  120, -10, -850
    ColocarEnDiagrama diag, eHttpUI,  155,  290, -10, -850
    ColocarEnDiagrama diag, eMW,      320,  460, -10, -850
    ColocarEnDiagrama diag, eRouter,  490,  620, -10, -850
    ColocarEnDiagrama diag, eUsr,     650,  760, -10, -850
    ColocarEnDiagrama diag, eEmpresa, 790,  895, -10, -850
    ColocarEnDiagrama diag, eAud,     925, 1070, -10, -850

    '--- Fragmento ALT: Ruta excluida vs ruta auditable ---
    NuevoFragmento pkg, diag, "alt", "[Ruta excluida (/docs,/health,/openapi.json)] / [else: Ruta auditable de la API]", _
                   0, 1080, -90, -820

    '--- Fragmento OPT: Header Authorization presente ---
    NuevoFragmento pkg, diag, "opt", "[Header Authorization presente: decodificar JWT]", _
                   315, 900, -310, -460

    '--- Fragmento LOOP: Enmascarar claves sensibles ---
    NuevoFragmento pkg, diag, "loop", "[Para cada clave en payload: password, token, hash, secret]", _
                   315, 465, -480, -540

    '--- MENSAJES ---
    Mensaje eActor,  eHttpUI, "1. Enviar solicitud HTTP (GET, POST, PUT, DELETE)",                1,  False
    Mensaje eHttpUI, eMW,     "2. Interceptar Request (metodo, ruta, body, headers)",             2,  False

    ' ALT: rama ruta excluida
    Mensaje eMW,    eRouter,  "3. call_next(request)",                                            3,  False
    Mensaje eRouter, eMW,     "4. Response HTTP",                                                  4,  True
    Mensaje eMW,    eHttpUI,  "5. Response directa sin registrar auditoria",                      5,  True

    ' ALT: rama ruta auditable (else)
    Mensaje eMW,    eRouter,  "6. call_next(request): procesar operacion",                        6,  False
    Mensaje eRouter, eMW,     "7. Response HTTP (status_code, payload)",                           7,  True

    ' OPT: decode JWT (self-call + consultas)
    MensajeReflexivo eMW, "decode_access_token(JWT)", 8
    Mensaje eMW,    eUsr,     "8. GET: extraer usuario_id y rol del token",                       9,  False
    Mensaje eMW,    eEmpresa, "9. GET: extraer empresa_id del tenant",                            10, False

    ' LOOP: enmascarar (self-call)
    MensajeReflexivo eMW, "_redact(): enmascarar con '***'", 11

    Mensaje eMW,    eAud,     "10. POST: guardar log HTTP con datos redactados (***)",            12, False
    Mensaje eMW,    eHttpUI,  "11. Devolver Response original intacta",                           13, True
    Mensaje eHttpUI, eActor,  "12. Renderizar resultado en la interfaz",                          14, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
    Session.Output "CU-05 completado."
End Sub

'--- Ejecutar ---
Main

