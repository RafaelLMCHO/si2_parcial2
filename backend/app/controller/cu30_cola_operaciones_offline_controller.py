"""Controlador Backend para CU-30: Consultar Cola de Operaciones Pendientes Offline."""
from asyncpg import Pool

class CU30ColaOperacionesOfflineController:
    @staticmethod
    async def consultar_cola(pool: Pool, empresa_id: str, sucursal_id: str = None):
        async with pool.acquire() as conn:
            sql = "SELECT * FROM operacion_pendiente WHERE empresa_id = $1"
            params = [empresa_id]
            if sucursal_id:
                sql += " AND sucursal_id = $2"
                params.append(sucursal_id)
            sql += " ORDER BY creada_en DESC"
            rows = await conn.fetch(sql, *params)
            return [dict(r) for r in rows]

