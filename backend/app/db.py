from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

import asyncpg

from app.core.config import get_settings

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("El pool de base de datos no esta inicializado")
    return _pool


async def _set_tenant_context(
    conn: asyncpg.Connection,
    empresa_id: UUID | str,
    usuario_id: UUID | str | None = None,
) -> None:
    await conn.execute("SET LOCAL ROLE fashion_app")
    await conn.execute(
        "SELECT set_config('app.empresa_id', $1, true)",
        str(empresa_id),
    )
    if usuario_id is not None:
        await conn.execute(
            "SELECT set_config('app.usuario_id', $1, true)",
            str(usuario_id),
        )


@asynccontextmanager
async def tenant_connection(
    empresa_id: UUID | str,
    usuario_id: UUID | str | None = None,
) -> AsyncIterator[asyncpg.Connection]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _set_tenant_context(conn, empresa_id, usuario_id)
            yield conn


@asynccontextmanager
async def admin_connection() -> AsyncIterator[asyncpg.Connection]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL ROLE fashion_superadmin")
            yield conn


async def audit_event(
    *,
    empresa_id: UUID | str | None,
    usuario_id: UUID | str | None,
    actor_tipo: str,
    accion: str,
    entidad: str,
    entidad_id: UUID | str | None = None,
    empresa_afectada_id: UUID | str | None = None,
    datos_antes: dict | None = None,
    datos_despues: dict | None = None,
    ip: str | None = None,
    es_accion_superadmin: bool = False,
    metodo: str | None = None,
    endpoint: str | None = None,
    parametros: dict | None = None,
) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            SELECT fn_registrar_auditoria(
                $1, $2, $3, $4, $5, $6, $7,
                $8::jsonb, $9::jsonb, $10::inet, $11, $12, $13, $14::jsonb
            )
            """,
            str(empresa_id) if empresa_id else None,
            str(empresa_afectada_id) if empresa_afectada_id else None,
            str(usuario_id) if usuario_id else None,
            actor_tipo,
            accion,
            entidad,
            str(entidad_id) if entidad_id else None,
            _json(datos_antes),
            _json(datos_despues),
            ip,
            es_accion_superadmin,
            metodo,
            endpoint,
            _json(parametros),
        )


def _json(value: dict | None) -> str | None:
    import json

    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, default=str)
