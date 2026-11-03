from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProveedorCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120, description="Razon social del proveedor")
    nit: str = Field(..., min_length=3, max_length=20, description="NIT o identificador tributario unico en la empresa")
    correo: EmailStr | None = Field(default=None, description="Correo de contacto")
    telefono: str | None = Field(default=None, max_length=20, description="Telefono comercial")


class ProveedorUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    nit: str | None = Field(default=None, min_length=3, max_length=20)
    correo: EmailStr | None = Field(default=None)
    telefono: str | None = Field(default=None, max_length=20)


class ProveedorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    nombre: str
    nit: str
    correo: str | None
    telefono: str | None
    created_at: datetime
    updated_at: datetime


class ProveedorListResponse(BaseModel):
    total: int
    items: list[ProveedorOut]

