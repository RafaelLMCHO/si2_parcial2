from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    empresa_slug: str | None = Field(default=None, max_length=120)
    correo: str = Field(
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class RegisterRequest(BaseModel):
    empresa_slug: str = Field(min_length=1, max_length=120)
    nombre: str = Field(min_length=2, max_length=120)
    correo: str = Field(
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    telefono: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    empresa_slug: str = Field(min_length=1, max_length=120)
    token: str = Field(min_length=20)


class UserOut(BaseModel):
    id: UUID
    empresa_id: UUID | None
    nombre: str
    correo: str
    telefono: str | None = None
    email_verificado: bool
    estado: str
    rol: str
    sucursal_id: UUID | None = None
    ultimo_acceso: datetime | None = None
    created_at: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UserOut


class RegisterResponse(BaseModel):
    mensaje: str
    usuario_id: UUID
    empresa_id: UUID
    email_verificado: bool = False
    verification_token: str | None = None


class VerifyEmailResponse(BaseModel):
    mensaje: str
    usuario_id: UUID
    empresa_id: UUID


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

