from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser
from app.api.permissions import require_tenant_admin
from app.schemas.coleccion import (
    ColeccionCreateRequest,
    ColeccionOut,
    ColeccionUpdateRequest,
    TemporadaCreateRequest,
    TemporadaOut,
    TemporadaUpdateRequest,
    TemporadasColeccionesResponse,
)
from app.services import coleccion_service

router = APIRouter(prefix="/temporadas-colecciones", tags=["Temporadas y Colecciones (CU-16)"])


@router.get("", response_model=TemporadasColeccionesResponse)
async def get_all(
    current: CurrentUser = Depends(require_tenant_admin),
) -> TemporadasColeccionesResponse:
    """CU-16: Obtener temporadas y colecciones activas del tenant."""
    return await coleccion_service.get_resumen_temporadas_colecciones(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
    )


# --- TEMPORADAS ---

@router.get("/temporadas", response_model=list[TemporadaOut])
async def list_temporadas(
    current: CurrentUser = Depends(require_tenant_admin),
) -> list[TemporadaOut]:
    """CU-16: Listar temporadas de moda."""
    return await coleccion_service.list_temporadas(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
    )


@router.post("/temporadas", response_model=TemporadaOut, status_code=201)
async def create_temporada(
    data: TemporadaCreateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> TemporadaOut:
    """CU-16: Crear nueva temporada validando fecha_inicio < fecha_fin."""
    return await coleccion_service.create_temporada(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        data=data,
    )


@router.put("/temporadas/{temporada_id}", response_model=TemporadaOut)
async def update_temporada(
    temporada_id: str,
    data: TemporadaUpdateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> TemporadaOut:
    """CU-16: Actualizar temporada."""
    return await coleccion_service.update_temporada(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        temporada_id=temporada_id,
        data=data,
    )


@router.delete("/temporadas/{temporada_id}")
async def delete_temporada(
    temporada_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> dict[str, str]:
    """CU-16: Eliminar temporada (si no tiene prendas asociadas)."""
    return await coleccion_service.delete_temporada(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        temporada_id=temporada_id,
    )


# --- COLECCIONES ---

@router.get("/colecciones", response_model=list[ColeccionOut])
async def list_colecciones(
    current: CurrentUser = Depends(require_tenant_admin),
) -> list[ColeccionOut]:
    """CU-16: Listar colecciones comerciales."""
    return await coleccion_service.list_colecciones(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
    )


@router.post("/colecciones", response_model=ColeccionOut, status_code=201)
async def create_coleccion(
    data: ColeccionCreateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> ColeccionOut:
    """CU-16: Crear nueva coleccion anual."""
    return await coleccion_service.create_coleccion(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        data=data,
    )


@router.put("/colecciones/{coleccion_id}", response_model=ColeccionOut)
async def update_coleccion(
    coleccion_id: str,
    data: ColeccionUpdateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> ColeccionOut:
    """CU-16: Actualizar coleccion comercial."""
    return await coleccion_service.update_coleccion(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        coleccion_id=coleccion_id,
        data=data,
    )


@router.delete("/colecciones/{coleccion_id}")
async def delete_coleccion(
    coleccion_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> dict[str, str]:
    """CU-16: Eliminar coleccion (si no tiene prendas asociadas)."""
    return await coleccion_service.delete_coleccion(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        coleccion_id=coleccion_id,
    )

