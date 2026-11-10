from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from asyncpg import Pool

from app.db import get_pool
from app.api.deps import CurrentUser, get_current_user
from app.schemas.sync import (
    CatalogoOfflinePackage,
    SoftLockCreate,
    SoftLockResponse,
    SoftLockListItem,
    SoftLockReleaseResponse,
    ValidarQrRequest,
    NotaCambioCreate,
    SyncBatchRequest,
    SyncBatchResponse,
    ResolucionConflictoRequest
)
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["Sincronización y Operaciones Offline"])

# CU-25: Descargar catálogo offline
@router.get("/catalogo-offline", response_model=CatalogoOfflinePackage)
async def descargar_catalogo_offline(
    sucursal_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    return await service.descargar_catalogo_offline(empresa_id=empresa_id, sucursal_id=sucursal_id)

# CU-27: Soft-Lock local con TTL
@router.get("/soft-locks", response_model=List[SoftLockListItem])
async def listar_soft_locks(
    sucursal_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    return await service.listar_soft_locks(empresa_id=empresa_id, sucursal_id=sucursal_id)


@router.post("/soft-locks", response_model=SoftLockResponse)
async def crear_soft_lock(
    datos: SoftLockCreate,
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    return await service.crear_soft_lock(empresa_id=empresa_id, datos=datos)


@router.delete("/soft-locks/{lock_id}", response_model=SoftLockReleaseResponse)
async def liberar_soft_lock(
    lock_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    return await service.liberar_soft_lock(empresa_id=empresa_id, lock_id=lock_id)

# CU-29: Validar comprobante y procesar cambio mediante QR
@router.post("/validar-qr")
async def validar_qr_comprobante(
    datos: ValidarQrRequest,
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    return await service.validar_qr_comprobante(empresa_id=empresa_id, qr_data=datos.qr_data)

@router.post("/nota-cambio")
async def procesar_nota_cambio(
    datos: NotaCambioCreate,
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    usuario_id = str(current_user.user_id)
    return await service.procesar_nota_cambio(empresa_id=empresa_id, usuario_id=usuario_id, datos=datos)

# CU-31: Sincronizar operaciones pendientes (Idempotencia RNF05)
@router.post("", response_model=SyncBatchResponse)
async def procesar_lote_sync(
    lote: SyncBatchRequest,
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    usuario_id = str(current_user.user_id)
    return await service.procesar_lote_sync(empresa_id=empresa_id, usuario_id=usuario_id, lote=lote)

# CU-32: Listar y resolver conflictos de sincronización
@router.get("/conflictos", response_model=List[dict])
async def listar_conflictos(
    sucursal_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    return await service.listar_conflictos(empresa_id=empresa_id, sucursal_id=sucursal_id)

@router.post("/conflictos/resolver")
async def resolver_conflicto(
    datos: ResolucionConflictoRequest,
    current_user: CurrentUser = Depends(get_current_user),
    pool: Pool = Depends(get_pool),
):
    service = SyncService(pool)
    empresa_id = str(current_user.empresa_id)
    usuario_id = str(current_user.user_id)
    return await service.resolver_conflicto(empresa_id=empresa_id, usuario_id=usuario_id, datos=datos)

