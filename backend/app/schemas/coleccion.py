from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.errors import api_error


class TemporadaCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=80, description="Ej: Primavera-Verano 2026")
    fecha_inicio: date | None = Field(default=None)
    fecha_fin: date | None = Field(default=None)

    @model_validator(mode="after")
    def validate_dates(self) -> "TemporadaCreateRequest":
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio >= self.fecha_fin:
                raise ValueError("La fecha de inicio debe ser anterior a la fecha de finalizacion")
        return self


class TemporadaUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    fecha_inicio: date | None = Field(default=None)
    fecha_fin: date | None = Field(default=None)

    @model_validator(mode="after")
    def validate_dates(self) -> "TemporadaUpdateRequest":
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio >= self.fecha_fin:
                raise ValueError("La fecha de inicio debe ser anterior a la fecha de finalizacion")
        return self


class TemporadaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    nombre: str
    fecha_inicio: date | None
    fecha_fin: date | None
    created_at: datetime
    updated_at: datetime


class ColeccionCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=80, description="Ej: Denim Urbano")
    anio: int | None = Field(default=None, ge=1900, le=2200)


class ColeccionUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    anio: int | None = Field(default=None, ge=1900, le=2200)


class ColeccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    nombre: str
    anio: int | None
    created_at: datetime
    updated_at: datetime


class TemporadasColeccionesResponse(BaseModel):
    temporadas: list[TemporadaOut]
    colecciones: list[ColeccionOut]

