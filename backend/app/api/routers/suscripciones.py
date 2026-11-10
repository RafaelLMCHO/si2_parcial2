from fastapi import APIRouter, Body, Depends, Request

from app.api.deps import CurrentUser
from app.api.permissions import require_tenant_admin
from app.schemas.saas import (
    MiSuscripcionCancelRequest,
    MiSuscripcionCancelResponse,
    MiSuscripcionChangeRequest,
    MiSuscripcionOut,
)
from app.services import saas_service

router = APIRouter(prefix="/mi-suscripcion", tags=["Suscripcion de la empresa"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=MiSuscripcionOut)
async def get_mi_suscripcion(
    current: CurrentUser = Depends(require_tenant_admin),
) -> MiSuscripcionOut:
    return await saas_service.get_mi_suscripcion(
        current.empresa_id,
        current.user_id,
    )


@router.put("", response_model=MiSuscripcionOut)
async def update_mi_suscripcion(
    data: MiSuscripcionChangeRequest,
    request: Request,
    current: CurrentUser = Depends(require_tenant_admin),
) -> MiSuscripcionOut:
    """CU-07: Cambiar el plan de suscripcion de la empresa actual validando limites (BR-02/BR-03)."""
    return await saas_service.change_mi_suscripcion(
        current.empresa_id,
        current.user_id,
        data,
        ip=_client_ip(request),
    )


@router.post("/cancelar", response_model=MiSuscripcionCancelResponse)
async def cancelar_mi_suscripcion(
    request: Request,
    data: MiSuscripcionCancelRequest | None = Body(default=None),
    current: CurrentUser = Depends(require_tenant_admin),
) -> MiSuscripcionCancelResponse:
    """CU-07: Cancelar la suscripcion activa de la empresa actual con registro en bitacora."""
    payload = data or MiSuscripcionCancelRequest()
    return await saas_service.cancel_mi_suscripcion(
        current.empresa_id,
        current.user_id,
        payload,
        ip=_client_ip(request),
    )
