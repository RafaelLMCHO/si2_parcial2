"""Controlador Backend para CU-27: Bloquear Stock Local Offline con TTL (Soft-Lock)."""
from asyncpg import Pool
from app.services.sync_service import SyncService
from app.schemas.sync import SoftLockCreate

class CU27BloquearStockSoftLockController:
    @staticmethod
    async def aplicar_soft_lock(pool: Pool, empresa_id: str, datos: SoftLockCreate):
        service = SyncService(pool)
        return await service.crear_soft_lock(empresa_id=empresa_id, datos=datos)

