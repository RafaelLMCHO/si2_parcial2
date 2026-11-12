from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class DireccionClienteOut(BaseModel):
    id: UUID
    etiqueta: Optional[str] = None
    destinatario: str
    telefono: str
    linea1: str
    linea2: Optional[str] = None
    ciudad: str
    departamento: Optional[str] = None
    referencia: Optional[str] = None
    es_principal: bool = False


class DireccionesClienteResponse(BaseModel):
    items: List[DireccionClienteOut]


class CheckoutValidarRequest(BaseModel):
    tipo_entrega: str = Field(pattern=r'^(envio|recojo)$')
    direccion_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    cupon: Optional[str] = None


class LineaFaltante(BaseModel):
    variante_id: UUID
    disponible: int
    solicitado: int


class CheckoutValidarOut(BaseModel):
    subtotal: float
    descuento: float
    impuesto: float
    costo_envio: float
    total_a_pagar: float
    sucursal_despacho_id: Optional[UUID]
    sucursal_despacho_nombre: Optional[str]
    cupon_id: Optional[UUID]
    lineas_faltantes: List[LineaFaltante] = []


class CrearOrdenRequest(BaseModel):
    tipo_entrega: str = Field(pattern=r'^(envio|recojo)$')
    direccion_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    cupon: Optional[str] = None


class OrdenCreadaOut(BaseModel):
    venta_id: UUID
    numero: str
    total_a_pagar: float
    estado: str


class VentaDetalleOut(BaseModel):
    id: UUID
    variante_id: UUID
    sku: str
    prenda_nombre: str
    talla: str
    color: str
    cantidad: int
    precio_lista: float
    precio_unitario: float
    descuento_linea: float
    subtotal: float


class VentaOut(BaseModel):
    id: UUID
    empresa_id: UUID
    numero: str
    canal: str
    estado: str
    subtotal: float
    descuento: float
    impuesto: float
    total: float
    cliente_nombre: Optional[str]
    cliente_documento: Optional[str]
    fecha_hora: datetime
    items: List[VentaDetalleOut]
    created_at: datetime


class PosItemRequest(BaseModel):
    variante_id: UUID
    cantidad: int = Field(gt=0)
    descuento_linea: Decimal = Field(default=Decimal("0"), ge=0)


class PosClienteRequest(BaseModel):
    tipo: str = Field(pattern=r'^(consumidor_final|identificado)$')
    nombre: Optional[str] = None
    documento: Optional[str] = None


class PosPagoRequest(BaseModel):
    metodo: str = Field(pattern=r'^(efectivo|tarjeta|qr)$')
    monto_recibido: Optional[Decimal] = None
    referencia: Optional[str] = None


class PosVentaRequest(BaseModel):
    idempotency_key: str
    items: List[PosItemRequest] = Field(min_length=1)
    cliente: PosClienteRequest
    pago: PosPagoRequest


class PosVentaOut(BaseModel):
    venta_id: UUID
    numero: str
    total: float
    cambio: Optional[float]
    metodo_pago: str
    estado: str
    comprobante_url: str
    intencion_pago: Optional[dict[str, Any]] = None


# Aliases para compatibilidad con controladores
OrdenCheckoutCreate = CrearOrdenRequest
VentaPosCreate = PosVentaRequest
