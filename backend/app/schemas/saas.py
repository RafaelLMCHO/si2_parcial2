from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

SuscripcionEstado = Literal["prueba", "activa", "mora", "suspendida", "cancelada"]


class EmpresaCreateRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    nit: str = Field(min_length=3, max_length=20)
    telefono: str | None = Field(default=None, max_length=20)
    direccion: str = Field(min_length=5, max_length=200)
    correo_admin: str = Field(min_length=3, max_length=254, pattern=EMAIL_PATTERN)
    nombre_admin: str = Field(min_length=2, max_length=120)

    @field_validator("nombre", "nit", "direccion", "nombre_admin")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacio")
        return value

    @field_validator("correo_admin")
    @classmethod
    def _clean_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("telefono")
    @classmethod
    def _clean_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class EmpresaCreateResponse(BaseModel):
    mensaje: str
    empresa_id: UUID
    slug: str
    nombre: str
    nit: str
    estado: str
    admin_usuario_id: UUID
    admin_correo: str
    password_temporal: str


class PlanOut(BaseModel):
    codigo: str
    nombre: str
    precio_mensual: Decimal
    moneda: str
    limites: dict[str, int | None]


class SuscripcionOut(BaseModel):
    id: UUID
    plan: PlanOut
    estado: str
    fecha_inicio: date
    fecha_fin: date | None
    renovacion_auto: bool
    dias_restantes: int | None
    por_vencer: bool
    limites: dict[str, int | None]
    uso: dict[str, int]
    ia_habilitada: bool


class EmpresaResumen(BaseModel):
    id: UUID
    nombre: str
    slug: str
    nit: str
    correo: str
    telefono: str | None
    direccion: str | None
    estado: str
    created_at: datetime
    sucursales_activas: int
    suscripcion: SuscripcionOut | None


class EmpresaListResponse(BaseModel):
    items: list[EmpresaResumen]
    total: int
    page: int
    page_size: int


class MiSuscripcionOut(BaseModel):
    empresa_id: UUID
    empresa_nombre: str
    suscripcion: SuscripcionOut


class SuscripcionUpsertRequest(BaseModel):
    plan_codigo: str = Field(min_length=1, max_length=20)
    fecha_inicio: date
    fecha_fin: date
    estado: SuscripcionEstado = "activa"
    renovacion_auto: bool = False

    @field_validator("plan_codigo")
    @classmethod
    def _clean_plan(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def _validate_dates(self) -> "SuscripcionUpsertRequest":
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("La fecha de vencimiento debe ser posterior a la fecha de inicio")
        return self


class EstadoEmpresaRequest(BaseModel):
    motivo: str | None = Field(default=None, max_length=200)

    @field_validator("motivo")
    @classmethod
    def _clean_motivo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class EstadoEmpresaResponse(BaseModel):
    mensaje: str
    empresa_id: UUID
    estado: str
    suscripcion_estado: str | None


class MetricasSaaSOut(BaseModel):
    total_tenants: int
    empresas_activas: int
    suscripciones_por_vencer: int
    volumen_transaccional: Decimal
    moneda: str = "BOB"
    periodo_inicio: date
    periodo_fin: date
