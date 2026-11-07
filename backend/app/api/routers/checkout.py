from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error
from app.schemas.venta import (
    CheckoutValidarOut,
    CheckoutValidarRequest,
    CrearOrdenRequest,
    OrdenCreadaOut,
)
from app.services import checkout_service, comprobante_service

router = APIRouter(prefix="/checkout", tags=["Checkout y Compras Online (CU-22)"])


@router.post("/validar", response_model=CheckoutValidarOut)
async def validar_checkout(
    data: CheckoutValidarRequest,
    current: CurrentUser = Depends(get_current_user),
) -> CheckoutValidarOut:
    """CU-22: Valida disponibilidad de inventario, calcula totales y aplica cupón."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await checkout_service.validar_checkout(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        tipo_entrega=data.tipo_entrega,
        direccion_id=str(data.direccion_id) if data.direccion_id else None,
        sucursal_id=str(data.sucursal_id) if data.sucursal_id else None,
        cupon_codigo=data.cupon,
    )
    return CheckoutValidarOut(**res)


@router.post("/ordenes", response_model=OrdenCreadaOut, status_code=status.HTTP_201_CREATED)
async def crear_orden(
    request: Request,
    data: CrearOrdenRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current: CurrentUser = Depends(get_current_user),
) -> OrdenCreadaOut:
    """CU-22: Crea la orden de compra pendiente de cobro en pasarela (idempotente)."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await checkout_service.crear_orden(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        idempotency_key=idempotency_key,
        tipo_entrega=data.tipo_entrega,
        direccion_id=str(data.direccion_id) if data.direccion_id else None,
        sucursal_id=str(data.sucursal_id) if data.sucursal_id else None,
        cupon_codigo=data.cupon,
        ip=request.client.host if request.client else None,
    )
    return OrdenCreadaOut(**res)


@router.post("/ordenes/{venta_id}/reintentar-pago")
async def reintentar_pago(
    venta_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """CU-22: Permite reintentar el pago si la pasarela lo rechazó anteriormente."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    return await checkout_service.reintentar_pago(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        venta_id=venta_id,
    )


@router.get("/ventas/{venta_id}/comprobante")
async def get_comprobante(
    venta_id: str,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
):
    """CU-22: Descarga o visualiza el comprobante digital en PDF / JSON."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    datos = await checkout_service.get_comprobante_data(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        venta_id=venta_id,
    )

    accept_header = request.headers.get("accept", "")
    if "application/pdf" in accept_header or request.query_params.get("format") == "pdf":
        pdf_bytes = comprobante_service.generar_comprobante_pdf(datos)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=comprobante_{datos.get('numero')}.pdf"},
        )

    return datos

