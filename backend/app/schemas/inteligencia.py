from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CU-34: Reporte Generativo con IA y Whitelist
# ---------------------------------------------------------------------------

class ReporteIaRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=1000)
    canal: str = Field(default="texto", pattern="^(texto|voz)$")
    audio_base64: Optional[str] = None


class ReporteIaResponse(BaseModel):
    consulta_id: UUID
    prompt_recibido: str
    tipo_reporte: str
    titulo: str
    resumen_ejecutivo: str
    kpis: Dict[str, Any]
    columnas: List[str]
    filas: List[Dict[str, Any]]
    tipo_grafico: str  # 'barras' | 'lineas' | 'torta' | 'tabla'
    datos_grafico: Dict[str, Any]
    parametros_aplicados: Dict[str, Any]
    sugerencias: List[str]
    permitido_exportar: bool = True


class ExportarReporteRequest(BaseModel):
    consulta_id: Optional[UUID] = None
    tipo_reporte: str
    formato: str = Field(default="xlsx", pattern="^(xlsx|pdf|csv)$")
    titulo: str
    resumen: Optional[str] = None
    columnas: List[str]
    filas: List[Dict[str, Any]]
    parametros: Optional[Dict[str, Any]] = None


class ExportarReporteResponse(BaseModel):
    reporte_id: UUID
    tipo_reporte: str
    formato: str
    archivo_url: str
    tamano_bytes: int
    generado_en: datetime
    contenido_base64: Optional[str] = None


# ---------------------------------------------------------------------------
# CU-35: Dashboard Analítico Machine Learning & TTS
# ---------------------------------------------------------------------------

class DemandaPrediccionItem(BaseModel):
    categoria_id: Optional[UUID] = None
    categoria_nombre: str
    periodo: str
    demanda_estimada: float
    intervalo_inferior: float
    intervalo_superior: float
    tendencia: str  # 'creciente' | 'estable' | 'decreciente'


class DemandaPrediccionResponse(BaseModel):
    modelo_nombre: str = "Regresion Demanda Textil"
    version: str = "2.0"
    metricas: Dict[str, Any]
    predicciones: List[DemandaPrediccionItem]


class SegmentoClienteItem(BaseModel):
    segmento_id: int
    nombre: str
    descripcion: str
    cantidad_clientes: int
    porcentaje_base: float
    ticket_promedio: float
    frecuencia_promedio: float
    estrategia_recomendada: str


class SegmentacionClientesResponse(BaseModel):
    modelo_nombre: str = "K-Means RFM Segmenter"
    version: str = "2.0"
    metricas: Dict[str, Any]
    total_clientes_analizados: int
    segmentos: List[SegmentoClienteItem]


class DashboardMlResponse(BaseModel):
    prediccion_demanda: DemandaPrediccionResponse
    segmentacion_clientes: SegmentacionClientesResponse
    sintesis_ejecutiva: str
    audio_tts_url: Optional[str] = None
    tiene_audio: bool = True


class SintesisTtsRequest(BaseModel):
    texto: str = Field(..., min_length=2, max_length=2000)
    voz: str = "es-ES-Standard-A"


class SintesisTtsResponse(BaseModel):
    texto: str
    audio_base64: str
    mime_type: str = "audio/wav"
    duracion_estimada_segundos: float


# ---------------------------------------------------------------------------
# CU-36: Vestidor Virtual con Realidad Aumentada (RA)
# ---------------------------------------------------------------------------

class PrendaArResponse(BaseModel):
    id: UUID
    prenda_id: UUID
    codigo_prenda: str
    nombre_prenda: str
    marca: Optional[str] = None
    categoria: Optional[str] = None
    modelo_url: str
    textura_url: Optional[str] = None
    puntos_ajuste: Dict[str, Any]
    talla_referencia: Optional[str] = None
    activo: bool


class AvatarClienteDto(BaseModel):
    id: UUID
    usuario_id: UUID
    nombre: str
    modelo_url: Optional[str] = None
    altura_cm: Optional[float] = None
    peso_kg: Optional[float] = None
    tono_piel: Optional[str] = None
    medidas: Dict[str, float] = {}


class IniciarSesionArRequest(BaseModel):
    prenda_id: UUID
    variante_id: Optional[UUID] = None
    avatar_id: Optional[UUID] = None


class IniciarSesionArResponse(BaseModel):
    sesion_id: UUID
    prenda_ar: PrendaArResponse
    avatar: Optional[AvatarClienteDto] = None
    estado: str
    iniciada_en: datetime


class FinalizarSesionArRequest(BaseModel):
    estado: str = Field(default="completada", pattern="^(completada|abandonada|fallida)$")
    resultado_url: Optional[str] = None

