from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, Field


class BackupModuloInfo(BaseModel):
    id: str
    nombre: str
    descripcion: str
    tablas: list[str]


class BackupManualCreate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    alcance: str = Field(default="empresa", pattern="^(global|empresa)$")
    empresa_id: str | None = None
    formato: str = Field(default="json", pattern="^(json|sql)$")
    destino: str = Field(default="ambos", pattern="^(local|nube|ambos)$")
    modulos: list[str] | None = None
    tablas: list[str] | None = None
    incluir_auditoria: bool = False


class BackupConfiguracionUpdate(BaseModel):
    activo: bool = False
    frecuencia: str = Field(
        default="diario",
        pattern="^(cada_hora|cada_2_horas|cada_4_horas|cada_6_horas|cada_12_horas|diario|semanal|mensual|fecha_especifica)$",
    )
    fecha_inicio: date | None = None
    fecha_especifica: date | None = None
    hora_ejecucion: str = "02:00"
    dia_semana: int = Field(default=0, ge=0, le=6)
    dia_mes: int = Field(default=1, ge=1, le=31)
    destino: str = Field(default="ambos", pattern="^(local|nube|ambos)$")
    formato: str = Field(default="json", pattern="^(json|sql)$")
    tablas: list[str] = ["catalogo", "inventario", "ventas", "reservas", "clientes"]
    retencion_dias: int = Field(default=30, ge=1, le=365)


class BackupConfiguracionOut(BaseModel):
    id: str
    empresa_id: str | None = None
    activo: bool
    frecuencia: str
    fecha_inicio: date | None = None
    fecha_especifica: date | None = None
    hora_ejecucion: str
    dia_semana: int
    dia_mes: int = 1
    destino: str
    formato: str
    tablas: list[str]
    retencion_dias: int
    ultima_ejecucion: datetime | None = None
    proxima_ejecucion: datetime | None = None
    estado_ultima_ejecucion: str | None = None
    error_ultima_ejecucion: str | None = None
    updated_at: datetime | None = None


class BackupRegistroOut(BaseModel):
    id: str
    empresa_id: str | None = None
    empresa_nombre: str | None = None
    usuario_id: str | None = None
    usuario_nombre: str | None = None
    nombre: str
    descripcion: str | None = None
    tipo: str
    alcance: str
    formato: str
    tablas_seleccionadas: list[str]
    tamano_bytes: int
    tamano_legible: str
    total_registros: int
    checksum_sha256: str | None = None
    guardado_local: bool
    ruta_local: str | None = None
    guardado_nube: bool
    url_nube: str | None = None
    proveedor_nube: str
    estado: str
    error_mensaje: str | None = None
    detalles_tablas: dict[str, int] = {}
    metadata: dict[str, Any] = {}
    created_at: datetime


class BackupListResponse(BaseModel):
    items: list[BackupRegistroOut]
    total: int
    page: int
    page_size: int


class BackupEstadisticasOut(BaseModel):
    total_backups: int
    total_locales: int
    total_nube: int
    total_automaticos: int
    total_manuales: int
    espacio_local_bytes: int
    espacio_local_legible: str
    espacio_nube_bytes: int
    espacio_nube_legible: str
    proveedor_nube: str
    ultimo_backup: datetime | None = None
    auto_backup_activo: bool
    proximo_auto_backup: datetime | None = None


class BackupRestaurarRequest(BaseModel):
    tablas: list[str] | None = None  # None = todas las tablas en el backup
    modo: str = Field(default="safe", pattern="^(safe|replace)$")  # safe: ON CONFLICT DO NOTHING, replace: upsert

