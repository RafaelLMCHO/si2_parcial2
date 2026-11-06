"""Controlador Backend para CU-15: Gestión de Proveedores."""
from asyncpg import Pool

class CU15GestionProveedoresController:
    @staticmethod
    async def listar_proveedores(pool: Pool, empresa_id: str):
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM proveedor WHERE empresa_id = $1 ORDER BY nombre ASC", empresa_id)
            return [dict(r) for r in rows]

    @staticmethod
    async def crear_proveedor(pool: Pool, empresa_id: str, nombre: str, contacto: str, telefono: str, email: str):
        async with pool.acquire() as conn:
            prov_id = await conn.fetchval(
                """
                INSERT INTO proveedor (empresa_id, nombre, contacto_nombre, telefono, email, activo)
                VALUES ($1, $2, $3, $4, $5, true) RETURNING id
                """,
                empresa_id, nombre, contacto, telefono, email
            )
            return {"id": str(prov_id), "nombre": nombre}

