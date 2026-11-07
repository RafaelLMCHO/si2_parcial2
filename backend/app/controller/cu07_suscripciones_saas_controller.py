"""Controlador Backend para CU-07: Suscripciones SaaS y Pagos Stripe."""
from asyncpg import Pool

class CU07SuscripcionesSaasController:
    @staticmethod
    async def obtener_suscripcion(pool: Pool, empresa_id: str):
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT s.*, p.nombre as plan_nombre, p.precio_mensual
                FROM suscripcion_saas s
                JOIN plan_saas p ON p.id = s.plan_id
                WHERE s.empresa_id = $1
                ORDER BY s.created_at DESC LIMIT 1
                """,
                empresa_id
            )
            return dict(row) if row else None

