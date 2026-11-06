"""Controlador Backend para CU-13: Catálogo Cliente (Exploración y Búsqueda)."""
from asyncpg import Pool

class CU13CatalogoClienteController:
    @staticmethod
    async def explorar_catalogo(pool: Pool, empresa_id: str, query: str = None, categoria_id: str = None):
        async with pool.acquire() as conn:
            sql = "SELECT id, codigo, nombre, descripcion, precio_base, categoria_id, imagen_url FROM prenda WHERE empresa_id = $1 AND activo = true"
            params = [empresa_id]
            if query:
                sql += " AND (nombre ILIKE $2 OR descripcion ILIKE $2)"
                params.append(f"%{query}%")
            rows = await conn.fetch(sql, *params)
            return [dict(r) for r in rows]

