from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser
from app.api.permissions import require_tenant_admin
from app.schemas.empleado import (
    EmpleadoCreateRequest,
    EmpleadoListResponse,
    EmpleadoOut,
    EmpleadoUpdateRequest,
    RolDisponibleOut,
)
from app.services import empleado_service

router = APIRouter(prefix="/empleados", tags=["Usuarios y Empleados por empresa (CU-10)"])


@router.get("", response_model=EmpleadoListResponse)
async def list_empleados(
    search: str | None = Query(None, description="Buscar por nombre o correo"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(require_tenant_admin),
) -> EmpleadoListResponse:
    """CU-10: Listar empleados pertenecientes al tenant del Administrador."""
    return await empleado_service.list_empleados(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/roles", response_model=list[RolDisponibleOut])
async def list_roles(
    current: CurrentUser = Depends(require_tenant_admin),
) -> list[RolDisponibleOut]:
    """CU-10: Listar roles asignables a nivel de tenant (excluyendo superadmin segun BR-12)."""
    return await empleado_service.list_roles_disponibles(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
    )


@router.get("/{empleado_id}", response_model=EmpleadoOut)
async def get_empleado(
    empleado_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> EmpleadoOut:
    """CU-10: Obtener detalles de un empleado."""
    return await empleado_service.get_empleado(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        empleado_id=empleado_id,
    )


@router.post("", response_model=EmpleadoOut, status_code=201)
async def create_empleado(
    data: EmpleadoCreateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> EmpleadoOut:
    """CU-10: Dar de alta un nuevo empleado en la empresa asignado a rol y sucursal (valida BR-12 -> 403 si intenta superadmin)."""
    return await empleado_service.create_empleado(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        data=data,
    )


@router.put("/{empleado_id}", response_model=EmpleadoOut)
async def update_empleado(
    empleado_id: str,
    data: EmpleadoUpdateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> EmpleadoOut:
    """CU-10: Modificar datos, rol, sucursal o estado del empleado."""
    return await empleado_service.update_empleado(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        empleado_id=empleado_id,
        data=data,
    )


@router.delete("/{empleado_id}")
async def delete_empleado(
    empleado_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> dict[str, str]:
    """CU-10: Dar de baja logica a un empleado y revocar sus sesiones activas."""
    return await empleado_service.delete_empleado(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        empleado_id=empleado_id,
    )

