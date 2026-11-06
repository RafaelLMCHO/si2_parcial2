"""Controlador Backend para CU-31: Sincronizar Operaciones Pendientes (Idempotencia RNF05)."""
from asyncpg import Pool
from app.services.sync_service import SyncService
from app.schemas.sync import SyncBatchRequest

class CU31SincronizarOperacionesController:
    @staticmethod
    async def sincronizar_lote(pool: Pool, empresa_id: str, usuario_id: str, lote: SyncBatchRequest):
        service = SyncService(pool)
        return await service.procesar_lote_sync(empresa_id=empresa_id, usuario_id=usuario_id, lote=lote)

