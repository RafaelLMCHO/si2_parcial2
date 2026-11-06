"""Controlador Backend para CU-08: Facturación SaaS e Historial de Facturas."""
from asyncpg import Pool

class CU08FacturacionSaasController:
    @staticmethod
    async def listar_facturas(pool: Pool, empresa_id: str):
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, empresa_id, monto, moneda, estado, stripe_invoice_id, pdf_url, created_at
                FROM factura_saas
                WHERE empresa_id = $1
                ORDER BY created_at DESC
                """,
                empresa_id
            )
            return [dict(r) for r in rows]

