"""Controlador Backend para CU-11: Gestión de Sucursales."""
from asyncpg import Pool

class CU11GestionSucursalesController:
    @staticmethod
    async def listar_sucursales(pool: Pool, empresa_id: str):
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM sucursal WHERE empresa_id = $1 ORDER BY nombre ASC", empresa_id)
            return [dict(r) for r in rows]

    @staticmethod
    async def crear_sucursal(pool: Pool, empresa_id: str, nombre: str, direccion: str, telefono: str):
        async with pool.acquire() as conn:
            sid = await conn.fetchval(
                "INSERT INTO sucursal (empresa_id, nombre, direccion, telefono, activo) VALUES ($1, $2, $3, $4, true) RETURNING id",
                empresa_id, nombre, direccion, telefono
            )
            return {"id": str(sid), "nombre": nombre}

