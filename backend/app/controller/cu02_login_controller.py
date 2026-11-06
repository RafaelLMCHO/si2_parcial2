"""Controlador Backend para CU-02: Inicio de Sesión Multi-inquilino."""
from asyncpg import Pool

class CU02LoginController:
    @staticmethod
    async def autenticar(pool: Pool, email: str, empresa_slug: str):
        async with pool.acquire() as conn:
            usuario = await conn.fetchrow(
                """
                SELECT u.id, u.empresa_id, u.email, u.password_hash, u.rol, u.activo, e.slug as empresa_slug
                FROM usuario u
                JOIN empresa e ON e.id = u.empresa_id
                WHERE u.email = $1 AND e.slug = $2 AND u.activo = true
                """,
                email, empresa_slug
            )
            return dict(usuario) if usuario else None

