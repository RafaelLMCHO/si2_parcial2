from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser
from app.api.permissions import require_tenant_admin
from app.schemas.sucursal import (
    SucursalCreateRequest,
    SucursalOut,
    SucursalesListResponse,
    SucursalUpdateRequest,
)
from app.services import sucursal_service

router = APIRouter(prefix="/sucursales", tags=["Sucursales (CU-11)"])


@router.get("", response_model=SucursalesListResponse)
async def list_sucursales(
    current: CurrentUser = Depends(require_tenant_admin),
) -> SucursalesListResponse:
    """CU-11: Listar sucursales de la empresa e indicar limite del plan."""
    return await sucursal_service.list_sucursales(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
    )


@router.get("/{sucursal_id}", response_model=SucursalOut)
async def get_sucursal(
    sucursal_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> SucursalOut:
    """CU-11: Obtener detalles de una sucursal."""
    return await sucursal_service.get_sucursal(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        sucursal_id=sucursal_id,
    )


@router.post("", response_model=SucursalOut, status_code=201)
async def create_sucursal(
    data: SucursalCreateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> SucursalOut:
    """CU-11: Dar de alta una sucursal comprobando el limite por plan (BR-02 -> HTTP 402 si se supera)."""
    return await sucursal_service.create_sucursal(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        data=data,
    )


@router.put("/{sucursal_id}", response_model=SucursalOut)
async def update_sucursal(
    sucursal_id: str,
    data: SucursalUpdateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> SucursalOut:
    """CU-11: Modificar datos o reactivar sucursal."""
    return await sucursal_service.update_sucursal(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        sucursal_id=sucursal_id,
        data=data,
    )


@router.delete("/{sucursal_id}")
async def delete_sucursal(
    sucursal_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> dict[str, str]:
    """CU-11: Dar de baja logica una sucursal."""
    return await sucursal_service.delete_sucursal(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        sucursal_id=sucursal_id,
    )

