"""Controlador Backend para CU-25: Descargar Catálogo Offline."""
from typing import Optional
from asyncpg import Pool
from app.services.sync_service import SyncService

class CU25DescargarCatalogoOfflineController:
    @staticmethod
    async def descargar_catalogo(pool: Pool, empresa_id: str, sucursal_id: Optional[str] = None):
        service = SyncService(pool)
        return await service.descargar_catalogo_offline(empresa_id=empresa_id, sucursal_id=sucursal_id)

