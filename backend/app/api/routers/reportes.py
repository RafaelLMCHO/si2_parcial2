from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import Response

from app.api.deps import CurrentUser, get_conn, require_permission
from app.schemas.inteligencia import (
    ExportarReporteRequest,
    ExportarReporteResponse,
    ReporteIaRequest,
    ReporteIaResponse,
)
from app.schemas.reportes import (
    DashboardConvencionalResponse,
    RotacionStockResponse,
    TopPrendasResponse,
    VentasPeriodoResponse,
)
from app.services import ia_reporte_service, reporte_service

router = APIRouter(prefix="/reportes", tags=["Reportes e Inteligencia"])


# ---------------------------------------------------------------------------
# CU-33: Reportes Convencionales
# ---------------------------------------------------------------------------

@router.get("/convencionales/dashboard", response_model=DashboardConvencionalResponse)
async def get_dashboard_convencional(
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-33: Obtiene el panel consolidado con KPIs, ventas por sucursal y rotación."""
    return await reporte_service.obtener_dashboard_convencional(conn, user.empresa_id)


@router.get("/convencionales/ventas", response_model=VentasPeriodoResponse)
async def get_ventas_periodo(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    sucursal_id: Optional[UUID] = Query(None),
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-33: Ventas agrupadas por período con filtros opcionales."""
    return await reporte_service.obtener_ventas_periodo(
        conn, user.empresa_id, fecha_inicio, fecha_fin, sucursal_id
    )


@router.get("/convencionales/rotacion", response_model=RotacionStockResponse)
async def get_rotacion_stock(
    categoria_id: Optional[UUID] = Query(None),
    sucursal_id: Optional[UUID] = Query(None),
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-33: Rotación de existencias y alertas de inventario crítico."""
    return await reporte_service.obtener_rotacion_stock(
        conn, user.empresa_id, categoria_id, sucursal_id
    )


@router.get("/convencionales/top-prendas", response_model=TopPrendasResponse)
async def get_top_prendas(
    limite: int = Query(10, ge=1, le=50),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-33: Ranking de las prendas más demandadas y vendidas."""
    return await reporte_service.obtener_top_prendas(
        conn, user.empresa_id, limite, fecha_inicio, fecha_fin
    )


# ---------------------------------------------------------------------------
# CU-34: Reportes Generativos con IA (Whitelist segura y Exportación)
# ---------------------------------------------------------------------------

@router.post("/ia/consultar", response_model=ReporteIaResponse)
async def solicitar_reporte_ia(
    payload: ReporteIaRequest,
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-34: Procesa consulta en lenguaje natural (texto/voz) bajo whitelist segura (BR-08) y Plan Pro (BR-03)."""
    return await ia_reporte_service.procesar_reporte_ia(
        conn, user.empresa_id, user.user_id, payload
    )


@router.post("/ia/exportar", response_model=ExportarReporteResponse)
async def exportar_reporte_dinamico(
    payload: ExportarReporteRequest,
    user: CurrentUser = Depends(require_permission("reportes:exportar")),
    conn=Depends(get_conn),
):
    """CU-34: Ensambla y descarga binario dinámico en formato Excel (.xlsx) o PDF (.pdf)."""
    return await ia_reporte_service.exportar_reporte(
        conn, user.empresa_id, user.user_id, payload
    )

