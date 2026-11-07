"""Controlador Backend para CU-01: Registro de Inquilino / Empresa."""
from asyncpg import Pool

class CU01RegistroInquilinoController:
    @staticmethod
    async def registrar_inquilino(pool: Pool, nombre_empresa: str, slug: str, admin_email: str, password_hash: str):
        async with pool.acquire() as conn:
            async with conn.transaction():
                empresa_id = await conn.fetchval(
                    "INSERT INTO empresa (nombre, slug) VALUES ($1, $2) RETURNING id",
                    nombre_empresa, slug
                )
                usuario_id = await conn.fetchval(
                    """
                    INSERT INTO usuario (empresa_id, email, password_hash, rol, activo)
                    VALUES ($1, $2, $3, 'admin_empresa', true)
                    RETURNING id
                    """,
                    empresa_id, admin_email, password_hash
                )
                return {"empresa_id": str(empresa_id), "usuario_id": str(usuario_id), "slug": slug}

