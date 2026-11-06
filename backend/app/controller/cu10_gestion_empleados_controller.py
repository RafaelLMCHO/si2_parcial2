"""Controlador Backend para CU-10: Gestión de Empleados, Usuarios y Roles."""
from asyncpg import Pool

class CU10GestionEmpleadosController:
    @staticmethod
    async def listar_empleados(pool: Pool, empresa_id: str):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, email, rol, activo, created_at FROM usuario WHERE empresa_id = $1 ORDER BY created_at DESC",
                empresa_id
            )
            return [dict(r) for r in rows]

    @staticmethod
    async def crear_empleado(pool: Pool, empresa_id: str, email: str, password_hash: str, rol: str):
        async with pool.acquire() as conn:
            uid = await conn.fetchval(
                "INSERT INTO usuario (empresa_id, email, password_hash, rol, activo) VALUES ($1, $2, $3, $4, true) RETURNING id",
                empresa_id, email, password_hash, rol
            )
            return {"id": str(uid), "email": email, "rol": rol}

