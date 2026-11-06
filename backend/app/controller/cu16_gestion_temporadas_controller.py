"""Controlador Backend para CU-16: Gestión de Temporadas y Colecciones."""
from asyncpg import Pool

class CU16GestionTemporadasController:
    @staticmethod
    async def listar_temporadas(pool: Pool, empresa_id: str):
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM temporada WHERE empresa_id = $1 ORDER BY fecha_inicio DESC", empresa_id)
            return [dict(r) for r in rows]

