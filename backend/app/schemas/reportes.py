from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ReporteFiltrosRequest(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    sucursal_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    limite: int = Field(default=10, ge=1, le=100)


class VentasPeriodoItem(BaseModel):
    periodo: str
    total_transacciones: int
    monto_total: float
    ticket_promedio: float


class VentasPeriodoResponse(BaseModel):
    items: List[VentasPeriodoItem]
    total_general: float
    total_operaciones: int
    ticket_promedio_general: float


class RotacionStockItem(BaseModel):
    prenda_id: UUID
    codigo: str
    nombre: str
    categoria: str
    stock_actual: int
    entradas: int
    salidas: int
    rotacion_ratio: float
    alerta_stock: bool


class RotacionStockResponse(BaseModel):
    items: List[RotacionStockItem]
    prendas_stock_critico: int
    stock_total_unidades: int


class TopPrendasItem(BaseModel):
    ranking: int
    prenda_id: UUID
    codigo: str
    nombre: str
    categoria: str
    cantidad_vendida: int
    total_ingresos: float


class TopPrendasResponse(BaseModel):
    items: List[TopPrendasItem]
    total_prendas_vendidas: int
    total_ingresos_generados: float


class DashboardConvencionalResponse(BaseModel):
    kpis: Dict[str, Any]
    ventas_por_sucursal: List[Dict[str, Any]]
    top_prendas: List[TopPrendasItem]
    rotacion_resumen: Dict[str, Any]
    ventas_tendencia_dias: List[Dict[str, Any]]

