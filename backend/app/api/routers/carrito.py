from typing import Optional
from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_current_user
from app.core.errors import api_error
from app.schemas.carrito import (
    CarritoItemRequest,
    CarritoItemUpdateRequest,
    CarritoOut,
)
from app.services import carrito_service

router = APIRouter(prefix="/carrito", tags=["Carrito de Compras (CU-22)"])


@router.get("", response_model=CarritoOut)
async def get_carrito(
    current: CurrentUser = Depends(get_current_user),
) -> CarritoOut:
    """CU-22: Obtener el carrito de compras del usuario autenticado."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await carrito_service.get_carrito(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
    )
    return CarritoOut(**res)


@router.post("/items", response_model=CarritoOut)
async def add_item_carrito(
    data: CarritoItemRequest,
    current: CurrentUser = Depends(get_current_user),
) -> CarritoOut:
    """CU-22: Agregar prenda al carrito de compras."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await carrito_service.add_item(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        variante_id=str(data.variante_id),
        cantidad=data.cantidad,
    )
    return CarritoOut(**res)


@router.patch("/items/{item_id}", response_model=CarritoOut)
async def update_item_carrito(
    item_id: str,
    data: CarritoItemUpdateRequest,
    current: CurrentUser = Depends(get_current_user),
) -> CarritoOut:
    """CU-22: Modificar cantidad de un ítem en el carrito."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await carrito_service.update_item(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        item_id=item_id,
        cantidad=data.cantidad,
    )
    return CarritoOut(**res)


@router.delete("/items/{item_id}", response_model=CarritoOut)
async def remove_item_carrito(
    item_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> CarritoOut:
    """CU-22: Eliminar un ítem del carrito."""
    if not current.empresa_id:
        raise api_error(400, "TENANT_REQUERIDO", "Debe pertenecer a un tenant")

    res = await carrito_service.remove_item(
        empresa_id=current.empresa_id,
        user_id=current.user_id,
        item_id=item_id,
    )
    return CarritoOut(**res)

