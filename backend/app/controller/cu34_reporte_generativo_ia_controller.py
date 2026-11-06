from uuid import UUID
from asyncpg import Connection
from app.services import ia_reporte_service
from app.schemas.inteligencia import (
    ExportarReporteRequest,
    ExportarReporteResponse,
    ReporteIaRequest,
    ReporteIaResponse,
)


class CU34ReporteGenerativoIaController:
    """Controlador Backend para el Caso de Uso CU-34:

    Solicitar reporte generativo IA y exportar PDF/Excel (voz/texto).
    """

    @staticmethod
    async def procesar_consulta_ia(
        conn: Connection,
        empresa_id: UUID,
        usuario_id: UUID,
        payload: ReporteIaRequest,
    ) -> ReporteIaResponse:
        return await ia_reporte_service.procesar_reporte_ia(
            conn, empresa_id, usuario_id, payload
        )

    @staticmethod
    async def exportar_documento(
        conn: Connection,
        empresa_id: UUID,
        usuario_id: UUID,
        payload: ExportarReporteRequest,
    ) -> ExportarReporteResponse:
        return await ia_reporte_service.exportar_reporte(
            conn, empresa_id, usuario_id, payload
        )

