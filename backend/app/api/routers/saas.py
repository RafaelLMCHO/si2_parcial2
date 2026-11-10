import io

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser
from app.api.permissions import require_superadmin
from app.schemas.saas import (
    EmpresaCreateRequest,
    EmpresaCreateResponse,
    EmpresaListResponse,
    EmpresaResumen,
    EstadoEmpresaRequest,
    EstadoEmpresaResponse,
    MetricasSaaSOut,
    MiSuscripcionOut,
    PlanCreateRequest,
    PlanDeleteResponse,
    PlanOut,
    PlanUpdateRequest,
    SuscripcionUpsertRequest,
)
from app.services import saas_service

router = APIRouter(prefix="/saas", tags=["SaaS Superadministrador"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/metricas", response_model=MetricasSaaSOut)
async def get_metricas(
    _: CurrentUser = Depends(require_superadmin),
) -> MetricasSaaSOut:
    return await saas_service.get_metricas()


@router.get("/planes", response_model=list[PlanOut])
async def list_planes(
    incluir_inactivos: bool = Query(default=False),
    _: CurrentUser = Depends(require_superadmin),
) -> list[PlanOut]:
    return await saas_service.list_planes(incluir_inactivos=incluir_inactivos)


@router.post("/planes", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: PlanCreateRequest,
    request: Request,
    current: CurrentUser = Depends(require_superadmin),
) -> PlanOut:
    """CU-06: Crear un nuevo plan SaaS con sus limites por recurso."""
    return await saas_service.create_plan(
        data,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )


@router.put("/planes/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: str,
    data: PlanUpdateRequest,
    request: Request,
    current: CurrentUser = Depends(require_superadmin),
) -> PlanOut:
    """CU-06: Actualizar un plan SaaS existente (por id numerico o codigo)."""
    return await saas_service.update_plan(
        plan_id,
        data,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )


@router.delete("/planes/{plan_id}", response_model=PlanDeleteResponse)
async def delete_plan(
    plan_id: str,
    request: Request,
    current: CurrentUser = Depends(require_superadmin),
) -> PlanDeleteResponse:
    """CU-06: Desactivar un plan SaaS si no tiene suscripciones activas."""
    return await saas_service.delete_plan(
        plan_id,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )


@router.get("/facturas")
async def list_facturas(
    _: CurrentUser = Depends(require_superadmin),
):
    return await saas_service.list_facturas()


@router.get("/facturas/{factura_id}/pdf")
async def get_factura_pdf(
    factura_id: str,
    request: Request,
    current: CurrentUser = Depends(require_superadmin),
) -> StreamingResponse:
    """CU-08: Descargar PDF de una factura SaaS."""
    pdf_bytes, filename = await saas_service.get_factura_pdf(
        factura_id,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/empresas", response_model=EmpresaListResponse)
async def list_empresas(
    search: str | None = Query(default=None, max_length=120),
    estado: str | None = Query(default=None, max_length=20),
    plan: str | None = Query(default=None, max_length=20),
    por_vencer: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: CurrentUser = Depends(require_superadmin),
) -> EmpresaListResponse:
    return await saas_service.list_empresas(
        search=search,
        estado=estado,
        plan=plan,
        por_vencer=por_vencer,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/empresas",
    response_model=EmpresaCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_empresa(
    data: EmpresaCreateRequest,
    request: Request,
    current: CurrentUser = Depends(require_superadmin),
) -> EmpresaCreateResponse:
    return await saas_service.create_empresa(
        data,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )


@router.get("/empresas/{empresa_id}", response_model=EmpresaResumen)
async def get_empresa(
    empresa_id: str,
    _: CurrentUser = Depends(require_superadmin),
) -> EmpresaResumen:
    return await saas_service.get_empresa(empresa_id)


@router.get("/empresas/{empresa_id}/suscripcion", response_model=MiSuscripcionOut)
async def get_empresa_suscripcion(
    empresa_id: str,
    _: CurrentUser = Depends(require_superadmin),
) -> MiSuscripcionOut:
    return await saas_service.get_empresa_suscripcion(empresa_id)


@router.put("/empresas/{empresa_id}/suscripcion", response_model=MiSuscripcionOut)
async def assign_suscripcion(
    empresa_id: str,
    data: SuscripcionUpsertRequest,
    request: Request,
    current: CurrentUser = Depends(require_superadmin),
) -> MiSuscripcionOut:
    return await saas_service.assign_suscripcion(
        empresa_id,
        data,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )


@router.post(
    "/empresas/{empresa_id}/suspender",
    response_model=EstadoEmpresaResponse,
)
async def suspend_empresa(
    empresa_id: str,
    request: Request,
    data: EstadoEmpresaRequest | None = None,
    current: CurrentUser = Depends(require_superadmin),
) -> EstadoEmpresaResponse:
    return await saas_service.suspend_empresa(
        empresa_id,
        data.motivo if data else None,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )


@router.post(
    "/empresas/{empresa_id}/reactivar",
    response_model=EstadoEmpresaResponse,
)
async def reactivate_empresa(
    empresa_id: str,
    request: Request,
    data: EstadoEmpresaRequest | None = None,
    current: CurrentUser = Depends(require_superadmin),
) -> EstadoEmpresaResponse:
    return await saas_service.reactivate_empresa(
        empresa_id,
        data.motivo if data else None,
        actor_id=current.user_id,
        ip=_client_ip(request),
    )
