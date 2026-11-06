from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ItemIngreso(BaseModel):
    variante_id: UUID
    cantidad: int = Field(gt=0)


class IngresoRequest(BaseModel):
    sucursal_id: UUID
    items: List[ItemIngreso] = Field(min_length=1)
    motivo: str = Field(min_length=1, max_length=200)
    referencia: Optional[str] = None


class AjusteRequest(BaseModel):
    sucursal_id: UUID
    variante_id: UUID
    cantidad: int = Field(ne=0)
    motivo: str = Field(min_length=1, max_length=200)
    referencia: Optional[str] = None


class ItemTransferencia(BaseModel):
    variante_id: UUID
    cantidad: int = Field(gt=0)


class TransferenciaRequest(BaseModel):
    origen_id: UUID
    destino_id: UUID
    items: List[ItemTransferencia] = Field(min_length=1)
    motivo: Optional[str] = None


class InventarioParametrosUpdate(BaseModel):
    stock_minimo: Optional[int] = Field(None, ge=0)
    ubicacion: Optional[str] = Field(None, max_length=60)


class InventarioVarianteOut(BaseModel):
    inventario_id: UUID
    sucursal_id: UUID
    sucursal_nombre: str
    stock_fisico: int
    stock_reservado: int
    stock_disponible: int
    stock_minimo: int
    ubicacion: Optional[str]
    bajo_minimo: bool
    actualizado_en: datetime


class InventarioPrendaOut(BaseModel):
    variante_id: UUID
    sku: str
    codigo_barras: Optional[str]
    prenda_id: UUID
    prenda_nombre: str
    talla: str
    color: str
    precio_venta: Decimal
    existencias: List[InventarioVarianteOut]


class InventarioListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[InventarioPrendaOut]


class MovimientoOut(BaseModel):
    id: int
    empresa_id: UUID
    variante_id: UUID
    sucursal_id: UUID
    tipo: str
    cantidad: int
    stock_anterior: int
    stock_nuevo: int
    referencia_tipo: Optional[str]
    referencia_id: Optional[UUID]
    motivo: Optional[str]
    usuario_id: Optional[UUID]
    ocurrido_en: datetime


class MovimientosListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[MovimientoOut]


class StockInsuficienteItem(BaseModel):
    variante_id: UUID
    solicitado: int
    maximo_disponible: int


class TransferenciaOut(BaseModel):
    id: UUID
    empresa_id: UUID
    origen_id: UUID
    destino_id: UUID
    estado: str
    items: List[ItemTransferencia]
    created_at: datetime


class DisponibilidadVarianteOut(BaseModel):
    variante_id: UUID
    sku: str
    talla: str
    color: str
    stock_disponible: int


class DisponibilidadSucursalOut(BaseModel):
    sucursal_id: UUID
    nombre: str
    direccion: str
    ciudad: str
    variantes: List[DisponibilidadVarianteOut]


class DisponibilidadPrendaOut(BaseModel):
    prenda_id: UUID
    agotado_en_todas: bool
    actualizado_en: datetime
    sucursales: List[DisponibilidadSucursalOut]


# Alias para compatibilidad con controladores
AjusteManualCreate = AjusteRequest
