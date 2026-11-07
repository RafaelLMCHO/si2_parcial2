"""Controlador Backend para CU-03: Perfil de Usuario y Cambio de Contraseña."""
from asyncpg import Pool

class CU03PerfilUsuarioController:
    @staticmethod
    async def obtener_perfil(pool: Pool, usuario_id: str, empresa_id: str):
        async with pool.acquire() as conn:
            usuario = await conn.fetchrow(
                "SELECT id, email, rol, activo, created_at FROM usuario WHERE id = $1 AND empresa_id = $2",
                usuario_id, empresa_id
            )
            return dict(usuario) if usuario else None

    @staticmethod
    async def actualizar_password(pool: Pool, usuario_id: str, nuevo_hash: str):
        async with pool.acquire() as conn:
            await conn.execute("UPDATE usuario SET password_hash = $1 WHERE id = $2", nuevo_hash, usuario_id)
            return True

