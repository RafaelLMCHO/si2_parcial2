from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ItemReserva(BaseModel):
    variante_id: UUID
    cantidad: int = Field(gt=0)


class ValidarReservaRequest(BaseModel):
    sucursal_id: UUID
    fecha_visita: datetime
    items: List[ItemReserva] = Field(min_length=1)


class CrearReservaRequest(BaseModel):
    sucursal_id: UUID
    fecha_visita: datetime
    items: List[ItemReserva] = Field(min_length=1)


class StockInsuficienteReserva(BaseModel):
    variante_id: UUID
    solicitado: int
    disponible: int


class ReservaItemOut(BaseModel):
    variante_id: UUID
    sku: str
    prenda_nombre: str
    talla: str
    color: str
    cantidad: int
    ubicacion: Optional[str]


class ReservaEstadoHistorialOut(BaseModel):
    estado_anterior: Optional[str]
    estado_nuevo: str
    motivo: Optional[str]
    usuario_id: Optional[UUID]
    ocurrido_en: datetime


class ReservaOut(BaseModel):
    id: UUID
    empresa_id: UUID
    usuario_id: UUID
    sucursal_id: UUID
    sucursal_nombre: Optional[str] = None
    codigo: str
    estado: str
    fecha_visita: datetime
    expira_en: datetime
    probador: Optional[str] = None
    items: List[ReservaItemOut]
    historial: Optional[List[ReservaEstadoHistorialOut]] = None
    created_at: datetime


class ReservaListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ReservaOut]


class CancelarReservaRequest(BaseModel):
    motivo: Optional[str] = None


class PrepararReservaRequest(BaseModel):
    probador: Optional[str] = None


class IncidenciaReservaRequest(BaseModel):
    variante_ids: List[UUID]
    motivo: str = Field(min_length=1, max_length=200)
    registrar_merma: bool = False


class AlternativaOut(BaseModel):
    variante_id: UUID
    sku: str
    prenda_nombre: str
    talla: str
    color: str
    sucursal_id: UUID
    sucursal_nombre: str
    stock_disponible: int


class IncidenciaReservaOut(BaseModel):
    reserva_id: UUID
    estado: str
    alternativas: List[AlternativaOut]


# Alias para compatibilidad con controladores
ReservaCreate = CrearReservaRequest
