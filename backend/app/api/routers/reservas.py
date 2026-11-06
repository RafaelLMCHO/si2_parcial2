from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request, status

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error
from app.schemas.reserva import (
    CancelarReservaRequest,
    CrearReservaRequest,
    IncidenciaReservaOut,
    IncidenciaReservaRequest,
    PrepararReservaRequest,
    ReservaListResponse,
    ReservaOut,
    ValidarReservaRequest,
)
from app.services import reserva_service

router = APIRouter(prefix="/reservas", tags=["Reservas (CU-19, CU-20, CU-21)"])


def _resolver_empresa(current: CurrentUser, empresa_param: Optional[str] = None) -> str:
    if current.rol == "superadmin":
        if not empresa_param:
            raise api_error(422, "EMPRESA_REQUERIDA", "Superadmin debe especificar empresa_id")
        return empresa_param
    return current.empresa_id


@router.post("/validar")
async def validar_reserva(
    data: ValidarReservaRequest,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-19: Valida disponibilidad de prendas en sucursal sin efectos secundarios."""
    empresa = _resolver_empresa(current, empresa_id)

    return await reserva_service.validar_reserva(
        empresa_id=empresa,
        user_id=current.user_id,
        sucursal_id=str(data.sucursal_id),
        fecha_visita=data.fecha_visita,
        items=[it.model_dump() for it in data.items],
    )


@router.post("", response_model=ReservaOut, status_code=status.HTTP_201_CREATED)
async def crear_reserva(
    request: Request,
    data: CrearReservaRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    cliente_id: Optional[str] = Query(None, description="Para Superadmin reservando por un cliente"),
    current: CurrentUser = Depends(get_current_user),
) -> ReservaOut:
    """CU-19: Realiza reserva de múltiples prendas en sucursal apartando stock temporalmente."""
    empresa = _resolver_empresa(current, empresa_id)
    usuario_objetivo = cliente_id if (current.rol == "superadmin" and cliente_id) else current.user_id

    res = await reserva_service.crear_reserva(
        empresa_id=empresa,
        user_id=usuario_objetivo,
        sucursal_id=str(data.sucursal_id),
        fecha_visita=data.fecha_visita,
        items=[it.model_dump() for it in data.items],
        cliente_uuid=idempotency_key,
        ip=request.client.host if request.client else None,
    )
    return ReservaOut(**res)


@router.get("", response_model=ReservaListResponse)
async def listar_reservas(
    estado: Optional[str] = Query(None),
    sucursal_id: Optional[str] = Query(None),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> ReservaListResponse:
    """CU-20: Consultar reservas. Cliente ve solo las suyas; Encargado ve su sucursal; Admin ve todas."""
    empresa = _resolver_empresa(current, empresa_id)

    res = await reserva_service.listar_reservas(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        sucursal_id_usuario=None,
        estado=estado,
        sucursal_id_filtro=sucursal_id,
        desde=desde,
        hasta=hasta,
        page=page,
        page_size=page_size,
    )
    return ReservaListResponse(**res)


@router.get("/por-preparar", response_model=ReservaListResponse)
async def listar_por_preparar(
    sucursal_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> ReservaListResponse:
    """CU-21: Bandeja de reservas pendientes de preparación física en tienda."""
    if current.rol not in {"encargado", "administrador", "superadmin"}:
        raise api_error(403, "PERMISO_DENEGADO", "Solo el personal de sucursal puede ver reservas por preparar")

    empresa = _resolver_empresa(current, empresa_id)

    res = await reserva_service.listar_por_preparar(
        empresa_id=empresa,
        user_id=current.user_id,
        sucursal_id_encargado=sucursal_id,
        page=page,
        page_size=page_size,
    )
    return ReservaListResponse(**res)


@router.get("/{reserva_id}", response_model=ReservaOut)
async def get_reserva(
    reserva_id: str,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> ReservaOut:
    """CU-20: Ver detalle de una reserva con su historial de estados."""
    empresa = _resolver_empresa(current, empresa_id)

    res = await reserva_service.get_reserva(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        reserva_id=reserva_id,
    )
    return ReservaOut(**res)


@router.post("/{reserva_id}/cancelar", response_model=ReservaOut)
async def cancelar_reserva(
    request: Request,
    reserva_id: str,
    data: CancelarReservaRequest,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> ReservaOut:
    """CU-20: Cancelar reserva pendiente y restituir stock reservado."""
    empresa = _resolver_empresa(current, empresa_id)

    res = await reserva_service.cancelar_reserva(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        reserva_id=reserva_id,
        motivo=data.motivo,
        ip=request.client.host if request.client else None,
    )
    return ReservaOut(**res)


@router.post("/{reserva_id}/preparar", response_model=ReservaOut)
async def preparar_reserva(
    request: Request,
    reserva_id: str,
    data: PrepararReservaRequest,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> ReservaOut:
    """CU-21: Marcar reserva como preparada en el probador asignado."""
    if current.rol not in {"encargado", "administrador", "superadmin"}:
        raise api_error(403, "PERMISO_DENEGADO", "Solo el encargado de sucursal puede preparar reservas")

    empresa = _resolver_empresa(current, empresa_id)

    res = await reserva_service.preparar_reserva(
        empresa_id=empresa,
        user_id=current.user_id,
        reserva_id=reserva_id,
        probador=data.probador,
        ip=request.client.host if request.client else None,
    )
    return ReservaOut(**res)


@router.post("/{reserva_id}/incidencia", response_model=IncidenciaReservaOut)
async def reportar_incidencia(
    request: Request,
    reserva_id: str,
    data: IncidenciaReservaRequest,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> IncidenciaReservaOut:
    """CU-21: Reportar prenda dañada o extraviada en reserva, ofreciendo alternativas."""
    if current.rol not in {"encargado", "administrador", "superadmin"}:
        raise api_error(403, "PERMISO_DENEGADO", "Solo el encargado puede reportar incidencias de reserva")

    empresa = _resolver_empresa(current, empresa_id)

    res = await reserva_service.reportar_incidencia(
        empresa_id=empresa,
        user_id=current.user_id,
        reserva_id=reserva_id,
        variante_ids=[str(vid) for vid in data.variante_ids],
        motivo=data.motivo,
        registrar_merma=data.registrar_merma,
        ip=request.client.host if request.client else None,
    )
    return IncidenciaReservaOut(**res)

