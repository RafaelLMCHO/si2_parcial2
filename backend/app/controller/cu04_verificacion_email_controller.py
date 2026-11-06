"""Controlador Backend para CU-04: Verificación de Email y Activación."""
from asyncpg import Pool

class CU04VerificacionEmailController:
    @staticmethod
    async def verificar_token(pool: Pool, token: str):
        async with pool.acquire() as conn:
            usuario_id = await conn.fetchval(
                "SELECT usuario_id FROM token_verificacion WHERE token = $1 AND usado = false AND expiracion > NOW()",
                token
            )
            if not usuario_id:
                return False
            async with conn.transaction():
                await conn.execute("UPDATE usuario SET activo = true WHERE id = $1", usuario_id)
                await conn.execute("UPDATE token_verificacion SET usado = true WHERE token = $1", token)
            return True

