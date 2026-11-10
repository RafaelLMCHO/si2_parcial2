from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: int
    empresa_id: UUID | None = None
    empresa_afectada_id: UUID | None = None
    usuario_id: UUID | None = None
    usuario_nombre: str | None = None
    usuario_correo: str | None = None
    actor_tipo: str
    accion: str
    entidad: str
    modulo: str
    entidad_id: UUID | None = None
    datos_antes: dict[str, Any] | None = None
    datos_despues: dict[str, Any] | None = None
    ip: str | None = None
    ip_origen: str | None = None
    ocurrido_en: datetime
    fecha_hora: datetime
    created_at: datetime
    es_accion_superadmin: bool = False
    metodo: str | None = None
    endpoint: str | None = None
    parametros: dict[str, Any] | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int

