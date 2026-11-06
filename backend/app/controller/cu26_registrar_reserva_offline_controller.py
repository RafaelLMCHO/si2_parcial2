"""Controlador Backend para CU-26: Registrar Reserva Offline (Generación UUID Local)."""
import json
from asyncpg import Pool

class CU26RegistrarReservaOfflineController:
    @staticmethod
    async def registrar_reserva_offline(pool: Pool, empresa_id: str, sucursal_id: str, usuario_id: str, reserva_uuid: str, payload: dict):
        async with pool.acquire() as conn:
            op_id = await conn.fetchval(
                """
                INSERT INTO operacion_pendiente (
                    id, empresa_id, sucursal_id, usuario_id, tipo,
                    payload, idempotency_key, estado
                ) VALUES ($1, $2, $3, $4, 'reserva_offline', $5, $6, 'pendiente')
                RETURNING id
                """,
                reserva_uuid, empresa_id, sucursal_id, usuario_id,
                json.dumps(payload), f"RES-OFF-{reserva_uuid}"
            )
            return {"operacion_id": str(op_id), "uuid": reserva_uuid, "estado": "pendiente"}

