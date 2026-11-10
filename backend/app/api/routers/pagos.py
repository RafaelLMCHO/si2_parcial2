import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Header, Query, Request, status

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error
from app.schemas.pago import (
    EstadoPagoOut,
    PagoIntencionOut,
    PagoIntencionRequest,
    PagoListResponse,
    PagoOut,
    ReembolsoCreate,
    ReembolsoOut,
)
from app.services import pago_service

router = APIRouter(prefix="/pagos", tags=["Pagos y Pasarela Stripe (CU-24)"])


def _resolver_empresa(current: CurrentUser, empresa_param: Optional[str] = None) -> str:
    if current.rol == "superadmin":
        if not empresa_param:
            raise api_error(422, "EMPRESA_REQUERIDA", "Superadmin debe especificar empresa_id")
        return empresa_param
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")
    return current.empresa_id


@router.get("", response_model=PagoListResponse)
async def listar_pagos(
    estado: Optional[str] = Query(None),
    venta_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> PagoListResponse:
    """CU-24: Listar pagos del tenant (clientes solo ven sus propias compras)."""
    empresa = _resolver_empresa(current, empresa_id)
    res = await pago_service.listar_pagos(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        estado=estado,
        venta_id=venta_id,
        page=page,
        page_size=page_size,
    )
    return PagoListResponse(**res)


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
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> PagoOut:
    """CU-24: Consultar detalles de un pago registrado."""
    empresa = _resolver_empresa(current, empresa_id)

    res = await pago_service.get_pago(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        pago_id=pago_id,
    )
    return PagoOut(**res)


@router.post("/{pago_id}/conciliar", response_model=EstadoPagoOut)
async def conciliar_pago(
    request: Request,
    pago_id: str,
    payment_method: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> EstadoPagoOut:
    """CU-24: Confirmar/conciliar estado de un PaymentIntent directamente con Stripe."""
    empresa = _resolver_empresa(current, empresa_id)
    res = await pago_service.conciliar_pago(
        empresa_id=empresa,
        user_id=current.user_id,
        rol=current.rol,
        pago_id=pago_id,
        confirmar_payment_method=payment_method,
        ip=request.client.host if request.client else None,
    )
    return EstadoPagoOut(**res)


@router.post("/{pago_id}/reembolsar", response_model=ReembolsoOut)
async def reembolsar_pago(
    request: Request,
    pago_id: str,
    data: ReembolsoCreate = Body(default_factory=ReembolsoCreate),
    empresa_id: Optional[str] = Query(None, description="Para Superadmin"),
    current: CurrentUser = Depends(get_current_user),
) -> ReembolsoOut:
    """CU-24: Emitir un reembolso total o parcial de un pago completado."""
    empresa = _resolver_empresa(current, empresa_id)
    res = await pago_service.reembolsar_pago(
        empresa_id=empresa,
        pago_id=pago_id,
        user_id=current.user_id,
        rol=current.rol,
        monto=data.monto,
        motivo=data.motivo,
        ip=request.client.host if request.client else None,
    )
    return ReembolsoOut(**res)


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

