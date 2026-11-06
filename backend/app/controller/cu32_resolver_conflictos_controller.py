"""Controlador Backend para CU-32: Resolver Conflictos de Sincronización (FIFO y Manual)."""
from typing import Optional
from asyncpg import Pool
from app.services.sync_service import SyncService
from app.schemas.sync import ResolucionConflictoRequest

class CU32ResolverConflictosController:
    @staticmethod
    async def listar_conflictos(pool: Pool, empresa_id: str, sucursal_id: Optional[str] = None):
        service = SyncService(pool)
        return await service.listar_conflictos(empresa_id=empresa_id, sucursal_id=sucursal_id)

    @staticmethod
    async def resolver_conflicto(pool: Pool, empresa_id: str, usuario_id: str, datos: ResolucionConflictoRequest):
        service = SyncService(pool)
        return await service.resolver_conflicto(empresa_id=empresa_id, usuario_id=usuario_id, datos=datos)

