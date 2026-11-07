"""Controlador Backend para CU-05: Auditoría y Logs del Sistema."""
from asyncpg import Pool

class CU05AuditoriaLogsController:
    @staticmethod
    async def listar_logs(pool: Pool, empresa_id: str, limit: int = 50, offset: int = 0):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, empresa_id, usuario_id, accion, modulo, detalle, ip, created_at
                FROM auditoria_log
                WHERE empresa_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                empresa_id, limit, offset
            )
            return [dict(r) for r in rows]

