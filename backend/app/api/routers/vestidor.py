from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_conn, require_permission
from app.schemas.inteligencia import (
    AvatarClienteDto,
    FinalizarSesionArRequest,
    IniciarSesionArRequest,
    IniciarSesionArResponse,
    PrendaArResponse,
)
from app.services import vestidor_ar_service

router = APIRouter(prefix="/vestidor", tags=["Vestidor Virtual y Realidad Aumentada"])


# ---------------------------------------------------------------------------
# CU-36: Vestidor Virtual con Realidad Aumentada (RA)
# ---------------------------------------------------------------------------

@router.get("/prendas", response_model=List[PrendaArResponse])
async def get_prendas_ar(
    user: CurrentUser = Depends(require_permission("catalogo:leer")),
    conn=Depends(get_conn),
):
    """CU-36: Catálogo de prendas preparadas para prueba virtual 3D/RA."""
    return await vestidor_ar_service.listar_prendas_ar(conn, user.empresa_id)


@router.get("/prendas/{prenda_id}", response_model=PrendaArResponse)
async def get_prenda_ar_detalle(
    prenda_id: UUID,
    user: CurrentUser = Depends(require_permission("catalogo:leer")),
    conn=Depends(get_conn),
):
    """CU-36: Configuración de modelo 3D, texturas y puntos de anclaje de una prenda."""
    return await vestidor_ar_service.obtener_prenda_ar_por_id(
        conn, user.empresa_id, prenda_id
    )


@router.get("/avatar", response_model=AvatarClienteDto)
async def get_mi_avatar(
    user: CurrentUser = Depends(require_permission("catalogo:leer")),
    conn=Depends(get_conn),
):
    """CU-36: Avatar del cliente y sus medidas anatómicas corporales."""
    return await vestidor_ar_service.obtener_o_crear_avatar(
        conn, user.empresa_id, user.user_id
    )


@router.post("/sesiones", response_model=IniciarSesionArResponse)
async def iniciar_sesion_vestidor(
    payload: IniciarSesionArRequest,
    user: CurrentUser = Depends(require_permission("catalogo:leer")),
    conn=Depends(get_conn),
):
    """CU-36: Registra el inicio de una sesión interactiva de vestidor virtual."""
    return await vestidor_ar_service.iniciar_sesion_prueba(
        conn, user.empresa_id, user.user_id, payload
    )


@router.put("/sesiones/{sesion_id}")
async def finalizar_sesion_vestidor(
    sesion_id: UUID,
    payload: FinalizarSesionArRequest,
    user: CurrentUser = Depends(require_permission("catalogo:leer")),
    conn=Depends(get_conn),
) -> Dict[str, Any]:
    """CU-36: Actualiza el estado y guarda el resultado de la sesión de prueba."""
    return await vestidor_ar_service.finalizar_sesion_prueba(
        conn, user.empresa_id, sesion_id, payload
    )

