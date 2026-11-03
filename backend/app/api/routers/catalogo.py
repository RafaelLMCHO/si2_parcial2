from decimal import Decimal
from fastapi import APIRouter, Depends, Header, Query, Request
from uuid import UUID

from app.api.deps import CurrentUser, bearer_scheme, get_current_user
from app.api.permissions import require_tenant_admin
from app.core.errors import api_error
from app.db import admin_connection
from app.schemas.catalogo import (
    AuxiliaresCatalogoResponse,
    PrendaCreateRequest,
    PrendaListResponse,
    PrendaOut,
    PrendaUpdateRequest,
    VarianteCreateRequest,
    VarianteOut,
)
from app.services import catalogo_service

router = APIRouter(prefix="/catalogo", tags=["Catalogo de productos (CU-12, CU-13, CU-14)"])


async def resolve_empresa_id(
    request: Request,
    empresa_slug: str | None = Query(None, description="Slug del tenant (para clientes/publico)"),
    x_empresa_slug: str | None = Header(None, alias="X-Empresa-Slug"),
) -> tuple[str, str | None]:
    """Resuelve empresa_id a partir del token JWT si esta presente, o del slug en query/header."""
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        try:
            current: CurrentUser = await get_current_user(request, await bearer_scheme(request))
            if current.empresa_id:
                return current.empresa_id, current.user_id
        except Exception:
            pass

    slug = (empresa_slug or x_empresa_slug or "").strip().lower()
    if not slug:
        raise api_error(400, "EMPRESA_REQUERIDA", "Debe especificar empresa_slug o iniciar sesion")

    async with admin_connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, estado FROM empresa WHERE lower(slug) = lower($1) AND deleted_at IS NULL",
            slug,
        )
        if row is None or row["estado"] != "activa":
            raise api_error(404, "EMPRESA_NO_ENCONTRADA", f"La tienda con identificador '{slug}' no existe o no esta activa")
        return str(row["id"]), None


# --------------------------------------------------------------------------
# CONSULTAS Y FILTRADO (CU-13 y CU-14) - Clientes, Movil, Offline & Web
# --------------------------------------------------------------------------

@router.get("/prendas", response_model=PrendaListResponse)
async def list_prendas(
    request: Request,
    empresa_slug: str | None = Query(None),
    categoria_id: str | None = Query(None),
    temporada_id: str | None = Query(None),
    coleccion_id: str | None = Query(None),
    talla_id: int | None = Query(None),
    color_id: int | None = Query(None),
    precio_min: Decimal | None = Query(None, ge=0),
    precio_max: Decimal | None = Query(None, ge=0),
    genero: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PrendaListResponse:
    """CU-13 y CU-14: Consultar catalogo de prendas con filtros multidimensionales y version para sincronizacion offline."""
    empresa_id, user_id = await resolve_empresa_id(request, empresa_slug)
    return await catalogo_service.list_prendas(
        empresa_id=empresa_id,
        user_id=user_id,
        categoria_id=categoria_id,
        temporada_id=temporada_id,
        coleccion_id=coleccion_id,
        talla_id=talla_id,
        color_id=color_id,
        precio_min=precio_min,
        precio_max=precio_max,
        genero=genero,
        search=search,
        solo_activas=True,
        limit=limit,
        offset=offset,
    )


@router.get("/prendas/{prenda_id}", response_model=PrendaOut)
async def get_prenda(
    prenda_id: str,
    request: Request,
    empresa_slug: str | None = Query(None),
) -> PrendaOut:
    """CU-13: Obtener el detalle de una prenda con sus variantes."""
    empresa_id, user_id = await resolve_empresa_id(request, empresa_slug)
    return await catalogo_service.get_prenda(
        empresa_id=empresa_id,
        prenda_id=prenda_id,
        user_id=user_id,
    )


@router.get("/auxiliares", response_model=AuxiliaresCatalogoResponse)
async def get_auxiliares(
    request: Request,
    empresa_slug: str | None = Query(None),
) -> AuxiliaresCatalogoResponse:
    """CU-14: Obtener listas maestras para poblar filtros (categorias, colores, tallas, temporadas)."""
    empresa_id, user_id = await resolve_empresa_id(request, empresa_slug)
    return await catalogo_service.get_auxiliares_catalogo(empresa_id=empresa_id, user_id=user_id)


# --------------------------------------------------------------------------
# ADMINISTRACION DE CATALOGO (CU-12) - Exclusivo Administrador de Empresa
# --------------------------------------------------------------------------

@router.get("/admin/prendas", response_model=PrendaListResponse)
async def list_prendas_admin(
    search: str | None = Query(None),
    categoria_id: str | None = Query(None),
    solo_activas: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(require_tenant_admin),
) -> PrendaListResponse:
    """CU-12: Listar todas las prendas del tenant (incluyendo inactivas) para administracion."""
    return await catalogo_service.list_prendas(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        categoria_id=categoria_id,
        search=search,
        solo_activas=solo_activas,
        limit=limit,
        offset=offset,
    )


@router.post("/admin/prendas", response_model=PrendaOut, status_code=201)
async def create_prenda(
    data: PrendaCreateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> PrendaOut:
    """CU-12: Crear prenda y sus variantes SKU (valida unicidad de SKU en el tenant)."""
    return await catalogo_service.create_prenda(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        data=data,
    )


@router.put("/admin/prendas/{prenda_id}", response_model=PrendaOut)
async def update_prenda(
    prenda_id: str,
    data: PrendaUpdateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> PrendaOut:
    """CU-12: Actualizar informacion base de una prenda."""
    return await catalogo_service.update_prenda(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        prenda_id=prenda_id,
        data=data,
    )


@router.delete("/admin/prendas/{prenda_id}")
async def delete_prenda(
    prenda_id: str,
    current: CurrentUser = Depends(require_tenant_admin),
) -> dict[str, str]:
    """CU-12: Baja logica de una prenda y sus variantes."""
    return await catalogo_service.delete_prenda(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        prenda_id=prenda_id,
    )


@router.post("/admin/prendas/{prenda_id}/variantes", response_model=VarianteOut, status_code=201)
async def add_variante(
    prenda_id: str,
    data: VarianteCreateRequest,
    current: CurrentUser = Depends(require_tenant_admin),
) -> VarianteOut:
    """CU-12: Anadir variante SKU adicional a una prenda existente."""
    return await catalogo_service.add_variante_to_prenda(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        prenda_id=prenda_id,
        data=data,
    )

