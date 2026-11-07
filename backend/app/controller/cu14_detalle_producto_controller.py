"""Controlador Backend para CU-14: Detalle de Producto y Variantes."""
from asyncpg import Pool

class CU14DetalleProductoController:
    @staticmethod
    async def obtener_detalle(pool: Pool, prenda_id: str, empresa_id: str):
        async with pool.acquire() as conn:
            prenda = await conn.fetchrow(
                "SELECT * FROM prenda WHERE id = $1 AND empresa_id = $2",
                prenda_id, empresa_id
            )
            if not prenda:
                return None
            variantes = await conn.fetch(
                "SELECT * FROM variante_prenda WHERE prenda_id = $1 AND empresa_id = $2 AND activo = true",
                prenda_id, empresa_id
            )
            res = dict(prenda)
            res["variantes"] = [dict(v) for v in variantes]
            return res

