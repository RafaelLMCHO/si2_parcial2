from __future__ import annotations
from datetime import datetime
from typing import List, Optional
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
    pasarela_id: Optional[str] = None
    referencia: Optional[str] = None
    created_at: datetime


class PagoListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PagoOut]


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
    monto: Optional[float] = Field(default=None, gt=0)
    motivo: Optional[str] = Field(default=None, max_length=200)


class ReembolsoOut(BaseModel):
    ok: bool = True
    pago_id: UUID
    venta_id: UUID
    estado: str
    venta_estado: str
    monto_reembolsado: float
    refund_id: Optional[str] = None
    motivo: Optional[str] = None
