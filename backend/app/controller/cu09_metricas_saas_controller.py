"""Controlador Backend para CU-09: Métricas Globales SaaS (Superadmin Dashboard)."""
from asyncpg import Pool

class CU09MetricasSaasController:
    @staticmethod
    async def obtener_metricas(pool: Pool):
        async with pool.acquire() as conn:
            tenants = await conn.fetchval("SELECT COUNT(*) FROM empresa")
            usuarios = await conn.fetchval("SELECT COUNT(*) FROM usuario")
            sucursales = await conn.fetchval("SELECT COUNT(*) FROM sucursal")
            mrr = await conn.fetchval("SELECT COALESCE(SUM(p.precio_mensual), 0) FROM suscripcion_saas s JOIN plan_saas p ON p.id = s.plan_id WHERE s.estado = 'activa'")
            return {
                "tenants_activos": tenants,
                "usuarios_totales": usuarios,
                "sucursales": sucursales,
                "mrr": float(mrr)
            }

