from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SucursalCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120, description="Denominacion o nombre de la sucursal")
    ciudad_id: int = Field(..., ge=1, description="ID de la ciudad correspondiente")
    direccion: str = Field(..., min_length=3, max_length=200, description="Direccion fisica")
    telefono: str | None = Field(default=None, max_length=20)
    es_matriz: bool = Field(default=False, description="Indica si es la sucursal central")


class SucursalUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    ciudad_id: int | None = Field(default=None, ge=1)
    direccion: str | None = Field(default=None, min_length=3, max_length=200)
    telefono: str | None = Field(default=None, max_length=20)
    es_matriz: bool | None = Field(default=None)
    estado: str | None = Field(default=None, pattern="^(activa|inactiva)$")


class SucursalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    ciudad_id: int
    ciudad_nombre: str | None = None
    nombre: str
    direccion: str
    telefono: str | None
    es_matriz: bool
    estado: str
    created_at: datetime
    updated_at: datetime


class SucursalesListResponse(BaseModel):
    total: int
    activas: int
    limite_plan: int
    items: list[SucursalOut]

