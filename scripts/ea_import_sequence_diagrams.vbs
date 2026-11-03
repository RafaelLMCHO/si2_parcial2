'========================================================================================
' Enterprise Architect 15 - Script de Automatización VBScript
' Propósito: Generar los Diagramas de Secuencia para los Casos de Uso CU-01 al CU-05
' Metodología: ICONIX (Actor, Boundary, Control, Entity, Métodos CRUD y Fragmentos alt/opt/loop)
' Proyecto: FashionStore SaaS - Segundo Parcial
'========================================================================================

Option Explicit

'----------------------------------------------------------------------------------------
' Procedimiento Principal
'----------------------------------------------------------------------------------------
Sub GenerarDiagramasSecuencia()
    On Error Resume Next

    Session.Output "==================================================================="
    Session.Output "Iniciando generación de Diagramas de Secuencia CU-01 a CU-05 en EA 15..."
    Session.Output "==================================================================="

    Dim rootPkg As EA.Package
    Set rootPkg = Repository.GetTreeSelectedPackage()

    If rootPkg Is Nothing Then
        Session.Prompt "Por favor seleccione un Paquete en el Explorador de Proyectos antes de ejecutar el script.", promptOK
        Exit Sub
    End If

    ' 1. Crear subpaquete contenedor
    Dim seqPkg As EA.Package
    Set seqPkg = rootPkg.Packages.AddNew("CU01_CU05_Diagramas_Secuencia", "")
    seqPkg.Update()
    rootPkg.Packages.Refresh()

    Session.Output "Paquete creado: " & seqPkg.Name

    ' 2. Generar cada uno de los 5 diagramas
    CrearCU01 seqPkg
    CrearCU02 seqPkg
    CrearCU03 seqPkg
    CrearCU04 seqPkg
    CrearCU05 seqPkg

    seqPkg.Diagrams.Refresh()
    seqPkg.Elements.Refresh()
    Repository.RefreshModelView seqPkg.PackageID

    Session.Output "==================================================================="
    Session.Output "¡Proceso finalizado con éxito! 5 Diagramas de Secuencia generados."
    Session.Output "==================================================================="
    Session.Prompt "Los 5 Diagramas de Secuencia han sido creados correctamente en el paquete '" & seqPkg.Name & "'.", promptOK
End Sub

'----------------------------------------------------------------------------------------
' Funciones Utilitarias del EA Object Model
'----------------------------------------------------------------------------------------

Function CrearElemento(pkg, nombre, tipo, estereotipo)
    Dim el As EA.Element
    Set el = pkg.Elements.AddNew(nombre, tipo)
    If estereotipo <> "" Then
        el.Stereotype = estereotipo
    End If
    el.Update()
    pkg.Elements.Refresh()
    Set CrearElemento = el
End Function

Function AgregarADiagrama(diag, el, xLeft, xRight, yTop, yBottom)
    Dim diagObj As EA.DiagramObject
    Set diagObj = diag.DiagramObjects.AddNew("", "")
    diagObj.ElementID = el.ElementID
    diagObj.left = xLeft
    diagObj.right = xRight
    diagObj.top = yTop
    diagObj.bottom = yBottom
    diagObj.Update()
    diag.DiagramObjects.Refresh()
    Set AgregarADiagrama = diagObj
End Function

Function AgregarMensaje(origen, destino, nombreMensaje, numSeq, esRetorno)
    Dim con As EA.Connector
    Set con = origen.Connectors.AddNew(nombreMensaje, "Sequence")
    con.SupplierID = destino.ElementID
    con.SequenceNo = numSeq
    If esRetorno Then
        con.Stereotype = "return"
    End If
    con.Update()
    origen.Connectors.Refresh()
    Set AgregarMensaje = con
End Function

Function AgregarFragmento(pkg, diag, nombre, operador, xLeft, xRight, yTop, yBottom)
    Dim frag As EA.Element
    Set frag = pkg.Elements.AddNew(nombre, "InteractionFragment")
    frag.PDATA1 = operador ' alt, opt, loop
    frag.Update()
    pkg.Elements.Refresh()

    Dim diagObj As EA.DiagramObject
    Set diagObj = diag.DiagramObjects.AddNew("", "")
    diagObj.ElementID = frag.ElementID
    diagObj.left = xLeft
    diagObj.right = xRight
    diagObj.top = yTop
    diagObj.bottom = yBottom
    diagObj.Update()
    diag.DiagramObjects.Refresh()
    Set AgregarFragmento = frag
End Function

'----------------------------------------------------------------------------------------
' CU-01: Iniciar Sesión (Login)
'----------------------------------------------------------------------------------------
Sub CrearCU01(pkg)
    Session.Output "Creando CU-01: Iniciar Sesión..."
    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-01 Iniciar Sesion (Login)", "Sequence")
    diag.Update()

    ' Lifelines (Posiciones X: 60, 220, 400, 580, 760, 940, 1120, 1300, 1480)
    Dim elActor, elBoundary, elControl, elEmpresa, elSuscrip, elRol, elUsuario, elSesion, elAudit
    Set elActor    = CrearElemento(pkg, "Usuario", "Actor", "")
    Set elBoundary = CrearElemento(pkg, "LoginComponent", "Sequence", "boundary")
    Set elControl  = CrearElemento(pkg, "login()", "Sequence", "control")
    Set elEmpresa  = CrearElemento(pkg, "Empresa", "Sequence", "entity")
    Set elSuscrip  = CrearElemento(pkg, "Suscripcion", "Sequence", "entity")
    Set elRol      = CrearElemento(pkg, "Rol", "Sequence", "entity")
    Set elUsuario  = CrearElemento(pkg, "Usuario", "Sequence", "entity")
    Set elSesion   = CrearElemento(pkg, "Sesion", "Sequence", "entity")
    Set elAudit    = CrearElemento(pkg, "BitacoraAuditoria", "Sequence", "entity")

    AgregarADiagrama diag, elActor,    60,   160,  -40, -900
    AgregarADiagrama diag, elBoundary, 220,  340,  -40, -900
    AgregarADiagrama diag, elControl,  400,  520,  -40, -900
    AgregarADiagrama diag, elEmpresa,  580,  690,  -40, -900
    AgregarADiagrama diag, elSuscrip,  740,  850,  -40, -900
    AgregarADiagrama diag, elRol,      900,  1000, -40, -900
    AgregarADiagrama diag, elUsuario,  1050, 1160, -40, -900
    AgregarADiagrama diag, elSesion,   1210, 1310, -40, -900
    AgregarADiagrama diag, elAudit,    1360, 1490, -40, -900

    ' Fragmentos alt / opt
    AgregarFragmento pkg, diag, "opt [Superadmin Global]", "opt", 380, 600, -80, -140
    AgregarFragmento pkg, diag, "alt [Credenciales validas y vigentes / Credenciales invalidas]", "alt", 40, 1520, -430, -850

    ' Mensajes
    AgregarMensaje elActor, elBoundary, "1. Ingresar empresa_slug, correo y clave", 1, False
    AgregarMensaje elBoundary, elControl, "2. POST /api/v1/auth/login", 2, False
    AgregarMensaje elControl, elEmpresa, "3. GET: buscar empresa activa por slug", 3, False
    AgregarMensaje elEmpresa, elControl, "4. empresa_id, estado='activa'", 4, True
    AgregarMensaje elControl, elSuscrip, "5. GET: verificar vigencia suscripcion", 5, False
    AgregarMensaje elSuscrip, elControl, "6. estado='activa', vigencia valida", 6, True
    AgregarMensaje elControl, elRol, "7. GET: consultar rol y permisos", 7, False
    AgregarMensaje elRol, elControl, "8. rol_nombre='administrador'", 8, True
    AgregarMensaje elControl, elUsuario, "9. GET: validar credenciales y correo verificado", 9, False
    AgregarMensaje elUsuario, elControl, "10. password_hash, email_verificado=true", 10, True
    AgregarMensaje elControl, elUsuario, "11. PATCH: actualizar ultimo_acceso = now()", 11, False
    AgregarMensaje elControl, elSesion, "12. POST: crear registro sesion con refresh_hash", 12, False
    AgregarMensaje elSesion, elControl, "13. session_id generado", 13, True
    AgregarMensaje elControl, elAudit, "14. POST: registrar auditoria login exitoso", 14, False
    AgregarMensaje elControl, elBoundary, "15. 200 OK: LoginResponse(access_token, refresh_token)", 15, True
    AgregarMensaje elBoundary, elActor, "16. Almacenar tokens y redirigir a /profile", 16, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
End Sub

'----------------------------------------------------------------------------------------
' CU-02: Registrarse y Verificar Correo
'----------------------------------------------------------------------------------------
Sub CrearCU02(pkg)
    Session.Output "Creando CU-02: Registrarse y Verificar Correo..."
    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-02 Registrarse y Verificar Correo", "Sequence")
    diag.Update()

    Dim elActor, elRegUI, elVerUI, elRegCtrl, elVerCtrl, elEmpresa, elRol, elUsuario, elToken, elAudit
    Set elActor   = CrearElemento(pkg, "Cliente", "Actor", "")
    Set elRegUI   = CrearElemento(pkg, "RegisterComponent", "Sequence", "boundary")
    Set elVerUI   = CrearElemento(pkg, "VerifyEmailComponent", "Sequence", "boundary")
    Set elRegCtrl = CrearElemento(pkg, "register()", "Sequence", "control")
    Set elVerCtrl = CrearElemento(pkg, "verify_email()", "Sequence", "control")
    Set elEmpresa = CrearElemento(pkg, "Empresa", "Sequence", "entity")
    Set elRol     = CrearElemento(pkg, "Rol", "Sequence", "entity")
    Set elUsuario = CrearElemento(pkg, "Usuario", "Sequence", "entity")
    Set elToken   = CrearElemento(pkg, "VerificacionCorreo", "Sequence", "entity")
    Set elAudit   = CrearElemento(pkg, "BitacoraAuditoria", "Sequence", "entity")

    AgregarADiagrama diag, elActor,   60,   160,  -40, -950
    AgregarADiagrama diag, elRegUI,   210,  320,  -40, -950
    AgregarADiagrama diag, elVerUI,   360,  480,  -40, -950
    AgregarADiagrama diag, elRegCtrl, 520,  630,  -40, -950
    AgregarADiagrama diag, elVerCtrl, 670,  780,  -40, -950
    AgregarADiagrama diag, elEmpresa, 820,  920,  -40, -950
    AgregarADiagrama diag, elRol,     960,  1050, -40, -950
    AgregarADiagrama diag, elUsuario, 1090, 1190, -40, -950
    AgregarADiagrama diag, elToken,   1230, 1350, -40, -950
    AgregarADiagrama diag, elAudit,   1390, 1510, -40, -950

    ' Fragmentos alt / opt
    AgregarFragmento pkg, diag, "alt [Correo disponible / Correo duplicado 409]", "alt", 40, 1530, -220, -500
    AgregarFragmento pkg, diag, "opt [Modo Demo activo: exponer token]", "opt", 500, 750, -380, -440
    AgregarFragmento pkg, diag, "alt [Token valido / Token invalido 400]", "alt", 40, 1530, -640, -910

    ' Mensajes Fase 1
    AgregarMensaje elActor, elRegUI, "1. Completar formulario de registro", 1, False
    AgregarMensaje elRegUI, elRegCtrl, "2. POST /api/v1/auth/register (datos)", 2, False
    AgregarMensaje elRegCtrl, elEmpresa, "3. GET: validar empresa existente", 3, False
    AgregarMensaje elRegCtrl, elRol, "4. GET: obtener id rol cliente", 4, False
    AgregarMensaje elRegCtrl, elUsuario, "5. GET: verificar no duplicidad correo", 5, False
    AgregarMensaje elRegCtrl, elUsuario, "6. POST: crear usuario (inactivo, no verificado)", 6, False
    AgregarMensaje elRegCtrl, elToken, "7. POST: crear token con expiracion", 7, False
    AgregarMensaje elRegCtrl, elAudit, "8. POST: registrar auditoria registro", 8, False
    AgregarMensaje elRegCtrl, elRegUI, "9. 201 Created: RegisterResponse", 9, True
    AgregarMensaje elRegUI, elActor, "10. Mostrar aviso: Revise su correo", 10, False

    ' Mensajes Fase 2
    AgregarMensaje elActor, elVerUI, "11. Ingresar token de confirmacion", 11, False
    AgregarMensaje elVerUI, elVerCtrl, "12. POST /api/v1/auth/verify-email", 12, False
    AgregarMensaje elVerCtrl, elToken, "13. GET: validar token por hash y expiracion", 13, False
    AgregarMensaje elVerCtrl, elUsuario, "14. PATCH: activar usuario y email_verificado=true", 14, False
    AgregarMensaje elVerCtrl, elToken, "15. DELETE: invalidar token consumido", 15, False
    AgregarMensaje elVerCtrl, elAudit, "16. POST: registrar auditoria verificacion", 16, False
    AgregarMensaje elVerCtrl, elVerUI, "17. 200 OK: Correo verificado", 17, True
    AgregarMensaje elVerUI, elActor, "18. Notificar cuenta activada (ir a login)", 18, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
End Sub

'----------------------------------------------------------------------------------------
' CU-03: Gestionar Perfil y Cambiar Contraseña
'----------------------------------------------------------------------------------------
Sub CrearCU03(pkg)
    Session.Output "Creando CU-03: Gestionar Perfil..."
    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-03 Gestionar Perfil y Contrasena", "Sequence")
    diag.Update()

    Dim elActor, elUI, elGet, elUpd, elPass, elUsuario, elSesion, elAudit
    Set elActor   = CrearElemento(pkg, "Usuario Auth", "Actor", "")
    Set elUI      = CrearElemento(pkg, "ProfileComponent", "Sequence", "boundary")
    Set elGet     = CrearElemento(pkg, "get_me()", "Sequence", "control")
    Set elUpd     = CrearElemento(pkg, "update_me()", "Sequence", "control")
    Set elPass    = CrearElemento(pkg, "change_password()", "Sequence", "control")
    Set elUsuario = CrearElemento(pkg, "Usuario", "Sequence", "entity")
    Set elSesion  = CrearElemento(pkg, "Sesion", "Sequence", "entity")
    Set elAudit   = CrearElemento(pkg, "BitacoraAuditoria", "Sequence", "entity")

    AgregarADiagrama diag, elActor,   60,   160,  -40, -920
    AgregarADiagrama diag, elUI,      220,  340,  -40, -920
    AgregarADiagrama diag, elGet,     400,  500,  -40, -920
    AgregarADiagrama diag, elUpd,     540,  640,  -40, -920
    AgregarADiagrama diag, elPass,    680,  810,  -40, -920
    AgregarADiagrama diag, elUsuario, 860,  960,  -40, -920
    AgregarADiagrama diag, elSesion,  1010, 1110, -40, -920
    AgregarADiagrama diag, elAudit,   1160, 1280, -40, -920

    ' Fragmentos
    AgregarFragmento pkg, diag, "opt [Modificacion de datos personales]", "opt", 40, 1300, -260, -420
    AgregarFragmento pkg, diag, "alt [Clave valida / Clave actual incorrecta 400]", "alt", 40, 1300, -520, -880
    AgregarFragmento pkg, diag, "loop [Para cada sesion activa remota (id <> sesion_actual)]", "loop", 660, 1130, -660, -740

    ' Carga perfil
    AgregarMensaje elActor, elUI, "1. Abrir vista perfil", 1, False
    AgregarMensaje elUI, elGet, "2. GET /api/v1/users/me (Bearer)", 2, False
    AgregarMensaje elGet, elUsuario, "3. GET: leer datos perfil por usuario_id", 3, False
    AgregarMensaje elUsuario, elGet, "4. datos usuario (sin hash)", 4, True
    AgregarMensaje elGet, elUI, "5. 200 OK: UserOut", 5, True
    AgregarMensaje elUI, elActor, "6. Renderizar datos en pantalla", 6, False

    ' Modificación
    AgregarMensaje elActor, elUI, "7. Modificar nombre/telefono y guardar", 7, False
    AgregarMensaje elUI, elUpd, "8. PATCH /api/v1/users/me (datos)", 8, False
    AgregarMensaje elUpd, elUsuario, "9. PUT / PATCH: actualizar nombre y telefono", 9, False
    AgregarMensaje elUpd, elAudit, "10. POST: registrar auditoria actualizacion", 10, False
    AgregarMensaje elUpd, elUI, "11. 200 OK: Perfil actualizado", 11, True

    ' Cambio clave
    AgregarMensaje elActor, elUI, "12. Ingresar password actual y nueva", 12, False
    AgregarMensaje elUI, elPass, "13. POST /api/v1/users/me/password", 13, False
    AgregarMensaje elPass, elUsuario, "14. GET: consultar password_hash actual", 14, False
    AgregarMensaje elPass, elUsuario, "15. PATCH: guardar nuevo password_hash", 15, False
    AgregarMensaje elPass, elSesion, "16. DELETE: revocar sesion remota (revocado_en=now)", 16, False
    AgregarMensaje elPass, elAudit, "17. POST: registrar auditoria cambio password", 17, False
    AgregarMensaje elPass, elUI, "18. 200 OK: Password actualizada", 18, True
    AgregarMensaje elUI, elActor, "19. Confirmar éxito y demas sesiones revocadas", 19, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
End Sub

'----------------------------------------------------------------------------------------
' CU-04: Cerrar Sesión y Refresco de Tokens
'----------------------------------------------------------------------------------------
Sub CrearCU04(pkg)
    Session.Output "Creando CU-04: Cerrar Sesión y Refresco..."
    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-04 Cerrar Sesion y Refresco", "Sequence")
    diag.Update()

    Dim elActor, elNavUI, elIntUI, elOutCtrl, elRefCtrl, elSesion, elUsuario, elAudit
    Set elActor   = CrearElemento(pkg, "Usuario Auth", "Actor", "")
    Set elNavUI   = CrearElemento(pkg, "Navbar / Profile", "Sequence", "boundary")
    Set elIntUI   = CrearElemento(pkg, "AuthInterceptor", "Sequence", "boundary")
    Set elOutCtrl = CrearElemento(pkg, "logout()", "Sequence", "control")
    Set elRefCtrl = CrearElemento(pkg, "refresh()", "Sequence", "control")
    Set elSesion  = CrearElemento(pkg, "Sesion", "Sequence", "entity")
    Set elUsuario = CrearElemento(pkg, "Usuario", "Sequence", "entity")
    Set elAudit   = CrearElemento(pkg, "BitacoraAuditoria", "Sequence", "entity")

    AgregarADiagrama diag, elActor,   60,   160,  -40, -850
    AgregarADiagrama diag, elNavUI,   210,  320,  -40, -850
    AgregarADiagrama diag, elIntUI,   360,  480,  -40, -850
    AgregarADiagrama diag, elOutCtrl, 520,  620,  -40, -850
    AgregarADiagrama diag, elRefCtrl, 660,  760,  -40, -850
    AgregarADiagrama diag, elSesion,  810,  910,  -40, -850
    AgregarADiagrama diag, elUsuario, 960,  1060, -40, -850
    AgregarADiagrama diag, elAudit,   1110, 1230, -40, -850

    ' Fragmentos
    AgregarFragmento pkg, diag, "opt [Preservar cola de sincronizacion offline]", "opt", 190, 340, -180, -240
    AgregarFragmento pkg, diag, "alt [Refresh token valido y activo / Token revocado 401]", "alt", 40, 1250, -460, -800

    ' Logout
    AgregarMensaje elActor, elNavUI, "1. Clic en Cerrar Sesion", 1, False
    AgregarMensaje elNavUI, elOutCtrl, "2. POST /api/v1/auth/logout (Bearer)", 2, False
    AgregarMensaje elOutCtrl, elSesion, "3. DELETE: revocar sesion (revocado_en=now)", 3, False
    AgregarMensaje elOutCtrl, elAudit, "4. POST: registrar auditoria logout", 4, False
    AgregarMensaje elOutCtrl, elNavUI, "5. 200 OK: Sesion cerrada", 5, True
    AgregarMensaje elNavUI, elActor, "6. Limpiar credenciales y redirigir a /login", 6, False

    ' Refresh
    AgregarMensaje elActor, elIntUI, "7. Peticion interceptada por token vencido 401", 7, False
    AgregarMensaje elIntUI, elRefCtrl, "8. POST /api/v1/auth/refresh (refresh_token)", 8, False
    AgregarMensaje elRefCtrl, elSesion, "9. GET: consultar sesion activa por hash", 9, False
    AgregarMensaje elRefCtrl, elUsuario, "10. GET: verificar usuario activo y suscripcion", 10, False
    AgregarMensaje elRefCtrl, elSesion, "11. PUT / PATCH: rotar nuevo refresh_token", 11, False
    AgregarMensaje elRefCtrl, elAudit, "12. POST: registrar auditoria refresh", 12, False
    AgregarMensaje elRefCtrl, elIntUI, "13. 200 OK: RefreshResponse(tokens)", 13, True
    AgregarMensaje elIntUI, elActor, "14. Reintento automatico exitoso", 14, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
End Sub

'----------------------------------------------------------------------------------------
' CU-05: Registrar Auditoría del Sistema
'----------------------------------------------------------------------------------------
Sub CrearCU05(pkg)
    Session.Output "Creando CU-05: Registrar Auditoría..."
    Dim diag As EA.Diagram
    Set diag = pkg.Diagrams.AddNew("CU-05 Registrar Auditoria Transversal", "Sequence")
    diag.Update()

    Dim elActor, elHttpUI, elMW, elRouter, elUsuario, elEmpresa, elAudit
    Set elActor   = CrearElemento(pkg, "Actor / Sistema", "Actor", "")
    Set elHttpUI  = CrearElemento(pkg, "HttpRequestBoundary", "Sequence", "boundary")
    Set elMW      = CrearElemento(pkg, "audit_middleware()", "Sequence", "control")
    Set elRouter  = CrearElemento(pkg, "FastAPI Router", "Sequence", "control")
    Set elUsuario = CrearElemento(pkg, "Usuario", "Sequence", "entity")
    Set elEmpresa = CrearElemento(pkg, "Empresa", "Sequence", "entity")
    Set elAudit   = CrearElemento(pkg, "BitacoraAuditoria", "Sequence", "entity")

    AgregarADiagrama diag, elActor,   60,   160,  -40, -850
    AgregarADiagrama diag, elHttpUI,  210,  340,  -40, -850
    AgregarADiagrama diag, elMW,      400,  520,  -40, -850
    AgregarADiagrama diag, elRouter,  580,  690,  -40, -850
    AgregarADiagrama diag, elUsuario, 750,  850,  -40, -850
    AgregarADiagrama diag, elEmpresa, 900,  1000, -40, -850
    AgregarADiagrama diag, elAudit,   1060, 1180, -40, -850

    ' Fragmentos
    AgregarFragmento pkg, diag, "alt [Ruta excluida (/docs, /health) / Ruta auditable de la API]", "alt", 40, 1200, -100, -800
    AgregarFragmento pkg, diag, "opt [Header Authorization presente: decodificar JWT]", "opt", 380, 1020, -310, -440
    AgregarFragmento pkg, diag, "loop [Para cada parametro sensible: enmascarar con ***]", "loop", 380, 540, -480, -560

    ' Mensajes
    AgregarMensaje elActor, elHttpUI, "1. Enviar solicitud HTTP (GET, POST, PUT, DELETE)", 1, False
    AgregarMensaje elHttpUI, elMW, "2. Interceptar Request (ruta, metodo, body)", 2, False
    AgregarMensaje elMW, elRouter, "3. call_next(request): procesar operacion", 3, False
    AgregarMensaje elRouter, elMW, "4. Response HTTP (status_code, payload)", 4, True
    AgregarMensaje elMW, elUsuario, "5. GET: extraer usuario_id y rol del token", 5, False
    AgregarMensaje elMW, elEmpresa, "6. GET: extraer empresa_id tenant", 6, False
    AgregarMensaje elMW, elAudit, "7. POST: guardar log HTTP con datos redactados (***)", 7, False
    AgregarMensaje elMW, elHttpUI, "8. Devolver Response original intacta", 8, True
    AgregarMensaje elHttpUI, elActor, "9. Renderizar respuesta en interfaz", 9, False

    diag.Update()
    Repository.ReloadDiagram diag.DiagramID
End Sub

' Ejecutar el script
GenerarDiagramasSecuencia

