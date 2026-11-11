from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

# CU-25: Catálogo Offline
class CatalogoOfflinePackage(BaseModel):
    empresa_id: str
    sucursal_id: Optional[str] = None
    generado_en: datetime
    sucursales: List[dict] = Field(default_factory=list)
    prendas: List[dict]
    variantes: List[dict]
    existencias: List[dict]
    total_articulos: int

# CU-27: Soft-Lock
class SoftLockCreate(BaseModel):
    sucursal_id: str
    variante_id: str
    cantidad: int = Field(gt=0)
    dispositivo_id: str
    ttl_minutos: int = Field(default=45, ge=1, le=120)

class SoftLockResponse(BaseModel):
    id: str
    sucursal_id: str
    variante_id: str
    cantidad: int
    expira_en: datetime
    activo: bool


class SoftLockListItem(BaseModel):
    id: str
    sucursal_id: str
    sucursal_nombre: Optional[str] = None
    variante_id: str
    sku: Optional[str] = None
    prenda_nombre: Optional[str] = None
    talla: Optional[str] = None
    color: Optional[str] = None
    dispositivo_id: str
    cantidad: int
    expira_en: datetime
    creado_en: datetime
    ttl_restante_segundos: int
    activo: bool


class SoftLockReleaseResponse(BaseModel):
    id: str
    liberado: bool
    mensaje: str

# CU-28: Venta Offline
class LineaVentaOffline(BaseModel):
    variante_id: str
    sku: str
    prenda_nombre: Optional[str] = None
    talla: Optional[str] = None
    color: Optional[str] = None
    cantidad: int = Field(gt=0)
    precio_unitario: float = Field(gt=0)

class VentaOfflinePayload(BaseModel):
    uuid: str  # UUID v4 local
    empresa_id: Optional[str] = None
    sucursal_id: str
    usuario_id: Optional[str] = None
    cliente_nombre: Optional[str] = "Consumidor Final"
    cliente_documento: Optional[str] = "0"
    fecha_hora_local: str
    forma_pago: str = "efectivo"
    lineas: List[LineaVentaOffline]
    total: float
    estado: str = "pendiente"

# CU-29: QR Comprobante y Cambio
class ValidarQrRequest(BaseModel):
    qr_data: str

class NotaCambioCreate(BaseModel):
    sucursal_id: str
    venta_origen_id: Optional[str] = None
    variante_devuelta_id: str
    variante_nueva_id: str
    cantidad: int = Field(default=1, gt=0)
    motivo: str
    qr_firma: Optional[str] = None

# CU-30 & CU-31: Sincronización y Cola de Operaciones
class OperacionSyncItem(BaseModel):
    id: str  # UUID v4
    tipo: str  # 'venta_offline' | 'reserva_offline' | 'cambio_offline'
    sucursal_id: str
    dispositivo_id: Optional[str] = "DEFAULT_DEVICE"
    payload: dict
    creada_en: str
    idempotency_key: str

class ConflictoSyncItem(BaseModel):
    id: str
    tipo: str
    causa: str
    detalle: Optional[str] = None

class SyncBatchRequest(BaseModel):
    dispositivo_id: Optional[str] = "DEFAULT_DEVICE"
    operaciones: List[OperacionSyncItem]

class SyncBatchResponse(BaseModel):
    confirmados: List[str]
    conflictos: List[ConflictoSyncItem]
    procesados_total: int

# CU-32: Resolución de Conflictos
class ResolucionConflictoRequest(BaseModel):
    operacion_id: str
    decision: str  # 'ajustar' | 'aceptar' | 'rechazar' | 'sustituir'
    motivo: Optional[str] = None
    detalle: Optional[dict] = None

