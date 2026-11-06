from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PagoIntencionRequest(BaseModel):
    venta_id: UUID


class PagoIntencionOut(BaseModel):
    pago_id: UUID
    client_secret: str
    publishable_key: str
    monto: int  # centavos
    moneda: str


class PagoOut(BaseModel):
    id: UUID
    venta_id: UUID
    monto: float
    metodo: str
    estado: str
    pasarela_id: Optional[str]
    referencia: Optional[str]
    created_at: datetime


class EstadoPagoOut(BaseModel):
    venta_id: UUID
    venta_estado: str
    pago_id: Optional[UUID]
    pago_estado: Optional[str]
    pasarela_id: Optional[str]
    mensaje_error: Optional[str]


# Aliases para compatibilidad con controladores
IntencionPagoCreate = PagoIntencionRequest

class ReembolsoCreate(BaseModel):
    monto: Optional[float] = None
    motivo: Optional[str] = None
