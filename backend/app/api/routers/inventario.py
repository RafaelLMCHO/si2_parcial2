from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error
from app.schemas.inventario import (
    AjusteRequest,
    DisponibilidadPrendaOut,
    IngresoRequest,
    InventarioListResponse,
    InventarioParametrosUpdate,
    MovimientosListResponse,
    TransferenciaRequest,
)
from app.services import inventario_service

router = APIRouter(prefix="/inventario", tags=["Inventario (CU-17, CU-18)"])

ROLES_PERMITIDOS_VER = {"superadmin", "administrador", "encargado", "cajero"}
ROLES_PERMITIDOS_AJUSTAR = {"superadmin", "administrador", "encargado"}
ROLES_PERMITIDOS_TRANSFERIR = {"superadmin", "administrador", "encargado"}


def _resolver_empresa(current: CurrentUser, empresa_param: Optional[str] = None) -> str:
    if current.rol == "superadmin":
        if not empresa_param:
            raise api_error(422, "EMPRESA_REQUERIDA", "El Superadmin debe especificar empresa_id en la consulta")
        return empresa_param
    return current.empresa_id


@router.get("", response_model=InventarioListResponse)
async def list_inventario(
    sucursal_id: Optional[str] = Query(None, description="Filtrar por sucursal"),
    prenda_id: Optional[str] = Query(None, description="Filtrar por prenda"),
    q: Optional[str] = Query(None, description="Buscar por SKU, código de barras o nombre"),
    solo_bajo_minimo: bool = Query(False, description="Solo existencias con stock <= mínimo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> InventarioListResponse:
    """CU-17: Matriz de existencias por sucursal y variante."""
    if current.rol not in ROLES_PERMITIDOS_VER:
        raise api_error(403, "PERMISO_DENEGADO", "No tiene permisos para consultar el inventario")

    empresa = _resolver_empresa(current, empresa_id)

    res = await inventario_service.listar_inventario(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        sucursal_id_filtro=sucursal_id,
        encargado_sucursal_id=None,  # el servicio lo resolverá desde usuario si es encargado
        prenda_id=prenda_id,
        q=q,
        solo_bajo_minimo=solo_bajo_minimo,
        page=page,
        page_size=page_size,
    )
    return InventarioListResponse(**res)


@router.post("/movimientos/ingreso")
async def registrar_ingreso(
    data: IngresoRequest,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-17: Ingreso de prendas por lote (tipo 'entrada')."""
    if current.rol not in ROLES_PERMITIDOS_AJUSTAR:
        raise api_error(403, "PERMISO_DENEGADO", "No tiene permisos para registrar ingresos de stock")

    empresa = _resolver_empresa(current, empresa_id)

    return await inventario_service.registrar_ingreso(
        empresa_id=empresa,
        user_id=current.user_id,
        sucursal_id=str(data.sucursal_id),
        items=[item.model_dump() for item in data.items],
        motivo=data.motivo,
        referencia=data.referencia,
    )


@router.post("/movimientos/ajuste")
async def registrar_ajuste(
    data: AjusteRequest,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-17: Ajuste de stock por merma o corrección (tipo 'ajuste')."""
    if current.rol not in ROLES_PERMITIDOS_AJUSTAR:
        raise api_error(403, "PERMISO_DENEGADO", "No tiene permisos para ajustar inventario")

    empresa = _resolver_empresa(current, empresa_id)

    return await inventario_service.registrar_ajuste(
        empresa_id=empresa,
        user_id=current.user_id,
        sucursal_id=str(data.sucursal_id),
        variante_id=str(data.variante_id),
        cantidad=data.cantidad,
        motivo=data.motivo,
        referencia=data.referencia,
    )


@router.post("/transferencias")
async def crear_transferencia(
    data: TransferenciaRequest,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-17: Transferencia inmediata de stock entre sucursales del mismo tenant."""
    if current.rol not in ROLES_PERMITIDOS_TRANSFERIR:
        raise api_error(403, "PERMISO_DENEGADO", "No tiene permisos para transferir stock")

    empresa = _resolver_empresa(current, empresa_id)

    return await inventario_service.crear_transferencia(
        empresa_id=empresa,
        user_id=current.user_id,
        origen_id=str(data.origen_id),
        destino_id=str(data.destino_id),
        items=[item.model_dump() for item in data.items],
        motivo=data.motivo,
    )


@router.patch("/{inventario_id}/parametros")
async def actualizar_parametros(
    inventario_id: str,
    data: InventarioParametrosUpdate,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-17: Actualizar parámetros de inventario (stock mínimo, ubicación en tienda)."""
    if current.rol not in ROLES_PERMITIDOS_AJUSTAR:
        raise api_error(403, "PERMISO_DENEGADO", "No tiene permisos para modificar parámetros de inventario")

    empresa = _resolver_empresa(current, empresa_id)

    return await inventario_service.actualizar_parametros(
        empresa_id=empresa,
        user_id=current.user_id,
        inventario_id=inventario_id,
        stock_minimo=data.stock_minimo,
        ubicacion=data.ubicacion,
    )


@router.get("/movimientos", response_model=MovimientosListResponse)
async def list_movimientos(
    sucursal_id: Optional[str] = Query(None),
    variante_id: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> MovimientosListResponse:
    """CU-17: Kárdex inmutable de movimientos de inventario."""
    if current.rol not in ROLES_PERMITIDOS_VER:
        raise api_error(403, "PERMISO_DENEGADO", "No tiene permisos para ver movimientos de inventario")

    empresa = _resolver_empresa(current, empresa_id)

    res = await inventario_service.listar_movimientos(
        empresa_id=empresa,
        user_id=current.user_id,
        sucursal_id=sucursal_id,
        variante_id=variante_id,
        tipo=tipo,
        desde=desde,
        hasta=hasta,
        page=page,
        page_size=page_size,
    )
    return MovimientosListResponse(**res)


@router.get("/prendas/{prenda_id}/disponibilidad", response_model=DisponibilidadPrendaOut)
async def get_disponibilidad_prenda(
    prenda_id: str,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> DisponibilidadPrendaOut:
    """CU-18: Consultar disponibilidad de una prenda en sucursales físicas (stock disponible en línea)."""
    empresa = _resolver_empresa(current, empresa_id)

    res = await inventario_service.get_disponibilidad_prenda(
        empresa_id=empresa,
        user_id=current.user_id,
        prenda_id=prenda_id,
    )
    return DisponibilidadPrendaOut(**res)


# Router adicional para la ruta exacta del spec: /api/v1/prendas/{prenda_id}/disponibilidad
prendas_router = APIRouter(prefix="/prendas", tags=["Disponibilidad en Tiendas (CU-18)"])


@prendas_router.get("/{prenda_id}/disponibilidad", response_model=DisponibilidadPrendaOut)
async def get_disponibilidad_directa(
    prenda_id: str,
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> DisponibilidadPrendaOut:
    """CU-18: Consultar disponibilidad directa por prenda."""
    empresa = _resolver_empresa(current, empresa_id)
    res = await inventario_service.get_disponibilidad_prenda(
        empresa_id=empresa,
        user_id=current.user_id,
        prenda_id=prenda_id,
    )
    return DisponibilidadPrendaOut(**res)

