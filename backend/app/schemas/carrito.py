from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CarritoItemRequest(BaseModel):
    variante_id: UUID
    cantidad: int = Field(gt=0)


class CarritoItemUpdateRequest(BaseModel):
    cantidad: int = Field(gt=0)


class CarritoItemOut(BaseModel):
    id: UUID
    variante_id: UUID
    sku: str
    prenda_nombre: str
    talla: str
    color: str
    imagen_url: Optional[str]
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class CarritoOut(BaseModel):
    id: UUID
    empresa_id: UUID
    usuario_id: Optional[UUID]
    estado: str
    items: List[CarritoItemOut]
    total: Decimal
    created_at: datetime
    updated_at: datetime


# Alias para compatibilidad con controladores
CarritoItemCreate = CarritoItemRequest
