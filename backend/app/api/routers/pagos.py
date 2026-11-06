import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, status

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error
from app.schemas.pago import (
    EstadoPagoOut,
    PagoIntencionOut,
    PagoIntencionRequest,
    PagoOut,
)
from app.services import pago_service

router = APIRouter(prefix="/pagos", tags=["Pagos y Pasarela Stripe (CU-24)"])


@router.post("/intencion", response_model=PagoIntencionOut)
async def crear_intencion(
    request: Request,
    data: PagoIntencionRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current: CurrentUser = Depends(get_current_user),
) -> PagoIntencionOut:
    """CU-24: Crea una intención de pago en Stripe Sandbox para cobrar la orden."""
    if not current.empresa_id and current.rol != "superadmin":
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    key = idempotency_key or str(uuid.uuid4())
    empresa = current.empresa_id

    res = await pago_service.crear_intencion_pago(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        venta_id=str(data.venta_id),
        idempotency_key=key,
        ip=request.client.host if request.client else None,
    )
    return PagoIntencionOut(**res)


@router.post("/webhook/stripe", status_code=status.HTTP_200_OK)
async def webhook_stripe(request: Request) -> dict:
    """
    CU-24: Webhook público para Stripe.
    Valida firma criptográfica, aplica idempotencia y concilia la venta.
    """
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    return await pago_service.procesar_webhook_stripe(
        payload_bytes=payload,
        signature=signature,
    )


@router.get("/{pago_id}", response_model=PagoOut)
async def get_pago(
    pago_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> PagoOut:
    """CU-24: Consultar detalles de un pago registrado."""
    if not current.empresa_id and current.rol != "superadmin":
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await pago_service.get_pago(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        rol=current.rol,
        pago_id=pago_id,
    )
    return PagoOut(**res)


@router.get("/ventas/{venta_id}/estado-pago", response_model=EstadoPagoOut)
async def get_estado_pago(
    venta_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> EstadoPagoOut:
    """CU-24: Polling del frontend mientras se confirma el cobro vía webhook."""
    if not current.empresa_id and current.rol != "superadmin":
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await pago_service.get_estado_pago(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        rol=current.rol,
        venta_id=venta_id,
    )
    return EstadoPagoOut(**res)

