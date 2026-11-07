"""Controlador Backend para CU-28: Registrar Venta de Contado Offline (Efectivo y Ticket Preliminar)."""
import json
from asyncpg import Pool
from app.schemas.sync import VentaOfflinePayload

class CU28VentaContadoOfflineController:
    @staticmethod
    async def asentar_venta_offline(pool: Pool, empresa_id: str, usuario_id: str, datos: VentaOfflinePayload):
        async with pool.acquire() as conn:
            op_id = await conn.fetchval(
                """
                INSERT INTO operacion_pendiente (
                    id, empresa_id, sucursal_id, usuario_id, tipo,
                    payload, idempotency_key, estado
                ) VALUES ($1, $2, $3, $4, 'venta_offline', $5, $6, 'pendiente')
                RETURNING id
                """,
                datos.uuid, empresa_id, datos.sucursal_id, usuario_id,
                datos.model_dump_json(), f"VENTA-OFF-{datos.uuid}"
            )
            return {
                "operacion_id": str(op_id),
                "uuid": datos.uuid,
                "estado": "pendiente",
                "leyenda": "VENTA EN MODO OFFLINE - PENDIENTE DE SINCRONIZACIÓN"
            }

