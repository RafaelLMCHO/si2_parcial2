"""Controlador Backend para CU-12: Catálogo Admin (Prendas y Variantes)."""
from asyncpg import Pool

class CU12CatalogoAdminController:
    @staticmethod
    async def listar_prendas(pool: Pool, empresa_id: str):
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM prenda WHERE empresa_id = $1 ORDER BY nombre ASC", empresa_id)
            return [dict(r) for r in rows]

    @staticmethod
    async def crear_prenda(pool: Pool, empresa_id: str, codigo: str, nombre: str, precio_base: float, categoria_id: str):
        async with pool.acquire() as conn:
            pid = await conn.fetchval(
                """
                INSERT INTO prenda (empresa_id, codigo, nombre, precio_base, categoria_id, activo)
                VALUES ($1, $2, $3, $4, $5, true) RETURNING id
                """,
                empresa_id, codigo, nombre, precio_base, categoria_id
            )
            return {"id": str(pid), "codigo": codigo, "nombre": nombre}

