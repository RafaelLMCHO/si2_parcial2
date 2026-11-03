import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings
from app.core.errors import api_error
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    new_verification_token,
    verify_password,
)
from app.db import admin_connection, audit_event, tenant_connection
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    UserOut,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.schemas.user import PasswordChangeRequest, UserUpdateRequest

logger = logging.getLogger(__name__)


def _value(row: Any, key: str, default: Any = None) -> Any:
    return row[key] if key in row.keys() else default


def _user_out(row: Any) -> UserOut:
    return UserOut(
        id=_value(row, "usuario_id", _value(row, "id")),
        empresa_id=_value(row, "empresa_id"),
        nombre=_value(row, "nombre"),
        correo=_value(row, "correo"),
        telefono=_value(row, "telefono"),
        email_verificado=bool(_value(row, "email_verificado", False)),
        estado=_value(row, "usuario_estado", _value(row, "estado", "activo")),
        rol=_value(row, "rol_nombre", _value(row, "rol", "")),
        sucursal_id=_value(row, "sucursal_id"),
        ultimo_acceso=_value(row, "ultimo_acceso"),
        created_at=_value(row, "created_at"),
    )


async def _safe_audit(**kwargs: Any) -> None:
    try:
        await audit_event(**kwargs)
    except Exception:
        logger.exception("No se pudo registrar el evento de auditoria")


def _validate_access(row: Any) -> None:
    if not bool(_value(row, "email_verificado", False)):
        raise api_error(403, "EMAIL_NO_VERIFICADO", "Debe verificar su correo antes de iniciar sesion")

    if _value(row, "usuario_estado") != "activo":
        raise api_error(403, "USUARIO_INACTIVO", "El usuario no esta activo")

    empresa_id = _value(row, "empresa_id")
    if empresa_id is None:
        return

    empresa_estado = _value(row, "empresa_estado")
    if empresa_estado == "pendiente_plan":
        raise api_error(
            403,
            "EMPRESA_PENDIENTE_PLAN",
            "La empresa aun no tiene un plan asignado",
        )
    if empresa_estado != "activa":
        raise api_error(403, "EMPRESA_NO_ACTIVA", "La empresa no se encuentra activa")

    suscripcion_estado = _value(row, "suscripcion_estado")
    if suscripcion_estado not in ("prueba", "activa"):
        raise api_error(402, "SUSCRIPCION_INACTIVA", "La empresa no tiene una suscripcion activa")

    fecha_fin = _value(row, "suscripcion_fecha_fin")
    if fecha_fin is not None and fecha_fin < date.today():
        raise api_error(402, "SUSCRIPCION_VENCIDA", "La suscripcion de la empresa esta vencida")


def _refresh_expiration() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_days)


async def login(data: LoginRequest, ip: str | None, user_agent: str | None) -> LoginResponse:
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM fn_login_lookup($1, $2)",
            data.empresa_slug,
            str(data.correo),
        )

    if row is None:
        await _safe_audit(
            empresa_id=None,
            usuario_id=None,
            actor_tipo="sistema",
            accion="login",
            entidad="auth",
            ip=ip,
            metodo="POST",
            endpoint="/api/v1/auth/login",
            parametros={"empresa_slug": data.empresa_slug, "correo": str(data.correo), "resultado": "fallido"},
        )
        raise api_error(401, "CREDENCIALES_INVALIDAS", "Correo o contrasena incorrectos")

    try:
        _validate_access(row)
    except Exception:
        await _safe_audit(
            empresa_id=_value(row, "empresa_id"),
            usuario_id=_value(row, "usuario_id"),
            actor_tipo="usuario",
            accion="login",
            entidad="auth",
            ip=ip,
            metodo="POST",
            endpoint="/api/v1/auth/login",
            parametros={"empresa_slug": data.empresa_slug, "correo": str(data.correo), "resultado": "rechazado"},
        )
        raise

    if not verify_password(data.password, _value(row, "password_hash", "")):
        await _safe_audit(
            empresa_id=_value(row, "empresa_id"),
            usuario_id=_value(row, "usuario_id"),
            actor_tipo="usuario",
            accion="login",
            entidad="auth",
            ip=ip,
            metodo="POST",
            endpoint="/api/v1/auth/login",
            parametros={"empresa_slug": data.empresa_slug, "correo": str(data.correo), "resultado": "fallido"},
        )
        raise api_error(401, "CREDENCIALES_INVALIDAS", "Correo o contrasena incorrectos")

    refresh_token = new_refresh_token()
    refresh_hash = hash_token(refresh_token)
    expires_at = _refresh_expiration()
    empresa_id = _value(row, "empresa_id")
    usuario_id = _value(row, "usuario_id")

    if empresa_id is not None:
        async with tenant_connection(empresa_id, usuario_id) as conn:
            session_id = await conn.fetchval(
                """
                INSERT INTO sesion (
                    empresa_id, usuario_id, refresh_token_hash, ip_origen, user_agent, expira_en
                ) VALUES ($1, $2, $3, $4::inet, $5, $6)
                RETURNING id
                """,
                empresa_id,
                usuario_id,
                refresh_hash,
                ip,
                user_agent,
                expires_at,
            )
            await conn.execute(
                "UPDATE usuario SET ultimo_acceso = now() WHERE id = $1",
                usuario_id,
            )
    else:
        async with admin_connection() as conn:
            session_id = await conn.fetchval(
                """
                INSERT INTO sesion (
                    empresa_id, usuario_id, refresh_token_hash, ip_origen, user_agent, expira_en
                ) VALUES (NULL, $1, $2, $3::inet, $4, $5)
                RETURNING id
                """,
                usuario_id,
                refresh_hash,
                ip,
                user_agent,
                expires_at,
            )
            await conn.execute(
                "UPDATE usuario SET ultimo_acceso = now() WHERE id = $1",
                usuario_id,
            )

    access_token, expires_in = create_access_token(
        user_id=str(usuario_id),
        session_id=str(session_id),
        empresa_id=str(empresa_id) if empresa_id else None,
        rol=_value(row, "rol_nombre", ""),
    )

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="superadmin" if empresa_id is None else "usuario",
        accion="login",
        entidad="sesion",
        entidad_id=session_id,
        ip=ip,
        es_accion_superadmin=empresa_id is None,
        metodo="POST",
        endpoint="/api/v1/auth/login",
        parametros={"empresa_slug": data.empresa_slug, "correo": str(data.correo), "resultado": "exitoso"},
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        usuario=_user_out(row),
    )


async def refresh(data: RefreshRequest, ip: str | None, user_agent: str | None) -> RefreshResponse:
    token_hash = hash_token(data.refresh_token)
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.id AS session_id,
                   s.empresa_id,
                   s.usuario_id,
                   u.nombre,
                   u.correo,
                   u.telefono,
                   u.email_verificado,
                   u.estado AS usuario_estado,
                   u.sucursal_id,
                   u.ultimo_acceso,
                   u.created_at,
                   r.nombre AS rol_nombre,
                   e.slug AS empresa_slug,
                   e.estado AS empresa_estado,
                   su.estado AS suscripcion_estado,
                   su.fecha_fin AS suscripcion_fecha_fin
              FROM sesion s
              JOIN usuario u ON u.id = s.usuario_id
              JOIN rol r ON r.id = u.rol_id
              LEFT JOIN empresa e ON e.id = s.empresa_id
              LEFT JOIN LATERAL (
                  SELECT s2.estado, s2.fecha_fin
                    FROM suscripcion s2
                   WHERE s2.empresa_id = s.empresa_id
                     AND s2.estado IN ('prueba', 'activa', 'mora')
                   ORDER BY s2.fecha_inicio DESC
                   LIMIT 1
              ) su ON true
             WHERE s.refresh_token_hash = $1
               AND s.revocado_en IS NULL
               AND s.expira_en > now()
            """,
            token_hash,
        )

    if row is None:
        raise api_error(401, "REFRESH_INVALIDO", "El token de refresco no es valido o fue revocado")

    _validate_access(row)

    new_refresh = new_refresh_token()
    new_hash = hash_token(new_refresh)
    new_expires = _refresh_expiration()
    empresa_id = _value(row, "empresa_id")
    usuario_id = _value(row, "usuario_id")
    session_id = _value(row, "session_id")

    if empresa_id is not None:
        async with tenant_connection(empresa_id, usuario_id) as conn:
            await conn.execute(
                """
                UPDATE sesion
                   SET refresh_token_hash = $1,
                       expira_en = $2,
                       ip_origen = $3::inet,
                       user_agent = $4
                 WHERE id = $5
                """,
                new_hash,
                new_expires,
                ip,
                user_agent,
                session_id,
            )
    else:
        async with admin_connection() as conn:
            await conn.execute(
                """
                UPDATE sesion
                   SET refresh_token_hash = $1,
                       expira_en = $2,
                       ip_origen = $3::inet,
                       user_agent = $4
                 WHERE id = $5
                """,
                new_hash,
                new_expires,
                ip,
                user_agent,
                session_id,
            )

    access_token, expires_in = create_access_token(
        user_id=str(usuario_id),
        session_id=str(session_id),
        empresa_id=str(empresa_id) if empresa_id else None,
        rol=_value(row, "rol_nombre", ""),
    )

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="superadmin" if empresa_id is None else "usuario",
        accion="access",
        entidad="sesion",
        entidad_id=session_id,
        ip=ip,
        es_accion_superadmin=empresa_id is None,
        metodo="POST",
        endpoint="/api/v1/auth/refresh",
        parametros={"resultado": "refresh"},
    )

    return RefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=expires_in,
    )


async def logout(empresa_id: str | None, usuario_id: str, session_id: str, ip: str | None) -> dict:
    if empresa_id is not None:
        async with tenant_connection(empresa_id, usuario_id) as conn:
            await conn.execute(
                "UPDATE sesion SET revocado_en = now() WHERE id = $1 AND revocado_en IS NULL",
                session_id,
            )
    else:
        async with admin_connection() as conn:
            await conn.execute(
                "UPDATE sesion SET revocado_en = now() WHERE id = $1 AND revocado_en IS NULL",
                session_id,
            )

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="superadmin" if empresa_id is None else "usuario",
        accion="logout",
        entidad="sesion",
        entidad_id=session_id,
        ip=ip,
        es_accion_superadmin=empresa_id is None,
        metodo="POST",
        endpoint="/api/v1/auth/logout",
        parametros={"resultado": "logout"},
    )
    return {"mensaje": "Sesion cerrada"}


def _send_verification_email(correo: str, token: str, empresa_slug: str) -> None:
    settings = get_settings()
    logger.info(
        "Correo de verificacion para %s (tenant=%s). Token: %s",
        correo,
        empresa_slug,
        token,
    )
    if settings.email_backend == "console":
        return


async def register(data: RegisterRequest, ip: str | None) -> RegisterResponse:
    settings = get_settings()
    async with admin_connection() as conn:
        empresa_id = await conn.fetchval("SELECT fn_empresa_por_slug($1)", data.empresa_slug)

    if empresa_id is None:
        raise api_error(404, "EMPRESA_NO_ENCONTRADA", "La empresa indicada no existe")

    async with tenant_connection(empresa_id) as conn:
        exists = await conn.fetchval(
            "SELECT id FROM usuario WHERE correo = $1 AND deleted_at IS NULL",
            str(data.correo),
        )
        if exists is not None:
            raise api_error(409, "CORREO_DUPLICADO", "Ya existe un usuario con ese correo en la empresa")

        rol_id = await conn.fetchval(
            "SELECT id FROM rol WHERE empresa_id = $1 AND nombre = 'cliente'",
            empresa_id,
        )
        if rol_id is None:
            raise api_error(500, "ROL_CLIENTE_NO_CONFIGURADO", "La empresa no tiene configurado el rol cliente")

        usuario_id = await conn.fetchval(
            """
            INSERT INTO usuario (empresa_id, rol_id, nombre, correo, password_hash, telefono, email_verificado, estado)
            VALUES ($1, $2, $3, $4, $5, $6, false, 'inactivo')
            RETURNING id
            """,
            empresa_id,
            rol_id,
            data.nombre,
            str(data.correo),
            hash_password(data.password),
            data.telefono,
        )

        token = new_verification_token()
        await conn.execute(
            """
            INSERT INTO verificacion_correo (empresa_id, usuario_id, token_hash, expira_en)
            VALUES ($1, $2, $3, $4)
            """,
            empresa_id,
            usuario_id,
            hash_token(token),
            datetime.now(timezone.utc)
            + timedelta(minutes=settings.verification_token_minutes),
        )

    _send_verification_email(str(data.correo), token, data.empresa_slug)

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="usuario",
        accion="insert",
        entidad="usuario",
        entidad_id=usuario_id,
        ip=ip,
        metodo="POST",
        endpoint="/api/v1/auth/register",
        parametros={"empresa_slug": data.empresa_slug, "correo": str(data.correo)},
    )

    return RegisterResponse(
        mensaje="Usuario registrado. Revise su correo para verificar la cuenta.",
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        verification_token=token if settings.expose_verification_token else None,
    )


async def verify_email(data: VerifyEmailRequest, ip: str | None) -> VerifyEmailResponse:
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM fn_verificar_correo($1, $2)",
            data.empresa_slug,
            hash_token(data.token),
        )

    if row is None:
        raise api_error(400, "TOKEN_INVALIDO", "El token de verificacion no es valido o expiro")

    usuario_id = _value(row, "usuario_id")
    empresa_id = _value(row, "empresa_id")

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="usuario",
        accion="update",
        entidad="usuario",
        entidad_id=usuario_id,
        ip=ip,
        metodo="POST",
        endpoint="/api/v1/auth/verify-email",
        parametros={"resultado": "correo_verificado"},
    )

    return VerifyEmailResponse(
        mensaje="Correo verificado correctamente",
        usuario_id=usuario_id,
        empresa_id=empresa_id,
    )


async def get_me(empresa_id: str | None, usuario_id: str) -> UserOut:
    sql = """
        SELECT u.id,
               u.empresa_id,
               u.nombre,
               u.correo,
               u.telefono,
               u.email_verificado,
               u.estado,
               u.sucursal_id,
               u.ultimo_acceso,
               u.created_at,
               r.nombre AS rol
          FROM usuario u
          JOIN rol r ON r.id = u.rol_id
         WHERE u.id = $1
           AND u.deleted_at IS NULL
    """
    if empresa_id is not None:
        async with tenant_connection(empresa_id, usuario_id) as conn:
            row = await conn.fetchrow(sql, usuario_id)
    else:
        async with admin_connection() as conn:
            row = await conn.fetchrow(sql, usuario_id)

    if row is None:
        raise api_error(404, "USUARIO_NO_ENCONTRADO", "Usuario no encontrado")
    return _user_out(row)


async def update_me(
    empresa_id: str | None,
    usuario_id: str,
    data: UserUpdateRequest,
    ip: str | None,
) -> UserOut:
    sql = """
        UPDATE usuario
           SET nombre = COALESCE($2, nombre),
               telefono = COALESCE($3, telefono),
               updated_at = now()
         WHERE id = $1
           AND deleted_at IS NULL
        RETURNING id
    """
    if empresa_id is not None:
        async with tenant_connection(empresa_id, usuario_id) as conn:
            updated = await conn.fetchval(sql, usuario_id, data.nombre, data.telefono)
    else:
        async with admin_connection() as conn:
            updated = await conn.fetchval(sql, usuario_id, data.nombre, data.telefono)

    if updated is None:
        raise api_error(404, "USUARIO_NO_ENCONTRADO", "Usuario no encontrado")

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="superadmin" if empresa_id is None else "usuario",
        accion="update",
        entidad="usuario",
        entidad_id=usuario_id,
        ip=ip,
        es_accion_superadmin=empresa_id is None,
        metodo="PATCH",
        endpoint="/api/v1/users/me",
        parametros={"campos": [k for k, v in data.model_dump().items() if v is not None]},
    )
    return await get_me(empresa_id, usuario_id)


async def change_password(
    empresa_id: str | None,
    usuario_id: str,
    session_id: str,
    data: PasswordChangeRequest,
    ip: str | None,
) -> dict:
    if data.password_actual == data.password_nueva:
        raise api_error(400, "PASSWORD_IGUAL", "La nueva contrasena debe ser diferente a la actual")

    if empresa_id is not None:
        async with tenant_connection(empresa_id, usuario_id) as conn:
            current_hash = await conn.fetchval(
                "SELECT password_hash FROM usuario WHERE id = $1 AND deleted_at IS NULL",
                usuario_id,
            )
            if current_hash is None:
                raise api_error(404, "USUARIO_NO_ENCONTRADO", "Usuario no encontrado")
            if not verify_password(data.password_actual, current_hash):
                raise api_error(400, "PASSWORD_INCORRECTA", "La contrasena actual es incorrecta")

            await conn.execute(
                "UPDATE usuario SET password_hash = $2, updated_at = now() WHERE id = $1",
                usuario_id,
                hash_password(data.password_nueva),
            )
            await conn.execute(
                """
                UPDATE sesion
                   SET revocado_en = now()
                 WHERE usuario_id = $1
                   AND id <> $2
                   AND revocado_en IS NULL
                """,
                usuario_id,
                session_id,
            )
    else:
        async with admin_connection() as conn:
            current_hash = await conn.fetchval(
                "SELECT password_hash FROM usuario WHERE id = $1 AND deleted_at IS NULL",
                usuario_id,
            )
            if current_hash is None:
                raise api_error(404, "USUARIO_NO_ENCONTRADO", "Usuario no encontrado")
            if not verify_password(data.password_actual, current_hash):
                raise api_error(400, "PASSWORD_INCORRECTA", "La contrasena actual es incorrecta")

            await conn.execute(
                "UPDATE usuario SET password_hash = $2, updated_at = now() WHERE id = $1",
                usuario_id,
                hash_password(data.password_nueva),
            )
            await conn.execute(
                """
                UPDATE sesion
                   SET revocado_en = now()
                 WHERE usuario_id = $1
                   AND id <> $2
                   AND revocado_en IS NULL
                """,
                usuario_id,
                session_id,
            )

    await _safe_audit(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        actor_tipo="superadmin" if empresa_id is None else "usuario",
        accion="update",
        entidad="usuario",
        entidad_id=usuario_id,
        ip=ip,
        es_accion_superadmin=empresa_id is None,
        metodo="POST",
        endpoint="/api/v1/users/me/password",
        parametros={"resultado": "password_cambiado"},
    )
    return {"mensaje": "Contrasena actualizada. Las demas sesiones fueron cerradas."}
