"""Controlador Backend para CU-06: Gestión de Planes SaaS (Superadmin)."""
from asyncpg import Pool

class CU06GestionPlanesController:
    @staticmethod
    async def listar_planes(pool: Pool):
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM plan_saas ORDER BY precio_mensual ASC")
            return [dict(r) for r in rows]

    @staticmethod
    async def crear_plan(pool: Pool, nombre: str, precio: float, limite_sucursales: int, limite_usuarios: int):
        async with pool.acquire() as conn:
            plan_id = await conn.fetchval(
                """
                INSERT INTO plan_saas (nombre, precio_mensual, limite_sucursales, limite_usuarios)
                VALUES ($1, $2, $3, $4) RETURNING id
                """,
                nombre, precio, limite_sucursales, limite_usuarios
            )
            return {"id": str(plan_id), "nombre": nombre}

