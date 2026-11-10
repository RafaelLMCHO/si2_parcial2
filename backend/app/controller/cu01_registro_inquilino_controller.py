"""Controlador Backend para CU-01: Registro publico de Inquilino / Empresa."""
from __future__ import annotations

import re
import secrets
import unicodedata
from datetime import date, datetime, timedelta, timezone
from typing import Any

from asyncpg import Pool

from app.core.errors import api_error
from app.core.security import hash_token, new_verification_token

_ROLE_DEFINITIONS = (
    ("administrador", "Acceso total al tenant", None),
    (
        "encargado",
        "Encargado de sucursal",
        (
            "ventas.crear",
            "ventas.ver",
            "inventario.ver",
            "inventario.ajustar",
            "stock.ajustar",
            "stock.transferir",
            "reservas.ver",
            "reservas.preparar",
            "reservas.cancelar",
            "catalogo.ver",
        ),
    ),
    (
        "cajero",
        "Operacion de ventas",
        ("ventas.crear", "ventas.ver", "inventario.ver", "catalogo.ver", "pagos.procesar"),
    ),
    (
        "cliente",
        "Cliente de la tienda en linea",
        (
            "catalogo.ver",
            "ventas.ver",
            "reservas.crear",
            "reservas.ver",
            "reservas.cancelar",
            "carrito.gestionar",
            "pagos.procesar",
        ),
    ),
)


def _slug_base(raw: str) -> str:
    normalized = unicodedata.normalize("NFKD", raw)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name.lower()).strip("-")
    return (slug or "empresa")[:80]


async def _unique_slug(conn: Any, raw: str) -> str:
    base = _slug_base(raw)
    candidate = base
    suffix = 2
    while await conn.fetchval("SELECT 1 FROM empresa WHERE slug = $1", candidate):
        candidate = f"{base[:72]}-{suffix}"
        suffix += 1
    return candidate


async def _unique_nit(conn: Any, raw_nit: str | None) -> str:
    if raw_nit and raw_nit.strip():
        nit = raw_nit.strip().upper()[:20]
        if await conn.fetchval("SELECT 1 FROM empresa WHERE nit = $1", nit):
            raise api_error(409, "NIT_DUPLICADO", "Ya existe una empresa registrada con ese NIT")
        return nit

    for _ in range(8):
        candidate = f"TEN-{secrets.token_hex(5).upper()}"
        if not await conn.fetchval("SELECT 1 FROM empresa WHERE nit = $1", candidate):
            return candidate
    raise api_error(500, "NIT_AUTOGENERADO_FALLO", "No se pudo generar un NIT unico")


class CU01RegistroInquilinoController:
    @staticmethod
    async def registrar_inquilino(
        pool: Pool,
        nombre_empresa: str,
        slug: str | None,
        admin_email: str,
        password_hash: str,
        *,
        nombre_admin: str = "Administrador",
        nit: str | None = None,
        telefono: str | None = None,
        direccion: str | None = None,
        plan_codigo: str = "basico",
        verification_token_minutes: int = 1440,
    ) -> dict[str, Any]:
        correo_norm = str(admin_email).strip().lower()

        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SET LOCAL ROLE fashion_superadmin")
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
                    f"email:{correo_norm}",
                )
                if await conn.fetchval(
                    "SELECT 1 FROM usuario WHERE correo = $1 AND deleted_at IS NULL",
                    correo_norm,
                ):
                    raise api_error(
                        409,
                        "CORREO_ADMIN_DUPLICADO",
                        "Ya existe un usuario registrado con ese correo",
                    )

                final_nit = await _unique_nit(conn, nit)
                final_slug = await _unique_slug(conn, slug or nombre_empresa)

                plan = await conn.fetchrow(
                    "SELECT id, codigo FROM plan WHERE lower(codigo) = $1 AND activo",
                    plan_codigo.strip().lower(),
                )
                if plan is None:
                    plan = await conn.fetchrow(
                        "SELECT id, codigo FROM plan WHERE activo ORDER BY precio_mensual ASC, id ASC LIMIT 1"
                    )

                empresa_estado = "activa" if plan is not None else "pendiente_plan"
                empresa_id = await conn.fetchval(
                    """
                    INSERT INTO empresa (nombre, slug, nit, correo, telefono, direccion, estado)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    nombre_empresa.strip(),
                    final_slug,
                    final_nit,
                    correo_norm,
                    telefono,
                    direccion,
                    empresa_estado,
                )

                role_ids: dict[str, Any] = {}
                for role_name, description, permissions in _ROLE_DEFINITIONS:
                    role_id = await conn.fetchval(
                        """
                        INSERT INTO rol (empresa_id, nombre, descripcion, es_global)
                        VALUES ($1, $2, $3, false)
                        ON CONFLICT (empresa_id, nombre)
                        DO UPDATE SET descripcion = EXCLUDED.descripcion
                        RETURNING id
                        """,
                        empresa_id,
                        role_name,
                        description,
                    )
                    role_ids[role_name] = role_id
                    if permissions is None:
                        await conn.execute(
                            """
                            INSERT INTO rol_permiso (rol_id, permiso_id)
                            SELECT $1, id FROM permiso
                            ON CONFLICT DO NOTHING
                            """,
                            role_id,
                        )
                    else:
                        await conn.execute(
                            """
                            INSERT INTO rol_permiso (rol_id, permiso_id)
                            SELECT $1, id FROM permiso WHERE codigo = ANY($2::text[])
                            ON CONFLICT DO NOTHING
                            """,
                            role_id,
                            list(permissions),
                        )

                hoy = date.today()
                plan_codigo_final = plan_codigo.strip().lower()
                if plan is not None:
                    plan_codigo_final = plan["codigo"]
                    await conn.execute(
                        """
                        INSERT INTO suscripcion (
                            empresa_id, plan_id, estado, fecha_inicio, fecha_fin, renovacion_auto
                        )
                        VALUES ($1, $2, 'prueba', $3, $4, false)
                        """,
                        empresa_id,
                        plan["id"],
                        hoy,
                        hoy + timedelta(days=14),
                    )

                usuario_id = await conn.fetchval(
                    """
                    INSERT INTO usuario (
                        empresa_id, rol_id, nombre, correo, password_hash,
                        telefono, email_verificado, estado
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, false, 'inactivo')
                    RETURNING id
                    """,
                    empresa_id,
                    role_ids["administrador"],
                    nombre_admin.strip(),
                    correo_norm,
                    password_hash,
                    telefono,
                )

                verification_token = new_verification_token()
                await conn.execute(
                    """
                    INSERT INTO verificacion_correo (empresa_id, usuario_id, token_hash, expira_en)
                    VALUES ($1, $2, $3, $4)
                    """,
                    empresa_id,
                    usuario_id,
                    hash_token(verification_token),
                    datetime.now(timezone.utc) + timedelta(minutes=verification_token_minutes),
                )

                return {
                    "empresa_id": str(empresa_id),
                    "usuario_id": str(usuario_id),
                    "slug": str(final_slug),
                    "nit": final_nit,
                    "plan_codigo": plan_codigo_final,
                    "verification_token": verification_token,
                }
