import asyncio
import json
import logging
from typing import Any

from fastapi import Request, Response

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db import audit_event

logger = logging.getLogger(__name__)

_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico")
_SKIP_AUTH_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/register",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/refresh",
}
_SENSITIVE_KEYS = (
    "password",
    "password_actual",
    "password_nueva",
    "password_hash",
    "token",
    "refresh_token",
    "authorization",
    "secret",
    "firma",
)
_MAX_BODY_CHARS = 4000


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    trusted = [p.strip() for p in get_settings().trusted_proxies.split(",") if p.strip()]
    if forwarded and trusted:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("***" if any(s in key.lower() for s in _SENSITIVE_KEYS) else _redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _parse_body(body: bytes) -> Any:
    if not body:
        return None
    if len(body) > _MAX_BODY_CHARS:
        return "<cuerpo demasiado grande>"
    try:
        return _redact(json.loads(body))
    except Exception:
        return "<cuerpo no json>"


async def _safe_audit(**kwargs: Any) -> None:
    try:
        await audit_event(**kwargs)
    except Exception:
        logger.exception("No se pudo registrar la auditoria HTTP")


async def audit_middleware(request: Request, call_next) -> Response:
    settings = get_settings()
    path = request.url.path

    body = b""
    if request.method in ("POST", "PUT", "PATCH") and not path.startswith(_SKIP_PREFIXES):
        try:
            body = await request.body()
            request._body = body
        except Exception:
            body = b""

    response = await call_next(request)

    if not settings.audit_enabled:
        return response
    if path.startswith(_SKIP_PREFIXES) or path in _SKIP_AUTH_PATHS:
        return response

    user_id: str | None = None
    empresa_id: str | None = None
    rol: str | None = None
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        try:
            payload = decode_access_token(authorization[7:])
            user_id = str(payload.get("sub")) if payload.get("sub") else None
            empresa_id = str(payload.get("empresa_id")) if payload.get("empresa_id") else None
            rol = str(payload.get("rol")) if payload.get("rol") else None
        except Exception:
            user_id = None

    actor_tipo = "sistema"
    if user_id is not None:
        actor_tipo = "superadmin" if empresa_id is None else "usuario"

    accion = {
        "GET": "access",
        "HEAD": "access",
        "OPTIONS": "access",
        "POST": "insert",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }.get(request.method, "access")

    parametros: dict[str, Any] = {
        "query": dict(request.query_params),
        "status": response.status_code,
    }
    parsed_body = _parse_body(body)
    if parsed_body is not None:
        parametros["body"] = parsed_body
    if rol:
        parametros["rol"] = rol

    asyncio.create_task(
        _safe_audit(
            empresa_id=empresa_id,
            usuario_id=user_id,
            actor_tipo=actor_tipo,
            accion=accion,
            entidad="http_request",
            ip=_client_ip(request),
            es_accion_superadmin=actor_tipo == "superadmin",
            metodo=request.method,
            endpoint=path,
            parametros=parametros,
        )
    )
    return response
