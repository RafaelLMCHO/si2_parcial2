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
    id: int | None = None
    codigo: str
    nombre: str
    precio_mensual: Decimal
    periodo: str = "mensual"
    moneda: str
    activo: bool = True
    limites: dict[str, int | None]


class PlanCreateRequest(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    nombre: str = Field(min_length=2, max_length=60)
    precio_mensual: Decimal | None = Field(default=None, ge=0)
    precio: Decimal | None = Field(default=None, ge=0)
    periodo: Literal["mensual", "anual"] = "mensual"
    moneda: str = Field(default="BOB", min_length=3, max_length=3)
    limites: dict[str, int | None] = Field(default_factory=dict)

    @field_validator("codigo")
    @classmethod
    def _clean_codigo(cls, value: str) -> str:
        clean = value.strip().lower()
        if not clean:
            raise ValueError("El codigo del plan no puede estar vacio")
        return clean

    @field_validator("nombre")
    @classmethod
    def _clean_nombre(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("El nombre del plan no puede estar vacio")
        return clean

    @field_validator("moneda")
    @classmethod
    def _clean_moneda(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("limites")
    @classmethod
    def _validate_limites(cls, value: dict[str, int | None]) -> dict[str, int | None]:
        cleaned: dict[str, int | None] = {}
        for k, v in value.items():
            key = str(k).strip()
            if not key:
                continue
            if v is not None and v < 0:
                raise ValueError(f"El limite '{key}' debe ser mayor o igual a 0")
            cleaned[key] = v
        return cleaned

    @model_validator(mode="after")
    def _resolve_precio(self) -> "PlanCreateRequest":
        if self.precio_mensual is None and self.precio is None:
            self.precio_mensual = Decimal("0.00")
        elif self.precio_mensual is None and self.precio is not None:
            self.precio_mensual = self.precio
        return self


class PlanUpdateRequest(BaseModel):
    codigo: str | None = Field(default=None, min_length=2, max_length=20)
    nombre: str | None = Field(default=None, min_length=2, max_length=60)
    precio_mensual: Decimal | None = Field(default=None, ge=0)
    precio: Decimal | None = Field(default=None, ge=0)
    periodo: Literal["mensual", "anual"] | None = None
    moneda: str | None = Field(default=None, min_length=3, max_length=3)
    activo: bool | None = None
    limites: dict[str, int | None] | None = None

    @field_validator("codigo")
    @classmethod
    def _clean_codigo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip().lower()
        if not clean:
            raise ValueError("El codigo no puede estar vacio")
        return clean

    @field_validator("nombre")
    @classmethod
    def _clean_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        if not clean:
            raise ValueError("El nombre no puede estar vacio")
        return clean

    @field_validator("moneda")
    @classmethod
    def _clean_moneda(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    @field_validator("limites")
    @classmethod
    def _validate_limites(cls, value: dict[str, int | None] | None) -> dict[str, int | None] | None:
        if value is None:
            return None
        cleaned: dict[str, int | None] = {}
        for k, v in value.items():
            key = str(k).strip()
            if not key:
                continue
            if v is not None and v < 0:
                raise ValueError(f"El limite '{key}' debe ser mayor o igual a 0")
            cleaned[key] = v
        return cleaned

    @model_validator(mode="after")
    def _resolve_precio(self) -> "PlanUpdateRequest":
        if self.precio_mensual is None and self.precio is not None:
            self.precio_mensual = self.precio
        return self


class PlanDeleteResponse(BaseModel):
    mensaje: str
    id: int
    codigo: str
    activo: bool


class MiSuscripcionChangeRequest(BaseModel):
    plan_codigo: str | None = Field(default=None, min_length=1, max_length=20)
    plan_id: int | None = Field(default=None, gt=0)
    renovacion_auto: bool | None = None

    @field_validator("plan_codigo")
    @classmethod
    def _clean_plan(cls, value: str | None) -> str | None:
        return value.strip().lower() if value is not None else None

    @model_validator(mode="after")
    def _validate_target(self) -> "MiSuscripcionChangeRequest":
        if not self.plan_codigo and self.plan_id is None:
            raise ValueError("Debe especificar plan_codigo o plan_id")
        return self


class MiSuscripcionCancelRequest(BaseModel):
    motivo: str = Field(
        default="Cancelacion solicitada por el administrador de empresa",
        min_length=3,
        max_length=300,
    )

    @field_validator("motivo")
    @classmethod
    def _clean_motivo(cls, value: str) -> str:
        clean = value.strip()
        if len(clean) < 3:
            raise ValueError("El motivo debe tener al menos 3 caracteres")
        return clean


class MiSuscripcionCancelResponse(BaseModel):
    mensaje: str
    empresa_id: UUID
    suscripcion_id: UUID
    estado: str
    renovacion_auto: bool
    motivo: str


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
    tenants_activos: int | None = None
    usuarios_totales: int | None = None
    sucursales: int | None = None
    mrr: Decimal | None = None
