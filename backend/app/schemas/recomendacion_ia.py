from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RecomendacionPrendaOut(BaseModel):
    id: UUID
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    categoria_nombre: str
    genero: str
    imagen_url: Optional[str] = None
    tallas_disponibles: List[str] = Field(default_factory=list)
    colores_disponibles: List[str] = Field(default_factory=list)
    rol_en_outfit: str = Field(
        ...,
        description="Superior, Inferior, Calzado, Accesorio o Prenda Principal",
    )
    score_afinidad: int = Field(
        ...,
        ge=0,
        le=100,
        description="Porcentaje de afinidad estilística (0-100%)",
    )
    por_que_combina: str = Field(
        ...,
        description="Explicación del estilista sobre armonía de color, corte y ocasión",
    )


class OutfitRecomendadoResponse(BaseModel):
    titulo_outfit: str = Field(..., description="Nombre del concepto de moda")
    estilo: str = Field(..., description="Categoría de estilo: Smart Casual, Cocktail, etc.")
    ocasion: str = Field(..., description="Ocasión recomendada")
    consejo_estilista_ia: str = Field(
        ...,
        description="Análisis del personal stylist con recomendaciones de uso y accesorios",
    )
    score_total: int = Field(..., ge=0, le=100)
    precio_total: float = Field(..., ge=0)
    prendas: List[RecomendacionPrendaOut] = Field(default_factory=list)
    sugerencia_vestidor_prompt: str = Field(
        ...,
        description="Prompt fotorrealista listo para probar el look completo en Decart Lucy (CU-36)",
    )
    motor_utilizado: str = Field(
        default="gemini-fashion-advisor",
        description="Motor IA (LLM o matriz heurística de alta costura)",
    )


class PromptEstiloRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Petición de estilo o evento en lenguaje natural",
    )
    genero: Optional[str] = Field(
        None,
        description="Filtro opcional: mujer, hombre, unisex, nino",
    )
    ocasion: Optional[str] = Field(None, description="Ocasión opcional")
    empresa_slug: Optional[str] = Field(None, description="Slug del tenant")


class OutfitParaPrendaRequest(BaseModel):
    prenda_id: UUID = Field(..., description="ID de la prenda seleccionada")
    ocasion: Optional[str] = Field(
        None,
        description="Ocasión: casual, noche, oficina, fiesta",
    )
    empresa_slug: Optional[str] = Field(None, description="Slug del tenant")

