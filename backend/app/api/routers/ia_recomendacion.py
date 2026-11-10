from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import CurrentUser, bearer_scheme, get_current_user
from app.core.errors import api_error
from app.db import admin_connection
from app.schemas.recomendacion_ia import (
    OutfitParaPrendaRequest,
    OutfitRecomendadoResponse,
    PromptEstiloRequest,
)
from app.services import ia_recomendacion_service

router = APIRouter(
    prefix="/ia/recomendaciones",
    tags=["CU-38: Recomendaciones IA de Catálogo (Personal Stylist)"],
)


async def _resolve_empresa(request: Request, slug_param: Optional[str] = None) -> UUID:
    """Resuelve empresa_id vía JWT o slug."""
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        try:
            current: CurrentUser = await get_current_user(request, await bearer_scheme(request))
            if current.empresa_id:
                return UUID(str(current.empresa_id))
        except Exception:
            pass

    slug = (slug_param or request.headers.get("x-empresa-slug") or "demo").strip().lower()
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM empresa WHERE lower(slug) = lower($1) AND deleted_at IS NULL LIMIT 1",
            slug,
        )
        if not row:
            # Fallback a primera empresa activa
            first_row = await conn.fetchrow(
                "SELECT id FROM empresa WHERE deleted_at IS NULL ORDER BY created_at ASC LIMIT 1"
            )
            if not first_row:
                raise api_error(404, "EMPRESA_NO_ENCONTRADA", "No hay empresas registradas")
            return first_row["id"]
        return row["id"]


@router.post("/estilo-prompt", response_model=OutfitRecomendadoResponse)
async def recomendar_por_estilo(
    request: Request,
    payload: PromptEstiloRequest,
) -> OutfitRecomendadoResponse:
    """CU-38: Recomienda un outfit armónico y estilizado a partir de una descripción en lenguaje natural."""
    empresa_id = await _resolve_empresa(request, payload.empresa_slug)
    return await ia_recomendacion_service.recomendar_por_prompt(
        empresa_id=empresa_id,
        prompt=payload.prompt,
        genero=payload.genero,
    )


@router.post("/outfit-prenda", response_model=OutfitRecomendadoResponse)
async def recomendar_para_prenda(
    request: Request,
    payload: OutfitParaPrendaRequest,
) -> OutfitRecomendadoResponse:
    """CU-38: Completa el look alrededor de una prenda específica seleccionada del catálogo."""
    empresa_id = await _resolve_empresa(request, payload.empresa_slug)
    return await ia_recomendacion_service.recomendar_outfit_para_prenda(
        empresa_id=empresa_id,
        prenda_id=payload.prenda_id,
        ocasion=payload.ocasion,
    )


@router.get("/tendencias", response_model=OutfitRecomendadoResponse)
async def tendencias_temporada(
    request: Request,
    empresa_slug: Optional[str] = Query(None),
    genero: Optional[str] = Query(None),
) -> OutfitRecomendadoResponse:
    """CU-38: Obtiene el outfit editorial recomendado para la temporada actual."""
    empresa_id = await _resolve_empresa(request, empresa_slug)
    return await ia_recomendacion_service.recomendar_por_prompt(
        empresa_id=empresa_id,
        prompt="Tendencia actual de alta costura, look sofisticado y moderno",
        genero=genero,
    )
