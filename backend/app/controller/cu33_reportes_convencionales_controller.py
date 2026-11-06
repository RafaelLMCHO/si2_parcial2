from datetime import date
from typing import Optional
from uuid import UUID
from asyncpg import Connection
from app.services import reporte_service
from app.schemas.reportes import (
    DashboardConvencionalResponse,
    RotacionStockResponse,
    TopPrendasResponse,
    VentasPeriodoResponse,
)


class CU33ReportesConvencionalesController:
    """Controlador Backend para el Caso de Uso CU-33:

    Generar reportes y dashboards convencionales (Básico y Profesional).
    """

    @staticmethod
    async def obtener_dashboard(
        conn: Connection,
        empresa_id: UUID,
    ) -> DashboardConvencionalResponse:
        return await reporte_service.obtener_dashboard_convencional(conn, empresa_id)

    @staticmethod
    async def consultar_ventas_periodo(
        conn: Connection,
        empresa_id: UUID,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        sucursal_id: Optional[UUID] = None,
    ) -> VentasPeriodoResponse:
        return await reporte_service.obtener_ventas_periodo(
            conn, empresa_id, fecha_inicio, fecha_fin, sucursal_id
        )

    @staticmethod
    async def consultar_rotacion_stock(
        conn: Connection,
        empresa_id: UUID,
        categoria_id: Optional[UUID] = None,
        sucursal_id: Optional[UUID] = None,
    ) -> RotacionStockResponse:
        return await reporte_service.obtener_rotacion_stock(
            conn, empresa_id, categoria_id, sucursal_id
        )

    @staticmethod
    async def consultar_top_prendas(
        conn: Connection,
        empresa_id: UUID,
        limite: int = 10,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> TopPrendasResponse:
        return await reporte_service.obtener_top_prendas(
            conn, empresa_id, limite, fecha_inicio, fecha_fin
        )

