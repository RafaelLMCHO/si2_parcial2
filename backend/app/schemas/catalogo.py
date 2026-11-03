from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- VARIANTES ---

class VarianteCreateRequest(BaseModel):
    talla_id: int = Field(..., ge=1, description="ID de la talla")
    color_id: int = Field(..., ge=1, description="ID del color")
    sku: str = Field(..., min_length=2, max_length=60, description="Codigo SKU unico dentro de la empresa")
    codigo_barras: str | None = Field(default=None, max_length=80)
    precio_venta: Decimal = Field(..., ge=0, description="Precio de venta al publico")
    costo: Decimal = Field(default=Decimal("0.00"), ge=0, description="Costo de adquisicion/produccion")


class VarianteUpdateRequest(BaseModel):
    talla_id: int | None = Field(default=None, ge=1)
    color_id: int | None = Field(default=None, ge=1)
    sku: str | None = Field(default=None, min_length=2, max_length=60)
    codigo_barras: str | None = Field(default=None, max_length=80)
    precio_venta: Decimal | None = Field(default=None, ge=0)
    costo: Decimal | None = Field(default=None, ge=0)
    estado: str | None = Field(default=None, pattern="^(activa|inactiva)$")


class VarianteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prenda_id: UUID
    talla_id: int
    talla_nombre: str | None = None
    color_id: int
    color_nombre: str | None = None
    color_hex: str | None = None
    sku: str
    codigo_barras: str | None = None
    precio_venta: Decimal
    costo: Decimal
    estado: str
    created_at: datetime
    updated_at: datetime


# --- PRENDAS ---

class PrendaCreateRequest(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50, description="Codigo interno de estilo o referencia")
    nombre: str = Field(..., min_length=2, max_length=160)
    descripcion: str | None = Field(default=None)
    marca: str | None = Field(default=None, max_length=80)
    genero: str = Field(default="unisex", pattern="^(mujer|hombre|nino|unisex)$")
    precio_base: Decimal = Field(..., ge=0, description="Precio base de referencia")
    categoria_id: UUID = Field(...)
    temporada_id: UUID | None = Field(default=None)
    coleccion_id: UUID | None = Field(default=None)
    proveedor_id: UUID | None = Field(default=None)
    imagen_url: str | None = Field(default=None, max_length=255)
    variantes: list[VarianteCreateRequest] = Field(default_factory=list, description="Variantes SKU iniciales")


class PrendaUpdateRequest(BaseModel):
    codigo: str | None = Field(default=None, min_length=2, max_length=50)
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    descripcion: str | None = Field(default=None)
    marca: str | None = Field(default=None, max_length=80)
    genero: str | None = Field(default=None, pattern="^(mujer|hombre|nino|unisex)$")
    precio_base: Decimal | None = Field(default=None, ge=0)
    categoria_id: UUID | None = Field(default=None)
    temporada_id: UUID | None = Field(default=None)
    coleccion_id: UUID | None = Field(default=None)
    proveedor_id: UUID | None = Field(default=None)
    imagen_url: str | None = Field(default=None, max_length=255)
    estado: str | None = Field(default=None, pattern="^(activa|inactiva|descontinuada)$")


class PrendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: str | None = None
    marca: str | None = None
    genero: str
    precio_base: Decimal
    moneda: str
    categoria_id: UUID
    categoria_nombre: str | None = None
    temporada_id: UUID | None = None
    temporada_nombre: str | None = None
    coleccion_id: UUID | None = None
    coleccion_nombre: str | None = None
    proveedor_id: UUID | None = None
    proveedor_nombre: str | None = None
    imagen_url: str | None = None
    estado: str
    created_at: datetime
    updated_at: datetime
    variantes: list[VarianteOut] = Field(default_factory=list)


class PrendaListResponse(BaseModel):
    total: int
    version_catalogo: int
    items: list[PrendaOut]


# --- AUXILIARES (Filtros CU-14) ---

class ItemSimple(BaseModel):
    id: int | str
    nombre: str
    extra: str | None = None


class AuxiliaresCatalogoResponse(BaseModel):
    categorias: list[ItemSimple]
    colores: list[ItemSimple]
    tallas: list[ItemSimple]
    temporadas: list[ItemSimple]
    colecciones: list[ItemSimple]

