from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser
from app.api.permissions import require_tenant_admin
from app.schemas.proveedor import (
    ProveedorCreateRequest,
    ProveedorListResponse,
    ProveedorOut,
    ProveedorUpdateRequest,
)
from app.services import proveedor_service

router = APIRouter(prefix="/proveedores", tags=["Proveedores textiles (CU-15)"])


@router.get("", response_model=ProveedorListResponse)
async def list_proveedores(
    search: str | None = Query(None, description="Buscar por nombre o NIT"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(require_tenant_admin),
) -> ProveedorListResponse:
    """CU-15: Listar proveedores textiles del tenant."""
    return await proveedor_service.list_proveedores(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{proveedor_id}", response_model=ProveedorOut)
async def get_proveedor(
    proveedor_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> ProveedorOut:
    """CU-15: Obtener un proveedor por ID."""
    return await proveedor_service.get_proveedor(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        proveedor_id=proveedor_id,
    )


@router.post("", response_model=ProveedorOut, status_code=201)
async def create_proveedor(
    data: ProveedorCreateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> ProveedorOut:
    """CU-15: Dar de alta un proveedor textil (validando NIT unico por tenant)."""
    return await proveedor_service.create_proveedor(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        data=data,
    )


@router.put("/{proveedor_id}", response_model=ProveedorOut)
async def update_proveedor(
    proveedor_id: str,
    data: ProveedorUpdateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> ProveedorOut:
    """CU-15: Modificar datos de un proveedor textil."""
    return await proveedor_service.update_proveedor(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        proveedor_id=proveedor_id,
        data=data,
    )


@router.delete("/{proveedor_id}")
async def delete_proveedor(
    proveedor_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> dict[str, str]:
    """CU-15: Dar de baja logica un proveedor textil."""
    return await proveedor_service.delete_proveedor(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        proveedor_id=proveedor_id,
    )

