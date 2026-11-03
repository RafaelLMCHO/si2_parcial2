from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmpleadoCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    correo: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=128, description="Contrasena inicial del empleado")
    rol: str = Field(..., min_length=2, max_length=50, description="Rol del empleado (cajero, encargado, administrador)")
    sucursal_id: UUID | None = Field(default=None, description="Sucursal fisica asignada")
    telefono: str | None = Field(default=None, max_length=20)


class EmpleadoUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    rol: str | None = Field(default=None, min_length=2, max_length=50)
    sucursal_id: UUID | None = Field(default=None)
    telefono: str | None = Field(default=None, max_length=20)
    estado: str | None = Field(default=None, pattern="^(activo|inactivo|bloqueado)$")


class EmpleadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    nombre: str
    correo: str
    rol_nombre: str
    sucursal_id: UUID | None = None
    sucursal_nombre: str | None = None
    telefono: str | None = None
    estado: str
    ultimo_acceso: datetime | None = None
    created_at: datetime


class EmpleadoListResponse(BaseModel):
    total: int
    items: list[EmpleadoOut]


class RolDisponibleOut(BaseModel):
    id: UUID
    nombre: str
    descripcion: str | None = None

