from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error
from app.schemas.venta import PosVentaOut, PosVentaRequest
from app.services import pos_service

router = APIRouter(prefix="/pos", tags=["Punto de Venta POS Online (CU-23)"])

ROLES_PERMITIDOS_POS = {"cajero", "administrador", "superadmin", "encargado"}


def _check_cajero(current: CurrentUser):
    if current.rol not in ROLES_PERMITIDOS_POS:
        raise api_error(403, "PERMISO_DENEGADO", "Solo cajeros o personal de caja pueden operar el POS")


@router.get("/variantes/barcode/{codigo}")
async def buscar_por_barcode(
    codigo: str,
    sucursal_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-23: Busca una variante por código de barras o SKU con existencias en la sucursal de caja."""
    _check_cajero(current)
    empresa = current.empresa_id

    return await pos_service.buscar_por_barcode(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        codigo=codigo,
        sucursal_id_param=sucursal_id,
    )


@router.get("/variantes/buscar")
async def buscar_variantes(
    q: Optional[str] = Query(None, description="Texto de búsqueda (nombre, SKU)"),
    sucursal_id: Optional[str] = Query(None, description="Para Superadmin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-23: Búsqueda rápida de catálogo para mostrador con stock disponible en sucursal."""
    _check_cajero(current)
    empresa = current.empresa_id

    return await pos_service.buscar_variantes(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        q=q,
        sucursal_id_param=sucursal_id,
        page=page,
        page_size=page_size,
    )


@router.post("/ventas", response_model=PosVentaOut)
async def crear_venta_pos(
    request: Request,
    data: PosVentaRequest,
    x_device_serial: Optional[str] = Header(None, alias="X-Device-Serial"),
    sucursal_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> PosVentaOut:
    """CU-23: Registrar venta presencial en mostrador (Efectivo, Tarjeta, QR)."""
    _check_cajero(current)
    empresa = current.empresa_id

    res = await pos_service.crear_venta_pos(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        idempotency_key=data.idempotency_key,
        items=[it.model_dump() for it in data.items],
        cliente=data.cliente.model_dump(),
        pago=data.pago.model_dump(),
        sucursal_solicitada=sucursal_id,
        device_serial=x_device_serial,
        ip=request.client.host if request.client else None,
    )
    return PosVentaOut(**res)


@router.get("/ventas/{venta_id}/ticket")
async def get_ticket(
    venta_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-23: Obtiene los datos del ticket térmico para impresión en mostrador."""
    _check_cajero(current)
    empresa = current.empresa_id

    return await pos_service.get_ticket_data(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        venta_id=venta_id,
    )

