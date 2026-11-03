from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser
from app.api.permissions import require_tenant_admin
from app.schemas.saas import MiSuscripcionOut
from app.services import saas_service

router = APIRouter(prefix="/mi-suscripcion", tags=["Suscripcion de la empresa"])


@router.get("", response_model=MiSuscripcionOut)
async def get_mi_suscripcion(
    current: CurrentUser = Depends(require_tenant_admin),
) -> MiSuscripcionOut:
    return await saas_service.get_mi_suscripcion(
        current.empresa_id,
        current.user_id,
    )
